FROM owasp/modsecurity-crs
RUN apt install -y wget nano curl python3-watchdog
RUN wget https://artifacts.elastic.co/downloads/beats/filebeat/filebeat-7.4.2-amd64.deb
RUN dpkg -i filebeat-7.4.2-amd64.deb
COPY filebeat.yml /etc/filebeat/filebeat.yml
COPY modsec_entry.sh /
COPY httpd.conf /usr/local/apache2/conf/httpd.conf
COPY robots.txt /usr/local/apache2/htdocs/
COPY index.html /usr/local/apache2/htdocs/
COPY login.html /usr/local/apache2/htdocs/
COPY modsecurity-extension.conf /app/modsecurity-extension.conf
COPY preprocess-modsec-log.py /app/preprocess-modsec-log.py
RUN touch /var/log/modsec_audit_processed.log
RUN cat /app/modsecurity-extension.conf >> /etc/modsecurity.d/modsecurity.conf
RUN chmod +x /modsec_entry.sh
EXPOSE 80/tcp 8080/tcp 8000/tcp 8888/tcp
CMD ["/modsec_entry.sh"]

#COPY filebeat.template.json /etc/filebeat/filebeat.template.json