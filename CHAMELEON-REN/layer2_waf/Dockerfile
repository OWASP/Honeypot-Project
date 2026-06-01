# Use the official OWASP ModSecurity Core Rule Set image
FROM owasp/modsecurity-crs:apache

# Set environment variables for CRS version and detection mode
ENV CRS_VERSION=4.1
ENV SEC_RULE_ENGINE=DetectionOnly

# Switch to root temporarily to create directories and set permissions
USER root

# ==========================================
# 1. FIX: PERSISTENCE & TELEMETRY DIRECTORIES
# ==========================================
# Ensure both the tracking data AND the JSON log directories exist and are writable
RUN mkdir -p /var/log/modsecurity-data && \
    chmod 777 /var/log/modsecurity-data && \
    mkdir -p /var/log/chameleon && \
    chmod 777 /var/log/chameleon

# ==========================================
# 2. FIX: AWS HEALTH CHECK PATHING
# ==========================================
# Create the exact directory expected by healthz.conf
RUN mkdir -p /var/www/html && \
    chmod 777 /var/www/html

# Copy the health check text file to the correct location
COPY conf/healthz.txt /var/www/html/healthz.txt

# ==========================================
# 3. FIX: LOAD ALL CONFIGURATIONS
# ==========================================
# Copy custom ModSecurity overrides
COPY conf/modsecurity.conf /etc/modsecurity.d/modsecurity-override.conf

# Copy the proxy routing map
COPY conf/proxy.conf /usr/local/apache2/conf/extra/httpd-vhosts.conf

# Copy AND explicitly include the healthz configuration so it doesn't spam logs
COPY conf/healthz.conf /usr/local/apache2/conf/extra/healthz.conf
RUN echo "Include conf/extra/healthz.conf" >> /usr/local/apache2/conf/httpd.conf