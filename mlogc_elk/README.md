## Proof of Concept For Sending the ModSecurity Logs to ELK 

The goal of this PoC to send the ModSecurity Audit Logs using mlogc to ELK

In this setup we have two Docker Containers. One for ModSecurity+mlogc and the other for ELK. 
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
cd Honeypot-Project/mlogc_elk/
docker-compose build
docker-compose up -d
```
*  Check the status of containers 
```
docker ps
```

*  Send the Logs from ModSec to ELK (Elastic Logstash Kibana)
    * Now we are ready to pump the data from the ModSec to ELK with the help of mlogc   
```
Run the below commands to observe the logs in the rubydebug console of logstash
curl localhost:9091/index.html?exec=/bin/bash
curl 'http://localhost:9091/?q="><script>alert(1)</script>'
```

*  Navigate to /var/log/mlogc/data directory 
```
cd /var/log/mlogc/data
```
    * You can see the modsecurity logs organized according to date and time.   


*  Wait for a minute or two for the logs to reach the ELK
*  Open http://localhost:5601/app/kibana in your browser 
*  Create an Index with the name mlogc* and Press Next 
![Alt text](./screenshots/mlogc_index_create.png?raw=true "mlogc index creation")
*  Use Time Filter field name: @timestamp 
![Alt text](./screenshots/mlogc_index_create_2.png?raw=true "mlogc index creation")
*  Navigate to Discover Menu on the Left Hand Side and logs can be visualized in Kibana Dashboard 
![Alt text](./screenshots/mlogc_logs.png?raw=true "Visualizing the ModSecurity Audit Logs")
*  **Issues**:
   * max virtual memory areas vm.max_map_count [65530] is too low, increase to at least [262144], Run the below command 
   ```
        sudo sysctl -w vm.max_map_count=262144
   ```

* **References**
    * https://elk-docker.readthedocs.io/
    * https://fossies.org/linux/modsecurity/mlogc/INSTALL
    * https://hub.docker.com/r/owasp/modsecurity-crs/
    
