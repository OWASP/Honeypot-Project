FROM logstash:7.5.1
COPY filebeat_logstash.conf /etc/logstash/conf.d/100-filebeat_logstash.conf	
WORKDIR /app/
USER root
ADD ./start.sh /usr/local/bin/start.sh
RUN chmod +x /usr/local/bin/start.sh
ADD logstash-modsecurity /app/logstash-modsecurity
ADD logstash-modsecurity.cfg /app/
RUN chmod +x /app/logstash-modsecurity/deploy.sh
RUN /app/logstash-modsecurity/deploy.sh logstash-modsecurity.cfg
#RUN apt-get update
#RUN apt install -y nano
#RUN apt install -y python3-pip
#RUN pip3 install pipenv 

EXPOSE 5044
#VOLUME /var/lib/elasticsearch
CMD [ "/usr/local/bin/start.sh" ]
 