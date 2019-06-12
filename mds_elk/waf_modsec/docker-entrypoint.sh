#!/bin/bash
curl -H 'Content-Type: application/json' -XPUT 'http://elk:9200/_template/filebeat' -d@/etc/filebeat/filebeat.template.json 
