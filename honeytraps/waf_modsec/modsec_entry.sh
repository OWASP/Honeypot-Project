#!/bin/sh
apachectl
filebeat -e -c /etc/filebeat/filebeat.yml -d "publish"
