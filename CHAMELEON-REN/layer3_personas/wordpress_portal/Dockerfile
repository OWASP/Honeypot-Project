# WordPress Research Portal
FROM wordpress:6.4.1-apache

# Install tools needed to download and extract vulnerable plugins/themes
RUN apt-get update && apt-get install -y wget unzip curl

# ==========================================
# 1. Spoof Premium Theme (Bricks CVE-2024-25600)
# ==========================================
# Premium themes aren't on the free repo, so we fake the folder and core CSS file
RUN mkdir -p /usr/src/wordpress/wp-content/themes/bricks \
    && echo "/* Theme Name: Bricks */" > /usr/src/wordpress/wp-content/themes/bricks/style.css

# ==========================================
# 2. Inject Real Plugin Bait 
# ==========================================
# (LiteSpeed CVE-2024-28000, Ultimate Member CVE-2024-1071, Backup Migration CVE-2023-6553)
RUN curl -o litespeed.zip -L https://downloads.wordpress.org/plugin/litespeed-cache.zip \
    && unzip litespeed.zip -d /usr/src/wordpress/wp-content/plugins/ \
    && rm litespeed.zip \
    && curl -o ultimate-member.zip -L https://downloads.wordpress.org/plugin/ultimate-member.zip \
    && unzip ultimate-member.zip -d /usr/src/wordpress/wp-content/plugins/ \
    && rm ultimate-member.zip \
    && curl -o backup-backup.zip -L https://downloads.wordpress.org/plugin/backup-backup.zip \
    && unzip backup-backup.zip -d /usr/src/wordpress/wp-content/plugins/ \
    && rm backup-backup.zip

# Set proper permissions for the Apache web server
RUN chown -R www-data:www-data /usr/src/wordpress/wp-content/

# ==========================================
# FIX: Server Spoofing Fix
# ==========================================
RUN echo "ServerTokens Prod" >> /etc/apache2/apache2.conf \
    && echo "ServerSignature Off" >> /etc/apache2/apache2.conf \
    && echo "expose_php = Off" > /usr/local/etc/php/conf.d/hide-php.ini
