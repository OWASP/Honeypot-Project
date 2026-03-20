#!/usr/bin/env bash
set -euo pipefail

IMAGE="${IMAGE:-waf_modsec:local}"
NAME="test-persona-fallback-$RANDOM$RANDOM"

cleanup() { docker rm -f "$NAME" >/dev/null 2>&1 || true; }
trap cleanup EXIT

docker run -d --name "$NAME" \
  -e CRSUPDATE=false \
  -e PERSONA=nonexistent_persona \
  "$IMAGE" >/dev/null

sleep 3

# Container should still be running (fallback to generic, not crash)
docker exec "$NAME" sh -lc '
  set -eu
  test -f /usr/local/apache2/htdocs/index.html
  test -f /app/modsecurity-extension.conf
'

echo "PASS: unknown persona falls back to generic correctly"
