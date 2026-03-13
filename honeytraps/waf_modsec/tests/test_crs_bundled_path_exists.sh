
#!/usr/bin/env bash

set -euo pipefail

IMAGE="${IMAGE:-waf_modsec:local}"
NAME="test-crs-bundled-$RANDOM$RANDOM"

cleanup() { docker rm -f "$NAME" >/dev/null 2>&1 || true; }
trap cleanup EXIT

docker run -d --name "$NAME" -e CRSUPDATE=false "$IMAGE" >/dev/null

# Wait for container to be up
for _ in {1..60}; do
  if docker inspect -f '{{.State.Running}}' "$NAME" 2>/dev/null | grep -q true; then
    break
  fi
  sleep 0.25
done

docker exec "$NAME" sh -lc '
  set -eu

  # From your include.conf
  CRS_DIR="/etc/modsecurity.d/owasp-crs"

  test -f /etc/modsecurity.d/include.conf
  test -f /etc/modsecurity.d/modsecurity.conf

  test -d "$CRS_DIR"
  test -f "$CRS_DIR/crs-setup.conf"
  test -d "$CRS_DIR/rules"
  ls -1 "$CRS_DIR"/rules/*.conf >/dev/null
'

echo "PASS: bundled CRS path and includes are present"
