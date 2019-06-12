FROM sebp/elk
ADD ./start.sh /usr/local/bin/start.sh
RUN chmod +x /usr/local/bin/start.sh
EXPOSE 5601 9200 9300 5044
VOLUME /var/lib/elasticsearch
CMD [ "/usr/local/bin/start.sh" ]
