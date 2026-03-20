#!/usr/bin/env bash
set -euo pipefail

IMAGE="${IMAGE:-waf_modsec:local}"
NAME="test-persona-swap-$RANDOM$RANDOM"

cleanup() { docker rm -f "$NAME" >/dev/null 2>&1 || true; }
trap cleanup EXIT

docker run -d --name "$NAME" \
  -e CRSUPDATE=false \
  -e PERSONA=generic \
  "$IMAGE" >/dev/null

sleep 3

# Trigger persona swap to wordpress
docker exec "$NAME" sh -lc 'echo "wordpress" > /tmp/persona_swap'

sleep 6

# Verify wordpress persona is now loaded
docker exec "$NAME" sh -lc '
  set -eu
  grep -q "WordPress" /usr/local/apache2/htdocs/index.html
  grep -q "wp-admin" /usr/local/apache2/htdocs/robots.txt
  grep -q "wp-login" /app/modsecurity-extension.conf
'

echo "PASS: persona swap from generic to wordpress works correctly"
