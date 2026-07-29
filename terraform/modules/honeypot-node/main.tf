# Reusable module for a single honeypot sensor node.
#
# Creates one EC2 instance, attaches an Elastic IP so Shodan always sees a
# stable public address, and wires up the security group and IAM profile.
# The userdata script bootstraps Docker, clones the repo, and starts the
# WAF stack automatically on first boot.
#
# Call this module once per region from the root main.tf, passing a
# different provider alias each time.

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# --- AMI: latest Ubuntu 24.04 LTS in this region ---
# We fetch it dynamically so the module works in any region without
# hardcoding AMI IDs, which are region-specific.
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd*/ubuntu-noble-24.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# --- security group ---
resource "aws_security_group" "sensor" {
  name        = "honeypot-sensor-${var.node_tag}"
  description = "Perimeter for honeypot sensor ${var.node_tag}. HTTP ports open to the world; SSH restricted."

  # Ports match the docker-compose.yml port mappings in honeytraps/waf_modsec.
  ingress {
    description = "HTTP decoy (primary listener)"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS decoy"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "ModSecurity WAF (port 8080)"
    from_port   = 8080
    to_port     = 8080
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Honeytrap listener (port 8000)"
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Honeytrap listener (port 8888)"
    from_port   = 8888
    to_port     = 8888
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "SSH admin access -- restrict var.admin_cidr to your IP in production"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.admin_cidr]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name    = "honeypot-sg-${var.node_tag}"
    Project = "owasp-honeypot"
  }
}

# --- EC2 instance ---
resource "aws_instance" "sensor" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.instance_type
  key_name               = var.key_name
  iam_instance_profile   = aws_iam_instance_profile.sensor.name
  vpc_security_group_ids = [aws_security_group.sensor.id]

  root_block_device {
    volume_size = var.volume_size_gb
    volume_type = "gp3"
    encrypted   = true
  }

  # templatefile() interpolates node_tag, aws_region, logstash_host, and
  # shodan_api_key into the bootstrap script before it is sent to EC2.
  user_data = templatefile("${path.module}/userdata.sh", {
    node_tag       = var.node_tag
    aws_region     = var.aws_region
    logstash_host  = var.logstash_host
    shodan_api_key = var.shodan_api_key
    repo_url       = var.repo_url
  })

  tags = {
    Name    = var.node_tag
    Project = "owasp-honeypot"
    Region  = var.aws_region
  }
}

# --- Elastic IP ---
# Allocated separately so the public IP survives instance stop/start cycles.
# persona_watchdog.py registers this IP with the Shodan API.
resource "aws_eip" "sensor" {
  instance = aws_instance.sensor.id
  domain   = "vpc"

  tags = {
    Name    = "honeypot-eip-${var.node_tag}"
    Project = "owasp-honeypot"
  }
}

# --- IAM: instance profile ---
# Grants only what the node actually needs: S3 PutObject for log archival.
# No EC2FullAccess -- the existing CHAMELEON-REN module was overly permissive;
# we scope this down properly.
resource "aws_iam_role" "sensor" {
  name = "honeypot-sensor-role-${var.node_tag}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })

  tags = {
    Project = "owasp-honeypot"
  }
}

resource "aws_iam_role_policy" "sensor_s3" {
  name = "honeypot-sensor-s3-${var.node_tag}"
  role = aws_iam_role.sensor.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["s3:PutObject", "s3:GetObject"]
      Resource = "arn:aws:s3:::owasp-honeypot-logs/*"
    }]
  })
}

resource "aws_iam_instance_profile" "sensor" {
  name = "honeypot-sensor-profile-${var.node_tag}"
  role = aws_iam_role.sensor.name
}
