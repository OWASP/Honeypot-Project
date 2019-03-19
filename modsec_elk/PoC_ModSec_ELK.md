## Proof of Concept For Sending the ModSecurity Logs to ELK 

The goal of this PoC to send the ModSecurity Audit Logs to ELK

In this setup we have two Docker Containers. One for ModSecurity and the other for ELK. 
### Step by Step Instructions
* Dependencies for the setup
    * Docker Installed on your Host machine
    * Ports 80,5044,9200 should be available free in host machine
    * If ports are not free, please change to appropriate values in docker-compose.yml

*   Clone this repository in your Host Machine
```
cd ~
git clone https://github.com/OWASP/Honeypot-Project.git
```
*   To start the setup run the below command
```
cd Honeypot-Project/modsec_elk/
docker-compose up -d
```
*  Check the status of containers 
```
docker ps
```
*  Install the Filebeat at ModSecurity-CRS Container
```
docker exec -it elk_app bash
wget  https://artifacts.elastic.co/downloads/beats/filebeat/filebeat-5.1.2-x86_64.rpm
rpm -vi filebeat-5.1.2-x86_64.rpm
```
*  Load the Filebeat template 
```
curl -H 'Content-Type: application/json' -XPUT 'http://localhost:9200/_template/filebeat' -d@/etc/filebeat/filebeat.template.json
```
*  Start the Filebeat at modsec_app
```
cp ~/Honey-Project/modsec_elk/filebeat.yml /etc/filebeat/filebeat.yml
/etc/init.d/filebeat start
filebeat.sh -e -c filebeat.yml -d "publish"
filebeat.sh setup -e \
  -E output.logstash.enabled=false \
  -E output.elasticsearch.hosts=['localhost:9200'] \
  -E output.elasticsearch.username=filebeat_internal \
  -E output.elasticsearch.password=changeme \
  -E setup.kibana.host=localhost:5601
```
*  Configuring  Logstash for Filebeat 
```
docker exec -it elk_app bash
cd ~/Honeypot-Project/modsec_elk/
cp filebeat_logstash.conf /etc/logstash/conf.d/
cd /etc/logstash/conf.d/
/opt/logstash/bin/logstash -f filebeat_logstash.conf
```
*  Send the Logs from ModSec to ELK 
    * Now we are ready to pump the data from the ModSec to ELK with the help of filebeat   
```
Run the below commands to observe the logs in the rubydebug console of logstash
curl localhost:80/index.html?exec=/bin/bash
curl 'http://localhost:8081/?q="><script>alert(1)</script>'
```
*  Logs can also be seen at Kibana Dashboard (http://localhost:5601/app/kibana)


