FROM httpd:2.4

COPY html/ /usr/local/apache2/htdocs/

# fake cgi binaries for the /cgi-bin/php and /cgi-bin/php5 probe paths (CVE-2012-1823)
COPY cgi-bin/php /usr/local/apache2/cgi-bin/php
COPY cgi-bin/php5 /usr/local/apache2/cgi-bin/php5
RUN chmod +x /usr/local/apache2/cgi-bin/php /usr/local/apache2/cgi-bin/php5

# Server header override is handled at the WAF layer via SecServerSignature.
COPY vhost.conf /usr/local/apache2/conf/extra/persona-apache22.conf

RUN echo "LoadModule headers_module modules/mod_headers.so" >> /usr/local/apache2/conf/httpd.conf \
 && echo "LoadModule cgi_module modules/mod_cgi.so" >> /usr/local/apache2/conf/httpd.conf \
 && echo "Include conf/extra/persona-apache22.conf" >> /usr/local/apache2/conf/httpd.conf

EXPOSE 80
