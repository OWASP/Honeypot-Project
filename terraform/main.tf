# Root configuration.
# Calls the honeypot-node module once per region using a dedicated provider alias.
# Adding a new region is additive: drop a new provider alias in providers.tf and
# a new module block here. Nothing else needs to change.

module "eu_west_1" {
  source = "./modules/honeypot-node"

  providers = {
    aws = aws.eu_west_1
  }

  aws_region     = "eu-west-1"
  node_tag       = "honeypot-eu-west-1"
  key_name       = var.key_name
  admin_cidr     = var.admin_cidr
  instance_type  = var.instance_type
  volume_size_gb = var.volume_size_gb
  logstash_host  = var.logstash_host
  shodan_api_key = var.shodan_api_key
  repo_url       = var.repo_url
}

module "us_east_1" {
  source = "./modules/honeypot-node"

  providers = {
    aws = aws.us_east_1
  }

  aws_region     = "us-east-1"
  node_tag       = "honeypot-us-east-1"
  key_name       = var.key_name
  admin_cidr     = var.admin_cidr
  instance_type  = var.instance_type
  volume_size_gb = var.volume_size_gb
  logstash_host  = var.logstash_host
  shodan_api_key = var.shodan_api_key
  repo_url       = var.repo_url
}

module "ap_south_1" {
  source = "./modules/honeypot-node"

  providers = {
    aws = aws.ap_south_1
  }

  aws_region     = "ap-south-1"
  node_tag       = "honeypot-ap-south-1"
  key_name       = var.key_name
  admin_cidr     = var.admin_cidr
  instance_type  = var.instance_type
  volume_size_gb = var.volume_size_gb
  logstash_host  = var.logstash_host
  shodan_api_key = var.shodan_api_key
  repo_url       = var.repo_url
}
