# eu-west-1 deployment values.
# Adrian's existing region (matches the awslogs-region in aws-ecs-container-definition.json).
# Use this as the stable single-region baseline before enabling the other regions.

key_name      = "honeypot-key-eu"
instance_type = "t3.medium"
admin_cidr    = "0.0.0.0/0" # replace with maintainer IP in production: "x.x.x.x/32"

# logstash_host and shodan_api_key should be passed via TF_VAR_ environment variables
# or a secrets manager -- never commit real values here.
# logstash_host  = "TF_VAR_logstash_host"
# shodan_api_key = "TF_VAR_shodan_api_key"
