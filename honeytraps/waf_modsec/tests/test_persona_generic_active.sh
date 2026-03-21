#!/usr/bin/env bash
set -euo pipefail

IMAGE="${IMAGE:-waf_modsec:local}"
NAME="test-persona-generic-$RANDOM$RANDOM"

cleanup() { docker rm -f "$NAME" >/dev/null 2>&1 || true; }
trap cleanup EXIT

docker run -d --name "$NAME" \
  -e CRSUPDATE=false \
  -e SHODAN_API_KEY="" \
  -p 0:80 \
  "$IMAGE" >/dev/null

sleep 5

PORT="$(docker inspect "$NAME" \
  --format '{{(index (index .NetworkSettings.Ports "80/tcp") 0).HostPort}}')"

# WAF should be responding
STATUS="$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:${PORT}/")"
test "$STATUS" = "200" || test "$STATUS" = "301" || test "$STATUS" = "302"

echo "PASS: generic persona — WAF is responding"
