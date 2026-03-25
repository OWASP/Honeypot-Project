
FROM owasp/modsecurity-crs:apache

USER root

ENV CRSUPDATE=false \
    CRSVERSION=latest \
    PERSONA=generic \
    SHODAN_API_KEY="" \
    SHODAN_POLL_INTERVAL=300

ARG FILEBEAT_VERSION=8.9.0
ARG FILEBEAT_SHA256=""
ARG TARGETARCH

RUN set -eu; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
      ca-certificates \
      coreutils \
      curl \
      gzip \
      python3 \
      python3-watchdog \
      tar \
      wget \
    ; \
    rm -rf /var/lib/apt/lists/*

COPY include.conf /etc/modsecurity.d/
COPY filebeat.yml /etc/filebeat/filebeat.yml
COPY modsec_entry.sh /modsec_entry.sh
COPY crs_update.sh /crs_update.sh

COPY httpd.conf /usr/local/apache2/conf/httpd.conf
COPY modsecurity-extension.conf /app/modsecurity-extension.conf
COPY preprocess-modsec-log.py /app/preprocess-modsec-log.py

COPY personas/ /personas/
COPY scripts/ /app/scripts/
COPY shodan_watcher.py /app/shodan_watcher.py

# Normalize line endings + ensure scripts are executable (fixes exit 126)
RUN set -eu; \
    sed -i 's/\r$//' /modsec_entry.sh /crs_update.sh /app/scripts/swap_persona.sh; \
    chmod 0755 /modsec_entry.sh /crs_update.sh /app/scripts/*.sh; \
    chmod go-w /etc/filebeat/filebeat.yml
