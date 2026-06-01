# Gibbon SIS Container (v25.0.00 Environment)
FROM php:8.2-apache

# Enable Apache mod_rewrite (required for Gibbon routing)
RUN a2enmod rewrite

# Install required PHP extensions, OS libraries, and git
RUN apt-get update && apt-get install -y \
    libzip-dev libpng-dev curl unzip git libicu-dev gettext \
    && docker-php-ext-configure intl \
    && docker-php-ext-install pdo pdo_mysql zip gd intl gettext

# Install Composer globally
COPY --from=composer:latest /usr/bin/composer /usr/bin/composer

# Download the GitHub tag archive and extract it perfectly into the web root
RUN curl -L https://github.com/GibbonEdu/core/archive/refs/tags/v25.0.00.tar.gz -o gibbon.tar.gz \
    && tar -xzf gibbon.tar.gz --strip-components=1 -C /var/www/html/ \
    && rm gibbon.tar.gz

# Run Composer to install all missing dependencies (the "vendor" folder)
RUN cd /var/www/html/ && composer install --no-dev --optimize-autoloader

# Set up the environment to receive the Gibbon installation
RUN mkdir -p /var/www/html/modules/rubrics/ \
    && chown -R www-data:www-data /var/www/html/

# ==========================================
# FIX: Server Spoofing Fix
# ==========================================
RUN echo "ServerTokens Prod" >> /etc/apache2/apache2.conf \
    && echo "ServerSignature Off" >> /etc/apache2/apache2.conf \
    && echo "expose_php = Off" > /usr/local/etc/php/conf.d/hide-php.ini
