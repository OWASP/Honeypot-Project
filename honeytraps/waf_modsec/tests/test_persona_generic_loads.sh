#!/usr/bin/env bash
set -euo pipefail

IMAGE="${IMAGE:-waf_modsec:local}"
NAME="test-persona-generic-$RANDOM$RANDOM"

cleanup() { docker rm -f "$NAME" >/dev/null 2>&1 || true; }
trap cleanup EXIT

docker run -d --name "$NAME" \
  -e CRSUPDATE=false \
  -e PERSONA=generic \
  "$IMAGE" >/dev/null

sleep 3

docker exec "$NAME" sh -lc '
  set -eu
  test -f /usr/local/apache2/htdocs/index.html
  test -f /usr/local/apache2/htdocs/login.html
  test -f /usr/local/apache2/htdocs/robots.txt
  test -f /app/modsecurity-extension.conf
'

echo "PASS: generic persona files loaded correctly"
