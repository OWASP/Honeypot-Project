# ap-south-1 deployment values.
# Mumbai -- covers Asia-Pacific traffic and is useful for IST-timezone monitoring.

key_name      = "honeypot-key-ap"
instance_type = "t3.medium"
admin_cidr    = "0.0.0.0/0" # replace with maintainer IP in production: "x.x.x.x/32"
