FROM sebp/elk:800
ADD ./start.sh /usr/local/bin/start.sh
RUN chmod +x /usr/local/bin/start.sh
EXPOSE 5601 9200 9300 504
VOLUME /var/lib/elasticsearch
CMD [ "/usr/local/bin/start.sh" ]
