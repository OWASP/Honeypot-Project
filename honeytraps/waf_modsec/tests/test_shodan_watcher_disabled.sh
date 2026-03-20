#!/usr/bin/env bash
set -euo pipefail

IMAGE="${IMAGE:-waf_modsec:local}"
NAME="test-shodan-disabled-$RANDOM$RANDOM"

cleanup() { docker rm -f "$NAME" >/dev/null 2>&1 || true; }
trap cleanup EXIT

# Start without SHODAN_API_KEY
docker run -d --name "$NAME" \
  -e CRSUPDATE=false \
  -e PERSONA=generic \
  "$IMAGE" >/dev/null

sleep 3

# Container should be running normally
docker exec "$NAME" sh -lc '
  set -eu
  # Apache should be running
  pgrep -x httpd || pgrep -x apache2
  # shodan_watcher should NOT be running
  ! pgrep -f shodan_watcher.py
'

echo "PASS: container runs normally without SHODAN_API_KEY, watcher disabled"
