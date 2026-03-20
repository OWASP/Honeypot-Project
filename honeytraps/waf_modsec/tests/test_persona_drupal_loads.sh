#!/usr/bin/env bash
set -euo pipefail

IMAGE="${IMAGE:-waf_modsec:local}"
NAME="test-persona-drupal-$RANDOM$RANDOM"

cleanup() { docker rm -f "$NAME" >/dev/null 2>&1 || true; }
trap cleanup EXIT

docker run -d --name "$NAME" \
  -e CRSUPDATE=false \
  -e PERSONA=drupal \
  "$IMAGE" >/dev/null

sleep 3

docker exec "$NAME" sh -lc '
  set -eu
  # index.html should contain Drupal generator tag
  grep -q "Drupal" /usr/local/apache2/htdocs/index.html
  # robots.txt should contain Drupal paths
  grep -q "/core/" /usr/local/apache2/htdocs/robots.txt
  # modsecurity-extension.conf should contain Drupal rules
  grep -q "user/login" /app/modsecurity-extension.conf
'

echo "PASS: drupal persona files loaded correctly"
