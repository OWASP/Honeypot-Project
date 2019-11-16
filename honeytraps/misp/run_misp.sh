#!/bin/bash
source './env'
docker run -it -p 443:443 -p 80:80  -p 3306:3306 -v $DOCKER_ROOT/misp-db:/var/lib/mysql  harvarditsecurity/misp
