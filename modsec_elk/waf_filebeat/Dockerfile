FROM owasp/modsecurity-crs
RUN wget  https://artifacts.elastic.co/downloads/beats/filebeat/filebeat-5.1.2-x86_64.rpm
RUN rpm -vi filebeat-5.1.2-x86_64.rpm
COPY filebeat.yml /etc/filebeat/filebeat.yml
COPY modsec_entry.sh /
RUN chmod +x modsec_entry.sh
CMD ["/modsec_entry.sh"]
