FROM logstash:7.17.10
USER root

# Copy the pipeline config
COPY waf_elk/filebeat_logstash.conf /usr/share/logstash/pipeline/filebeat_logstash.conf

# Download the GeoLite2-ASN database for ISP/ASN enrichment.
# You need a free MaxMind account: https://www.maxmind.com/en/geolite2/signup
# Pass your license key at build time: docker build --build-arg MAXMIND_LICENSE_KEY=<key>
ARG MAXMIND_LICENSE_KEY=""
RUN if [ -n "$MAXMIND_LICENSE_KEY" ]; then \
      curl -sSL "https://download.maxmind.com/app/geoip_download?edition_id=GeoLite2-ASN&license_key=${MAXMIND_LICENSE_KEY}&suffix=tar.gz" \
        | tar -xzO --wildcards '*/GeoLite2-ASN.mmdb' \
        > /usr/share/logstash/GeoLite2-ASN.mmdb && \
      echo "GeoLite2-ASN database downloaded successfully."; \
    else \
      echo "MAXMIND_LICENSE_KEY not set - stripping the ASN enrichment block so logstash doesn't crash on boot"; \
      sed -i '/# --- ASN\/ISP enrichment start ---/,/# --- ASN\/ISP enrichment end ---/d' /usr/share/logstash/pipeline/filebeat_logstash.conf; \
    fi

USER logstash
EXPOSE 5044
