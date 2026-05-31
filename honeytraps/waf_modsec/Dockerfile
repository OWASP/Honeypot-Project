FROM owasp/modsecurity-crs:apache
USER root
RUN apt update && apt install -y wget nano curl
COPY include.conf /etc/modsecurity.d/
ARG FILEBEAT_VERSION=8.9.0
ARG TARGETARCH=amd64
RUN wget -q https://artifacts.elastic.co/downloads/beats/filebeat/filebeat-${FILEBEAT_VERSION}-${TARGETARCH}.deb \
    && dpkg -i filebeat-${FILEBEAT_VERSION}-${TARGETARCH}.deb \
    && rm filebeat-${FILEBEAT_VERSION}-${TARGETARCH}.deb
COPY filebeat.yml /etc/filebeat/filebeat.yml
RUN chmod go-w /etc/filebeat/filebeat.yml
COPY modsec_entry.sh /
RUN mkdir -p /usr/local/apache2/conf/extra && touch /usr/local/apache2/conf/extra/httpd-logging-after-modsec.conf
COPY httpd.conf /usr/local/apache2/conf/httpd.conf
COPY robots.txt /usr/local/apache2/htdocs/
COPY index.html /usr/local/apache2/htdocs/
COPY login.html /usr/local/apache2/htdocs/
COPY modsecurity-extension.conf /app/modsecurity-extension.conf
RUN cat /app/modsecurity-extension.conf >> /etc/modsecurity.d/modsecurity.conf
RUN touch /var/log/modsec_audit.log && chmod 666 /var/log/modsec_audit.log
RUN chmod +x /modsec_entry.sh
RUN mkdir -p /usr/local/apache2/conf/extra && touch /usr/local/apache2/conf/extra/httpd-logging-after-modsec.conf
EXPOSE 80/tcp 8080/tcp 8000/tcp 8888/tcp
CMD ["/modsec_entry.sh"]

#COPY filebeat.template.json /etc/filebeat/filebeat.template.json