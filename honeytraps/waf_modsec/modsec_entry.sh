#!/bin/sh
mkdir -p /tmp/modsecurity/data
chown -R daemon:daemon /tmp/modsecurity/data

# Configure reverse proxy if BACKEND is specified
PROXY_CONF="/usr/local/apache2/conf/extra/httpd-proxy.conf"
if [ -n "$BACKEND" ]; then
    echo "[modsec_entry] Configuring reverse proxy to BACKEND: $BACKEND"
    cat <<PROXY_EOF > "$PROXY_CONF"
ProxyRequests Off
ProxyPreserveHost On

<Proxy *>
    Require all granted
</Proxy>

# Preserve local active deception lures
ProxyPass /robots.txt !
ProxyPass /login.php.bak !
ProxyPass /login.html !
ProxyPass /form.html !

# Proxy all other traffic to active persona backend
ProxyPass / ${BACKEND}/ retry=1 timeout=10
ProxyPassReverse / ${BACKEND}/
PROXY_EOF
else
    echo "[modsec_entry] No BACKEND specified; serving local static decoy files."
    cat <<PROXY_EOF > "$PROXY_CONF"
# Standalone mode: no active persona backend configured
PROXY_EOF
fi

apachectl
python3 /app/rule_watcher.py &
filebeat -e -c /etc/filebeat/filebeat.yml -d "publish"
