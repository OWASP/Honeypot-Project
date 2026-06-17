
#!/usr/bin/env bash

set -euo pipefail

IMAGE="${IMAGE:-waf_modsec:local}"
NAME="test-entry-order-$RANDOM$RANDOM"
NETWORK="test-entry-order-net-$RANDOM$RANDOM"
PERSONA_NAME="test-entry-persona-$RANDOM$RANDOM"
TMPDIR="$(mktemp -d)"

cleanup() {
  docker rm -f "$PERSONA_NAME" >/dev/null 2>&1 || true
  docker rm -f "$NAME" >/dev/null 2>&1 || true
  docker network rm "$NETWORK" >/dev/null 2>&1 || true
  rm -rf "$TMPDIR"
}
trap cleanup EXIT

# Fake updater: sleeps, then writes an OK status file
cat >"$TMPDIR/crs_update.sh" <<'SH'
#!/bin/sh
set -eu
STATUS="${CRS_UPDATE_STATUS_FILE:-/tmp/crs_update_status.json}"
echo "[fake-updater] starting" >&2
sleep 3
mkdir -p "$(dirname "$STATUS")" 2>/dev/null || true
printf "%s\n" '{"attempted":true,"result":"ok","reason":"fake","crsVersion":"fake","tarballUrl":"fake","crsDir":"/etc/modsecurity.d/owasp-crs"}' > "$STATUS"
echo "[fake-updater] done" >&2
exit 0
SH
chmod +x "$TMPDIR/crs_update.sh"

# Provide persona-app DNS target so Apache proxy can serve traffic.
docker network create "$NETWORK" >/dev/null
docker run -d --name "$PERSONA_NAME" \
  --network "$NETWORK" \
  --network-alias persona-app \
  nginx:alpine >/dev/null

docker run -d --name "$NAME" \
  --network "$NETWORK" \
  -e CRSUPDATE=true \
  -e LOGSTASH_HOST=127.0.0.1:5044 \
  -e CRS_UPDATE_STATUS_FILE=/tmp/crs_update_status.json \
  -v "$TMPDIR/crs_update.sh:/crs_update.sh:ro" \
  "$IMAGE" >/dev/null

# During updater sleep, Apache should NOT be serving yet
sleep 1
if docker exec "$NAME" sh -lc 'curl -fsS --max-time 1 http://127.0.0.1/ >/dev/null 2>&1'; then
  echo "FAIL: HTTP served before updater completed" >&2
  docker logs "$NAME" >&2 || true
  exit 1
fi

# After updater completes, HTTP should come up and status should exist
for _ in {1..30}; do
  if docker exec "$NAME" sh -lc 'curl -fsS --max-time 1 http://127.0.0.1/ >/dev/null 2>&1'; then
    docker exec "$NAME" sh -lc 'test -f /tmp/crs_update_status.json && grep -Eq "\"result\":\"ok\"" /tmp/crs_update_status.json'
    echo "PASS: updater ran before Apache served traffic"
    exit 0
  fi
  sleep 0.5
done

echo "FAIL: HTTP never became ready" >&2
docker logs "$NAME" >&2 || true
exit 1
