## Proof of Concept For Setting the Honeytraps using ModSecurity and Logging them at ELK

The goal of this PoC to set the ModSecurity based Honeytraps. Basically we will lay honeytraps using the rules of ModSecurity. In this PoC, we will consider different such honeytraps and gather information about the attacker. There are three phases of recognizing the attack. 

*    Luring the Attacker with a bait
*    Identifying the Attacker from his/her actions
*	 Gathering the Information about the Attacker


| Bait | Identification of Attacker | Information of Attacker| 
| --- | --- | --- | 
| Adding Fake Listen Ports | If the web client is trying to access these fake ports, it will tagged as malicious | IP Address of the web client and ports used by it|



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
cd Honeypot-Project/honeytraps/
docker-compose build
docker-compose up -d
```
*  Check the status of containers 
```
docker ps
```

*  HoneyTrap-1 (Adding Fake HTTP Ports for Listening)
    * In this we will use additional ports of 8000,8080,8888 for listening
    * All the traffic that is received on these port is tagged malicious   
    * Open the browser and enter the HostIP with any of above three ports (like shown in the image below)
![Alt text](./screenshots/honeytrap1_bait.png?raw=true "Accessing Fake Ports")
	* Alternatively run the below command from terminal
```
curl <Host-IP>:8080/index.html
```
	*  Wait for a minute or two for the logs to reach the ELK
	*  Open http://localhost:5601/app/kibana in your browser 
	*  Create an Index with the name filebeat* and Press Next 
![Alt text](./screenshots/filebeat_index_create.png?raw=true "Filebeat index creation")
	*  Use Time Filter field name: @timestamp 
![Alt text](./screenshots/filebeat_index_create_2.png?raw=true "Filebeat index creation")
	*  Navigate to Discover Menu on the Left Hand Side and logs can be visualized in Kibana Dashboard 
![Alt text](./screenshots/honeytrap1_logs.png?raw=true "Visualizing the Honeytrap-1 Logs")
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
    