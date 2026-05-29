FROM logstash:7.17.10
WORKDIR /app/
COPY ./ /app
COPY ./pipeline /usr/share/logstash/pipeline
USER root

# Download the GeoLite2-ASN database for ISP/ASN enrichment.
# Requires a free MaxMind account: https://www.maxmind.com/en/geolite2/signup
# Pass your license key at build time: docker build --build-arg MAXMIND_LICENSE_KEY=<key>
ARG MAXMIND_LICENSE_KEY=""
RUN if [ -n "$MAXMIND_LICENSE_KEY" ]; then \
      curl -sSL "https://download.maxmind.com/app/geoip_download?edition_id=GeoLite2-ASN&license_key=${MAXMIND_LICENSE_KEY}&suffix=tar.gz" \
        | tar -xzO --wildcards '*/GeoLite2-ASN.mmdb' \
        > /usr/share/logstash/GeoLite2-ASN.mmdb && \
      echo "GeoLite2-ASN database downloaded successfully."; \
    else \
      echo "MAXMIND_LICENSE_KEY not set - removing ASN enrichment block from logstash.conf to prevent validation crash."; \
      sed -i '/# --- ASN\/ISP enrichment start ---/,/# --- ASN\/ISP enrichment end ---/d' /usr/share/logstash/pipeline/logstash.conf; \
    fi

EXPOSE 5044