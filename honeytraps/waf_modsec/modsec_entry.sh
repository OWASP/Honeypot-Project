#!/bin/sh
filebeat -e -c /etc/filebeat/filebeat.yml &
apachectl -DFOREGROUND
