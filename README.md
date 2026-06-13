# OWASP Honeypot-Project

The goal of the OWASP Honeypot Project is to identify emerging attacks against web applications and report them to the community, in order to facilitate protection against such targeted attacks.

Based around the earlier OWASP/WASC Distributed Web Honeypots Project (https://github.com/SpiderLabs/owasp-distributed-web-honeypots)

The primary aims of the project are

*    Real-time, detailed Web Application Threat Attack Data
*    Threat Reports to the community

## Organization of the repository

This repository is organized into various directories. Below table shows the purpose of each one. 

| Directory | Purpose | 
| --- | --- | 
| `honeytraps` | Focuses on building honeytraps and reporting threat intelligence | 
| `mds_elk` | Shows a PoC for sending the ModSecurity Audit Logs to ELK using Filebeat|
| `misp-doc` | Assists in setting the MISP Server and creating threat events using PyMISP |
| `mlogc_elk` | Shows a PoC for sending the ModSecurity Audit Logs to ELK using ModSecurity Audit Log Collector (mlogc) |
| `docs` | Contains architecture documentation, such as the [v1.1 Schema Migration Guide](docs/SCHEMA_MIGRATION.md) and [JSON schemas](docs/v1.1_schema.json) |

Please go to respective directories for complete documentation.

# Project Roadmap

Last reviewed: June 2026

This repository currently reflects a set of active proof-of-concept paths and longer-term ideas. The roadmap below distinguishes completed work from ongoing focus areas and future opportunities.

## Completed

* ModSecurity honeypot proof of concept with audit log capture and console analysis
* ModSecurity audit log export to JSON and forwarding into ELK/Logstash/Kibana
* mlogc-based ModSecurity audit log forwarding to ELK
* MISP threat intelligence sharing proof of concept and PyMISP event generation

## Current priorities

* Maintain and document ELK-based attack visualization workflows
* Maintain and document MISP-based threat intelligence sharing
* Keep ModSecurity / mlogc ingestion pipelines current and usable
* Improve contributor onboarding for the existing PoCs in `honeytraps/`, `mds_elk/`, `mlogc_elk/`, and `misp-doc/`

## Future / longer-term ideas

* STIX/TAXII interoperability with MISP and honeypot telemetry
* Machine learning-assisted rule tuning and threat intelligence-driven rule updates
* New lightweight honeypot personas or small-footprint Docker / Raspberry Pi sensor options
* New CRS-based VM honeypot / probe designs
