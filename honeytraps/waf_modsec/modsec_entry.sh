#!/bin/sh
set -eu
log() { echo "[entrypoint] $*" >&2; }

touch /var/log/modsec_audit_processed.log

CRS_UPDATE_RC=0
CRSUPDATE_RAW="${CRSUPDATE:-false}"
CRSUPDATE_NORM="$(printf '%s' "$CRSUPDATE_RAW" | tr '[:upper:]' '[:lower:]' | tr -d '[:space:]')"

case "$CRSUPDATE_NORM" in
  true|1|yes|on)
    /crs_update.sh || CRS_UPDATE_RC=$?
    ;;
  *)
    log "CRS update disabled (CRSUPDATE=${CRSUPDATE_RAW})"
    ;;
esac

log "CRS update exit code: $CRS_UPDATE_RC"

# ── Persona loading ──────────────────────────────────────────
PERSONA="${PERSONA:-generic}"
PERSONA_DIR="/personas/${PERSONA}"

if [ ! -d "$PERSONA_DIR" ]; then
  log "Persona '${PERSONA}' not found, falling back to generic"
  PERSONA="generic"
  PERSONA_DIR="/personas/generic"
fi

load_persona() {
  local persona="$1"
  local persona_dir="/personas/${persona}"

  if [ ! -d "$persona_dir" ]; then
    log "Persona '${persona}' not found, skipping swap."
    return 1
  fi

  log "Loading persona: ${persona}"
  cp "${persona_dir}/modsecurity-extension.conf" /app/modsecurity-extension.conf
  cp "${persona_dir}/index.html"   /usr/local/apache2/htdocs/index.html
  cp "${persona_dir}/login.html"   /usr/local/apache2/htdocs/login.html
  cp "${persona_dir}/robots.txt"   /usr/local/apache2/htdocs/robots.txt

  grep -v -f /app/modsecurity-extension.conf \
    /etc/modsecurity.d/modsecurity.conf \
    > /tmp/modsec_clean.conf 2>/dev/null || true
  cp /tmp/modsec_clean.conf /etc/modsecurity.d/modsecurity.conf
  cat /app/modsecurity-extension.conf >> /etc/modsecurity.d/modsecurity.conf

  log "Persona '${persona}' loaded successfully."
}

load_persona "$PERSONA"

# ── Start services ───────────────────────────────────────────
python3 /app/preprocess-modsec-log.py &
PREPROCESS_PID=$!

apachectl -D FOREGROUND &
APACHE_PID=$!

filebeat -e -c /etc/filebeat/filebeat.yml -d "publish" &
FILEBEAT_PID=$!

# Start Shodan watcher if API key is set
SHODAN_PID=""
if [ -n "${SHODAN_API_KEY:-}" ]; then
  python3 /app/shodan_watcher.py &
  SHODAN_PID=$!
  log "Shodan watcher started (PID: $SHODAN_PID)"
else
  log "SHODAN_API_KEY not set — Shodan watcher disabled."
fi

PERSONA_SWAP_FILE="${PERSONA_SWAP_FILE:-/tmp/persona_swap}"

shutdown() {
  log "Shutdown requested; stopping processes..."
  kill -TERM "$FILEBEAT_PID" "$APACHE_PID" "$PREPROCESS_PID" 2>/dev/null || true
  [ -n "$SHODAN_PID" ] && kill -TERM "$SHODAN_PID" 2>/dev/null || true
  wait "$FILEBEAT_PID" 2>/dev/null || true
  wait "$APACHE_PID" 2>/dev/null || true
  wait "$PREPROCESS_PID" 2>/dev/null || true
  [ -n "$SHODAN_PID" ] && wait "$SHODAN_PID" 2>/dev/null || true
}

trap 'shutdown; exit 0' INT TERM

# ── Main watchdog loop ───────────────────────────────────────
while :; do
  # Check for persona swap request from Shodan watcher
  if [ -f "$PERSONA_SWAP_FILE" ]; then
    NEW_PERSONA="$(cat "$PERSONA_SWAP_FILE")"
    rm -f "$PERSONA_SWAP_FILE"
    log "Persona swap requested: ${PERSONA} -> ${NEW_PERSONA}"
    if load_persona "$NEW_PERSONA"; then
      PERSONA="$NEW_PERSONA"
      # Graceful Apache reload to pick up new ModSecurity rules
      apachectl graceful || log "Apache graceful reload failed"
    fi
  fi

  if ! kill -0 "$APACHE_PID" 2>/dev/null; then
    log "Apache exited"
    shutdown
    exit 1
  fi

  if ! kill -0 "$FILEBEAT_PID" 2>/dev/null; then
    log "Filebeat exited"
    shutdown
    exit 1
  fi

  sleep 5
done
