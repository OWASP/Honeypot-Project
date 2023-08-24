FROM ubuntu:focal
WORKDIR /app/
USER root
ENV LC_ALL="C.UTF-8"
RUN apt-get update
RUN apt-get install -y nano python3-pip
RUN pip3 install pipenv
RUN pipenv install
COPY ./ /app
CMD ["/bin/bash", "/app/start.sh"]
