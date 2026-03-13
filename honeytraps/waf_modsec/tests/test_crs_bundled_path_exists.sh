
#!/usr/bin/env bash

set -euo pipefail

IMAGE="${IMAGE:-waf_modsec:local}"
NAME="test-crs-bundled-$RANDOM$RANDOM"

cleanup() { docker rm -f "$NAME" >/dev/null 2>&1 || true; }
trap cleanup EXIT

docker run -d --name "$NAME" -e CRSUPDATE=false "$IMAGE" >/dev/null

docker exec "$NAME" sh -lc '
  set -eu
  CRS_DIR="/etc/modsecurity.d/owasp-crs"

  test -f /etc/modsecurity.d/include.conf
  test -f /etc/modsecurity.d/modsecurity.conf

  # include.conf expects these paths
  test -d "$CRS_DIR"
  test -f "$CRS_DIR/crs-setup.conf"
  test -d "$CRS_DIR/rules"
  ls -1 "$CRS_DIR"/rules/*.conf >/dev/null
'

echo "PASS: bundled CRS exists where include.conf expects"
