# OWASP Honeypot Project

The OWASP Honeypot Project is a production-grade, adaptive web application honeypot that captures structured attack intelligence, rotates its identity when fingerprinted, and exports threat data directly to MISP and STIX 2.1. It deploys across multiple AWS regions with a single command.

---

## Repository Layout

| Directory | Purpose |
| --- | --- |
| `honeytraps/` | Core honeypot stack: ModSecurity WAF, honeytrap plugin, persona rotation engine, and four vulnerable application personas |
| `terraform/` | Multi-region AWS deployment module (eu-west-1, us-east-1, ap-south-1) and `deploy_fleet.py` provisioning wrapper |
| `threat_intel/` | MISP and STIX 2.1 exporters that read directly from the v1.1 JSON schema |
| `profiles/` | Industry segment profiles (education/research, financial, general) |
| `docs/` | v1.1 schema reference and mlogc-to-v1.1 migration guide |
| `mds_elk/` | PoC: ModSecurity audit logs shipped to ELK via Filebeat |
| `mlogc_elk/` | PoC: ModSecurity audit logs shipped to ELK via mlogc |
| `misp-doc/` | MISP server setup and PyMISP event generation reference |
| `scripts/` | Helper scripts (`update_kibana.py` for importing dashboards via API) |

---

## Getting Started

### Run locally

```bash
cd honeytraps/waf_modsec
cp sample-env .env          # fill in LOGSTASH_HOST
docker compose up -d
```

The WAF container exposes port 9091 (HTTP), 8080, 8000, and 8888. Attack events are written in v1.1 JSON format and forwarded to Logstash via Filebeat.

### Deploy to AWS (all three regions)

```bash
python terraform/deploy_fleet.py \
  --key-name your-key-pair \
  --logstash-host 10.0.0.5:5044 \
  --shodan-api-key $SHODAN_KEY
```

Secrets can also be passed as environment variables to keep them out of shell history:

```bash
export TF_VAR_logstash_host="10.0.0.5:5044"
export TF_VAR_shodan_api_key="..."
python terraform/deploy_fleet.py --key-name your-key-pair
```

Use `--dry-run` to run `terraform plan` only, or `--yes` to skip the confirmation prompt in CI.

---

## Components

### Honeytrap Plugin (`honeytraps/waf_modsec/plugins/`)

A CRS 4.x plugin covering fake high-value endpoints, scanner fingerprints, rapid probing detection, and credential canaries. Rule IDs are allocated in the reserved 9,500,000 to 9,999,999 range so they never collide with core CRS rules.

`rule_watcher.py` watches the plugin directory for changes and reloads rules via `apachectl graceful` with no container restart. If graceful reload fails three times consecutively it falls back to a full container restart so the honeypot never ends up in an inconsistent state.

### Chameleon Persona Engine (`honeytraps/persona_watchdog.py`)

Polls the Shodan Honeyscore and host API every 60 seconds. On detection (score above the configured threshold, default 0.4) it swaps the `docker-compose.override.yml` to a new persona and issues a graceful reload. Every rotation is logged to `honeytraps/rotation_log.jsonl`.

```bash
# manual rotation (force immediately without waiting for Shodan)
python honeytraps/persona_watchdog.py --force-rotate

# adjust detection sensitivity
python honeytraps/persona_watchdog.py --threshold 0.4 --interval 60
```

### Personas (`honeytraps/personas/`)

Four self-contained vulnerable application personas. Each is a directory with a `Dockerfile`, `vhost.conf`, and `persona.json`. Adding a new persona requires no changes to the engine.

| Persona | Simulated application | CVE lures |
| --- | --- | --- |
| `wordpress-5.0` | WordPress 5.0.3 | CVE-2019-8942, CVE-2019-8943 |
| `phpmyadmin-4.8.1` | phpMyAdmin 4.8.1 | CVE-2018-12613 |
| `iis-7.5-fastcgi` | IIS 7.5 + FastCGI | CVE-2010-2730 |
| `apache-2.2-php5` | Apache 2.2 + PHP-CGI | CVE-2012-1823 |

### Industry Segment Profiles (`profiles/`)

Switch the entire deployment context with one environment variable:

```bash
HONEYPOT_PROFILE=financial docker compose up -d
```

| Profile | Shodan threshold | Min severity forwarded to MISP |
| --- | --- | --- |
| `education_research` | 0.55 | LOW |
| `financial` | 0.40 | HIGH |
| `general` | 0.60 | MEDIUM |

### Threat Intelligence Exporters (`threat_intel/exporters/`)

Both exporters read directly from the v1.1 JSON schema produced by the Logstash pipeline. No intermediate format conversion.

```bash
# MISP batch push
python -m threat_intel.exporters.misp_exporter --mode batch \
  --input events.json --url https://misp.example.com --key $MISP_KEY

# STIX 2.1 bundle to file + TAXII push
python -m threat_intel.exporters.stix_exporter \
  --input events.json --output bundle.json \
  --taxii-url https://taxii.example.com/collections/honeypot/
```

### Automated CRS Updates (`.github/workflows/crs-update.yml`)

A nightly workflow checks for new CRS releases, builds the WAF image, runs a smoke test, and opens a PR automatically. LTS point releases (v4.25.x) get a ready-to-merge PR with auto-merge enabled. Non-LTS releases get a draft PR for maintainer review.

Current pinned version: see `honeytraps/CRS_VERSION`.

### v1.1 JSON Schema (`docs/`)

All attack events are indexed in a versioned schema covering `event_envelope`, `persona_context`, `attack_classification` (with `honeytrap_triggered` boolean and `cve_triggered` CVE ID string), `mitre_attack` (array of technique IDs), `geoip2` (country, city, ASN, ISP), full request/response, and `feed_metadata`.

See `docs/SCHEMA_MIGRATION.md` for the full field mapping from the legacy mlogc format.

---

## Roadmap

### Completed

- v1.1 structured JSON logging schema with GeoIP2 and MITRE ATT&CK enrichment
- Automated CRS version management with nightly GitHub Actions workflow
- Honeytrap CRS 4.x plugin with hot-reload via `rule_watcher.py`
- Chameleon Persona Engine with Shodan Honeyscore-triggered rotation
- Four vulnerable application personas (WordPress, phpMyAdmin, IIS, Apache/PHP-CGI)
- Multi-region AWS deployment via Terraform and `deploy_fleet.py`
- MISP and STIX 2.1 threat intelligence exporters
- Industry segment profiles (education/research, financial, general)

---

## License

Apache 2.0
