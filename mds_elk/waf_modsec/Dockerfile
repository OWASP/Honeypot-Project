FROM owasp/modsecurity-crs
RUN apt install -y wget nano curl
RUN wget https://artifacts.elastic.co/downloads/beats/filebeat/filebeat-7.2.0-amd64.deb
RUN dpkg -i filebeat-7.2.0-amd64.deb
COPY filebeat.yml /etc/filebeat/filebeat.yml
COPY filebeat.template.json /etc/filebeat/filebeat.template.json
COPY modsec_entry.sh /
COPY modsecurity.conf /etc/modsecurity.d/
RUN chmod +x /modsec_entry.sh
CMD ["/modsec_entry.sh"]
