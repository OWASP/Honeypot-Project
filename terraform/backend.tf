# Remote state backend using S3.
#
# Each workspace corresponds to one environment (e.g. staging, production).
# As of provider v6, state locking is handled natively by S3, so no
# DynamoDB table is required anymore.
#
# One-time setup before first use:
#   aws s3 mb s3://owasp-honeypot-tfstate --region eu-west-1

terraform {
  backend "s3" {
    bucket  = "owasp-honeypot-tfstate"
    key     = "fleet/terraform.tfstate"
    region  = "eu-west-1"
    encrypt = true
  }
}
