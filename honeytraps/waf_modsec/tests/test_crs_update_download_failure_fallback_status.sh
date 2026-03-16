
#!/usr/bin/env bash
set -euo pipefail

IMAGE="${IMAGE:-waf_modsec:local}"
NAME="test-crs-dl-fail-$RANDOM$RANDOM"

STATUS_FILE="/tmp/crs_update_status.json"
CRS_DIR="/etc/modsecurity.d/owasp-crs"

cleanup() { docker rm -f "$NAME" >/dev/null 2>&1 || true; }
trap cleanup EXIT

docker run -d --name "$NAME" -e CRSUPDATE=false "$IMAGE" >/dev/null

# Force an unreachable URL inside the container (connection refused fast)
BAD_URL="http://127.0.0.1:1/crs.tgz"

docker exec "$NAME" sh -lc "
  set -eu

  export CRSUPDATE=true
  export CRSVERSION='latest'
  export CRS_TARBALL_URL='$BAD_URL'
  export CRS_UPDATE_STATUS_FILE='$STATUS_FILE'

  # Updater should fallback and still exit 0
  /crs_update.sh

  test -f '$STATUS_FILE'
  grep -Eq '\"attempted\":true' '$STATUS_FILE'
  grep -Eq '\"result\":\"fallback\"' '$STATUS_FILE'
  grep -Eq '\"crsVersion\":\"latest\"' '$STATUS_FILE'
  grep -Eq '\"tarballUrl\":\"'\"\$(printf \"%s\" \"$BAD_URL\" | sed -e 's/[.[\\\\*^$(){}+?|]/\\\\\\\\&/g')\"'\"'\"' '$STATUS_FILE'
  grep -Eq '\"crsDir\":\"$CRS_DIR\"' '$STATUS_FILE'

  # Bundled CRS should still be present and valid
  test -d '$CRS_DIR'
  test -f '$CRS_DIR/crs-setup.conf'
  test -d '$CRS_DIR/rules'
  ls -1 '$CRS_DIR'/rules/*.conf >/dev/null

  # No staging/rollback dirs should be created on early fallback
  test ! -e '${CRS_DIR}.new'
  test ! -e '${CRS_DIR}.old'
"

echo 'PASS: download failure -> fallback status and bundled CRS remains'
