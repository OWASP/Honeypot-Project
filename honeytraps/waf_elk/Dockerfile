FROM sebp/elk
COPY filebeat_logstash.conf /etc/logstash/conf.d/filebeat_logstash.conf	
WORKDIR /app/waf_elk/
ADD ./start.sh /usr/local/bin/start.sh
ADD ./kibana-client.py kibana-client.py
RUN chmod +x /usr/local/bin/start.sh
RUN apt update
RUN apt install -y nano
RUN apt install -y python3-pip
RUN pip3 install pipenv 
RUN pipenv install elasticsearch pymisp

EXPOSE 5601 9200 9300 5044
VOLUME /var/lib/elasticsearch
CMD [ "/usr/local/bin/start.sh" ]
 