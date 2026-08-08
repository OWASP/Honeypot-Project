# threat_intel

Threat intelligence exporters for the OWASP Honeypot Project.

Both exporters consume events in the v1.1 JSON schema produced by the
project's Logstash pipeline. The sample_event.json file in this directory
can be used to test either exporter without a live honeypot stack running.

## Directory structure

```
threat_intel/
├── exporters/
│   ├── misp_exporter.py    # PyMISP exporter (batch + real-time)
│   └── stix_exporter.py    # STIX 2.1 exporter (local file + TAXII push)
├── sample_event.json       # Example v1.1 event for smoke-testing
├── requirements.txt
└── README.md
```

## Setup

```bash
cd threat_intel
pip install -r requirements.txt
```

## MISP exporter

### Batch mode

Reads a JSON file containing one or more events and pushes all of them
to MISP in one shot.

```bash
python exporters/misp_exporter.py \
    --mode batch \
    --input sample_event.json \
    --url https://misp.example.com \
    --key YOUR_MISP_AUTOMATION_KEY
```

### Real-time mode

Tails a file line by line (Logstash JSON codec output). Only events with
severity CRITICAL or HIGH are forwarded to MISP immediately. Events with
lower severity are silently skipped.

```bash
python exporters/misp_exporter.py \
    --mode realtime \
    --input /var/log/honeypot/events.ndjson \
    --url https://misp.example.com \
    --key YOUR_MISP_AUTOMATION_KEY
```

Add `--no-verify` when connecting to a local or development MISP instance
that uses a self-signed certificate.

### What gets pushed

Each honeypot event becomes one MISP event containing:

- Source IP attribute (ip-src)
- Request line as free text
- Honeypot node IP (ip-dst)
- GeoIP2 enrichment (country, ASN, ISP) as a text attribute
- CVE as a vulnerability attribute (if the event has one)
- Raw event JSON as a text attribute so no detail is lost
- Tags for severity, honeypot profile, MITRE technique IDs, and CVE

## STIX 2.1 exporter

### Write to a local file

```bash
python exporters/stix_exporter.py \
    --input sample_event.json \
    --output bundle.json
```

### Push to a TAXII 2.1 collection

```bash
python exporters/stix_exporter.py \
    --input sample_event.json \
    --taxii-url https://taxii.example.com/api/root/collections/honeypot/objects/ \
    --taxii-user admin \
    --taxii-pass secret
```

Both `--output` and `--taxii-url` can be combined to write locally and push
in the same run.

### STIX objects produced

For each event:

| Object | Content |
|---|---|
| `AttackPattern` | One per MITRE ATT&CK technique ID found in the event |
| `Indicator` | Source IP pattern with links to the AttackPatterns above |
| `ObservedData` | Single observation wrapping the source IPv4 address |

All objects carry TLP:WHITE marking by default and reference the OWASP
Honeypot Project as the producer identity.

The bundle is validated by the stix2 library at construction time before
it is written or pushed, so malformed objects are caught locally.

## Notes on the MISP API version

The exporter is pinned to `pymisp==2.5.34.1`. On startup it checks the
connected MISP instance version and warns if it is below 2.5. If you see
that warning, updating your MISP instance is recommended before production
use.
