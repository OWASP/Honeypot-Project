#!/bin/bash
chmod go-w /etc/filebeat/filebeat.yml
apachectl
filebeat -e -c /etc/filebeat/filebeat.yml -d "publish"
