#!/usr/bin/env bash
# Bootstrap script for a honeypot sensor node.
# Runs as root via EC2 user_data on first boot.
# All output is mirrored to /var/log/honeypot-bootstrap.log and the system journal
# so failures are easy to diagnose from the EC2 console or CloudWatch.
#
# shellcheck disable=SC2154
# ${node_tag}, ${aws_region}, ${repo_url}, ${logstash_host}, ${shodan_api_key},
# ${honeypot_persona}, ${honeypot_profile} are Terraform templatefile()
# substitutions. They are fully resolved before this script is ever executed
# by bash on the EC2 instance.

set -euo pipefail
exec > >(tee /var/log/honeypot-bootstrap.log | logger -t honeypot-bootstrap -s 2>/dev/console) 2>&1

echo "=== honeypot bootstrap starting ==="
echo "node_tag: ${node_tag}"
echo "region:   ${aws_region}"

# --- system packages ---
apt-get update -y
apt-get install -y git docker.io docker-compose-v2

systemctl enable docker
systemctl start docker
usermod -aG docker ubuntu

# --- clone repo ---
REPO_DIR="/home/ubuntu/honeypot"
git clone "${repo_url}" "$REPO_DIR"
chown -R ubuntu:ubuntu "$REPO_DIR"

# --- write .env so docker compose picks up the right values ---
# LOGSTASH_HOST wires Filebeat (already baked into the WAF image) to the
# central Logstash instance. The other env vars are read by persona_watchdog.py
# and the Logstash filter mutate block to tag every event with region and node.
cat > "$REPO_DIR/honeytraps/.env" <<ENV
LOGSTASH_HOST=${logstash_host}
SHODAN_API_KEY=${shodan_api_key}
HONEYPOT_NODE_ID=${node_tag}
AWS_REGION=${aws_region}
HONEYPOT_PERSONA=${honeypot_persona}
HONEYPOT_PROFILE=${honeypot_profile}
ENV

chown ubuntu:ubuntu "$REPO_DIR/honeytraps/.env"

# --- start the WAF stack ---
cd "$REPO_DIR/honeytraps/waf_modsec"
docker compose up -d

echo "=== honeypot bootstrap complete ==="
