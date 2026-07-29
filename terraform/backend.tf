# Remote state backend using S3.
#
# Each workspace corresponds to one environment (e.g. staging, production).
# The DynamoDB table provides state locking so two concurrent applies never
# clobber each other.
#
# One-time setup before first use:
#   aws s3 mb s3://owasp-honeypot-tfstate --region eu-west-1
#   aws dynamodb create-table \
#     --table-name owasp-honeypot-tfstate-lock \
#     --attribute-definitions AttributeName=LockID,AttributeType=S \
#     --key-schema AttributeName=LockID,KeyType=HASH \
#     --billing-mode PAY_PER_REQUEST \
#     --region eu-west-1

terraform {
  backend "s3" {
    bucket         = "owasp-honeypot-tfstate"
    key            = "fleet/terraform.tfstate"
    region         = "eu-west-1"
    dynamodb_table = "owasp-honeypot-tfstate-lock"
    encrypt        = true
  }
}
