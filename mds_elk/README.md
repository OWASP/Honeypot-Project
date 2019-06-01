## Proof of Concept For Sending the ModSecurity Logs to ELK 

The goal of this PoC to send the ModSecurity Audit Logs to ELK

In this setup we have two Docker Containers. One for ModSecurity and the other for ELK. 
### Step by Step Instructions
* Dependencies for the setup
    * Docker Installed on your Host machine
    * Ports listed in docker-compose.yml should be available free in host machine
    * If ports are not free, please change to appropriate values in docker-compose.yml

*   Clone this repository in your Host Machine
```
cd ~
git clone https://github.com/OWASP/Honeypot-Project.git
```
*   To start the setup run the below command
```
cd Honeypot-Project/mds_elk/
docker-compose build
docker-compose up -d
```
*  Check the status of containers 
```
docker ps
```

*  Send the Logs from ModSec to ELK (Elastic Logstash Kibana)
    * Now we are ready to pump the data from the ModSec to ELK with the help of filebeat   
```
Run the below commands to observe the logs in the rubydebug console of logstash
curl localhost:9091/index.html?exec=/bin/bash
curl 'http://localhost:9091/?q="><script>alert(1)</script>'
```

*  Wait for a minute or two for the logs to reach the ELK
*  Open http://localhost:5601/app/kibana in your browser 
*  Create an Index with the name filebeat* and Press Next 
![Alt text](./screenshots/filebeat_index_create.png?raw=true "Filebeat index creation")
*  Use Time Filter field name: @timestamp 
![Alt text](./screenshots/filebeat_index_create_2.png?raw=true "Filebeat index creation")
*  Navigate to Discover Menu on the Left Hand Side and logs can be visualized in Kibana Dashboard 
![Alt text](./screenshots/filebeat_logs.png?raw=true "Visualizing the ModSecurity Audit Logs")
*  **Issues**:
   * max virtual memory areas vm.max_map_count [65530] is too low, increase to at least [262144], Run the below command 
   ```
        sudo sysctl -w vm.max_map_count=262144
   ```
   * If there is problem running with logstash, try with 
  ```
    /opt/logstash/bin/logstash --path.data /tmp/logstash/data -e filebeat_logstash.conf
```
* **References**
    * https://elk-docker.readthedocs.io/
    * https://www.elastic.co/guide/en/beats/filebeat/5.1/filebeat-installation.html
    * https://medium.com/tensult/log-centralization-using-filebeat-and-logstash-11640f77cf70  
    * https://github.com/docker-library/elasticsearch/issues/111
    * https://hub.docker.com/r/owasp/modsecurity-crs/
    