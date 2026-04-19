# WAF ModSecurity Honeypot

A modular, extensible honeypot built on Apache + ModSecurity with OWASP CRS, featuring chameleon persona switching, Shodan-aware container swapping, and automated CRS updates.

> AWS ECS setup can be found [here](https://github.com/OWASP/Honeypot-Project/wiki/AWS-ECS-Setup-for-ModSecurity-Honeypot).

---

## Features

- **ModSecurity WAF** with OWASP Core Rule Set (CRS) — auto-updated on container start
- **Chameleon Personas** — dynamically impersonate WordPress, Drupal, Moodle, CAS, or a generic server
- **Shodan Watcher** — monitors Shodan for new scanner activity and auto-swaps the active persona
- **CRS Auto-Update** — pulls latest CRS rules from GitHub on every container start
- **Pinned Docker base images** — reproducible builds across Linux, macOS, and Windows
- **Log shipping** via Filebeat → Logstash (optional, non-blocking)
- **CI tested** via GitHub Actions

---

## Project Structure

```
honeytraps/waf_modsec/
├── Dockerfile                        # Main WAF container
├── docker-compose.yml                # Base compose (WAF + Filebeat)
├── docker-compose.personas.yml       # Persona containers (WordPress, Drupal, Moodle, CAS)
├── modsec_entry.sh                   # Container entrypoint
├── modsecurity-extension.conf        # Custom ModSecurity rules
├── httpd.conf                        # Apache config
├── crs_update.sh                     # CRS auto-update script
├── shodan_watcher.py                 # Shodan-aware persona swapper
├── filebeat.yml                      # Log shipping config (optional)
├── personas/
│   ├── generic/                      # Default persona
│   ├── wordpress/                    # WordPress fingerprint
│   ├── drupal/                       # Drupal fingerprint
│   ├── moodle/                       # Moodle (higher-ed) fingerprint
│   └── cas/                          # CAS SSO fingerprint
└── tests/
    ├── test_crs_update.sh            # CRS updater tests
    └── test_personas.sh              # Persona integration tests
```

---

## Prerequisites

- Docker >= 24.0 (with pinned base image support)
- Docker Compose >= 2.0
- Python 3.9+ (for Shodan watcher)
- A Shodan API key (optional, for auto persona swapping)

---

## Setup

```bash
cd ~/Honeypot-Project/honeytraps/waf_modsec
cp sample-env env
# Edit env file — set LOGSTASH_HOST (optional), SHODAN_API_KEY (optional)
docker compose build
```

> **Note for Windows users:** If you see `\r` errors in Docker, run:
> ```bash
> sed -i 's/\r//' modsec_entry.sh crs_update.sh
> ```

> **Note:** `httpd-logging-after-modsec.conf` must be commented out in `httpd.conf` for local development.

---

## Running the Honeypot

### Basic (WAF only)

```bash
docker compose up
```

### With a specific persona

```bash
# WordPress persona
docker compose --profile wordpress up

# Drupal persona
docker compose --profile drupal up

# Moodle persona
docker compose --profile moodle up

# CAS persona
docker compose --profile cas up
```

### With Shodan auto-swap

```bash
# Set your Shodan API key in env file first
docker compose up
python3 shodan_watcher.py
```

The Shodan watcher monitors for new scanner probes and automatically swaps the active persona container to present the most deceptive fingerprint.

---

## Ports

| Port | Description |
|------|-------------|
| 9091 | Honeypot access (passive) |
| 8000 | Triggers logging |
| 8080 | Triggers logging |
| 8888 | Triggers logging |

---

## CRS Auto-Update

On every container start, `crs_update.sh` pulls the latest OWASP CRS rules from GitHub automatically. No manual intervention needed.

To test the updater:

```bash
bash tests/test_crs_update.sh
```

---

## Personas

Personas allow the honeypot to impersonate different CMS platforms to attract targeted attackers. Each persona includes:

- Realistic HTTP headers and error pages
- CMS-specific `robots.txt`
- CVE-style probe paths (e.g. `wp-login.php`, `user/login`, `moodle/login`)
- Shodan-aware context tags

| Persona | Impersonates | Key Paths |
|---------|-------------|-----------|
| `generic` | Plain Apache server | `/` |
| `wordpress` | WordPress 6.x | `/wp-login.php`, `/wp-admin/` |
| `drupal` | Drupal 10.x | `/user/login`, `/admin/` |
| `moodle` | Moodle LMS | `/login/index.php`, `/moodle/` |
| `cas` | CAS SSO | `/cas/login`, `/cas/serviceValidate` |

---

## Log Shipping

Logs are shipped via **Filebeat → Logstash** (optional). Set `LOGSTASH_HOST` in your `env` file to enable. If not set, the container starts normally without log shipping.

```env
LOGSTASH_HOST=your-logstash-host:5044   # optional
```

---

## Running Tests

```bash
# CRS updater tests
bash tests/test_crs_update.sh

# Persona integration tests (requires Docker)
bash tests/test_personas.sh
```

CI runs automatically on every push via GitHub Actions.

---

## Uploading to DockerHub

```bash
cd ~/Honeypot-Project/honeytraps/waf_modsec
docker build ./ -t <dockerhub-username>/honeytrap-modsec
docker push <dockerhub-username>/honeytrap-modsec
```

> The image currently resides at [floyd0122/honeytrap-modsec](https://hub.docker.com/repository/docker/floyd0122/honeytrap-modsec). This should be moved to the OWASP DockerHub account in the future, and `aws-ecs-container-definition.json` updated accordingly.

---

## Related Issues

- [#20 — Lists of feature and optimisation requirements](https://github.com/OWASP/Honeypot-Project/issues/20)
- [#9 — Create module for CMSs](https://github.com/OWASP/Honeypot-Project/issues/9)
- [#6 — Develop new alternative small footprint honeypots](https://github.com/OWASP/Honeypot-Project/issues/6)

---

## Contributing

Please follow the [OWASP Honeypot Project contributing guidelines](https://github.com/OWASP/Honeypot-Project/blob/master/CONTRIBUTING.md) before submitting PRs.
