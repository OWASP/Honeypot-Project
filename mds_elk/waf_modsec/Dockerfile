<<<<<<< HEAD
FROM owasp/modsecurity-crs:3.3-apache
RUN apt install -y wget nano curl
RUN wget https://artifacts.elastic.co/downloads/beats/filebeat/filebeat-7.2.0-amd64.deb
RUN dpkg -i filebeat-7.2.0-amd64.deb
=======
FROM owasp/modsecurity-crs:apache
USER root
RUN apt-get update && apt-get install -y wget nano curl
ARG FILEBEAT_VERSION=7.17.10
ARG TARGETARCH=amd64
RUN wget -q https://artifacts.elastic.co/downloads/beats/filebeat/filebeat-${FILEBEAT_VERSION}-${TARGETARCH}.deb \
    && dpkg -i filebeat-${FILEBEAT_VERSION}-${TARGETARCH}.deb \
    && rm filebeat-${FILEBEAT_VERSION}-${TARGETARCH}.deb
>>>>>>> upstream/master
COPY filebeat.yml /etc/filebeat/filebeat.yml
COPY modsec_entry.sh /
COPY modsecurity.conf /etc/modsecurity.d/
RUN chmod +x /modsec_entry.sh
CMD ["/modsec_entry.sh"]
