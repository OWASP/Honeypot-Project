# To Commit 8170f64 from b32ec05

* Separated Honeypot from the ELK docker-composer

* Created Honeypot docker container, also image on docker hub

* Created AWS ECS task definition for Honeypot

* Created documentation on how to deploy Honeypot on AWS Elastic Container Service (ECS) using the aws-cli

* Implemented ModSecurity Log preprocessing so they are completely JSON (reliable, but not the best way) with python.

* ELK correctly containerized with docker, fixed config file placements and improved separation from each other

* Changed folder structure to reflect docker changes

* Pushing events to MISP is containerized as a service

* Event push service for Elaticsearch->MISP is reworked
  
  * Improved reliability
  
  * Switched to ExtendedPyMIP module, the old one is deprecated and will be removed early 2020
  
  * Using async for connections wherever possible (mainly for elastic connection)
  
  * Improve MISP tagging and attribute handling for events
