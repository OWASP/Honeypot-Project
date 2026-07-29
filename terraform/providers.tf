# Provider aliases for the three deployment regions.
# Each alias maps to one module call in main.tf.
# Add a new alias + module block to expand the fleet to an additional region.

terraform {
  required_version = ">= 1.5"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  alias   = "eu_west_1"
  region  = "eu-west-1"
  profile = var.aws_profile
}

provider "aws" {
  alias   = "us_east_1"
  region  = "us-east-1"
  profile = var.aws_profile
}

provider "aws" {
  alias   = "ap_south_1"
  region  = "ap-south-1"
  profile = var.aws_profile
}
