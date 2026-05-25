FROM owasp/modsecurity-crs:apache
USER root
RUN apt-get update && apt-get install -y nano wget curl default-jre libapache2-mod-security2
COPY mlogc.conf /etc/mlogc.conf
RUN rm -f /etc/modsecurity.d/modsecurity.conf
COPY httpd.conf /etc/apache2/apache2.conf
COPY mod_security.conf /etc/apache2/conf-available/mod_security.conf
RUN a2enconf mod_security 2>/dev/null || true
RUN wget -q https://artifacts.elastic.co/downloads/logstash/logstash-7.17.10-linux-x86_64.tar.gz \
    && tar xzf logstash-7.17.10-linux-x86_64.tar.gz \
    && mv logstash-7.17.10 /usr/share/logstash \
    && rm logstash-7.17.10-linux-x86_64.tar.gz
COPY logstash.conf /usr/share/logstash/logstash.conf
ADD config /usr/share/logstash/config
ADD ./start.sh /usr/share/logstash/start.sh
WORKDIR /usr/share/logstash
RUN chmod u+x start.sh
ENTRYPOINT ["./start.sh"]
