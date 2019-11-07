#!/bin/bash
source '../env' #Importing variables from env file
set -u
if [[ -z {$DOCKER_ROOT} ]]; then
    echo "DOCKER_ROOT is not set in the env file! exiting"
    exit 1
fi

chown $USER:docker $DOCKER_ROOT
mkdir -p $DOCKER_ROOT/misp-db
chown $USER:docker $DOCKER_ROOT/misp-db
docker pull harvarditsecurity/misp
docker run -it --rm -v $DOCKER_ROOT/misp-db:/var/lib/mysql harvarditsecurity/misp /init-db