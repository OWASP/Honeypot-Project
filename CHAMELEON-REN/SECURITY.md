# 🛡️ CHAMELEON-REN: Security & Privacy Guide

**Document Purpose:** Proof of GDPR Compliance, IAM Integration, and Operational Sandboxing for NREN deployments.  
**Target Audience:** University IT Security Teams, Legal & Compliance Officers, SOC NREN Operators.

## 📖 Overview
Operating a high-interaction honeypot on a Research and Education (R&E) network carries inherent risks. The CHAMELEON-REN architecture has been engineered with a "Zero-Trust, Zero-Egress" philosophy to ensure the system safely absorbs cyberattacks without risking campus network integrity or violating European data privacy laws.

---

## 🛑 Section 1: System Hardening & Isolation

### 1.1 Egress Denial (Network Isolation)
* **Architecture:** All vulnerable persona containers are strictly bound to the `chameleon_internal` Docker bridge network.
* **Mechanism:** No ports are mapped to the external host interface (`0.0.0.0`). The only path in or out is through the strictly controlled Layer 1 Nginx Reverse Proxy.
* **Result:** If an attacker achieves Remote Code Execution (RCE) on a honeypot persona, they cannot initiate outbound connections to download malware payloads or participate in DDoS botnets.

### 1.2 Resource Starvation (Compute Limits)
* **Architecture:** Hard physical limits are enforced on the host's compute resources via Docker `deploy` configurations.
* **Mechanism:** Every persona container is strictly limited to 0.50 CPUs and 512M of RAM.
* **Result:** Cryptomining or volumetric attack attempts will immediately hit a compute ceiling, rendering the attack unviable and protecting the AWS billing account.

---

## 🔑 Section 2: Identity & Access Management (AWS IAM)
To achieve a "Zero-Touch" deployment without risking credential theft, CHAMELEON-REN relies entirely on dynamic AWS IAM Roles.

* **No Hardcoded Keys:** AWS Access Keys are **never** stored in the `.env` file or container environmental variables.
* **Principle of Least Privilege:** Terraform automatically generates an IAM Instance Profile granting the EC2 instance strictly scoped `s3:PutObject` permissions solely for the designated telemetry bucket. If the honeypot is compromised, the attacker cannot access or enumerate the wider AWS environment.

---

## ⚖️ Section 3: Privacy & Retention Standards (GDPR Compliance)
Because honeypots inadvertently capture IP addresses and potentially raw payload data (which can contain Personally Identifiable Information - PII), CHAMELEON-REN operates under strict GDPR data minimization principles.

### 3.1 IP Pseudonymisation (Salted SHA-256)
Raw attacker IP addresses are never stored in plain text.
* **Mechanism:** The Layer 4 Logstash pipeline applies a cryptographic Salted SHA-256 hash to the `source_ip` field before the data ever leaves the compute instance.
* **Compliance:** This transforms PII into pseudonymised telemetry, allowing SOC analysts to track repeat offenders without violating data privacy laws.

### 3.2 Payload Truncation & Sanitization
* **Mechanism:** Logstash is configured to extract only the specific attack vectors (e.g., SQLi strings, malicious User-Agents, triggered ModSecurity rules). Raw, unparsed HTTP request bodies are dropped.
* **Compliance:** This guarantees that if an attacker inadvertently uploads a file containing third-party PII, that data is destroyed in transit and never enters the S3 Data Lake.

### 3.3 Automated S3 Lifecycle Deletion Rules
Data is not held indefinitely. The Terraform IaC blueprint configures the S3 Telemetry Bucket with strict lifecycle policies:
1. **Active Storage:** Telemetry is kept in hot storage for 30 days for immediate SOC analysis.
2. **Cold Storage:** Data is transitioned to AWS Glacier for academic historical review.
3. **Data Death:** All records are automatically and permanently deleted after 5 years, satisfying standard R&E grant retention maximums.

---

## ✅ Section 4: Pre-Flight Security Checklist
Before exposing the CHAMELEON-REN system to the public internet, the NREN operator must verify the following:

- [ ] **Vault Lockdown (`chmod 600`):** Has the `.env` file been restricted to root-only access to prevent unauthorized lateral credential theft?
- [ ] **Infrastructure Secrets:** Verified that the `.env` and `.terraform` directories are excluded from version control via the strict `.gitignore` policy.
- [ ] **IAM Integrity:** Verified that the deployment relies on the AWS EC2 IAM Instance Profile, with NO static `AWS_ACCESS_KEY_ID` variables present in the environment.
- [ ] **Administrative Lockdown:** Verified in `main.tf` that Port 22 (SSH) is explicitly locked down from `0.0.0.0/0` to the specific `/32` IP address of the authorized operator prior to deployment.
- [ ] **Default Passwords:** Verified that all dummy database credentials (`.env.example`) have been securely changed.
- [ ] **Container Isolation:** Verified that no persona container utilizes the `ports: ["80:80"]` directive, relying entirely on internal proxy routing.
