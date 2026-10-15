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

# --- write the env file docker compose actually reads ---
# Compose resolves env_file relative to the directory the compose file lives in,
# so this has to land in waf_modsec/. A file written one level up in honeytraps/
# is never picked up by anything. The repo ships sample-env and gitignores env,
# so after a fresh clone the file compose needs is simply not there and
# "docker compose up" refuses to start -- we have to create it here.
#
# LOGSTASH_HOST wires Filebeat (already baked into the WAF image) to the central
# Logstash instance. The rest is read by persona_watchdog.py and by the Logstash
# filter mutate block that tags every event with region and node.
COMPOSE_DIR="$REPO_DIR/honeytraps/waf_modsec"

cat > "$COMPOSE_DIR/env" <<ENV
LOGSTASH_HOST=${logstash_host}
SHODAN_API_KEY=${shodan_api_key}
HONEYPOT_NODE_ID=${node_tag}
AWS_REGION=${aws_region}
HONEYPOT_PERSONA=${honeypot_persona}
HONEYPOT_PROFILE=${honeypot_profile}
ENV

chown ubuntu:ubuntu "$COMPOSE_DIR/env"
chmod 600 "$COMPOSE_DIR/env" # holds the shodan key

# --- publish the decoy on port 80 ---
# The committed compose file maps the decoy to host port 9091 so it does not
# collide with a local web server during development. On a sensor node we want
# it on 80: that is the port the security group opens and the port scanners
# actually hit. The override file is gitignored, so writing it here is safe.
cat > "$COMPOSE_DIR/docker-compose.override.yml" <<'OVERRIDE'
services:
  modsec_crs:
    ports:
      - "80:80"
OVERRIDE

chown ubuntu:ubuntu "$COMPOSE_DIR/docker-compose.override.yml"

# --- start the WAF stack ---
cd "$COMPOSE_DIR"
docker compose up -d

# "compose up -d" still exits 0 for a container that starts and dies a second
# later, so confirm something is really running before we call this a success.
# Failing here is what makes a broken bootstrap visible in the console log
# instead of leaving a silently empty node behind.
if [ -z "$(docker compose ps --status running --quiet)" ]; then
  echo "FATAL: the WAF stack did not stay up" >&2
  docker compose ps --all >&2
  docker compose logs --no-color --tail 50 >&2
  exit 1
fi

echo "=== honeypot bootstrap complete ==="
echo "persona_watchdog.py reads the same values:"
echo "  set -a; . $COMPOSE_DIR/env; set +a"
