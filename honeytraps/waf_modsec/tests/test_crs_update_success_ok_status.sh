
#!/usr/bin/env bash

set -euo pipefail

IMAGE="${IMAGE:-waf_modsec:local}"
NAME="test-crs-update-$RANDOM$RANDOM"

cleanup() { docker rm -f "$NAME" >/dev/null 2>&1 || true; }
trap cleanup EXIT

# Start a container we can exec into
docker run -d --name "$NAME" -e CRSUPDATE=false "$IMAGE" >/dev/null

# Run the real updater script (as shipped in your Dockerfile)
docker exec "$NAME" sh -lc '
  set -eu
  /crs_update.sh
'

# Validate that CRS is still in a usable state, and Apache config parses
docker exec "$NAME" sh -lc '
  set -eu
  CRS_DIR="/etc/modsecurity.d/owasp-crs"

  test -d "$CRS_DIR"
  test -f "$CRS_DIR/crs-setup.conf"
  test -d "$CRS_DIR/rules"
  ls -1 "$CRS_DIR"/rules/*.conf >/dev/null

  # Basic syntax check (does not start Apache)
  apachectl -t
'

echo "PASS: updater runs and CRS remains loadable"
