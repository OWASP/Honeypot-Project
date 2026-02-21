Overview

This project provides a containerised demonstration environment for an OWASP ModSecurity Web Application Firewall (WAF) honeypot.

The objective of this demo is to:

=> Deploy Apache with ModSecurity 2.9.x
=> Integrate OWASP Core Rule Set (CRS 3.3.8)
=> Implement custom HoneyTrap deception rules
=> Enable persistent IP tracking (stateful behaviour)
=> Provide a working telemetry pipeline (ModSecurity → Filebeat → Logstash)
=> Deliver a stable, reproducible, demonstration-ready environment

The system is designed for research, demonstration, and educational purposes.


1. Architecture

Windows 10/11
→ WSL2 (Ubuntu 22.04 LTS)
→ Docker Desktop (WSL backend)
→ Containers:
	1. Apache + ModSecurity (modsec_app)
	2. Logstash

This setup mirrors a Linux production deployment while remaining lightweight for development and demonstration.


2. System Requirements

=> Windows 10/11 (or native Linux)
=> WSL2 enabled (for Windows users)
=> Ubuntu 22.04 LTS
=> Docker Desktop (WSL2 backend enabled)
=> Git


3. Installation Guide

## Step 1 – Install Docker Desktop (Windows)

=> Download from: https://www.docker.com/products/docker-desktop/

=> During installation:
	1. Enable WSL2 backend
	2. Keep default settings

Update WSL kernel:
	wsl --update
	wsl --shutdown

## Step 2 – Install Ubuntu (WSL)

=> Install Ubuntu 22.04 LTS from Microsoft Store.

Inside Ubuntu:
	sudo apt update && sudo apt upgrade -y
	sudo apt install git curl unzip

Enable Docker access inside Ubuntu:

	sudo usermod -aG docker $USER

Restart Ubuntu after running this command.

Step 3 – Clone the Repository

	git clone https://github.com/OWASP/Honeypot-Project.git
	cd Honeypot-Project/Gautam-Honeypot-Demo/waf_modsec


4. Running the Demo

1. Prepare Runtime Directories

Create required folders:
	mkdir -p modsecurity-data
	mkdir -p logstash/output
	chmod 777 modsecurity-data
	chmod 777 logstash/output

These prevent DBM permission errors and enable persistent state tracking.

2. Build and Start Containers

	docker compose build
	docker compose up -d

Verify:
	docker ps

Expected:
	modsec_app → Up (healthy)
	logstash → Up


5. Validation & Testing

# Health Check
	curl -k http://localhost:8000/healthz

Expected output:
OK

# Normal Traffic
	curl -k http://localhost:8080/

Expected:
HTTP 200
Login page displayed

# Cross-Site Scripting (XSS) Test
	curl -k "http://localhost:8080/?q=<script>alert(1)</script>"

Expected:
HTTP 403 Forbidden
CRS rule triggered

# SQL Injection (SQLi) Test
	curl -k "http://localhost:8080/?q=' OR 1=1 --"

Expected:
HTTP 403 Forbidden

# HoneyTrap Deception Test (Fake Port)
	curl -k http://localhost:8888/

Triggers custom HoneyTrap rule.

# Cookie Manipulation Test
	curl -k -H "Cookie: Admin=1" http://localhost:8080/

Triggers deception logging rule.

# Log Pipeline Verification

Processed logs can be viewed using:
	tail -n 3 logstash/output/modsec-events.ndjson

This confirms:
=> ModSecurity logging
=> Filebeat shipping
=> Logstash processing
=> Structured JSON output


6. Persistent Stateful Tracking

This demo includes a permanent fix for ModSecurity DBM storage.

Key configuration:
	SecDataDir /var/log/modsecurity-data

This directory is host-mounted to:
	./modsecurity-data

This ensures:
=> IP reputation tracking persists
=> Anomaly scores survive container restarts
=> No collection_store permission errors occur


7. Important Note Regarding ELK & MISP Folders

The following folders remain in the repository intentionally:
=> honeytraps/waf_elk
=> mds_elk
=> misp-doc
=> mlogc_elk

These are part of the broader OWASP Honeypot ecosystem.

This specific demo (Gautam-Honeypot-Demo/waf_modsec) does not require ELK or MISP to operate.

They are preserved for:
=> Future integrations
=> Other contributors
=> Extended research scenarios


8. Stopping the Environment
	docker compose down

This will:
=> Stop containers
=> Preserve configurations
=> Preserve persistent state directory


9. Summary

This project delivers:
=> Containerised OWASP ModSecurity WAF
=> CRS 3.3.8 integration
=> Custom deception rules
=> Persistent state tracking
=> Working logging pipeline
=> Stable container health monitoring

The environment is fully reproducible and suitable for technical demonstrations and research presentations.
