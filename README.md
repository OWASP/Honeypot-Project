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

Please go to respective directories for complete documentation.

# Project Roadmap

As of <strong>August, 2018, the  priorities for the next 6 months</strong> are:
<strong>
*   ~~Setup Proof of Concept to understand how ModSecurity baed Honeypot/Probe interacts with a receiving console (develop a VM and/or Docker based test solution to store logs from multiple probes).~~
*   ~~Evaluate console options to visualise threat data received from ModSecurity Honeypots/probes in MosSecurity Audit Console, WAF-FLE, Fluent and bespoke scripts for single and multiple probes.~~
*   ~~Develop a mechanism to convert from stored MySQL to JSON format.~~
*   ~~Provide a mechanism to convert ModSecurity mlogc audit log output into JSON format.~~
*   ~~Provide a mechanism to convert mlogc audit log output directly into ELK (ElasticSearch/Logstash/Kibana) to visualise the data.~~
*   Provide a mechanism to forward honest output into threat intelligence format such as STIX using something like the MISP project(https://www.misp-project.org) to share Threat data coming from the Honeypots making it easy to export/import data from formats such as STIX and TAXII., may require use of concurrent logs in a format that MISP can deal with.
*   ~~Consider new alternatives for log transfer including the use of MLOGC-NG or other possible approaches.~~
*   Develop a new VM based honeypot/probe based on CRS v3.1.
*   Develop new alternative small footprint honeypot/probe formats utilising Docker & Raspberry Pi.
*   Develop machine learning approach to automatically be able to update the rule set being used by the probe based on cyber threat intelligence received.
</strong>