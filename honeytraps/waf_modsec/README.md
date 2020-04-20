# WAF ModSecurity Honeypot docker image

The AWS ECS setup can be found [here](https://github.com/OWASP/Honeypot-Project/wiki/AWS-ECS-Setup-for-ModSecurity-Honeypot).

## Setup Honeypot

```bashag-0-1dttmup1hag-1-1dttmup1h
cd ~/Honeypot-Project/honeytraps/waf_modsec
cp sample-env env
# change the IP where your ELK image/service will be running in the "env" file
docker-compose build
```

## Running Honeypot

```bash
cd ~/Honeypot-Project/honeytraps/waf_modsec
docker-compose up
```

## Accessing the Honeypot

Port 9091 is open, and can be accessed.

Port 8000,8080,8888 are open and can be accessed, these will trigger logging.

## Uploading (latest) image to DockerHub

The Honeytrap docker image is needed by the AWS container definition ```honeytraps/waf_modsec/aws-ecs-container-definition.json``` under the ```"image"``` tag.

The Image currently resides in my personal DockerHub account named as [floyd0122/honeytrap-modsec](https://hub.docker.com/repository/docker/floyd0122/honeytrap-modsec). In the future this needs to be pushed to OWASPs account.

When it is moved to a new location, the AWS config needs to be changed accordingly.

#### To upload a new/latest image

Make sure you are logged in to docker

```bash
cd ~/Honeypot-Project/honeytraps/waf_modsec
docker build ./ -t <Dockerhub username>/honeytrap-modsec
docker push <Dockerbub username>/honeytrap-modsec
```


