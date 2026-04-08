# OWASP Honeypot Project

**Identify emerging web application attacks and share threat intelligence with the security community.**

Based on the OWASP/WASC Distributed Web Honeypots Project ([Original Project](https://github.com/SpiderLabs/owasp-distributed-web-honeypots))

---

## What This Project Does

- **Real-time Web Application Threat Data** - Capture live attacks as they happen
- **Community Threat Reports** - Share attack intelligence with the security community

---

## Repository Structure

This project has multiple components. Each directory is self-contained with its own documentation:

| Directory | What It Does | Start Here |
|-----------|--------------|------------|
| **`honeytraps/`** | Main honeypot implementations and threat intelligence reporting | [📖 Documentation](honeytraps/README.md) |
| **`mds_elk/`** | Send ModSecurity logs to ELK using Filebeat (Proof of Concept) | [📖 Documentation](mds_elk/README.md) |
| **`misp-doc/`** | Set up MISP server and create threat events with PyMISP | [📖 Documentation](misp-doc/README.md) |
| **`mlogc_elk/`** | Send ModSecurity logs to ELK using mlogc (Proof of Concept) | [📖 Documentation](mlogc_elk/README.md) |

> **New to this project?** Start with the [`honeytraps/`](honeytraps/README.md) directory - it contains the core honeypot setup.

---

## Quick Navigation

**I want to...**

- **Deploy a basic honeypot** → See [`honeytraps/README.md`](honeytraps/README.md)
- **Visualize attacks with ELK** → See [`mds_elk/README.md`](mds_elk/README.md) or [`mlogc_elk/README.md`](mlogc_elk/README.md)
- **Share threat intelligence** → See [`misp-doc/README.md`](misp-doc/README.md)
- **Understand the architecture** → See [`honeytraps/README.md`](honeytraps/README.md)

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
- **GitHub Repository**: [github.com/OWASP/Honeypot-Project](https://github.com/OWASP/Honeypot-Project)

---

## License

This project follows OWASP licensing guidelines.
