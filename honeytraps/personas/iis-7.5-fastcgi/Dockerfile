FROM httpd:2.4

COPY html/ /usr/local/apache2/htdocs/

# ASP.NET headers only, Server header is handled at the WAF layer.
COPY vhost.conf /usr/local/apache2/conf/extra/persona-iis75.conf

RUN echo "LoadModule headers_module modules/mod_headers.so" >> /usr/local/apache2/conf/httpd.conf \
 && echo "Include conf/extra/persona-iis75.conf" >> /usr/local/apache2/conf/httpd.conf

EXPOSE 80
