FROM logstash:7.17.10
WORKDIR /app/
COPY ./ /app
COPY ./pipeline /usr/share/logstash/pipeline
USER root
EXPOSE 5044