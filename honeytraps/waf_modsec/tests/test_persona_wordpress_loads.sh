#!/usr/bin/env bash
set -euo pipefail

IMAGE="${IMAGE:-waf_modsec:local}"
NAME="test-persona-wordpress-$RANDOM$RANDOM"

cleanup() { docker rm -f "$NAME" >/dev/null 2>&1 || true; }
trap cleanup EXIT

docker run -d --name "$NAME" \
  -e CRSUPDATE=false \
  -e PERSONA=wordpress \
  "$IMAGE" >/dev/null

sleep 3

docker exec "$NAME" sh -lc '
  set -eu
  # index.html should contain WordPress generator tag
  grep -q "WordPress" /usr/local/apache2/htdocs/index.html
  # robots.txt should contain wp-admin
  grep -q "wp-admin" /usr/local/apache2/htdocs/robots.txt
  # modsecurity-extension.conf should contain WordPress rules
  grep -q "wp-login" /app/modsecurity-extension.conf
'

echo "PASS: wordpress persona files loaded correctly"
