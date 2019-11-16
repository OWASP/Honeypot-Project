# ~/bin/sh
url='http://'${LOGSTASH_HOST}':9200/_template/filebeat'
curl -H 'Content-Type: application/json' -XPUT ${url} -d@/etc/filebeat/filebeat.template.json
chmod go-w /etc/filebeat/filebeat.yml
apachectl 	
filebeat -e -c filebeat.yml -d "publish"
