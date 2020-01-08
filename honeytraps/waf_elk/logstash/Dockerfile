FROM logstash:7.5.1
WORKDIR /app/
USER root
ADD logstash-modsecurity /app/logstash-modsecurity
ADD logstash-modsecurity.cfg /app/
RUN chmod +x /app/logstash-modsecurity/deploy.sh
RUN /app/logstash-modsecurity/deploy.sh logstash-modsecurity.cfg
EXPOSE 5044
 