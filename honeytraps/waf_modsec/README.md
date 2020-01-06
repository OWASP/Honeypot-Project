# WAF ModSecurity Honeypot docker image

The AWS ECS setup can be found [here](https://github.com/OWASP/Honeypot-Project/wiki/AWS-ECS-Setup-for-ModSecurity-Honeypot).

## Setup Honeypot

```bashag-0-1dttmup1hag-1-1dttmup1h
cd ~/Honeypot-Project/honeytraps/waf_modsec
cp sample-env env
# change the IP where your ELK image/service will be running
docker-compose build
```

## Running Honeypot

```bash
cd ~/Honeypot-Project/honeytraps/waf_modsec
docker-compose up
```

## Accessing the Honeypot

Port 9091is open, and can be accessed.

Port 8000,8080,8888 are open and can be accessed, these will trigger logging.
