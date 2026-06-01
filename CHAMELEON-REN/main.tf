provider "aws" {
}

resource "aws_security_group" "chameleon_sg" {
  name        = "chameleon_ren_honeypot_sg_automated"
  description = "Strict perimeter for high-interaction honeypot"

  ingress {
    description = "HTTP - Open to the world"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS - Open to the world"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "SSH - Admin Access Only"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # Your exact IP HERE - WARNING: For production security, replace 0.0.0.0/0 with your strict IP (e.g., "x.x.x.x/32")
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# Dynamically fetch the absolute latest Ubuntu 24.04 AMI in your region
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical's official AWS Account

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd*/ubuntu-noble-24.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

resource "aws_instance" "chameleon_sensor" {
  ami           = data.aws_ami.ubuntu.id # Uses the dynamically fetched ID!
  instance_type = "t3.medium"
  key_name      = "chameleon-key"

  iam_instance_profile = aws_iam_instance_profile.chameleon_profile.name

  vpc_security_group_ids = [aws_security_group.chameleon_sg.id]

  root_block_device {
    volume_size = 30
    volume_type = "gp3"
  }

user_data = <<-EOF
    #!/bin/bash
    exec > >(tee /var/log/chameleon-provisioning.log|logger -t user-data -s 2>/dev/console) 2>&1
    echo "Starting CHAMELEON-REN Automated Provisioning..."

    apt-get update -y
    apt-get install -y git docker.io docker-compose-v2

    systemctl start docker
    systemctl enable docker
    usermod -aG docker ubuntu

    cd /home/ubuntu
    git clone https://github.com/gautamjuvarajiya/chameleon-ren-release.git chameleon-ren
    chown -R ubuntu:ubuntu chameleon-ren

    cd chameleon-ren
    
    # CRITICAL DEPLOYMENT FIX: Generate the .env file locally on the EC2 instance
    cp .env.example .env
    sed -i "s/chameleon-ren-telemetry-YOUR-UNIQUE-ID/${aws_s3_bucket.telemetry_bucket.bucket}/g" .env
    
    docker compose up -d
    echo "Provisioning Complete!"
  EOF

  tags = {
    Name    = "chameleon-ren-sensor-automated"
    Project = "CHAMELEON-REN"
  }
}

resource "aws_s3_bucket" "telemetry_bucket" {
  bucket = "chameleon-ren-telemetry-automated-${random_id.bucket_suffix.hex}"
}

resource "random_id" "bucket_suffix" {
  byte_length = 4
}

# 1. Create the IAM Role
resource "aws_iam_role" "chameleon_role" {
  name = "HoneypotEvasionRole"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
    }]
  })
}

# 2. Attach EC2 Permissions (For Python Evasion Script)
resource "aws_iam_role_policy_attachment" "ec2_full_access" {
  role       = aws_iam_role.chameleon_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2FullAccess"
}

# 3. Attach S3 Permissions (For Logstash Telemetry)
resource "aws_iam_role_policy" "s3_access" {
  name = "HoneypotS3Policy"
  role = aws_iam_role.chameleon_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action   = ["s3:PutObject", "s3:ListBucket"]
        Effect   = "Allow"
        Resource = [
          aws_s3_bucket.telemetry_bucket.arn,
          "$${aws_s3_bucket.telemetry_bucket.arn}/*"
        ]
      }
    ]
  })
}

# 4. Create an Instance Profile
resource "aws_iam_instance_profile" "chameleon_profile" {
  name = "HoneypotEvasionProfile"
  role = aws_iam_role.chameleon_role.name
}
