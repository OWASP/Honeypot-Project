#!/usr/bin/env python3
"""
MISP exporter for honeypot attack events.

Reads structured JSON events produced by the v1.1 schema Logstash pipeline
and pushes them to a MISP instance via PyMISP.

Two modes:
  batch     -- reads a JSON file of events and pushes all of them in one go
  realtime  -- watches a log file line by line and pushes only events that
               have severity CRITICAL or HIGH (i.e. high-severity only)

Usage:
    # Batch mode
    python misp_exporter.py --mode batch --input /path/to/events.json \
        --url https://misp.example.com --key YOUR_MISP_KEY

    # Real-time mode (tail a Logstash output file)
    python misp_exporter.py --mode realtime --input /var/log/honeypot/events.json \
        --url https://misp.example.com --key YOUR_MISP_KEY

    # Skip TLS verification for local/dev MISP instances
    python misp_exporter.py --mode batch --input events.json \
        --url https://localhost --key YOUR_KEY --no-verify
"""

import argparse
import json
import logging
import sys
import time

try:
    from pymisp import PyMISP, MISPEvent, MISPAttribute
except ImportError:
    sys.exit(
        "pymisp is not installed. Run: pip install pymisp==2.4.187"
    )

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
    level=logging.INFO,
)
log = logging.getLogger(__name__)

# Severities that qualify for real-time push.
REALTIME_SEVERITIES = {"CRITICAL", "HIGH"}

# MISP distribution level: 0 = Your organisation only.
# Adjust to 1 (community) or 2 (connected) before production use.
DEFAULT_DISTRIBUTION = 0

# MISP threat level: 1 = High, 2 = Medium, 3 = Low, 4 = Undefined.
THREAT_LEVEL_MAP = {
    "CRITICAL": 1,
    "HIGH": 2,
    "MEDIUM": 3,
    "LOW": 3,
}

# MISP analysis level: 0 = Initial, 1 = Ongoing, 2 = Completed.
DEFAULT_ANALYSIS = 0


def connect(url, key, verify_tls):
    """Return an authenticated PyMISP instance."""
    log.info("Connecting to MISP at %s", url)
    try:
        misp = PyMISP(url, key, ssl=verify_tls)
    except Exception as exc:
        sys.exit("Could not connect to MISP: %s" % exc)

    # Warn clearly if the MISP version is outside the tested range so
    # operators aren't surprised by API differences at runtime.
    try:
        version = misp.get_version()
        log.info("MISP version: %s", version.get("version", "unknown"))
        major = int(version.get("version", "0.0.0").split(".")[0])
        if major < 2:
            log.warning(
                "MISP version %s is below the tested range (>=2.5). "
                "Some API calls may not work as expected.",
                version.get("version"),
            )
    except Exception:
        log.warning("Could not retrieve MISP version info.")

    return misp


def build_misp_event(event):
    """
    Build a MISPEvent from a single v1.1 schema event dict.

    The event dict is expected to match the JSON schema defined in the
    project docs. Missing optional fields are handled gracefully.
    """
    envelope = event.get("event_envelope", {})
    attack = event.get("attack_classification", {})
    geoip = event.get("geoip2", {})
    request = event.get("request", {})
    persona = event.get("persona_context", {})
    mitre = event.get("mitre_attack", [])

    severity = attack.get("severity", "LOW").upper()
    threat_level = THREAT_LEVEL_MAP.get(severity, 4)

    info_str = (
        "[Honeypot] {attack_type} | {persona} | {region} | {ts}".format(
            attack_type=attack.get("type", "Unknown"),
            persona=persona.get("name", "unknown"),
            region=envelope.get("aws_region", "unknown"),
            ts=envelope.get("timestamp", ""),
        )
    )

    misp_event = MISPEvent()
    misp_event.info = info_str
    misp_event.distribution = DEFAULT_DISTRIBUTION
    misp_event.threat_level_id = threat_level
    misp_event.analysis = DEFAULT_ANALYSIS

    # Add tags for severity, persona profile, and MITRE techniques.
    misp_event.add_tag("honeypot:severity=\"%s\"" % severity)
    misp_event.add_tag(
        "honeypot:profile=\"%s\"" % persona.get("profile", "general")
    )
    for technique in mitre:
        misp_event.add_tag("mitre-attack:technique=\"%s\"" % technique)

    if attack.get("cve_triggered"):
        misp_event.add_tag(
            "honeypot:cve=\"%s\"" % attack["cve_triggered"]
        )

    # Core attributes.
    src_ip = event.get("transaction", {}).get("remote_address")
    if src_ip:
        misp_event.add_attribute("ip-src", src_ip)

    request_line = request.get("request_line", "")
    if request_line:
        misp_event.add_attribute("text", request_line, comment="request line")

    node_ip = envelope.get("honeypot_ip")
    if node_ip:
        misp_event.add_attribute(
            "ip-dst", node_ip, comment="honeypot node IP"
        )

    if geoip.get("country"):
        misp_event.add_attribute(
            "text",
            "country=%s asn=%s isp=%s" % (
                geoip.get("country", ""),
                geoip.get("asn", ""),
                geoip.get("isp", ""),
            ),
            comment="GeoIP2 enrichment",
        )

    cve = attack.get("cve_triggered")
    if cve:
        misp_event.add_attribute("vulnerability", cve)

    # Raw event as a free-text attribute so nothing is lost.
    misp_event.add_attribute(
        "text",
        json.dumps(event, indent=2),
        comment="raw honeypot event (v1.1 schema)",
    )

    return misp_event


def push_event(misp, event):
    """Push a single v1.1 event dict to MISP. Returns True on success."""
    try:
        misp_event = build_misp_event(event)
        result = misp.add_event(misp_event)
        if "Event" in result:
            log.info(
                "Pushed event id=%s info=%s",
                result["Event"].get("id"),
                result["Event"].get("info"),
            )
            return True
        log.error("Unexpected MISP response: %s", result)
        return False
    except Exception as exc:
        log.error("Failed to push event: %s", exc)
        return False


def run_batch(misp, input_path):
    """Read all events from a JSON file and push each one to MISP."""
    try:
        with open(input_path, "r") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        sys.exit("Could not read input file %s: %s" % (input_path, exc))

    events = data if isinstance(data, list) else [data]
    log.info("Batch mode: loaded %d event(s) from %s", len(events), input_path)

    pushed = 0
    failed = 0
    for ev in events:
        if push_event(misp, ev):
            pushed += 1
        else:
            failed += 1

    log.info("Batch complete. pushed=%d failed=%d", pushed, failed)


def run_realtime(misp, input_path):
    """
    Tail input_path line by line. Each line must be a self-contained JSON
    object (Logstash JSON codec output). Only events with severity CRITICAL
    or HIGH are forwarded to MISP immediately.
    """
    log.info("Real-time mode: watching %s (CRITICAL/HIGH only)", input_path)
    try:
        fh = open(input_path, "r")
    except OSError as exc:
        sys.exit("Could not open input file %s: %s" % (input_path, exc))

    # Seek to the end so we only pick up new events, not historical ones.
    fh.seek(0, 2)

    while True:
        line = fh.readline()
        if not line:
            time.sleep(1)
            continue
        line = line.strip()
        if not line:
            continue
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            log.warning("Skipping non-JSON line: %s", line[:120])
            continue

        severity = (
            ev.get("attack_classification", {}).get("severity", "").upper()
        )
        if severity not in REALTIME_SEVERITIES:
            continue

        push_event(misp, ev)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Push honeypot events to MISP (batch or real-time)."
    )
    parser.add_argument(
        "--mode",
        choices=["batch", "realtime"],
        required=True,
        help="batch: push all events from a file. realtime: tail a file and push high-severity events.",
    )
    parser.add_argument(
        "--input",
        required=True,
        metavar="FILE",
        help="Path to the JSON events file.",
    )
    parser.add_argument(
        "--url",
        required=True,
        metavar="URL",
        help="Base URL of the MISP instance (e.g. https://misp.example.com).",
    )
    parser.add_argument(
        "--key",
        required=True,
        metavar="API_KEY",
        help="MISP automation key.",
    )
    parser.add_argument(
        "--no-verify",
        action="store_true",
        default=False,
        help="Disable TLS certificate verification (for local/dev instances only).",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    misp = connect(args.url, args.key, verify_tls=not args.no_verify)

    if args.mode == "batch":
        run_batch(misp, args.input)
    else:
        run_realtime(misp, args.input)


if __name__ == "__main__":
    main()
