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

# Load persona
PERSONA="${PERSONA:-generic}"
PERSONA_DIR="/personas/${PERSONA}"

if [ ! -d "$PERSONA_DIR" ]; then
  log "Persona '${PERSONA}' not found, falling back to generic"
  PERSONA="generic"
  PERSONA_DIR="/personas/generic"
fi

log "Loading persona: ${PERSONA}"

# Copy persona files into place
cp "${PERSONA_DIR}/modsecurity-extension.conf" /app/modsecurity-extension.conf
cp "${PERSONA_DIR}/index.html" /usr/local/apache2/htdocs/index.html
cp "${PERSONA_DIR}/login.html" /usr/local/apache2/htdocs/login.html
cp "${PERSONA_DIR}/robots.txt" /usr/local/apache2/htdocs/robots.txt

# Append persona rules to modsecurity.conf fresh each startup
grep -v -f /app/modsecurity-extension.conf /etc/modsecurity.d/modsecurity.conf > /tmp/modsec_clean.conf 2>/dev/null || true
cp /tmp/modsec_clean.conf /etc/modsecurity.d/modsecurity.conf
cat /app/modsecurity-extension.conf >> /etc/modsecurity.d/modsecurity.conf

log "Persona '${PERSONA}' loaded successfully"

python3 /app/preprocess-modsec-log.py &
PREPROCESS_PID=$!

apachectl -D FOREGROUND &
APACHE_PID=$!

filebeat -e -c /etc/filebeat/filebeat.yml -d "publish" &
FILEBEAT_PID=$!

shutdown() {
  log "Shutdown requested; stopping processes..."
  kill -TERM "$FILEBEAT_PID" "$APACHE_PID" "$PREPROCESS_PID" 2>/dev/null || true
  wait "$FILEBEAT_PID" 2>/dev/null || true
  wait "$APACHE_PID" 2>/dev/null || true
  wait "$PREPROCESS_PID" 2>/dev/null || true
}

trap 'shutdown; exit 0' INT TERM

while :; do
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
  sleep 1
done
