
#!/usr/bin/env bash
set -euo pipefail

IMAGE="${IMAGE:-waf_modsec:local}"
NAME="test-crs-lock-held-$RANDOM$RANDOM"

STATUS_FILE="/tmp/crs_update_status.json"
LOCK_DIR="/tmp/crsupdate.lock"
CRS_DIR="/etc/modsecurity.d/owasp-crs"

cleanup() { docker rm -f "$NAME" >/dev/null 2>&1 || true; }
trap cleanup EXIT

docker run -d --name "$NAME" -e CRSUPDATE=false "$IMAGE" >/dev/null

docker exec "$NAME" sh -lc "
  set -eu

  # Simulate another updater instance holding the lock
  mkdir -p '$LOCK_DIR'

  export CRSUPDATE=true
  export CRSVERSION='latest'
  export CRS_TARBALL_URL='http://example.invalid/never-used.tgz'
  export CRS_UPDATE_STATUS_FILE='$STATUS_FILE'

  # Should skip due to lock and exit 0
  /crs_update.sh

  test -f '$STATUS_FILE'
  status=\"\$(cat '$STATUS_FILE' | tr -d '\n\r')\"

  # Minimal assertions (avoid overfitting JSON field order)
  echo \"\$status\" | grep -Eq '\"attempted\":true'
  echo \"\$status\" | grep -Eq '\"result\":\"skipped\"'
  echo \"\$status\" | grep -Eq '\"reason\":\"Updater lock held; skipping\"'

  # Bundled CRS should still be present and valid
  test -d '$CRS_DIR'
  test -f '$CRS_DIR/crs-setup.conf'
  test -d '$CRS_DIR/rules'
  ls -1 '$CRS_DIR'/rules/*.conf >/dev/null
"

echo "PASS: lock held -> skipped status and bundled CRS remains"
