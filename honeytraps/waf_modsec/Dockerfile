FROM owasp/modsecurity-crs
RUN apt install -y wget nano curl
RUN wget https://artifacts.elastic.co/downloads/beats/filebeat/filebeat-7.4.2-amd64.deb
RUN dpkg -i filebeat-7.4.2-amd64.deb
COPY filebeat.yml /etc/filebeat/filebeat.yml
COPY filebeat.template.json /etc/filebeat/filebeat.template.json
COPY modsec_entry.sh /
COPY robots.txt /home/
COPY index.html /usr/local/apache2/htdocs/
COPY login.html /usr/local/apache2/htdocs/
COPY httpd-extension.conf /app/httpd-extension.conf
COPY modsecurity-extension.conf /app/modsecurity-extension.conf
RUN cat /app/httpd-extension.conf >> /usr/local/apache2/conf/httpd.conf
RUN cat /app/modsecurity-extension.conf >> /etc/modsecurity.d/modsecurity.conf
RUN chmod +x /modsec_entry.sh
CMD ["/modsec_entry.sh"]
