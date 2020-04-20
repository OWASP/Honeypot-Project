## Building Honeytraps and Reporting Threat Intelligence

The goal of this PoC to set the ModSecurity based Honeytraps. In this PoC, we will consider different such honeytraps and gather information about the attacker. 

There are three phases of recognizing the attack.

* Luring the Attacker with a bait
* Identifying the Attacker from his/her actions
* Gathering the Information about the Attacker (From the logs)

| Bait                            | Identification of Attacker                                                               |
| ------------------------------- | ---------------------------------------------------------------------------------------- |
| Adding Fake Listen Ports        | If the web client is trying to access these fake ports, it will tagged as malicious      |
| Adding Fake entry in robots.txt | If it accesses the restricted location,  it will tagged as malicious                     |
| Adding Fake HTML comments       | If it accesses the Debugging information from HTML comments, it can be marked malicious  |
| Adding Fake Hidden Form Fields  | If it manipulates the hidden form field(s) set by the web server, it is tagged malicious |
| Adding Fake Cookie Data         | If it manipulates the cookies set by the web server, it is tagged malicious              |

Basically we will lay honeytraps using the Core Rule Set (CRS) rules of ModSecurity. ModSecurity is Web Application Firewall which runs on the web server. We gather the attack information using the Audit logs of ModSecurity. In order to handle the audit logs in a structured manner, we send the logs to Elasticsearch Logstash Kibana(ELK) Stack. ELK provides an efficient way for handling the logs and visualizing them. At ELK, we filter the relevant logs from the non-relevant ones. All the relevant log information is reported to Malware Information Sharing Platform (MISP). 

In this setup we have three Docker Containers. Each one for ModSecurity+Apache Web Server, ELK and MISP (as shown in below architecture diagram).

![Alt text](./honeytrap_arch.jpg?raw=true "Building Honeytraps and Reporing Threat Intelligence")

~~A step by step video demonstration is shown at https://www.youtube.com/watch?v=uE-uYwqEZYA~~ -- **Outdated**

### Setup Instructions

1. Dependencies for the setup
   
   * Docker Installed on your Host machine
   *    Atleast 8GB of RAM on your Host machine
   * Ports listed in docker-compose.yml should be available free in host machine
   * If ports are not free, please change to appropriate values in docker-compose.yml

2. Clone this repository into your Host Machine

  ```bash
  cd ~
  git clone --recurse-submodules https://github.com/OWASP/Honeypot-Project.git
  cd ~/Honeypot-Project/honeytraps
  ```

3. Setup MISP server, then ELK, then Modsecurity Honeypot as specified in their own README (located in ```misp, waf_elk and waf_modsec``` respecitvely)

4. Start all 3 of them them as specified in their own READMEs

5. Generate some web traffic using curl

  ```bash
  curl 'localhost:9091/index.html?exec=/bin/bash'
  curl 'http://localhost:9091/?q="><script>alert(1)</script>'
  ```

  The logs should reach MISP in about 1-2 minutes, if you log in (details in the MISP README) you should be able to see them.

## Usage

* **Kibana Dashboard Visualization**
  
  * Open Kibana [http://localhost:5601/app/kibana](http://localhost:5601/app/kibana)
  
  * Click on Dashboard from left hand side and click on Honeytrap Dashboard then you will see various information gathered through all honeytraps
    ![Alt text](./screenshots/savedObj3.png?raw=true "Saved Object Creation")

* **Threat Reporting at MISP**
  
  * All the information gathered through all honeytraps is automically reported at MISP dashboard. Go to MISP URL (https://localhost) for viewing them.
    ![Alt text](./screenshots/events.png?raw=true "Honeytrap Events at MISP")
  * The events and tags are auto-generated from `misp-push.py`
    ![Alt text](./screenshots/tags.png?raw=true "Honeytrap Events at MISP")
    ![Alt text](./screenshots/event-details.png?raw=true "Honeytrap Events at MISP")

## Implemented Honeytrap Baits

**HoneyTrap-1 (Adding Fake HTTP Ports for Listening)**

* In this we will use additional ports of 8000,8080,8888 for listening

* All the traffic that is received on these port is tagged malicious   

* Open the browser and enter the HostIP with any of above three ports (like shown in the image below)
  ![Alt text](./screenshots/honeytrap1_bait.png?raw=true "Accessing Fake Ports")

* Alternatively run the below command from terminal
  
  ```
  curl <Host-IP>:8888/index.html
  ```

* Navigate to Discover Menu on the Left Hand Side and Honeytrap-1 Logs can be visualized in Kibana Dashboard 
  ![Alt text](./screenshots/honeytrap1_logs.png?raw=true "Visualizing the Honeytrap-1 Logs")

* **HoneyTrap-2 (Adding Fake Disallow Entry in robots.txt file)**
  
  * Every website maintains its robots.txt to advise the allowed and disallowed entries to the crawler
  * Based on these entries, crawler should not access the Disallowed entries, but the Disallow is just a suggestion in the robots.txt, so we will add a fake Disallow entry in the robots.txt file
  * Whoever tries to access this location is marked malicious 
  * We can also have a fake authentication on this fake location to get the username/password pairs from the attacker  
  * Open the robots.txt page and try to access Fake Disallowed robots.txt Entry (like shown in the image below)
    ![Alt text](./screenshots/honeytrap2_bait.png?raw=true "Accessing Fake Disallow robots.txt Entry")
  * Access the fake location mentioned in the robots.txt file 
    ![Alt text](./screenshots/honeytrap2_bait_2.png?raw=true "Accessing Fake Disallow robots.txt Location + Authentication ")    
  * In the below log screenshot we can see that Attacker has used the Admin as Username and Password as "Password" to get access to the fake location mentioned in robots.txt, all the tries (of username/password) of attacker are logged at ELK
    ![Alt text](./screenshots/honeytrap2_logs.png?raw=true "Visualizing the Honeytrap-2 Logs")

* **HoneyTrap-3 (Adding Fake HTML Comments in the login page)**
  
  * In this trap, we will add a fake HTML comment in the login page, this fake comment redirects the attacker to some other location. Whoever tries to access this location is tagged malicious   
  * Open the Host-IP:9091/login.html in browser and try to access comments of page (like shown in the image below). The highlighted line in the below picture shows the fake HTML comment added by the ModSecurity
    ![Alt text](./screenshots/honeytrap3_bait.png?raw=true "Accessing Fake HTML comment")
  * Try to access the location mentioned in the HTML comment
    ![Alt text](./screenshots/honeytrap3_bait_2.png?raw=true "Accessing HTML comment specified location")    
  * In the below log screenshot we can see that Attacker is tagged
    ![Alt text](./screenshots/honeytrap3_logs.png?raw=true "Visualizing the Honeytrap-3 Logs")

* **HoneyTrap-4 (Adding Fake Hidden Form Fields)**
  
  * HTML hidden form fields are just like normal form fields, except for one distinct difference: The browser doesn’t display them to the user. Hidden fields are used as a mechanism to pass data from one request to another, and their contents are not supposed to be altered
  * This is how the raw HTML hidden form field looks in the source
  * `<input type="hidden" value="front" name="context">`
  * Just as we did with adding fake HTML comments, we can use the same methodology to inject fake HTML hidden form fields. The key to this technique is the closing `</form>` HTML tag. We will inject our honeytrap data just before it.
  * Whoever tries to manipulate this form field is tagged malicious   
  * Open the Host-IP:9091 in browser and try to access hidden form field of page (like shown in the image below). 
    The highlighted line in the below picture shows the fake HTML comment added by the ModSecurity
    ![Alt text](./screenshots/honeytrap4_bait.png?raw=true "Accessing Fake Hidden Form Field")
  * Change the hidden field value to true, put some data in the form and submit it
    ![Alt text](./screenshots/honeytrap4_bait_2.png?raw=true "Changing the hidden form field value")    
  * In the below log screenshot we can see that Attacker is tagged at ELK
    ![Alt text](./screenshots/honeytrap4_logs.png?raw=true "Visualizing the Honeytrap-4 Logs")

* **HoneyTrap-5 (Adding Fake Cookies)**
  
  * The HTTP protocol has no built-in session awareness. This means that each transaction is independent from the others. The application, therefore, needs a method to track who someone is and what actions he has previously taken (for instance, in a multistep process). Cookies were created precisely for this purpose
  * The application issues `Set-Cookie` response header data to the client web browser.
  * Much like attackers take aim at parameter payloads, they also attempt to alter cookie data that the application hands out. This can be done with the tools like http://www.editthiscookie.com/ 
  * Open the Host-IP:9091 in browser and open the site information to access the cookie information (like shown in the image below). 
    The highlighted line in the below picture shows the cookie data is `Admin:0`
    ![Alt text](./screenshots/honeytrap5_bait.png?raw=true "Accessing Cookies")
  * We try change the cookie data using `editthiscookie` chrome-extension (you can others similar to this). We try to change `Admin:0` to `Admin:5` after that fill the form and submit the data 
    ![Alt text](./screenshots/honeytrap5_bait_2.png?raw=true "Changing the cookie value")    
  * In the below log screenshot we can see that Attacker is tagged at ELK who changed the cookie value
    ![Alt text](./screenshots/honeytrap4_logs.png?raw=true "Visualizing the Honeytrap-5 Logs")

* Please check the ```waf_modsec/modsecurity-extension.conf``` file for more information about the honeytraps.

## **Known Issues**:

* max virtual memory areas vm.max_map_count [65530] is too low, increase to at least [262144], Run the below command 
  
  ```
     sudo sysctl -w vm.max_map_count=262144
  ```

## **References**

* Web Application Defender's Cookbook: Battling Hackers and Protecting Users 
* http://www.editthiscookie.com/
* https://www.trustwave.com/en-us/resources/blogs/spiderlabs-blog/detecting-malice-with-modsecurity-honeytraps/
* https://www.trustwave.com/en-us/resources/blogs/spiderlabs-blog/setting-honeytraps-with-modsecurity-adding-fake-hidden-form-fields/
* https://www.trustwave.com/en-us/resources/blogs/spiderlabs-blog/setting-honeytraps-with-modsecurity-adding-fake-cookies/
* https://www.trustwave.com/en-us/resources/blogs/spiderlabs-blog/setting-honeytraps-with-modsecurity-adding-fake-robotstxt-disallow-entries/
* https://logz.io/learn/complete-guide-elk-stack/
* https://misp-project.org
* https://github.com/harvard-itsecurity/docker-misp
* https://pymisp.readthedocs.io/
