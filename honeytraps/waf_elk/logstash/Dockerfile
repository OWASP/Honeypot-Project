FROM logstash:7.5.1
WORKDIR /app/
COPY ./ /app
COPY ./pipeline /usr/share/logstash/pipeline
USER root
EXPOSE 5044
 