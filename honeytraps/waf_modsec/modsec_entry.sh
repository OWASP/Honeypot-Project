
#!/bin/sh

set -eu

# Optional CRS update (no-op unless CRSUPDATE=true)
/crs_update.sh || true

apachectl

python3 /app/preprocess-modsec-log.py &

filebeat -e -c filebeat.yml -d "publish"
