
#!/bin/sh

set -eu

log() { echo "[entrypoint] $*" >&2; }

CRS_UPDATE_RC=0
/crs_update.sh || CRS_UPDATE_RC=$?
log "CRS update exit code: $CRS_UPDATE_RC"

python3 /app/preprocess-modsec-log.py &
PREPROCESS_PID=$!

apachectl -D FOREGROUND &
APACHE_PID=$!

filebeat -e -c filebeat.yml -d "publish" &
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
