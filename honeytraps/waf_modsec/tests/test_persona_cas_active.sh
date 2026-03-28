#!/usr/bin/env bash
set -euo pipefail

NAME="test-cas-$RANDOM$RANDOM"

cleanup() { docker rm -f "$NAME" >/dev/null 2>&1 || true; }
trap cleanup EXIT

docker build -t test-cas-persona ./personas/cas >/dev/null 2>&1
docker run -d --name "$NAME" \
  -p 0:80 \
  test-cas-persona >/dev/null

sleep 3

PORT="$(docker inspect "$NAME" \
  --format '{{(index (index .NetworkSettings.Ports "80/tcp") 0).HostPort}}')"

grep -qi "Central Authentication" <<< "$(curl -fsS "http://localhost:${PORT}/cas/login")"
grep -q "UP" <<< "$(curl -fsS "http://localhost:${PORT}/cas/status")"
grep -qi "SAML2" <<< "$(curl -fsS "http://localhost:${PORT}/idp/profile/SAML2/Redirect/SSO")"
grep -q "/cas/" <<< "$(curl -fsS "http://localhost:${PORT}/robots.txt")"

echo "PASS: CAS/SAML persona container has expected endpoints"
