FROM sebp/elk:800
COPY filebeat_logstash.conf /etc/logstash/conf.d/filebeat_logstash.conf
ADD ./start.sh /usr/local/bin/start.sh
RUN chmod +x /usr/local/bin/start.sh

# Download the GeoLite2-ASN database for ISP/ASN enrichment.
# Requires a free MaxMind account: https://www.maxmind.com/en/geolite2/signup
# Pass your license key at build time: docker build --build-arg MAXMIND_LICENSE_KEY=<key>
ARG MAXMIND_LICENSE_KEY=""
RUN if [ -n "$MAXMIND_LICENSE_KEY" ]; then \
      curl -sSL "https://download.maxmind.com/app/geoip_download?edition_id=GeoLite2-ASN&license_key=${MAXMIND_LICENSE_KEY}&suffix=tar.gz" \
        | tar -xzO --wildcards '*/GeoLite2-ASN.mmdb' \
        > /etc/logstash/GeoLite2-ASN.mmdb && \
      echo "GeoLite2-ASN database downloaded successfully."; \
    else \
      echo "MAXMIND_LICENSE_KEY not set - removing ASN enrichment block from filebeat_logstash.conf to prevent validation crash."; \
      sed -i '/# --- ASN\/ISP enrichment start ---/,/# --- ASN\/ISP enrichment end ---/d' /etc/logstash/conf.d/filebeat_logstash.conf; \
    fi

EXPOSE 5601 9200 9300 5044
VOLUME /var/lib/elasticsearch
CMD [ "/usr/local/bin/start.sh" ]
