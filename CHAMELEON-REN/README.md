# 🦎 CHAMELEON-REN: Operator Handbook

**Target Audience:** NREN Security Operations Centers (SOC)  
**Version:** 1.0.0 (Release Candidate)  
**SLA:** Deployment to Operational State in ≤ 60 Minutes  

## 📖 Overview
CHAMELEON-REN is a modular, high-interaction honeypot architecture designed specifically for the Research and Education (R&E) sector. It utilises a Layer 1 dynamic routing engine to instantly swap vulnerable "personas" (e.g., Student Information Systems, VLEs, ERPs) based on real-time attacker behavior, funnelling all telemetry to a secure, pseudonymised S3 data lake.

This runbook details the standardized **"Zero-Touch"** deployment pipeline and the strict integration schema for injecting new personas.

---

## 🚀 Section 1: Installation & Config Guide (Quickstart)

### Prerequisites
* **Local Machine:** Linux, macOS, or Windows (via WSL2) terminal with `git`, `terraform` (v1.5+), and `aws-cli` installed.
* **Target Environment:** AWS Account (Any Global Region) with administrative IAM privileges.
* **SSH Key Pair:** Log into your AWS EC2 Console, create a new RSA Key Pair named exactly `chameleon-key`, and download the `.pem` file to your local machine. Secure it locally: `chmod 400 chameleon-key.pem`.

### Deployment Pipeline

**Step 1: Vault Configuration**
Clone the repository and initialize the environment variables. **Do NOT commit the `.env` file.**
*(Note: AWS Credentials are no longer required in the `.env` file. The system utilizes automated AWS IAM Roles).*

```bash
git clone [https://github.com/gautamjuvarajiya/chameleon-ren-release.git](https://github.com/gautamjuvarajiya/chameleon-ren-release.git)
cd chameleon-ren-release
cp .env.example .env
nano .env # Populate your Shodan API Key and secure Database Passwords
```

**Step 2: Cloud Infrastructure Provisioning (Terraform)**
Execute the IaC blueprint. This provisions the EC2 Sensor, strict Security Groups (Ports 80/443 open), the S3 Telemetry Bucket, and the IAM Instance Profile.

```bash
terraform init
terraform plan
terraform apply --auto-approve
```

**Step 3: Automated Sensor Instantiation & Verification**
CHAMELEON-REN utilises a fully automated `user_data` provisioning script. You do not need to manually install Docker or configure the honeypot. Terraform dynamically fetches the newly created S3 Bucket name and injects it into the EC2 host automatically.

1. Once Terraform outputs `Apply complete!`, note the generated AWS Public IP address.
2. **Wait exactly 3 to 5 minutes.** (AWS is pulling the containers and configuring the self-healing telemetry pipeline).
3. SSH into the newly provisioned EC2 instance:
   ```bash
   ssh -i "chameleon-key.pem" ubuntu@<EC2_PUBLIC_IP>
   ```
4. Verify the zero-touch deployment limits (0.50 CPU / 512MiB RAM) are enforced:
   ```bash
   docker stats --no-stream
   ```
5. Verify all layers are running successfully: `docker compose ps`

---

## 🧩 Section 2: Persona Integration Schema (SOP)

CHAMELEON-REN is designed for modular extensibility. To add a new deception persona (e.g., a vulnerable Joomla CMS), SOC operators must strictly follow this four-step schema to inherit the unified security, routing, and telemetry properties.

### Step 1: Container Definition (`docker-compose.yml`)
* ⚠️ **Crucial Rule (Egress Isolation):** The container MUST only be attached to the `chameleon_internal` network. Do not expose direct host ports.
* ⚠️ **Resource Guardrails:** Enforce limits to prevent botnet participation.

```yaml
  new_persona_trap:
    image: vulnerable-joomla:latest
    networks:
      - chameleon_internal
    deploy:
      resources:
        limits:
          cpus: '0.50'
          memory: 512M
```

### Step 2: State Resilience & Database Seeding
If the persona requires a database to simulate "Data Theft," mount an exported `.sql` file into the database container's initialization directory to ensure the honeypot "self-heals" its dummy data upon reboot.

### Step 3: Edge Routing & Perimeter Spoofing (`nginx.conf`)
Add a routing block in the Layer 1 Nginx reverse proxy to strip native application headers, preventing fingerprinting.

```nginx
location /new_persona/ {
    proxy_pass http://new_persona_trap:80/;
    proxy_hide_header X-Powered-By;
    proxy_hide_header Server;
    add_header Server nginx/1.24.0 always;
}
```

### Step 4: Telemetry Mapping (`logstash.conf`)
Tag the new persona in the JSON dataset for your SOC dashboard.

```ruby
else if [request][uri] =~ "/new_persona" {
  mutate { add_field => { "active_persona" => "Joomla CMS (Trap Type)" } }
}
```

---

## ⚙️ Section 3: Switching Rules & Troubleshooting

### The Python Switching Engine Logic
The Layer 1 Python Stimulus Engine sits behind Nginx and reads raw incoming traffic.
1. **Shodan Evasion:** The script dynamically fetches the AWS host's public IP on boot. If the IP matches the Shodan API `honeypot` tag, it routes all traffic to a benign static page to evade scanners.
2. **Path Matching:** If the attacker requests `/moodle`, the engine dynamically switches the upstream route to the Moodle container.
3. **Default Fallback:** Unrecognised probes default to the WordPress portal.

### SOC Troubleshooting Cheat Sheet

| Symptom | Diagnostic Command | Remediation |
| :--- | :--- | :--- |
| **Telemetry not reaching S3** | `docker logs chameleon-ren-logstash-1` | Verify Terraform successfully attached the IAM Role to the EC2 instance. (Do NOT check `.env` for AWS keys; they are intentionally absent). |
| **Persona container crashing** | `docker stats` | Check if the container is hitting the `512M` memory limit. Adjust in `docker-compose.yml`. |
| **Attacker bypasses proxy** | `docker network inspect chameleon_internal` | Ensure the persona container has no published ports (`0.0.0.0:XX`) overriding the internal network. |
| **Shodan evasion failing** | `docker logs chameleon-ren-evasion-1` | Verify the Python engine is running and successfully fetched the dynamic Public IP. Check `SHODAN_API_KEY` validity. |
| **Pipeline/Container Death** | `docker compose ps` | **Wait 60 seconds.** The system is engineered for Chaos Resilience. Docker will auto-restart the dead service, and Filebeat's buffer ensures zero data loss during the crash. |
