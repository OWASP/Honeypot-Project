#!/bin/sh

set -eu

sleep 3

/app/scripts/swap_persona.sh generic 2>/dev/null || true

log() { echo "[entrypoint] $*" >&2; }

touch /var/log/modsec_audit_processed.log

# CRS update
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

# Start services
python3 /app/preprocess-modsec-log.py &
PREPROCESS_PID=$!

apachectl -D FOREGROUND &
APACHE_PID=$!

# Start Filebeat only if LOGSTASH_HOST is configured
FILEBEAT_PID=""
if [ -n "${LOGSTASH_HOST:-}" ]; then
  log "Starting Filebeat (LOGSTASH_HOST=${LOGSTASH_HOST})..."
  filebeat -e -c /etc/filebeat/filebeat.yml -d "publish" &
  FILEBEAT_PID=$!
  log "Filebeat started (PID: $FILEBEAT_PID)"
else
  log "LOGSTASH_HOST not set — Filebeat disabled (CI/test mode)."
fi

# Start Shodan watcher if API key is set
SHODAN_PID=""
if [ -n "${SHODAN_API_KEY:-}" ]; then
  log "Starting Shodan watcher..."
  python3 /app/shodan_watcher.py &
  SHODAN_PID=$!
  log "Shodan watcher started (PID: $SHODAN_PID)"
else
  log "SHODAN_API_KEY not set — Shodan watcher disabled."
fi

shutdown() {
  log "Shutdown requested; stopping processes..."
  [ -n "$FILEBEAT_PID" ] && kill -TERM "$FILEBEAT_PID" 2>/dev/null || true
  kill -TERM "$APACHE_PID" "$PREPROCESS_PID" 2>/dev/null || true
  [ -n "$SHODAN_PID" ] && kill -TERM "$SHODAN_PID" 2>/dev/null || true
  [ -n "$FILEBEAT_PID" ] && wait "$FILEBEAT_PID" 2>/dev/null || true
  wait "$APACHE_PID" 2>/dev/null || true
  wait "$PREPROCESS_PID" 2>/dev/null || true
  [ -n "$SHODAN_PID" ] && wait "$SHODAN_PID" 2>/dev/null || true
}

trap 'shutdown; exit 0' INT TERM

while :; do
  if ! kill -0 "$APACHE_PID" 2>/dev/null; then
    log "Apache exited"
    shutdown
    exit 1
  fi
  # Only check Filebeat if it was started
  if [ -n "$FILEBEAT_PID" ] && ! kill -0 "$FILEBEAT_PID" 2>/dev/null; then
    log "Filebeat exited"
    shutdown
    exit 1
  fi
  sleep 5
done
