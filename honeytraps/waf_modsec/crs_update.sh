
#!/bin/sh
set -eu

log() { echo "[crs-update] $*" >&2; }

# Keep CRS installed where include.conf expects it (override if needed)
CRS_DIR="${CRS_DIR:-/etc/modsecurity.d/owasp-crs}"

# Feature flag (default off)
CRSUPDATE="${CRSUPDATE:-false}"
case "$(printf "%s" "$CRSUPDATE" | tr '[:upper:]' '[:lower:]')" in
  1|true|yes|y|on) ;;
  *) log "CRSUPDATE not enabled; using bundled CRS."; exit 0 ;;
esac

CRSVERSION="${CRSVERSION:-}"
CRS_TARBALL_URL="${CRS_TARBALL_URL:-}"
CRS_EXPECTED_SHA256="${CRS_EXPECTED_SHA256:-}"

if [ -z "$CRSVERSION" ] || [ -z "$CRS_TARBALL_URL" ]; then
  log "Missing CRSVERSION or CRS_TARBALL_URL; falling back to bundled CRS."
  exit 0
fi

TMP_BASE="${TMPDIR:-/tmp}"
WORKDIR="$(mktemp -d "$TMP_BASE/crsupdate.XXXXXX")"
cleanup() { rm -rf "$WORKDIR" || true; }
trap cleanup EXIT

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
  if command -v sha256sum >/dev/null 2>&1; then
    echo "$CRS_EXPECTED_SHA256  $TARBALL" | sha256sum -c - >/dev/null 2>&1
  elif command -v shasum >/dev/null 2>&1; then
    echo "$CRS_EXPECTED_SHA256  $TARBALL" | shasum -a 256 -c - >/dev/null 2>&1
  else
    log "No sha256 tool available; skipping integrity check."
    return 0
  fi
}

log "Downloading CRS $CRSVERSION ..."
if ! download; then
  log "No curl/wget or download failed; falling back to bundled CRS."
  exit 0
fi

if [ ! -s "$TARBALL" ]; then
  log "Downloaded tarball empty; falling back to bundled CRS."
  exit 0
fi

if ! sha256_check; then
  log "SHA256 mismatch; falling back to bundled CRS."
  exit 0
fi

if ! tar -xzf "$TARBALL" -C "$EXTRACT_DIR"; then
  log "Extract failed; falling back to bundled CRS."
  exit 0
fi

CRS_ROOT=""
for d in "$EXTRACT_DIR"/* "$EXTRACT_DIR"/*/*; do
  [ -d "$d" ] || continue
  if [ -f "$d/crs-setup.conf" ] && [ -d "$d/rules" ]; then
    CRS_ROOT="$d"
    break
  fi
done

if [ -z "$CRS_ROOT" ]; then
  log "Expected CRS layout not found; falling back to bundled CRS."
  exit 0
fi

NEW_DIR="${CRS_DIR}.new"
OLD_DIR="${CRS_DIR}.old"

rm -rf "$NEW_DIR" "$OLD_DIR" 2>/dev/null || true
mkdir -p "$(dirname "$CRS_DIR")"
cp -R "$CRS_ROOT" "$NEW_DIR"

if [ ! -f "$NEW_DIR/crs-setup.conf" ] || [ ! -d "$NEW_DIR/rules" ]; then
  log "Staged CRS invalid; falling back to bundled CRS."
  rm -rf "$NEW_DIR" 2>/dev/null || true
  exit 0
fi

# Swap before Apache starts
if [ -d "$CRS_DIR" ]; then
  mv "$CRS_DIR" "$OLD_DIR"
fi
mv "$NEW_DIR" "$CRS_DIR"

log "CRS updated to $CRSVERSION at $CRS_DIR."
exit 0
