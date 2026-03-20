FROM owasp/modsecurity-crs:apache

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
COPY shodan_watcher.py /app/shodan_watcher.py

RUN set -eu; \
    chmod go-w /etc/filebeat/filebeat.yml; \
    chmod +x /modsec_entry.sh /crs_update.sh; \
    chmod +x /app/shodan_watcher.py; \
    touch /var/log/modsec_audit_processed.log; \
    cat /app/modsecurity-extension.conf >> /etc/modsecurity.d/modsecurity.conf; \
    ARCH="${TARGETARCH:-amd64}"; \
    case "$ARCH" in amd64|arm64) ;; *) echo "Unsupported arch: $ARCH" >&2; exit 1 ;; esac; \
    FILEBEAT_DEB="filebeat-${FILEBEAT_VERSION}-${ARCH}.deb"; \
    wget -qO "/tmp/${FILEBEAT_DEB}" "https://artifacts.elastic.co/downloads/beats/filebeat/${FILEBEAT_DEB}"; \
    if [ -n "$FILEBEAT_SHA256" ]; then \
      echo "${FILEBEAT_SHA256}  /tmp/${FILEBEAT_DEB}" | sha256sum -c -; \
    fi; \
    dpkg -i "/tmp/${FILEBEAT_DEB}"; \
    rm -f "/tmp/${FILEBEAT_DEB}"

EXPOSE 80/tcp 8080/tcp 8000/tcp 8888/tcp

CMD ["/modsec_entry.sh"]
