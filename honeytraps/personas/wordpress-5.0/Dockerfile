FROM httpd:2.4

# fake WP file tree - this is what scanners see when they probe the endpoints.
COPY html/ /usr/local/apache2/htdocs/

# load mod_headers and include our persona config.
COPY vhost.conf /usr/local/apache2/conf/extra/persona-wordpress.conf

RUN echo "LoadModule headers_module modules/mod_headers.so" >> /usr/local/apache2/conf/httpd.conf \
 && echo "Include conf/extra/persona-wordpress.conf" >> /usr/local/apache2/conf/httpd.conf

EXPOSE 80
