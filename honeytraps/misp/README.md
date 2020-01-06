# MISP docker image

## MISP Setup

- Create an env file for MISP
  
  ```bash
  cp ~/Honeypot-Project/honeytraps/misp/sample-env ~/Honeypot-Project/honeytraps/misp/env
  ```

- Set DOCKER_ROOT variable in the env file to a path to your liking (```/docker``` or ```~/docker``` for example) where the database will be intialised

- Setup MISP
  
  ```bash
  cd ~/Honeypot-Project/honeytraps/misp
  ./setup_misp.sh
  ```

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
