
#!/usr/bin/env bash

set -euo pipefail

IMAGE="${IMAGE:-waf_modsec:local}"
NET="test-crs-net-$RANDOM$RANDOM"
FIX="test-crs-fixture-$RANDOM$RANDOM"
APP="test-crs-app-$RANDOM$RANDOM"
TMP="$(mktemp -d)"
VERSION="4.1.0-fixture"
STATUS_FILE="/tmp/crs_update_status.json"
CRS_DIR="/etc/modsecurity.d/owasp-crs"

cleanup() {
  docker rm -f "$APP" >/dev/null 2>&1 || true
  docker rm -f "$FIX" >/dev/null 2>&1 || true
  docker network rm "$NET" >/dev/null 2>&1 || true
  rm -rf "$TMP"
}
trap cleanup EXIT

# Build a minimal CRS-like tarball with unique markers
mkdir -p "$TMP/coreruleset-$VERSION/rules"

cat >"$TMP/coreruleset-$VERSION/crs-setup.conf.example" <<'EOF'
# fixture crs-setup
SecAction "id:900990,phase:1,pass,nolog,tag:'fixture-setup-marker'"
EOF

cat >"$TMP/coreruleset-$VERSION/rules/REQUEST-900-EXCLUSION-RULES-BEFORE-CRS.conf" <<'EOF'
# fixture rule marker: fixture-rule-marker
SecRule REQUEST_URI "@beginsWith /" "id:900001,phase:1,pass,nolog"
EOF

tar -C "$TMP" -czf "$TMP/crs.tgz" "coreruleset-$VERSION"

# Compute sha256 for enforcement
SHA256="$(sha256sum "$TMP/crs.tgz" | awk '{print $1}')"

docker network create "$NET" >/dev/null

# Serve tarball over an isolated Docker network (no public internet)
docker run -d --name "$FIX" --network "$NET" -v "$TMP:/srv:ro" python:3-alpine \
  sh -lc 'cd /srv && python -m http.server 8000' >/dev/null

TARBALL_URL="http://$FIX:8000/crs.tgz"

docker run -d --name "$APP" --network "$NET" -e CRSUPDATE=false "$IMAGE" >/dev/null

HAD_OLD="no"
if docker exec "$APP" sh -lc "test -d '$CRS_DIR'"; then HAD_OLD="yes"; fi

# Run updater deterministically (fixture URL + sha)
docker exec \
  -e CRSUPDATE=true \
  -e CRSVERSION="$VERSION" \
  -e CRS_TARBALL_URL="$TARBALL_URL" \
  -e CRS_EXPECTED_SHA256="$SHA256" \
  -e CRS_UPDATE_STATUS_FILE="$STATUS_FILE" \
  "$APP" sh -lc 'set -eu; /crs_update.sh'

# Assert status JSON semantics and installed content markers (fixed-string checks)
docker exec \
  -e STATUS_FILE="$STATUS_FILE" \
  -e VERSION="$VERSION" \
  -e TARBALL_URL="$TARBALL_URL" \
  -e CRS_DIR="$CRS_DIR" \
  "$APP" sh -lc '
    set -eu

    test -f "$STATUS_FILE"
    grep -F "\"attempted\":true" "$STATUS_FILE"
    grep -F "\"result\":\"ok\"" "$STATUS_FILE"
    grep -F "\"crsVersion\":\"$VERSION\"" "$STATUS_FILE"
    grep -F "\"tarballUrl\":\"$TARBALL_URL\"" "$STATUS_FILE"
    grep -F "\"crsDir\":\"$CRS_DIR\"" "$STATUS_FILE"

    test -f "$CRS_DIR/crs-setup.conf"
    grep -q "fixture-setup-marker" "$CRS_DIR/crs-setup.conf"
    ls -1 "$CRS_DIR"/rules/*.conf >/dev/null
    grep -Rqs "fixture-rule-marker" "$CRS_DIR/rules
  '

if [ "$HAD_OLD" = "yes" ]; then
  docker exec "$APP" sh -lc "test -d '$CRS_DIR.old'"
fi

echo "PASS: updater installs fixture CRS and writes ok status"
