# MISP docker image

## MISP Setup

- Create an env file for MISP
  
  ```bash
  cp ~/Honeypot-Project/honeytraps/misp/sample-env ~/Honeypot-Project/honeytraps/misp/env
  ```

- Set DOCKER_ROOT variable in the env file to a path to your liking (```/docker``` or ```~/docker``` for example) where the database will be intialised and stored on your system. The folder should be only used by docker.

- Setup MISP
  
  ```bash
  cd ~/Honeypot-Project/honeytraps/misp
  ./setup_misp.sh
  ```

**Note that the ```setup_misp.sh``` script will ask for sudo! It is needed to create the folder if it does not exist and to set the correct permissions. Follow the steps manually in the script if you do not trust it.**

## Running MISP

Run the start script

```bash
cd ~/Honeypot-Project/honeytraps/misp
./run_misp.sh
```

## Using MISP

The web interface can be accessed from ```https://localhost```. 

Default Login details:

```bash
Login: admin@admin.test
Password: admin
```

You will be asked to change the password the first time you log in.
