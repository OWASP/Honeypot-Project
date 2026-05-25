FROM owasp/modsecurity-crs:apache
USER root
RUN apt-get update && apt-get install -y wget nano curl
RUN wget -q https://artifacts.elastic.co/downloads/beats/filebeat/filebeat-7.17.10-amd64.deb \
    && dpkg -i filebeat-7.17.10-amd64.deb \
    && rm filebeat-7.17.10-amd64.deb
COPY filebeat.yml /etc/filebeat/filebeat.yml
COPY modsec_entry.sh /
COPY modsecurity.conf /etc/modsecurity.d/
RUN chmod +x /modsec_entry.sh
CMD ["/modsec_entry.sh"]
