# ~/bin/sh
curl -H 'Content-Type: application/json' -XPUT 'http://elk:9200/_template/filebeat' -d@/etc/filebeat/filebeat.template.json
chmod go-w /etc/filebeat/filebeat.yml
apachectl
filebeat -e -c filebeat.yml -d "publish"
