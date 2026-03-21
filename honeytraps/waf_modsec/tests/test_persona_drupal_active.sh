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

# Check Drupal fingerprint header
HEADERS="$(curl -sI "http://localhost:${PORT}/")"
echo "$HEADERS" | grep -qi "X-Generator"
echo "$HEADERS" | grep -qi "Drupal"

# Check Drupal index page has generator meta
curl -s "http://localhost:${PORT}/" | grep -qi "Drupal"

# Check robots.txt has Drupal paths
curl -s "http://localhost:${PORT}/robots.txt" | grep -q "/core/"

echo "PASS: Drupal persona container has correct fingerprint"
