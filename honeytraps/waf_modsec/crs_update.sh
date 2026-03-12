
#!/bin/sh

set -eu

log() { echo "[crs-update] $*" >&2; }

# Keep CRS installed where include.conf expects it (override if needed)
CRS_DIR="${CRS_DIR:-/etc/modsecurity.d/owasp-crs}"

# Runtime status file (created/overwritten on each run)
CRS_UPDATE_STATUS_FILE="${CRS_UPDATE_STATUS_FILE:-/tmp/crs_update_status.json}"

# Feature flag (default off)
CRSUPDATE="${CRSUPDATE:-false}"
case "$(printf "%s" "$CRSUPDATE" | tr '[:upper:]' '[:lower:]')" in
  1|true|yes|y|on) ;;
  *)
    log "CRSUPDATE not enabled; using bundled CRS."
    # Best-effort status write
    mkdir -p "$(dirname "$CRS_UPDATE_STATUS_FILE")" 2>/dev/null || true
    printf "%s\n" "{\"attempted\":false,\"result\":\"skipped\",\"reason\":\"CRSUPDATE disabled\"}" > "$CRS_UPDATE_STATUS_FILE" 2>/dev/null || true
    exit 0
    ;;
esac

CRSVERSION="${CRSVERSION:-}"
CRS_TARBALL_URL="${CRS_TARBALL_URL:-}"
CRS_EXPECTED_SHA256="${CRS_EXPECTED_SHA256:-}"

json_escape() {
  # Minimal JSON string escaping for log/status purposes
  printf "%s" "$1" | sed \
    -e 's/\\/\\\\/g' \
    -e 's/"/\\"/g' \
    -e 's/\r/\\r/g' \
    -e 's/\n/\\n/g' \
    -e 's/\t/\\t/g'
}

write_status() {
  attempted="$1"   # true/false
  result="$2"      # ok/fallback/skipped
  reason="$3"      # free text
  installed_path="${4:-}"

  reason_esc="$(json_escape "$reason")"
  version_esc="$(json_escape "$CRSVERSION")"
  url_esc="$(json_escape "$CRS_TARBALL_URL")"
  path_esc="$(json_escape "$installed_path")"

  mkdir -p "$(dirname "$CRS_UPDATE_STATUS_FILE")" 2>/dev/null || true

  tmp="${CRS_UPDATE_STATUS_FILE}.tmp.$$"
  printf "%s\n" \
    "{"\
"\"attempted\":$attempted,"\
"\"result\":\"$result\","\
"\"reason\":\"$reason_esc\","\
"\"crsVersion\":\"$version_esc\","\
"\"tarballUrl\":\"$url_esc\","\
"\"crsDir\":\"$path_esc\""\
"}" > "$tmp" 2>/dev/null || return 0

  mv -f "$tmp" "$CRS_UPDATE_STATUS_FILE" 2>/dev/null || true
}

fallback() {
  msg="$1"
  log "$msg"
  write_status true "fallback" "$msg" "$CRS_DIR" || true
  exit 0
}

# Basic required inputs
if [ -z "$CRSVERSION" ] || [ -z "$CRS_TARBALL_URL" ]; then
  log "Missing CRSVERSION or CRS_TARBALL_URL; falling back to bundled CRS."
  write_status true "fallback" "Missing CRSVERSION or CRS_TARBALL_URL" "$CRS_DIR" || true
  exit 0
fi

# If checksum is provided, enforce availability and format.
if [ -n "$CRS_EXPECTED_SHA256" ]; then
  # Normalize to lowercase for format check
  sha_lc="$(printf "%s" "$CRS_EXPECTED_SHA256" | tr '[:upper:]' '[:lower:]')"
  case "$sha_lc" in
    [0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]*)
      # Must be exactly 64 hex chars
      if [ "$(printf "%s" "$sha_lc" | wc -c | tr -d ' ')" != "64" ]; then
        fallback "CRS_EXPECTED_SHA256 must be 64 hex chars; falling back to bundled CRS."
      fi
      ;;
    *)
      fallback "CRS_EXPECTED_SHA256 is not valid hex; falling back to bundled CRS."
      ;;
  esac

  if ! command -v sha256sum >/dev/null 2>&1 && ! command -v shasum >/dev/null 2>&1; then
    fallback "No sha256 tool available to enforce CRS_EXPECTED_SHA256; falling back to bundled CRS."
  fi
else
  # Optional: nudge users toward supply-chain safety for pinned versions
  if [ "$CRSVERSION" != "latest" ]; then
    log "Warning: CRSVERSION is pinned but CRS_EXPECTED_SHA256 is not set."
  fi
fi

TMP_BASE="${TMPDIR:-/tmp}"
WORKDIR="$(mktemp -d "$TMP_BASE/crsupdate.XXXXXX")"
cleanup() { rm -rf "$WORKDIR" 2>/dev/null || true; }
trap cleanup EXIT

# Simple lock to avoid concurrent updates at container start (best-effort)
LOCKDIR="$TMP_BASE/crsupdate.lock"
if ! mkdir "$LOCKDIR" 2>/dev/null; then
  log "Another CRS update appears in progress; skipping."
  write_status true "skipped" "Updater lock held; skipping" "$CRS_DIR" || true
  exit 0
fi
trap 'rmdir "$LOCKDIR" 2>/dev/null || true; cleanup' EXIT

TARBALL="$WORKDIR/crs.tgz"
EXTRACT_DIR="$WORKDIR/extract"
mkdir -p "$EXTRACT_DIR"

download() {
  if command -v curl >/dev/null 2>&1; then
    curl -fsSL "$CRS_TARBALL_URL" -o "$TARBALL"
  elif command -v wget >/dev/null 2>&1; then
    wget -qO "$TARBALL" "$CRS_TARBALL_URL"
  else
    return 1
  fi
}

sha256_check() {
  [ -n "$CRS_EXPECTED_SHA256" ] || return 0

  expected_lc="$(printf "%s" "$CRS_EXPECTED_SHA256" | tr '[:upper:]' '[:lower:]')"

  if command -v sha256sum >/dev/null 2>&1; then
    actual_lc="$(sha256sum "$TARBALL" | awk '{print $1}' | tr '[:upper:]' '[:lower:]')"
  else
    actual_lc="$(shasum -a 256 "$TARBALL" | awk '{print $1}' | tr '[:upper:]' '[:lower:]')"
  fi

  [ "$actual_lc" = "$expected_lc" ]
}

looks_like_crs_root() {
  d="$1"
  [ -d "$d" ] || return 1
  [ -d "$d/rules" ] || return 1

  # Must contain at least one CRS rule file
  if ! ls "$d/rules"/*.conf >/dev/null 2>&1; then
    return 1
  fi

  # Must have either an example setup or a real setup file
  if [ -f "$d/crs-setup.conf" ] || [ -f "$d/crs-setup.conf.example" ]; then
    return 0
  fi

  return 1
}

log "Downloading CRS $CRSVERSION ..."
if ! download; then
  fallback "No curl/wget or download failed; falling back to bundled CRS."
fi

if [ ! -s "$TARBALL" ]; then
  fallback "Downloaded tarball empty; falling back to bundled CRS."
fi

if ! sha256_check; then
  fallback "SHA256 mismatch; falling back to bundled CRS."
fi

# Extract (portable flags)
if ! tar -xzf "$TARBALL" -C "$EXTRACT_DIR"; then
  fallback "Extract failed; falling back to bundled CRS."
fi

# Find a valid CRS root directory
CRS_ROOT=""
for d in "$EXTRACT_DIR" "$EXTRACT_DIR"/* "$EXTRACT_DIR"/*/*; do
  [ -d "$d" ] || continue
  if looks_like_crs_root "$d"; then
    CRS_ROOT="$d"
    break
  fi
done

if [ -z "$CRS_ROOT" ]; then
  fallback "Expected CRS layout not found; falling back to bundled CRS."
fi

NEW_DIR="${CRS_DIR}.new"
OLD_DIR="${CRS_DIR}.old"

rm -rf "$NEW_DIR" 2>/dev/null || true
mkdir -p "$(dirname "$CRS_DIR")"

# Copy contents (not the directory name itself)
mkdir -p "$NEW_DIR"
cp -R "$CRS_ROOT"/. "$NEW_DIR"/

# Ensure crs-setup.conf exists for include.conf expectations
if [ ! -f "$NEW_DIR/crs-setup.conf" ] && [ -f "$NEW_DIR/crs-setup.conf.example" ]; then
  cp "$NEW_DIR/crs-setup.conf.example" "$NEW_DIR/crs-setup.conf"
fi

if ! looks_like_crs_root "$NEW_DIR"; then
  rm -rf "$NEW_DIR" 2>/dev/null || true
  fallback "Staged CRS invalid after copy; falling back to bundled CRS."
fi

# Swap before Apache starts, with simple rollback
rm -rf "$OLD_DIR" 2>/dev/null || true

if [ -d "$CRS_DIR" ]; then
  if ! mv "$CRS_DIR" "$OLD_DIR" 2>/dev/null; then
    rm -rf "$NEW_DIR" 2>/dev/null || true
    fallback "Failed to move existing CRS aside; falling back to bundled CRS."
  fi
fi

if ! mv "$NEW_DIR" "$CRS_DIR" 2>/dev/null; then
  # rollback if possible
  rm -rf "$CRS_DIR" 2>/dev/null || true
  if [ -d "$OLD_DIR" ]; then
    mv "$OLD_DIR" "$CRS_DIR" 2>/dev/null || true
  fi
  fallback "Failed to activate new CRS; rolled back to bundled CRS."
fi

log "CRS updated to $CRSVERSION at $CRS_DIR."
write_status true "ok" "CRS updated successfully" "$CRS_DIR" || true
exit 0
