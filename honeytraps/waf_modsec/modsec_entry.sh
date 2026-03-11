
#!/bin/sh
set -eu

log() { echo "[modsec_entry] $*"; }

CRSUPDATE="${CRSUPDATE:-false}"
APACHE_FOREGROUND_CMD="${APACHE_FOREGROUND_CMD:-apachectl -D FOREGROUND}"

PREPROCESS_PID=""
FILEBEAT_PID=""
APACHE_PID=""

cleanup() {
  log "Shutdown signal received; stopping processes..."

  # Stop Apache first (main service)
  if [ -n "${APACHE_PID}" ]; then
    kill -TERM "${APACHE_PID}" 2>/dev/null || true
  fi

  # Stop sidecars
  [ -n "${FILEBEAT_PID}" ] && kill -TERM "${FILEBEAT_PID}" 2>/dev/null || true
  [ -n "${PREPROCESS_PID}" ] && kill -TERM "${PREPROCESS_PID}" 2>/dev/null || true

  # Reap children
  wait 2>/dev/null || true
}

trap cleanup INT TERM

# Optional CRS update (no-op unless CRSUPDATE=true)
if [ "${CRSUPDATE}" = "true" ]; then
  if [ -x "/crs_update.sh" ]; then
    log "CRSUPDATE=true; running /crs_update.sh"
    /crs_update.sh || log "CRS update failed; continuing (fail-open)"
  else
    log "CRSUPDATE=true but /crs_update.sh not found/executable; continuing"
  fi
else
  log "CRSUPDATE!=true; skipping CRS update"
fi

if [ -f "/app/preprocess-modsec-log.py" ]; then
  log "Starting preprocess-modsec-log.py"
  python3 /app/preprocess-modsec-log.py &
  PREPROCESS_PID="$!"
else
  log "preprocess-modsec-log.py not found; skipping"
fi

if command -v filebeat >/dev/null 2>&1; then
  log "Starting filebeat"
  filebeat -e -c filebeat.yml -d "publish" &
  FILEBEAT_PID="$!"
else
  log "filebeat not found; skipping"
fi

log "Starting Apache (${APACHE_FOREGROUND_CMD})"
sh -c "${APACHE_FOREGROUND_CMD}" &
APACHE_PID="$!"

# Keep container tied to Apache lifecycle
wait "${APACHE_PID}"
