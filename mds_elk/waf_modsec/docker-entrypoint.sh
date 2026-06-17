#!/bin/bash
curl -H 'Content-Type: application/json' -XPUT 'http://elasticsearch:9200/_template/filebeat' -d@/etc/filebeat/filebeat.template.json 
