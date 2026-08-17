# us-east-1 deployment values.
# North Virginia -- high attacker traffic volume, good complement to EU coverage.

key_name      = "honeypot-key-us"
instance_type = "t3.medium"
admin_cidr    = "0.0.0.0/0" # replace with maintainer IP in production: "x.x.x.x/32"
