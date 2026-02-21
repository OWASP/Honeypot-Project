#!/bin/sh
set -e

# Ensure ModSecurity collections dir is writable even when bind-mounted
: "${MODSEC_DATA_DIR:=/var/log/modsecurity-data}"
mkdir -p "$MODSEC_DATA_DIR" || true
chmod 777 "$MODSEC_DATA_DIR" || true

# Start Apache in foreground-friendly way
apachectl start

python3 /app/preprocess-modsec-log.py &
filebeat -e -c /etc/filebeat/filebeat.yml -d "publish"

