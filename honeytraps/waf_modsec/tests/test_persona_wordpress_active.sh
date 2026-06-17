#!/usr/bin/env bash
set -euo pipefail

IMAGE="${IMAGE:-waf_modsec:local}"
NETWORK="test-honeypot-$RANDOM$RANDOM"
WAF_NAME="test-waf-wp-$RANDOM$RANDOM"
WP_NAME="test-wp-$RANDOM$RANDOM"

cleanup() {
  docker rm -f "$WAF_NAME" "$WP_NAME" >/dev/null 2>&1 || true
  docker network rm "$NETWORK" >/dev/null 2>&1 || true
}
trap cleanup EXIT

# Create test network
docker network create "$NETWORK" >/dev/null

# Start WordPress persona container with persona-app alias
docker run -d --name "$WP_NAME" \
  --network "$NETWORK" \
  --network-alias persona-app \
  --build-arg . \
  $(docker build -q ./personas/wordpress) >/dev/null 2>&1 || \
docker run -d --name "$WP_NAME" \
  --network "$NETWORK" \
  --network-alias persona-app \
  waf_modsec_persona-wordpress 2>/dev/null || true

sleep 3

# Check WordPress fingerprint headers directly from persona container
HEADERS="$(curl -sI "http://localhost:$(docker inspect "$WP_NAME" \
  --format '{{(index (index .NetworkSettings.Ports "80/tcp") 0).HostPort}}' 2>/dev/null || echo 9999)/" 2>/dev/null || true)"

# Verify WordPress body or response headers (avoid wget|grep SIGPIPE with pipefail)
BODY="$(docker exec "$WP_NAME" wget -qO- http://localhost/ 2>/dev/null || printf '')"
HDRS="$(docker exec "$WP_NAME" wget -qS http://localhost/ 2>&1 || true)"
grep -qi "WordPress" <<< "$BODY" || grep -qi "PHP/7.4.3" <<< "$HDRS"

VER="$(docker exec "$WP_NAME" wget -qO- http://localhost/wp-includes/version.php 2>/dev/null || printf '')"
grep -q '$wp_version' <<< "$VER"
grep -q '5.8.1' <<< "$VER"

echo "PASS: WordPress persona container has correct fingerprint"
