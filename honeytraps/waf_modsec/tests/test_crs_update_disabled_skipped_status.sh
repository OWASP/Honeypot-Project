
#!/usr/bin/env bash
set -euo pipefail

IMAGE="${IMAGE:-waf_modsec:local}"
NAME="test-crsupdate-disabled-$RANDOM$RANDOM"

STATUS_FILE="/tmp/crs_update_status.json"
CRS_DIR="/etc/modsecurity.d/owasp-crs"

cleanup() { docker rm -f "$NAME" >/dev/null 2>&1 || true; }
trap cleanup EXIT

# Start container normally with updater disabled
docker run -d --name "$NAME" -e CRSUPDATE=false "$IMAGE" >/dev/null

# Run the updater explicitly (still disabled via env) and assert behavior
docker exec "$NAME" sh -lc "
  set -eu

  export CRSUPDATE=false
  export CRS_UPDATE_STATUS_FILE='$STATUS_FILE'

  /crs_update.sh

  test -f '$STATUS_FILE'
  status=\"\$(cat '$STATUS_FILE' | tr -d '\n\r')\"
  test \"\$status\" = '{\"attempted\":false,\"result\":\"skipped\",\"reason\":\"CRSUPDATE disabled\"}'

  # Bundled CRS should still be present and valid
  test -d '$CRS_DIR'
  test -f '$CRS_DIR/crs-setup.conf'
  test -d '$CRS_DIR/rules'
  ls -1 '$CRS_DIR'/rules/*.conf >/dev/null

  # No update/rollback dirs should be created
  test ! -e '${CRS_DIR}.new'
  test ! -e '${CRS_DIR}.old'
"

echo "PASS: CRSUPDATE disabled -> skipped status and bundled CRS remains"
