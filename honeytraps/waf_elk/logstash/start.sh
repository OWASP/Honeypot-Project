#!/bin/bash

#echo "installing Python dependencies if not exists..."
#pipenv install

#echo "Staring Misp Push service"
#pipenv run python3 /app/kibana-client.py &
/opt/logstash/bin/logstash -f /etc/logstash/conf.d/100-filebeat_logstash.conf
logstash
