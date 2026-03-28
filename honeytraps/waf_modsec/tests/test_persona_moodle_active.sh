#!/usr/bin/env bash
set -euo pipefail

NAME="test-moodle-$RANDOM$RANDOM"

cleanup() { docker rm -f "$NAME" >/dev/null 2>&1 || true; }
trap cleanup EXIT

docker build -t test-moodle-persona ./personas/moodle >/dev/null 2>&1
docker run -d --name "$NAME" \
  -p 0:80 \
  test-moodle-persona >/dev/null

sleep 3

PORT="$(docker inspect "$NAME" \
  --format '{{(index (index .NetworkSettings.Ports "80/tcp") 0).HostPort}}')"

HEADERS="$(curl -sI "http://localhost:${PORT}/")"
grep -qi "X-Powered-By" <<< "$HEADERS"
grep -qi "PHP" <<< "$HEADERS"

grep -qi "Moodle 3.9.3" <<< "$(curl -fsS "http://localhost:${PORT}/")"
grep -qi "Log in" <<< "$(curl -fsS "http://localhost:${PORT}/login/index.php")"
grep -q "/admin/" <<< "$(curl -fsS "http://localhost:${PORT}/robots.txt")"

echo "PASS: Moodle persona container has correct fingerprint"
