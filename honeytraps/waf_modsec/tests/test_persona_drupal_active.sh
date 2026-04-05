#!/usr/bin/env bash
set -euo pipefail

IMAGE="${IMAGE:-waf_modsec:local}"
NAME="test-drupal-$RANDOM$RANDOM"

cleanup() { docker rm -f "$NAME" >/dev/null 2>&1 || true; }
trap cleanup EXIT

# Build and run drupal persona container directly
docker build -t test-drupal-persona ./personas/drupal >/dev/null 2>&1
docker run -d --name "$NAME" \
  -p 0:80 \
  test-drupal-persona >/dev/null

sleep 3

PORT="$(docker inspect "$NAME" \
  --format '{{(index (index .NetworkSettings.Ports "80/tcp") 0).HostPort}}')"

# Check Drupal fingerprint header (here-strings avoid curl|grep SIGPIPE with pipefail)
HEADERS="$(curl -sI "http://localhost:${PORT}/")"
grep -qi "X-Generator" <<< "$HEADERS"
grep -qi "Drupal" <<< "$HEADERS"

grep -qi "Drupal" <<< "$(curl -fsS "http://localhost:${PORT}/")"
grep -q "/core/" <<< "$(curl -fsS "http://localhost:${PORT}/robots.txt")"

grep -qi "Drupal" <<< "$(curl -fsS "http://localhost:${PORT}/misc/drupal.js")"
grep -q '$Id:' <<< "$(curl -fsS "http://localhost:${PORT}/misc/drupal.js")"

echo "PASS: Drupal persona container has correct fingerprint"
