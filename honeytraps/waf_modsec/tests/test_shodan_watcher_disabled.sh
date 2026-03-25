#!/usr/bin/env bash
set -euo pipefail

IMAGE="${IMAGE:-waf_modsec:local}"
NAME="test-shodan-disabled-$RANDOM$RANDOM"

cleanup() { docker rm -f "$NAME" >/dev/null 2>&1 || true; }
trap cleanup EXIT

# Start without SHODAN_API_KEY
docker run -d --name "$NAME" \
  -e CRSUPDATE=false \
  -e SHODAN_API_KEY="" \
  "$IMAGE" >/dev/null

sleep 5

# Container should still be running
docker inspect "$NAME" --format '{{.State.Running}}' | grep -q "true"

# Shodan watcher should NOT be running
docker exec "$NAME" sh -lc '
  set -eu
  ! pgrep -f shodan_watcher.py
'

# Apache should be running
docker exec "$NAME" sh -lc '
  set -eu
  pgrep -x httpd || pgrep -x apache2
'

# Logs should confirm watcher disabled
docker logs "$NAME" 2>&1 | grep -q "Shodan watcher disabled"

echo "PASS: container runs normally without SHODAN_API_KEY, watcher disabled"
