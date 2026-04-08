# OWASP Honeypot Project

**Identify emerging web application attacks and share threat intelligence with the security community.**

Based on the OWASP/WASC Distributed Web Honeypots Project ([Original Project](https://github.com/SpiderLabs/owasp-distributed-web-honeypots))

---

## What This Project Does

- **Real-time Web Application Threat Data** - Capture live attacks as they happen
- **Community Threat Reports** - Share attack intelligence with the security community

---

## Which Docker Compose File Should I Use?

Choose based on what you need:

| Use Case | Docker Compose Location | Command |
|----------|------------------------|---------|
| **Basic honeypot only** | `honeytraps/waf_modsec/` | `cd honeytraps/waf_modsec && docker-compose up -d` |
| **Honeypot + ELK visualization** | `honeytraps/waf_elk/` | `cd honeytraps/waf_elk && docker-compose up -d` |
| **Existing ModSecurity → ELK (Filebeat)** | `mds_elk/` | `cd mds_elk && docker-compose up -d` |
| **Existing ModSecurity → ELK (mlogc)** | `mlogc_elk/` | `cd mlogc_elk && docker-compose up -d` |
| **MISP threat intelligence** | `honeytraps/misp/` | `cd honeytraps/misp && docker-compose up -d` |

> **New users:** Start with `honeytraps/waf_modsec/` for a basic setup.

---

## Repository Structure

This project has 4 main components:

### 🎯 Core Honeypots (`honeytraps/`)
**Purpose:** Deploy honeypots that capture attacks and report to threat intelligence platforms

| Subdirectory | What It Does |
|--------------|--------------|
| `waf_modsec/` | Basic ModSecurity honeypot (start here) |
| `waf_elk/` | Honeypot with built-in ELK visualization |
| `misp/` | Honeypot with MISP threat intel integration |

📖 [See honeytraps/README.md](honeytraps/README.md)

---

### 📊 Log Integration Options (PoC)
**Purpose:** Send logs from existing ModSecurity instances to ELK

| Directory | Method | When to Use |
|-----------|--------|-------------|
| `mds_elk/` | Filebeat | Modern log shipping |
| `mlogc_elk/` | mlogc | Legacy audit log collector |

📖 See [mds_elk/README.md](mds_elk/README.md) or [mlogc_elk/README.md](mlogc_elk/README.md)

---

### 🔧 Setup Guides (`misp-doc/`)
**Purpose:** Documentation for setting up MISP server and PyMISP integration

📖 [See misp-doc/README.md](misp-doc/README.md)

---

### Decision Tree


---

## Quick Navigation

**I want to...**

- **Deploy a basic honeypot** → `cd honeytraps/waf_modsec/` and see [README](honeytraps/README.md)
- **Visualize attacks with ELK** → `cd honeytraps/waf_elk/` or see [mds_elk](mds_elk/README.md) / [mlogc_elk](mlogc_elk/README.md)
- **Share threat intelligence** → `cd honeytraps/misp/` and see [misp-doc](misp-doc/README.md)
- **Understand the architecture** → See [honeytraps/README.md](honeytraps/README.md)

---

## Prerequisites

Before starting, make sure you have:

- **Docker & Docker Compose** installed
- **4GB+ RAM** (8GB+ recommended for ELK stack)
- **Basic networking knowledge** (port forwarding, firewall rules)

Detailed requirements are in each component's README.

---

## Project Status

### ✅ Completed
- ModSecurity-based honeypot/probe implementations
- VM and Docker deployment options
- ModSecurity Audit Console integration
- MySQL to JSON conversion
- mlogc audit log to JSON conversion
- ELK stack integration (Filebeat and mlogc)
- Alternative log transfer methods (mlogc-ng)

### 🚧 In Progress
- MISP threat intelligence integration (STIX/TAXII format)
- CRS v3.1 based VM honeypot
- Small footprint Docker & Raspberry Pi honeypots
- Machine learning for automated rule updates based on threat intelligence

---

## Contributing

Contributions are welcome! Each component has its own setup and contribution guidelines in its README.

**Ideas for contributions:**
- Improve documentation clarity
- Add new honeypot configurations
- Enhance ELK dashboards
- Develop new threat intelligence integrations
- Create deployment automation scripts

---

## Getting Help

1. **Check the specific component's README** - Each directory has detailed documentation
2. **Review existing issues** - [GitHub Issues](https://github.com/OWASP/Honeypot-Project/issues)
3. **Open a new issue** - Describe what you tried and what didn't work

---

## Project Links

- **OWASP Project Page**: [owasp.org/www-project-honeypot](https://owasp.org/www-project-honeypot/)


---

## License

This project follows OWASP licensing guidelines.
