# Schema Migration: mlogc to v1.1 JSON

## Background

The original `mlogc_elk` stack shipped raw mlogc-format logs to Elasticsearch with no
normalisation stage. The `mds_elk` and `honeytraps` stacks now emit structured JSON via
`SecAuditLogFormat JSON`, and both Logstash pipelines map that output to the v1.1 schema
documented here.

---

## Field Mapping

| Legacy mlogc field | v1.1 field | Notes |
|---|---|---|
| `transaction.id` | `transaction.transaction_id` | Renamed for clarity |
| `transaction.time` | `transaction.time` + `event_envelope.timestamp` | Copied to both locations |
| `transaction.client_ip` | `transaction.remote_address` | Renamed to match ModSecurity JSON key |
| `transaction.client_port` | `transaction.remote_port` | |
| `transaction.host_ip` | `transaction.local_address` | |
| `transaction.host_port` | `transaction.local_port` | |
| `request.line` | `request.request_line` | |
| `request.headers.*` | `request.headers.*` | Pass-through |
| `response.status` | `response.status` | |
| `response.headers.*` | `response.headers.*` | Pass-through |
| `audit_data.messages[*].severity` | `attack_classification.severity` | Extracted from message array |
| `audit_data.messages[*].id` | `attack_classification.honeytrap_rule_id` | First rule ID in chain |
| _(not present)_ | `attack_classification.type` | Derived from CRS rule file path |
| _(not present)_ | `attack_classification.honeytrap_triggered` | true if rule_id is in 9500000-9999999 (the honeytrap plugin range) |
| _(not present)_ | `attack_classification.cve_triggered` | Extracted from `[tag "CVE-..."]` in message |
| _(not present)_ | `mitre_attack` | Array of technique IDs derived from rule file |
| _(not present)_ | `geoip2.*` | GeoIP2 City enrichment from remote_address |
| _(not present)_ | `geoip2.asn` / `geoip2.isp` | ASN enrichment (requires GeoLite2-ASN.mmdb) |
| _(not present)_ | `event_envelope.*` | Node identity and schema version metadata |
| _(not present)_ | `persona_context.*` | Active honeypot persona from env vars |
| _(not present)_ | `response.honeytoken_triggered` | true when `Admin=` appears in Set-Cookie |
| _(not present)_ | `feed_metadata.export_timestamp` | Logstash @timestamp at index time |
| _(not present)_ | `feed_metadata.batch_id` | At ingestion `"pending_export"`, rewritten later by export daemon |

---

## Two-Event Schema Split

The v1.1 Logstash pipeline splits the log stream into two distinct event types to avoid carrying unnecessary fields. The `event_type` field separates them for Kibana queries and S3 filtering.

### 1. Attack Event (`event_type: "attack"`)
Emitted on every HTTP request hitting the honeypot. Contains full ModSecurity audit data, MITRE ATT&CK mappings, and GeoIP enrichments.

### 2. Persona Rotation Event (`event_type: "persona_rotation"`)
Emitted only when the honeypot persona changes (triggered by Shodan, scheduled rotation, or manual operator action).

The following fields are new in v1.1 they don't exist in mlogc output and are added by the Logstash pipeline:

| Field | Type | Description |
|---|---|---|
| `event_type` | keyword | `"attack"` or `"persona_rotation"` |
| `persona_rotation.previous_persona` | keyword | The persona before rotation, or `null` for initial deployment |
| `persona_rotation.new_persona` | keyword | The newly activated persona |
| `persona_rotation.trigger` | keyword | e.g., `"manual"`, `"shodan"`, `"scheduled"` |
| `persona_rotation.trigger_detail` | text | Explanation of the trigger |
| `persona_rotation.timestamp` | date | |
| `persona_rotation.shodan_honeyscore` | float | Conditional field: present if trigger was Shodan |
| `event_envelope.version` | keyword | Schema version, currently `"1.1"` |
| `event_envelope.node_id` | keyword | From `HONEYPOT_NODE_ID` env var |
| `event_envelope.honeypot_ip` | keyword | From `HONEYPOT_IP` env var |
| `event_envelope.aws_region` | keyword | From `AWS_REGION` env var, `"local"` if unset |
| `persona_context.name` | keyword | From `HONEYPOT_PERSONA` env var |
| `persona_context.profile` | keyword | From `HONEYPOT_PROFILE` env var |
| `attack_classification.type` | keyword | XSS, SQLi, LFI/RFI, RCE, Scanner, Path Traversal, UNKNOWN |
| `attack_classification.severity` | keyword | CRITICAL, ERROR, WARNING, NOTICE, INFO, UNKNOWN |
| `attack_classification.honeytrap_triggered` | boolean | |
| `attack_classification.cve_triggered` | keyword | e.g. `CVE-2012-1823`, absent if no CVE tag |
| `mitre_attack` | keyword (array) | e.g. `["T1190", "T1059.007"]` |
| `geoip2.country` | keyword | ISO 3166-1 alpha-2 country code |
| `geoip2.city` | keyword | |
| `geoip2.latitude` | float | |
| `geoip2.longitude` | float | |
| `geoip2.asn` | keyword | e.g. `AS13335`, absent if ASN db missing |
| `geoip2.isp` | keyword | Absent if ASN db missing |
| `response.honeytoken_triggered` | boolean | |
| `feed_metadata.export_timestamp` | date | |
| `feed_metadata.batch_id` | keyword | At ingestion `"pending_export"`, rewritten later by export daemon |

---

## Kibana Index Pattern

Both stacks index into `honeypot-attacks-YYYY.MM.dd`. The Kibana index pattern
`honeypot-attacks-*` covers all daily indices.

Import `kibana/export.ndjson` via **Stack Management > Saved Objects > Import** to load
the pre-built dashboards, or use `scripts/update_kibana.py` to import via the API.

---

## ASN/ISP Enrichment

The `geoip2.asn` and `geoip2.isp` fields require the GeoLite2-ASN database. Download
`GeoLite2-ASN.mmdb` from MaxMind and place it at:

- `/usr/share/logstash/GeoLite2-ASN.mmdb` inside the Logstash container

Events missing the ASN database are tagged with `_asn_lookup_failure` but still index
cleanly.
