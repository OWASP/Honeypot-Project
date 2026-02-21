
FROM owasp/modsecurity-crs:apache
USER root
RUN apt update && apt install -y wget nano curl python3-watchdog
COPY include.conf /etc/modsecurity.d/
RUN wget https://artifacts.elastic.co/downloads/beats/filebeat/filebeat-8.9.0-amd64.deb
RUN dpkg -i filebeat-8.9.0-amd64.deb
COPY filebeat.yml /etc/filebeat/filebeat.yml
RUN chmod go-w /etc/filebeat/filebeat.yml
COPY modsec_entry.sh /
COPY httpd.conf /usr/local/apache2/conf/httpd.conf
COPY robots.txt /usr/local/apache2/htdocs/
COPY index.html /usr/local/apache2/htdocs/
COPY login.html /usr/local/apache2/htdocs/
COPY modsecurity-extension.conf /app/modsecurity-extension.conf
COPY preprocess-modsec-log.py /app/preprocess-modsec-log.py
COPY ssl-8443.conf /usr/local/apache2/conf/extra/ssl-8443.conf
RUN touch /var/log/modsec_audit_processed.log
RUN touch /var/log/modsec_audit.log
RUN chown -R httpd:httpd /var/log
RUN cat /app/modsecurity-extension.conf >> /etc/modsecurity.d/modsecurity.conf
RUN chmod +x /modsec_entry.sh
EXPOSE 8080/tcp 8443/tcp 8000/tcp 8888/tcp
RUN mkdir -p /usr/local/apache2/conf/extra && touch /usr/local/apache2/conf/extra/httpd-logging-after-modsec.conf
COPY healthz.conf /usr/local/apache2/conf/extra/healthz.conf
RUN echo "ok" > /usr/local/apache2/htdocs/healthz.txt
ENV MODSEC_DATA_DIR=/var/log/modsecurity-data
RUN mkdir -p /var/log/modsecurity-data \
 && chmod 777 /var/log/modsecurity-data
CMD ["/modsec_entry.sh"]

#COPY filebeat.template.json /etc/filebeat/filebeat.template.json
