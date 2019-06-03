FROM sebp/elk
COPY filebeat_logstash.conf /etc/logstash/conf.d/filebeat_logstash.conf
ADD ./start.sh /usr/local/bin/start.sh
RUN chmod +x /usr/local/bin/start.sh
EXPOSE 5601 9200 9300 5044
VOLUME /var/lib/elasticsearch
CMD [ "/usr/local/bin/start.sh" ]
