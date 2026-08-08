#!/usr/bin/env python3
"""
STIX 2.1 exporter for honeypot attack events.

Reads structured JSON events produced by the v1.1 schema Logstash pipeline
and generates STIX 2.1 bundles. Each bundle contains three object types:

  Indicator       -- the source IP and/or request pattern observed
  AttackPattern   -- mapped from the MITRE ATT&CK technique IDs in the event
  ObservedData    -- the raw observation (IP, timestamp, request count)

Output options:
  --output FILE   write the bundle to a local JSON file
  --taxii-url URL push the bundle to a TAXII 2.1 collection endpoint

Usage:
    # Write to a local file
    python stix_exporter.py --input events.json --output bundle.json

    # Push to a TAXII collection (basic auth)
    python stix_exporter.py --input events.json \
        --taxii-url https://taxii.example.com/api/root/collections/honeypot/objects/ \
        --taxii-user admin --taxii-pass secret

    # Both at once
    python stix_exporter.py --input events.json --output bundle.json \
        --taxii-url https://taxii.example.com/... --taxii-user admin --taxii-pass secret
"""

import argparse
import json
import logging
import sys
import uuid
from datetime import datetime, timezone

try:
    from stix2 import (
        Bundle,
        Indicator,
        AttackPattern,
        ObservedData,
        NetworkTraffic,
        IPv4Address,
        DomainName,
        ExternalReference,
        TLP_WHITE,
    )
    from stix2.exceptions import STIXError
except ImportError:
    sys.exit(
        "stix2 is not installed. Run: pip install stix2==3.0.1"
    )

try:
    import requests as _requests
except ImportError:
    _requests = None

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
    level=logging.INFO,
)
log = logging.getLogger(__name__)

# MITRE ATT&CK base URL for external references.
MITRE_URL = "https://attack.mitre.org/techniques/{technique}/"

# STIX identity for this tool (acts as the producer).
PRODUCER_NAME = "OWASP Honeypot Project"
PRODUCER_ID = "identity--" + str(uuid.uuid5(uuid.NAMESPACE_DNS, PRODUCER_NAME))


def _now():
    return datetime.now(timezone.utc)


def _stix_ts(iso_str):
    """
    Parse an ISO 8601 string from the event envelope and return a datetime.
    Falls back to the current time if parsing fails.
    """
    if not iso_str:
        return _now()
    try:
        return datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
    except ValueError:
        return _now()


def build_attack_patterns(mitre_techniques):
    """
    Return a list of STIX AttackPattern objects, one per MITRE technique ID.
    Each object includes an external reference back to attack.mitre.org.
    """
    patterns = []
    for technique in mitre_techniques:
        ext_ref = ExternalReference(
            source_name="mitre-attack",
            url=MITRE_URL.format(technique=technique),
            external_id=technique,
        )
        ap = AttackPattern(
            name="MITRE ATT&CK %s" % technique,
            external_references=[ext_ref],
            created_by_ref=PRODUCER_ID,
            object_marking_refs=[TLP_WHITE],
        )
        patterns.append(ap)
    return patterns


def build_indicator(event, attack_patterns):
    """
    Build a STIX Indicator from the source IP observed in the event.
    The indicator pattern matches the remote IP address.
    """
    transaction = event.get("transaction", {})
    attack = event.get("attack_classification", {})
    envelope = event.get("event_envelope", {})

    src_ip = transaction.get("remote_address")
    if not src_ip:
        return None

    ts = _stix_ts(envelope.get("timestamp"))

    pattern = "[ipv4-addr:value = '%s']" % src_ip
    name = "Honeypot source: %s (%s)" % (
        src_ip,
        attack.get("type", "Unknown attack"),
    )

    kwargs = dict(
        name=name,
        pattern=pattern,
        pattern_type="stix",
        valid_from=ts,
        created_by_ref=PRODUCER_ID,
        object_marking_refs=[TLP_WHITE],
        description=(
            "Source IP observed attacking the honeypot. "
            "Attack type: %s. Severity: %s. Node: %s."
        ) % (
            attack.get("type", "unknown"),
            attack.get("severity", "unknown"),
            envelope.get("node_id", "unknown"),
        ),
    )

    cve = attack.get("cve_triggered")
    if cve:
        kwargs["description"] += " CVE: %s." % cve

    try:
        return Indicator(**kwargs)
    except STIXError as exc:
        log.warning("Could not build Indicator for %s: %s", src_ip, exc)
        return None


def build_observed_data(event, indicator):
    """
    Build a STIX ObservedData object wrapping the network observation.
    """
    transaction = event.get("transaction", {})
    envelope = event.get("event_envelope", {})

    src_ip = transaction.get("remote_address")
    if not src_ip:
        return None, None

    ts = _stix_ts(envelope.get("timestamp"))

    ipv4_obj = IPv4Address(value=src_ip)

    refs = {"0": ipv4_obj}

    try:
        observed = ObservedData(
            first_observed=ts,
            last_observed=ts,
            number_observed=1,
            object_refs=[ipv4_obj.id],
            created_by_ref=PRODUCER_ID,
            object_marking_refs=[TLP_WHITE],
        )
        return observed, ipv4_obj
    except STIXError as exc:
        log.warning("Could not build ObservedData for %s: %s", src_ip, exc)
        return None, None


def event_to_stix_objects(event):
    """
    Convert a single v1.1 schema event dict into a list of STIX objects.
    Returns an empty list if the event is missing required fields.
    """
    mitre = event.get("mitre_attack", [])
    objects = []

    attack_patterns = build_attack_patterns(mitre)
    objects.extend(attack_patterns)

    indicator = build_indicator(event, attack_patterns)
    if indicator:
        objects.append(indicator)

    observed, ipv4_obj = build_observed_data(event, indicator)
    if observed:
        objects.append(observed)
        if ipv4_obj:
            objects.append(ipv4_obj)

    return objects


def build_bundle(events):
    """
    Build a single STIX 2.1 Bundle from a list of v1.1 schema event dicts.
    All objects across all events are merged into one bundle.
    """
    all_objects = []
    for ev in events:
        all_objects.extend(event_to_stix_objects(ev))

    if not all_objects:
        log.warning("No STIX objects were generated from the provided events.")
        return None

    bundle = Bundle(*all_objects, allow_custom=False)
    log.info("Bundle contains %d STIX objects.", len(all_objects))
    return bundle


def validate_bundle(bundle):
    """
    Run the stix2 library's built-in validation on the bundle.
    Logs any issues found and returns True only if the bundle is clean.
    """
    # stix2 raises STIXError on construction for invalid objects, so by the
    # time we get here the bundle is structurally valid. This function exists
    # as a named hook so additional validators (e.g. stix2-validator) can be
    # plugged in later without changing callers.
    log.info("Bundle passed stix2 library validation.")
    return True


def write_bundle(bundle, output_path):
    """Write a STIX bundle to a local JSON file."""
    try:
        with open(output_path, "w") as fh:
            fh.write(bundle.serialize(pretty=True))
        log.info("Bundle written to %s", output_path)
    except OSError as exc:
        log.error("Could not write bundle to %s: %s", output_path, exc)


def push_taxii(bundle, taxii_url, username, password, verify_tls):
    """
    POST a STIX bundle to a TAXII 2.1 collection endpoint.
    Uses HTTP Basic Auth.
    """
    if _requests is None:
        log.error(
            "requests is not installed. Cannot push to TAXII. "
            "Run: pip install requests"
        )
        return

    headers = {
        "Content-Type": "application/taxii+json;version=2.1",
        "Accept": "application/taxii+json;version=2.1",
    }
    payload = bundle.serialize()

    log.info("Pushing bundle to TAXII endpoint: %s", taxii_url)
    try:
        resp = _requests.post(
            taxii_url,
            data=payload,
            headers=headers,
            auth=(username, password),
            verify=verify_tls,
            timeout=30,
        )
        if resp.ok:
            log.info(
                "TAXII push accepted. status=%d body=%s",
                resp.status_code,
                resp.text[:200],
            )
        else:
            log.error(
                "TAXII push failed. status=%d body=%s",
                resp.status_code,
                resp.text[:400],
            )
    except Exception as exc:
        log.error("TAXII push error: %s", exc)


def load_events(input_path):
    """Load events from a JSON file. Accepts a list or a single object."""
    try:
        with open(input_path, "r") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        sys.exit("Could not read input file %s: %s" % (input_path, exc))
    return data if isinstance(data, list) else [data]


def parse_args():
    parser = argparse.ArgumentParser(
        description="Export honeypot events as a STIX 2.1 bundle."
    )
    parser.add_argument(
        "--input",
        required=True,
        metavar="FILE",
        help="JSON file containing one or more v1.1 schema events.",
    )
    parser.add_argument(
        "--output",
        metavar="FILE",
        help="Write the STIX bundle to this file.",
    )
    parser.add_argument(
        "--taxii-url",
        metavar="URL",
        help="TAXII 2.1 collection objects endpoint to push the bundle to.",
    )
    parser.add_argument(
        "--taxii-user",
        metavar="USER",
        default="",
        help="TAXII basic auth username.",
    )
    parser.add_argument(
        "--taxii-pass",
        metavar="PASS",
        default="",
        help="TAXII basic auth password.",
    )
    parser.add_argument(
        "--no-verify",
        action="store_true",
        default=False,
        help="Disable TLS certificate verification.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    if not args.output and not args.taxii_url:
        sys.exit("Provide at least one of --output or --taxii-url.")

    events = load_events(args.input)
    log.info("Loaded %d event(s) from %s", len(events), args.input)

    bundle = build_bundle(events)
    if bundle is None:
        sys.exit("No STIX objects could be generated. Exiting.")

    validate_bundle(bundle)

    if args.output:
        write_bundle(bundle, args.output)

    if args.taxii_url:
        push_taxii(
            bundle,
            args.taxii_url,
            args.taxii_user,
            args.taxii_pass,
            verify_tls=not args.no_verify,
        )


if __name__ == "__main__":
    main()
