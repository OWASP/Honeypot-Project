output "fleet_elastic_ips" {
  description = "Elastic IPs for all sensor nodes, keyed by region. These are the stable public addresses registered with Shodan."
  value = {
    "eu-west-1"  = module.eu_west_1.elastic_ip
    "us-east-1"  = module.us_east_1.elastic_ip
    "ap-south-1" = module.ap_south_1.elastic_ip
  }
}

output "fleet_instance_ids" {
  description = "EC2 instance IDs for all sensor nodes, keyed by region."
  value = {
    "eu-west-1"  = module.eu_west_1.instance_id
    "us-east-1"  = module.us_east_1.instance_id
    "ap-south-1" = module.ap_south_1.instance_id
  }
}

output "fleet_public_dns" {
  description = "Public DNS names for all sensor nodes, keyed by region."
  value = {
    "eu-west-1"  = module.eu_west_1.public_dns
    "us-east-1"  = module.us_east_1.public_dns
    "ap-south-1" = module.ap_south_1.public_dns
  }
}
