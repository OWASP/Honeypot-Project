

OWASP Honeypot Project

Real-time web application threat intelligence and attack data collection

The OWASP Honeypot Project identifies emerging attacks against web applications and reports them to the security community, facilitating protection against targeted threats.
Based on the earlier OWASP/WASC Distributed Web Honeypots Project (GitHub)

Table of Contents

About
Quick Start
Prerequisites
Getting Started
Repository Structure
Documentation
Use Cases
Troubleshooting
Contributing
Project Status


About
The OWASP Honeypot Project provides:

Real-time Web Application Threat Data - Live attack detection and logging
Community Threat Reports - Shared intelligence on emerging attack patterns
ModSecurity-Based Honeypots - Industry-standard WAF technology
Multiple Deployment Options - Docker, VM, cloud-ready solutions


Quick Start
Get a basic honeypot running in under 5 minutes:
Bash# 1. Clone the repository
git clone https://github.com/OWASP/Honeypot-Project.git
cd Honeypot-Project

# 2. Navigate to the honeytrap directory
cd honeytraps/waf_modsec

# 3. Copy and configure environment variables
cp sample-env .env
# Edit .env with your settings

# 4. Start the honeypot
docker-compose up -d

# 5. Check logs
docker-compose logs -f

Your honeypot is now capturing attacks! See Getting Started for detailed setup.

Prerequisites
Before you begin, ensure you have:
Required Software

Docker: Version 20.10+ (Install Docker)
Docker Compose: Version 1.29+ (Install Compose)
Git: For cloning the repository

System Requirements

RAM: Minimum 4GB (8GB+ recommended for ELK stack)
Disk Space: 10GB free space minimum
Network: Open ports 80, 443, and ELK stack ports (9200, 5601, 5044)
OS: Linux (Ubuntu 20.04+), macOS, or Windows with WSL2

Optional (for advanced features)

MISP Server: For threat intelligence integration
Cloud Account: AWS/Azure/GCP for distributed deployment
Python 3.8+: For custom scripts and PyMISP integration


Getting Started
Step 1: Choose Your Deployment
Select the setup that matches your needs:



Setup
Purpose
Best For




waf_modsec
Basic ModSecurity honeypot
First-time users, testing


waf_elk
Honeypot + ELK visualization
Production monitoring


mds_elk
ModSecurity logs to ELK via Filebeat
Existing ModSecurity users


mlogc_elk
ModSecurity logs via mlogc
Legacy audit log collectors



Step 2: Basic Setup (waf_modsec)
Bashcd honeytraps/waf_modsec

# Configure environment
cp sample-env .env
nano .env  # Edit with your settings

# Start services
docker-compose up -d

# Verify it's running
docker-compose ps

Step 3: Advanced Setup (with ELK Stack)
Bashcd honeytraps/waf_elk

# Configure environment
cp misp-push/sample-env misp-push/.env

# Start ELK and honeypot
./start_docker.sh

# Access Kibana
open http://localhost:5601

Step 4: Configure MISP Integration (Optional)
For threat intelligence sharing:
Bashcd honeytraps/misp

# Setup MISP server
./setup_misp.sh

# Configure and run
./run_misp.sh

See misp-doc/README.md for detailed MISP configuration.

Repository Structure
This repository is organized into focused components:



Directory
Purpose
Quick Link




honeytraps/
Core honeypot implementations with threat reporting
View →


↳ waf_modsec/
ModSecurity-based honeypot probe
Setup Guide →


↳ waf_elk/
Honeypot with ELK stack integration
Setup Guide →


↳ misp/
MISP threat intelligence integration
Setup Guide →


mds_elk/
ModSecurity → ELK via Filebeat (PoC)
View →


mlogc_elk/
ModSecurity → ELK via mlogc (PoC)
View →


misp-doc/
MISP server setup and PyMISP examples
View →




Documentation
Each component has detailed documentation:

Honeytrap Architecture - Overview and design
ModSecurity Honeypot Setup - Detailed deployment guide
ELK Integration Guide - Visualization and analysis
MISP Threat Intel Setup - Threat intelligence sharing
AWS ECS Deployment - Cloud deployment


Use Cases
Security Research
Monitor real-world attacks against web applications in controlled environments
Threat Intelligence
Generate actionable intelligence on attack patterns, tools, and techniques
Blue Team Training
Provide realistic attack data for SOC analysts and incident responders
Community Protection
Share threat data via MISP to help organizations defend proactively

Troubleshooting
Common Issues
Docker containers won't start
Bash# Check Docker is running
docker ps

# Check logs for errors
docker-compose logs

# Verify ports aren't in use
netstat -tuln | grep -E '80|443|5601|9200'

ELK stack fails with memory errors
Bash# Increase Docker memory (Docker Desktop)
# Settings → Resources → Memory: Set to 8GB+

# Or set vm.max_map_count for Elasticsearch
sudo sysctl -w vm.max_map_count=262144

Can't access Kibana at localhost:5601
Bash# Wait for Elasticsearch to fully start (can take 2-3 minutes)
docker-compose logs elasticsearch

# Check Elasticsearch health
curl http://localhost:9200/_cluster/health

No attacks being logged
Bash# Verify honeypot is exposed to internet (if testing)
# Check ModSecurity is in DetectionOnly mode
# Review logs for configuration errors
docker-compose logs modsecurity

Getting Help

Check component-specific README files in each directory
Review screenshots in honeytraps/screenshots/ for expected output
Open an issue on GitHub Issues


Contributing
We welcome contributions! Here's how to get started:

Fork the repository
Create a feature branch: git checkout -b feature/your-feature
Make your changes
Test thoroughly: Ensure Docker builds and runs correctly
Submit a Pull Request

Contribution Ideas

Add new honeypot personas (see honeytraps/waf_modsec/personas/)
Improve documentation and examples
Create new ELK dashboards
Develop additional threat intelligence integrations
Fix bugs and improve error handling



ModSecurity-based honeypot probes
ELK stack integration (Filebeat and mlogc)
MISP threat intelligence sharing
Docker and cloud deployment options
Multiple honeypot personas (WordPress, Drupal, Moodle, etc.)
Automated threat detection and logging


📋 Roadmap
See CHANGELOG.md for detailed version history and upcoming features.

License
This project is part of OWASP and follows OWASP licensing guidelines.
