FROM owasp/modsecurity-crs
RUN yum install -y mlogc nano
RUN yum install -y java
RUN yum install -y wget
COPY mlogc.conf /etc/mlogc.conf
RUN rm /etc/httpd/modsecurity.d/modsecurity.conf
COPY httpd.conf /etc/httpd/conf/httpd.conf
COPY mod_security.conf /etc/httpd/conf.d/
COPY 10-modsecurty.conf /etc/httpd/conf.modules.d/
RUN wget https://artifacts.elastic.co/downloads/logstash/logstash-6.1.0.rpm
RUN rpm -ivh logstash-6.1.0.rpm
COPY logstash.conf /usr/share/logstash/
ADD config /usr/share/logstash/config	
ADD ./start.sh /usr/share/logstash/start.sh
WORKDIR /usr/share/logstash
RUN chmod u+x start.sh
ENTRYPOINT ["./start.sh"]
