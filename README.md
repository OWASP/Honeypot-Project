# OWASP Honeypot Project

The OWASP Honeypot Project identifies emerging attacks against web applications and reports them to the security community.

Based on the earlier OWASP/WASC Distributed Web Honeypots Project (https://github.com/SpiderLabs/owasp-distributed-web-honeypots)

## What This Project Provides

- Real-time web application threat data
- Community threat reports and intelligence sharing
- ModSecurity-based honeypots
- Multiple deployment options (Docker, cloud)

## Getting Started

This repository contains several components. Choose the one that fits your needs:

| Component | Description | Documentation |
|-----------|-------------|---------------|
| `honeytraps/waf_modsec` | ModSecurity honeypot probe | [README](honeytraps/waf_modsec/README.md) |
| `honeytraps/waf_elk` | Honeypot with ELK stack | [README](honeytraps/waf_elk/README.md) |
| `honeytraps/misp` | MISP threat intelligence | [README](honeytraps/misp/README.md) |
| `mds_elk` | ModSecurity to ELK via Filebeat | [README](mds_elk/README.md) |
| `mlogc_elk` | ModSecurity to ELK via mlogc | [README](mlogc_elk/README.md) |
| `misp-doc` | MISP setup guide | [README](misp-doc/README.md) |

## Prerequisites

- Docker & Docker Compose
- 4GB+ RAM (8GB+ for ELK stack)
- Open ports: 80, 443, 5601, 9200, 5044

See individual component READMEs for detailed setup instructions.
