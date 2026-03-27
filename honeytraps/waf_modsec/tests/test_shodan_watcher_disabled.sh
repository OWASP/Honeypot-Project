#!/usr/bin/env bash
set -euo pipefail

IMAGE="${IMAGE:-waf_modsec:local}"
NAME="test-shodan-disabled-$RANDOM$RANDOM"
NETWORK="test-shodan-disabled-net-$RANDOM$RANDOM"
PERSONA_NAME="test-shodan-persona-$RANDOM$RANDOM"

cleanup() {
  docker rm -f "$PERSONA_NAME" >/dev/null 2>&1 || true
  docker rm -f "$NAME" >/dev/null 2>&1 || true
  docker network rm "$NETWORK" >/dev/null 2>&1 || true
}
trap cleanup EXIT

# Provide persona-app backend so Apache proxy can serve requests.
docker network create "$NETWORK" >/dev/null
docker run -d --name "$PERSONA_NAME" \
  --network "$NETWORK" \
  --network-alias persona-app \
  nginx:alpine >/dev/null

# Start without SHODAN_API_KEY
docker run -d --name "$NAME" \
  --network "$NETWORK" \
  -e CRSUPDATE=false \
  -e LOGSTASH_HOST=127.0.0.1:5044 \
  -e SHODAN_API_KEY="" \
  "$IMAGE" >/dev/null

sleep 2

# Container should still be running
docker inspect "$NAME" --format '{{.State.Running}}' | grep -q "true"

# Apache should be serving traffic (allow startup/proxy warmup time)
ready=false
for _ in {1..30}; do
  if docker exec "$NAME" sh -lc 'curl -fsS --max-time 2 http://127.0.0.1/ >/dev/null'; then
    ready=true
    break
  fi
  sleep 1
done

if [ "$ready" != "true" ]; then
  echo "FAIL: Apache/proxy did not become ready" >&2
  docker logs "$NAME" >&2 || true
  exit 1
fi

# Logs should confirm watcher disabled
docker logs "$NAME" 2>&1 | grep -q "Shodan watcher disabled"

echo "PASS: container runs normally without SHODAN_API_KEY, watcher disabled"
