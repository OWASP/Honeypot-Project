#!/bin/sh
mkdir -p /tmp/modsecurity/data
chown -R daemon:daemon /tmp/modsecurity/data
apachectl
python3 /app/rule_watcher.py &
filebeat -e -c /etc/filebeat/filebeat.yml -d "publish"
