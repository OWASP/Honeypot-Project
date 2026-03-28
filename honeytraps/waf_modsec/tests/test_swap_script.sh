#!/usr/bin/env bash
set -euo pipefail

IMAGE="${IMAGE:-waf_modsec:local}"
NETWORK="test-honeypot-$RANDOM$RANDOM"
GENERIC_NAME="persona-generic"
WP_NAME="persona-wordpress"

cleanup() {
  docker rm -f "$GENERIC_NAME" "$WP_NAME" >/dev/null 2>&1 || true
  docker network rm "$NETWORK" >/dev/null 2>&1 || true
}
trap cleanup EXIT

# Create test network
docker network create "$NETWORK" >/dev/null

# Start generic persona
docker run -d --name "$GENERIC_NAME" \
  --network "$NETWORK" \
  --network-alias persona-app \
  nginx:alpine >/dev/null

sleep 2

# Verify generic is running
grep -q "true" <<< "$(docker inspect "$GENERIC_NAME" --format '{{.State.Running}}')"

# Build wordpress persona if not exists
docker build -t persona-wordpress-test ./personas/wordpress >/dev/null 2>&1

# Pre-create wordpress container so swap_persona.sh can docker start it
docker create --name "$WP_NAME" \
  --network "$NETWORK" \
  --network-alias persona-app \
  persona-wordpress-test >/dev/null 2>&1 || true

# Run swap script inside WAF container
WAF_CONTAINER="$(docker run -d \
  -e CRSUPDATE=false \
  -e SHODAN_API_KEY="" \
  -v /var/run/docker.sock:/var/run/docker.sock \
  "$IMAGE")"

sleep 3

docker exec "$WAF_CONTAINER" /app/scripts/swap_persona.sh wordpress

sleep 2

# Verify wordpress is now running
grep -q "true" <<< "$(docker inspect "$WP_NAME" --format '{{.State.Running}}')"

# Verify generic is stopped
grep -q "false" <<< "$(docker inspect "$GENERIC_NAME" --format '{{.State.Running}}')"

docker rm -f "$WAF_CONTAINER" >/dev/null 2>&1 || true

echo "PASS: swap_persona.sh correctly stopped generic and started wordpress"
