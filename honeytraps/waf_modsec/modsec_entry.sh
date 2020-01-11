# ~/bin/sh
apachectl
python3 /app/preprocess-modsec-log.py &
filebeat -e -c filebeat.yml -d "publish"
