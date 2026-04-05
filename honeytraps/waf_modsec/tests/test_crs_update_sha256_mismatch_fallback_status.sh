
#!/usr/bin/env bash
set -euo pipefail

IMAGE="${IMAGE:-waf_modsec:local}"
NAME="test-crs-sha-mismatch-$RANDOM$RANDOM"
SRV="test-crs-sha-srv-$RANDOM$RANDOM"
NET="test-crs-sha-net-$RANDOM$RANDOM"

STATUS_FILE="/tmp/crs_update_status.json"
CRS_DIR="/etc/modsecurity.d/owasp-crs"

TMPDIR="$(mktemp -d)"
cleanup() {
  docker rm -f "$NAME" "$SRV" >/dev/null 2>&1 || true
  docker network rm "$NET" >/dev/null 2>&1 || true
  rm -rf "$TMPDIR" >/dev/null 2>&1 || true
}
trap cleanup EXIT

# --- Build a minimal "valid" CRS tarball (layout the updater accepts) ---
mkdir -p "$TMPDIR/crs/rules"
printf '%s\n' "# minimal setup example" > "$TMPDIR/crs/crs-setup.conf.example"
printf '%s\n' "# minimal rule file" > "$TMPDIR/crs/rules/REQUEST-900-EXCLUSION-RULES-BEFORE-CRS.conf"
tar -C "$TMPDIR/crs" -czf "$TMPDIR/crs.tgz" .

# --- Start a tiny HTTP server to host the tarball ---
docker network create "$NET" >/dev/null

docker run -d --name "$SRV" --network "$NET" \
  -v "$TMPDIR:/srv:ro" \
  python:3-alpine sh -lc "cd /srv && python -m http.server 8000" >/dev/null

# --- Start the WAF container (updater invoked via docker exec below) ---
docker run -d --name "$NAME" --network "$NET" -e CRSUPDATE=false "$IMAGE" >/dev/null

# Record a baseline checksum of bundled CRS content
BASELINE="$(docker exec "$NAME" sh -lc "set -eu; sha256sum '$CRS_DIR/crs-setup.conf' | awk '{print \$1}'")"

# Intentionally wrong expected SHA256 (64 hex chars)
WRONG_SHA="0000000000000000000000000000000000000000000000000000000000000000"
URL="http://$SRV:8000/crs.tgz"

docker exec "$NAME" sh -lc "
  set -eu

  export CRSUPDATE=true
  export CRSVERSION='test'
  export CRS_TARBALL_URL='$URL'
  export CRS_EXPECTED_SHA256='$WRONG_SHA'
  export CRS_UPDATE_STATUS_FILE='$STATUS_FILE'

  /crs_update.sh

  # Status should indicate fallback
  test -f '$STATUS_FILE'
  grep -Eq '\"attempted\":true' '$STATUS_FILE'
  grep -Eq '\"result\":\"fallback\"' '$STATUS_FILE'

  # Bundled CRS should remain intact (no swap performed)
  test -d '$CRS_DIR'
  test -f '$CRS_DIR/crs-setup.conf'
  test -d '$CRS_DIR/rules'
  ls -1 '$CRS_DIR'/rules/*.conf >/dev/null

  # No successful swap artifacts
  test ! -e '${CRS_DIR}.old'
"

# Verify crs-setup.conf unchanged vs baseline
AFTER="$(docker exec "$NAME" sh -lc "set -eu; sha256sum '$CRS_DIR/crs-setup.conf' | awk '{print \$1}'")"
test "$AFTER" = "$BASELINE"

echo "PASS: SHA256 mismatch -> fallback status; bundled CRS unchanged"
