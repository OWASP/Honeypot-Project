*Located in the repo's Wiki section*

# Basic AWS Amazon Elastic Container Service (ECS) Setup for Modsecurity Honeypot

### WARNING: ALL LINKS PROVIDED ARE FOR THE DEFAULT REGION ON AWS CONSOLE, PLEASE MAKE SURE YOU SELECT YOUR DESIRED REGION.

### 0. Install and Set up aws-cli (if needed)

1. Install aws-cli

2. Go to https://console.aws.amazon.com/iam/home#/security_credentials

3. Create or use an Access Key from the "Access Keys" section
   
   You need:
   
   * Access Key ID
   
   * Secret Access Key
   
   * Default Region ID - what is displayed at the region selection, like "eu-west-1"
   
   * Default output format (can be none)

Configure aws-cli:

```bash
aws configure
```

### 1. Set up Task for docker container

The docker image used for this task can be found [here](https://hub.docker.com/r/floyd0122/honeytrap-modsec):

1. Edit the following entries in ```honeytraps/waf_modsec/aws-ecs-container-definition.json```:
   
   * Change "LOGSTASH_HOST" env value to your logstash server IP and port
   
   * Change "awslogs-region" in "logConfiguration" to your region

2. Create the task:
   
   ```bash
   cd ~/Honeypot-Project/honeytraps/waf_modsec
   aws ecs register-task-definition --cli-input-json "$(cat aws-ecs-container-definition.json | tr '\n' ' ')"
   ```
   
   You can observe the created task [here](https://console.aws.amazon.com/ecs/home#/taskDefinitions). Note that running this command creates a new revision for the Task definition automatically instead overwriting it.    

3. Create log group for the task
   
   ```bash
   aws logs create-log-group --log-group-name "/ecs/honeytrap-modsec"
   ```

### 2. Create Cluster for the Honeypot (if you want to use it in an existing one just skip this)

Creating a cluster to run services in:

```bash
aws ecs create-cluster --cluster-name "modsec-honeytrap"
```

You can observe the created cluster [here](https://eu-west-1.console.aws.amazon.com/ecs/home?region=eu-west-1#/clusters)

### 3. Create a Networking for the cluster and service

This is a specific example, the IP and subnet ranges can be changed freely.

1. Create a Virtual Private Cloud (vpc) if you need a separate one ([reference](https://docs.aws.amazon.com/vpc/latest/userguide/what-is-amazon-vpc.html)):
   
   ```bash
   aws ec2 create-vpc --cidr-block 10.0.0.0/16
   #note vpc-id
   aws ec2 create-internet-gateway
   #note internetGateway-id
   # Add internet-gateway to private cloud
   aws ec2 attach-internet-gateway --internet-gateway-id <internetGateway-id> --vpc-id <vpc-id>
   # Find route table id
   aws ec2 describe-route-tables --filters Name=vpc-id,Values=<vpc-id>
   # note the route-table-id
   # Add route to gateway in the route-table
   aws ec2 create-route --route-table-id <route-table-id> --destination-cidr-block 0.0.0.0/0 --gateway-id <internetGateway-id>
   ```
   
   Please note the "VpcId" in the output.

2. Create a subnet in the vpc what the service will use:
   
   ```bash
   aws ec2 create-subnet --vpc-id <vpc-id> --cidr-block 10.0.0.0/24
   ```
   
   Please note the "Subnetid" fiels's value in the ouput.

3. Create a Security group (port rules) for the Virtual Private Cloud what the Service will use.
   
   *This is not necessary as a default group is created for the VPC upon creation but it is good practice to separate the services*
   
   ```bash
   aws ec2 create-security-group --group-name "EC2Container-honeytrap" --description "Port rules for the Honeytrap Docker Container" --vpc-id <vpc-id>
   # Adding the required rules
   aws ec2 authorize-security-group-ingress --group-id <group-id> --protocol tcp --cidr 0.0.0.0/0 --port 80 
   aws ec2 authorize-security-group-ingress --group-id <group-id> --protocol tcp --cidr 0.0.0.0/0 --port 8080
   aws ec2 authorize-security-group-ingress --group-id <group-id> --protocol tcp --cidr 0.0.0.0/0 --port 8000
   aws ec2 authorize-security-group-ingress --group-id <group-id> --protocol tcp --cidr 0.0.0.0/0 --port 8888
   ```
   
   Please note the group ID.
   
   ```bash
   aws ec2 create-network-interface --description "HoneyTrap Network Interface" --subnet-id <subnet-id> --groups <group-id>
   ```

Note: You can most (not all) of this on through the Web UI [here](https://console.aws.amazon.com/vpc/home#vpcs:sort=VpcId) as well.

### 4. Create Service responsible for the Task created above and link them together

This will be added to the Cluster and ran there using FARGATE (serverless).

1. Create Service using the Subnet ID and the Security Group ID:
   
   ```bash
   aws ecs create-service \
   --service-name "honeytrap-service" \
   --cluster "modsec-honeytrap" \
   --task-definition "honeytrap" \
   --desired-count 1 \
   --launch-type "FARGATE" \
   --network-configuration "awsvpcConfiguration={subnets=[<subnet-id>],securityGroups=[<securitygroup-id>],assignPublicIp=ENABLED}"
   ```
   
   If all went well the Service is created and can be observed [here](https://console.aws.amazon.com/ecs/home#/clusters/modsec-honeytrap/services). 
   
   * Select "Tasks" tab
   
   * Select the running task (Click on the Task id)
   
   * Observe the Public IP adress
   
   * Expand the Containter and click on "View logs in CloudWatch" to see the docker output
