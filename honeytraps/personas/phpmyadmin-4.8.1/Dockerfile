FROM httpd:2.4

COPY html/ /usr/local/apache2/htdocs/

COPY vhost.conf /usr/local/apache2/conf/extra/persona-phpmyadmin.conf

RUN echo "LoadModule headers_module modules/mod_headers.so" >> /usr/local/apache2/conf/httpd.conf \
 && echo "Include conf/extra/persona-phpmyadmin.conf" >> /usr/local/apache2/conf/httpd.conf

EXPOSE 80
