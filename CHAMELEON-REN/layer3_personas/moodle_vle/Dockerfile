# Moodle VLE Container
FROM php:8.1-apache

# Install Moodle system requirements and the TeX notation filter dependencies
RUN apt-get update && apt-get install -y \
    libpng-dev libzip-dev libicu-dev \
    texlive-base \
    && docker-php-ext-install gd zip intl mysqli

# Download and extract Moodle core
RUN curl -L https://download.moodle.org/download.php/direct/stable403/moodle-latest-403.tgz -o moodle.tgz \
    && tar -xzf moodle.tgz -C /var/www/html --strip-components=1 \
    && rm moodle.tgz

# Ensure the TeX filter directory is exposed and writable for payload capture
RUN mkdir -p /var/www/html/filter/tex/ \
    && chown -R www-data:www-data /var/www/html/

# ==========================================
# FIX 1: PHP Limits (From WP2 Troubleshooting)
# ==========================================
RUN echo 'max_input_vars = 5000' > /usr/local/etc/php/conf.d/moodle-custom.ini

# ==========================================
# FIX 2: Server Spoofing Fix
# ==========================================
RUN echo "ServerTokens Prod" >> /etc/apache2/apache2.conf \
    && echo "ServerSignature Off" >> /etc/apache2/apache2.conf \
    && echo "expose_php = Off" > /usr/local/etc/php/conf.d/hide-php.ini
