# ~/bin/sh
curl -H 'Content-Type: application/json' -XPUT 'http://elk:9200/_template/filebeat' -d@/etc/filebeat/filebeat.template.json
/etc/init.d/filebeat start
apachectl 	
filebeat.sh -e -c filebeat.yml -d "publish"

