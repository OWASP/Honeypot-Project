# Tomcat 9.0.98 Persona (CVE-2025-24813)

This is a discrete Docker container designed to act as a honeypot persona for Apache Tomcat.

## The Lure
This container specifically mimics **Tomcat 9.0.98**. The `DefaultServlet` in the `web.xml` configuration has been intentionally modified to set `readonly` to `false`. 

This misconfiguration allows "partial PUT" requests, serving as a high-value lure for automated scanners and attackers hunting for the **CVE-2025-24813** Remote Code Execution vulnerability.

## Usage
To spin up this standalone persona:
```bash
docker compose up -d --build