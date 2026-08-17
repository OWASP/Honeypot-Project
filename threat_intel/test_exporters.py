#!/usr/bin/env python3
"""
End-to-end test suite for the threat_intel exporters.

Tests run without a live MISP instance or TAXII server. All network
calls are skipped; what gets tested is all the logic that actually runs
in production: parsing, object construction, validation, file I/O,
severity filtering, and edge-case handling.

Run from the threat_intel directory:
    python3 test_exporters.py
"""

import json
import os
import sys
import tempfile
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

PASS = "\033[92mPASS\033[0m"
FAIL = "\033[91mFAIL\033[0m"

_results = []


def test(name):
    """Decorator that registers and runs a test function."""
    def decorator(fn):
        try:
            fn()
            _results.append((name, True, None))
            print("[%s] %s" % (PASS, name))
        except Exception as exc:
            _results.append((name, False, exc))
            print("[%s] %s" % (FAIL, name))
            traceback.print_exc()
        return fn
    return decorator


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

FULL_EVENT = {
    "event_type": "attack",
    "event_envelope": {
        "version": "1.1",
        "timestamp": "2026-08-08T04:30:00Z",
        "node_id": "honeypot-node-aws-eu-west-1",
        "honeypot_ip": "54.72.134.201",
        "aws_region": "eu-west-1",
    },
    "persona_context": {"name": "apache-2.2-php5", "profile": "education/research"},
    "attack_classification": {
        "type": "XSS",
        "severity": "CRITICAL",
        "honeytrap_triggered": True,
        "honeytrap_rule_id": "9500001",
        "cve_triggered": "CVE-2012-1823",
    },
    "mitre_attack": ["T1190", "T1059.007"],
    "geoip2": {
        "country": "IN",
        "city": "Mumbai",
        "asn": "AS13335",
        "isp": "Cloudflare Inc.",
        "latitude": 19.076,
        "longitude": 72.8777,
    },
    "transaction": {
        "time": "2026-08-08T04:30:00Z",
        "transaction_id": "XNWg7dIVjbnaIo0jT3v1-wAAIA",
        "remote_address": "203.0.113.42",
        "remote_port": 56224,
        "local_address": "54.72.134.201",
        "local_port": 80,
    },
    "request": {
        "request_line": "GET /?q=<script>alert(1)</script> HTTP/1.1",
        "headers": {"Host": "54.72.134.201", "User-Agent": "Mozilla/5.0"},
    },
    "response": {
        "protocol": "HTTP/1.1",
        "status": 403,
        "honeytoken_triggered": False,
        "headers": {"Content-Type": "text/html; charset=iso-8859-1"},
    },
    "feed_metadata": {
        "batch_id": "batch-2026-08-08-001",
        "export_timestamp": "2026-08-08T04:35:00Z",
    },
}

# Event missing optional fields to test graceful handling.
MINIMAL_EVENT = {
    "event_type": "attack",
    "event_envelope": {
        "version": "1.1",
        "timestamp": "2026-08-08T05:00:00Z",
        "node_id": "honeypot-node-aws-us-east-1",
        "aws_region": "us-east-1",
    },
    "attack_classification": {"type": "SQLi", "severity": "HIGH"},
    "mitre_attack": ["T1190"],
    "transaction": {"remote_address": "198.51.100.7"},
}

# Event with no source IP at all.
NO_IP_EVENT = {
    "event_type": "attack",
    "event_envelope": {"version": "1.1", "timestamp": "2026-08-08T06:00:00Z"},
    "attack_classification": {"type": "LFI", "severity": "MEDIUM"},
    "mitre_attack": [],
    "transaction": {},
}


# ---------------------------------------------------------------------------
# STIX exporter tests
# ---------------------------------------------------------------------------

from exporters.stix_exporter import (
    build_attack_patterns,
    build_indicator,
    build_observed_data,
    build_bundle,
    validate_bundle,
    load_events,
    write_bundle,
    event_to_stix_objects,
    meets_min_severity as stix_meets_min_severity,
    filter_by_severity,
)


@test("STIX: two AttackPattern objects built for two MITRE technique IDs")
def _():
    patterns = build_attack_patterns(["T1190", "T1059.007"])
    assert len(patterns) == 2, "expected 2 patterns, got %d" % len(patterns)
    names = [p.name for p in patterns]
    assert "MITRE ATT&CK T1190" in names
    assert "MITRE ATT&CK T1059.007" in names


@test("STIX: external references on AttackPattern point to attack.mitre.org")
def _():
    patterns = build_attack_patterns(["T1190"])
    ref = patterns[0].external_references[0]
    assert "attack.mitre.org" in ref.url
    assert ref.external_id == "T1190"


@test("STIX: Indicator built from full event has correct IP pattern")
def _():
    indicator = build_indicator(FULL_EVENT, [])
    assert indicator is not None
    assert "203.0.113.42" in indicator.pattern


@test("STIX: Indicator description includes CVE when present")
def _():
    indicator = build_indicator(FULL_EVENT, [])
    assert "CVE-2012-1823" in indicator.description


@test("STIX: Indicator returns None when source IP is missing")
def _():
    indicator = build_indicator(NO_IP_EVENT, [])
    assert indicator is None, "expected None for event without IP"


@test("STIX: ObservedData built for event with IP")
def _():
    observed, ipv4_obj = build_observed_data(FULL_EVENT, None)
    assert observed is not None
    assert ipv4_obj is not None
    assert ipv4_obj.value == "203.0.113.42"


@test("STIX: ObservedData returns None when source IP is missing")
def _():
    observed, ipv4_obj = build_observed_data(NO_IP_EVENT, None)
    assert observed is None


@test("STIX: full event produces 5 STIX objects")
def _():
    objects = event_to_stix_objects(FULL_EVENT)
    types = [o.type for o in objects]
    assert "attack-pattern" in types
    assert "indicator" in types
    assert "observed-data" in types
    assert "ipv4-addr" in types
    assert len(objects) == 5, "expected 5, got %d: %s" % (len(objects), types)


@test("STIX: minimal event (no CVE, no geoip) produces objects without error")
def _():
    objects = event_to_stix_objects(MINIMAL_EVENT)
    assert len(objects) >= 1, "expected at least 1 object"


@test("STIX: event with no IP and no MITRE produces empty object list")
def _():
    objects = event_to_stix_objects(NO_IP_EVENT)
    # No indicator, no observed-data (no IP), no attack-patterns (empty MITRE).
    assert len(objects) == 0, "expected 0, got %d" % len(objects)


@test("STIX: bundle built from multiple events merges all objects")
def _():
    bundle = build_bundle([FULL_EVENT, MINIMAL_EVENT])
    assert bundle is not None
    parsed = json.loads(bundle.serialize())
    # Full event gives 5 objects, minimal gives at least 3. Total > 5.
    assert len(parsed["objects"]) > 5


@test("STIX: bundle is None when all events produce zero objects")
def _():
    bundle = build_bundle([NO_IP_EVENT])
    assert bundle is None


@test("STIX: validate_bundle returns True for a valid bundle")
def _():
    bundle = build_bundle([FULL_EVENT])
    result = validate_bundle(bundle)
    assert result is True


@test("STIX: write_bundle writes a parseable JSON file")
def _():
    bundle = build_bundle([FULL_EVENT])
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        write_bundle(bundle, tmp_path)
        with open(tmp_path) as fh:
            data = json.load(fh)
        assert data.get("type") == "bundle"
        assert len(data["objects"]) == 5
    finally:
        os.unlink(tmp_path)


@test("STIX: load_events handles a JSON list")
def _():
    events = load_events("sample_event.json")
    assert isinstance(events, list)
    assert len(events) == 1


@test("STIX: load_events wraps a single JSON object in a list")
def _():
    with tempfile.NamedTemporaryFile(
        suffix=".json", mode="w", delete=False
    ) as tmp:
        json.dump(MINIMAL_EVENT, tmp)
        tmp_path = tmp.name
    try:
        events = load_events(tmp_path)
        assert isinstance(events, list)
        assert len(events) == 1
    finally:
        os.unlink(tmp_path)


@test("STIX: bundle from sample_event.json matches expected structure")
def _():
    events = load_events("sample_event.json")
    bundle = build_bundle(events)
    assert bundle is not None
    parsed = json.loads(bundle.serialize())
    assert parsed["type"] == "bundle"
    types = [o["type"] for o in parsed["objects"]]
    assert "indicator" in types
    assert "attack-pattern" in types
    assert "observed-data" in types
    assert "ipv4-addr" in types


# ---------------------------------------------------------------------------
# MISP exporter tests (logic only, no network calls)
# ---------------------------------------------------------------------------

from exporters.misp_exporter import (
    build_misp_event,
    REALTIME_SEVERITIES,
    THREAT_LEVEL_MAP,
    meets_min_severity as misp_meets_min_severity,
)


@test("MISP: build_misp_event returns a MISPEvent for a full event")
def _():
    from pymisp import MISPEvent
    result = build_misp_event(FULL_EVENT)
    assert isinstance(result, MISPEvent)


@test("MISP: MISPEvent info field contains attack type and persona")
def _():
    result = build_misp_event(FULL_EVENT)
    assert "XSS" in result.info
    assert "apache-2.2-php5" in result.info


@test("MISP: CRITICAL severity maps to threat_level_id 1")
def _():
    result = build_misp_event(FULL_EVENT)
    assert result.threat_level_id == 1


@test("MISP: HIGH severity maps to threat_level_id 2")
def _():
    high_event = json.loads(json.dumps(FULL_EVENT))
    high_event["attack_classification"]["severity"] = "HIGH"
    result = build_misp_event(high_event)
    assert result.threat_level_id == 2


@test("MISP: MISPEvent attributes include the source IP")
def _():
    result = build_misp_event(FULL_EVENT)
    attr_values = [a.value for a in result.attributes]
    assert "203.0.113.42" in attr_values


@test("MISP: MISPEvent attributes include the CVE as vulnerability type")
def _():
    result = build_misp_event(FULL_EVENT)
    vuln_attrs = [
        a for a in result.attributes if a.type == "vulnerability"
    ]
    assert len(vuln_attrs) == 1
    assert vuln_attrs[0].value == "CVE-2012-1823"


@test("MISP: MISPEvent attributes include the request line")
def _():
    result = build_misp_event(FULL_EVENT)
    text_attrs = [a.value for a in result.attributes if a.type == "text"]
    assert any("GET" in v for v in text_attrs)


@test("MISP: MISPEvent attributes include the raw event JSON")
def _():
    result = build_misp_event(FULL_EVENT)
    text_attrs = [a.value for a in result.attributes if a.type == "text"]
    raw_attrs = [v for v in text_attrs if "event_envelope" in v]
    assert len(raw_attrs) == 1, "expected raw event attribute"


@test("MISP: build_misp_event works for a minimal event without error")
def _():
    result = build_misp_event(MINIMAL_EVENT)
    assert result is not None


@test("MISP: build_misp_event works when no CVE field is present")
def _():
    event = json.loads(json.dumps(MINIMAL_EVENT))
    result = build_misp_event(event)
    vuln_attrs = [a for a in result.attributes if a.type == "vulnerability"]
    assert len(vuln_attrs) == 0


@test("MISP: real-time severity filter passes CRITICAL and HIGH only")
def _():
    assert "CRITICAL" in REALTIME_SEVERITIES
    assert "HIGH" in REALTIME_SEVERITIES
    assert "MEDIUM" not in REALTIME_SEVERITIES
    assert "LOW" not in REALTIME_SEVERITIES


@test("MISP: THREAT_LEVEL_MAP covers all expected severity values")
def _():
    for sev in ("CRITICAL", "HIGH", "MEDIUM", "LOW"):
        assert sev in THREAT_LEVEL_MAP, "%s missing from THREAT_LEVEL_MAP" % sev


@test("MISP: MISPEvent tags include severity and profile tags")
def _():
    result = build_misp_event(FULL_EVENT)
    tag_names = [t.name for t in result.tags]
    assert any("CRITICAL" in t for t in tag_names)
    assert any("education/research" in t for t in tag_names)


@test("MISP: MISPEvent tags include MITRE technique IDs")
def _():
    result = build_misp_event(FULL_EVENT)
    tag_names = [t.name for t in result.tags]
    assert any("T1190" in t for t in tag_names)
    assert any("T1059.007" in t for t in tag_names)


# ---------------------------------------------------------------------------
# meets_min_severity and filter_by_severity tests
# ---------------------------------------------------------------------------

@test("severity: CRITICAL passes when min_severity is CRITICAL")
def _():
    assert misp_meets_min_severity("CRITICAL", "CRITICAL") is True
    assert stix_meets_min_severity("CRITICAL", "CRITICAL") is True


@test("severity: HIGH passes when min_severity is MEDIUM")
def _():
    assert misp_meets_min_severity("HIGH", "MEDIUM") is True
    assert stix_meets_min_severity("HIGH", "MEDIUM") is True


@test("severity: LOW is blocked when min_severity is MEDIUM")
def _():
    assert misp_meets_min_severity("LOW", "MEDIUM") is False
    assert stix_meets_min_severity("LOW", "MEDIUM") is False


@test("severity: MEDIUM is blocked when min_severity is HIGH")
def _():
    assert misp_meets_min_severity("MEDIUM", "HIGH") is False
    assert stix_meets_min_severity("MEDIUM", "HIGH") is False


@test("severity: missing severity always passes so no data is silently dropped")
def _():
    assert misp_meets_min_severity("", "HIGH") is True
    assert misp_meets_min_severity(None, "CRITICAL") is True


@test("STIX: filter_by_severity keeps only events at or above threshold")
def _():
    events = [
        {"attack_classification": {"severity": "CRITICAL"}},
        {"attack_classification": {"severity": "HIGH"}},
        {"attack_classification": {"severity": "MEDIUM"}},
        {"attack_classification": {"severity": "LOW"}},
    ]
    result = filter_by_severity(events, "HIGH")
    severities = [e["attack_classification"]["severity"] for e in result]
    assert severities == ["CRITICAL", "HIGH"], "got: %s" % severities


# Four events with distinct severities used for end-to-end pipeline tests.
MIXED_SEVERITY_EVENTS = [
    {
        "event_type": "attack",
        "event_envelope": {"version": "1.1", "timestamp": "2026-08-14T10:00:00Z"},
        "attack_classification": {"type": "XSS", "severity": "CRITICAL"},
        "mitre_attack": ["T1190"],
        "transaction": {"remote_address": "10.0.0.1"},
    },
    {
        "event_type": "attack",
        "event_envelope": {"version": "1.1", "timestamp": "2026-08-14T10:01:00Z"},
        "attack_classification": {"type": "SQLi", "severity": "HIGH"},
        "mitre_attack": ["T1190"],
        "transaction": {"remote_address": "10.0.0.2"},
    },
    {
        "event_type": "attack",
        "event_envelope": {"version": "1.1", "timestamp": "2026-08-14T10:02:00Z"},
        "attack_classification": {"type": "LFI", "severity": "MEDIUM"},
        "mitre_attack": [],
        "transaction": {"remote_address": "10.0.0.3"},
    },
    {
        "event_type": "attack",
        "event_envelope": {"version": "1.1", "timestamp": "2026-08-14T10:03:00Z"},
        "attack_classification": {"type": "Scan", "severity": "LOW"},
        "mitre_attack": [],
        "transaction": {"remote_address": "10.0.0.4"},
    },
]


@test("pipeline: min_severity=CRITICAL passes only 1 of 4 events into STIX bundle")
def _():
    events = filter_by_severity(MIXED_SEVERITY_EVENTS, "CRITICAL")
    assert len(events) == 1
    bundle = build_bundle(events)
    assert bundle is not None
    parsed = json.loads(bundle.serialize())
    ips = [o["value"] for o in parsed["objects"] if o["type"] == "ipv4-addr"]
    assert ips == ["10.0.0.1"], "got: %s" % ips


@test("pipeline: min_severity=HIGH passes 2 of 4 events into STIX bundle")
def _():
    events = filter_by_severity(MIXED_SEVERITY_EVENTS, "HIGH")
    assert len(events) == 2
    bundle = build_bundle(events)
    assert bundle is not None
    parsed = json.loads(bundle.serialize())
    ips = sorted(o["value"] for o in parsed["objects"] if o["type"] == "ipv4-addr")
    assert ips == ["10.0.0.1", "10.0.0.2"], "got: %s" % ips


@test("pipeline: min_severity=MEDIUM passes 3 of 4 events (MEDIUM has no IP so 2 in bundle)")
def _():
    events = filter_by_severity(MIXED_SEVERITY_EVENTS, "MEDIUM")
    assert len(events) == 3
    # MEDIUM event has no MITRE techniques and IP is present, so it still builds an ipv4-addr.
    bundle = build_bundle(events)
    assert bundle is not None
    parsed = json.loads(bundle.serialize())
    ips = sorted(o["value"] for o in parsed["objects"] if o["type"] == "ipv4-addr")
    assert "10.0.0.1" in ips
    assert "10.0.0.2" in ips
    assert "10.0.0.3" in ips


@test("pipeline: min_severity=LOW passes all 4 events into bundle (full noise capture)")
def _():
    events = filter_by_severity(MIXED_SEVERITY_EVENTS, "LOW")
    assert len(events) == 4
    bundle = build_bundle(events)
    assert bundle is not None
    parsed = json.loads(bundle.serialize())
    ips = sorted(o["value"] for o in parsed["objects"] if o["type"] == "ipv4-addr")
    assert len(ips) == 4


@test("pipeline: MISP batch filter min_severity=HIGH produces MISPEvents for correct events only")
def _():
    events = filter_by_severity(MIXED_SEVERITY_EVENTS, "HIGH")
    assert len(events) == 2
    misp_events = [build_misp_event(ev) for ev in events]
    attack_types = [e.info for e in misp_events]
    assert any("XSS" in t for t in attack_types)
    assert any("SQLi" in t for t in attack_types)
    assert not any("LFI" in t for t in attack_types)
    assert not any("Scan" in t for t in attack_types)


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

print()
total = len(_results)
passed = sum(1 for _, ok, _ in _results if ok)
failed = total - passed

print("=" * 60)
print("Results: %d/%d passed" % (passed, total))
if failed:
    print("Failed tests:")
    for name, ok, exc in _results:
        if not ok:
            print("  - %s: %s" % (name, exc))
    sys.exit(1)
else:
    print("All tests passed.")
