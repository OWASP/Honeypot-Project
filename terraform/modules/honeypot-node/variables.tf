variable "aws_region" {
  description = "AWS region to deploy this node into."
  type        = string
}

variable "instance_type" {
  description = "EC2 instance type. t3.medium covers our two-container stack comfortably."
  type        = string
  default     = "t3.medium"
}

variable "key_name" {
  description = "Name of the EC2 key pair to use for SSH access."
  type        = string
}

variable "admin_cidr" {
  description = "CIDR block that is allowed to SSH into the node (port 22). Lock this down to the maintainer's IP in production."
  type        = string
  default     = "0.0.0.0/0"
}

variable "node_tag" {
  description = "Unique tag used to identify this sensor in Kibana dashboards and rotation logs (e.g. 'honeypot-eu-west-1')."
  type        = string
}

variable "logstash_host" {
  description = "host:port of the central Logstash instance. Filebeat inside the WAF container ships audit logs here."
  type        = string
}

variable "shodan_api_key" {
  description = "Shodan API key passed to persona_watchdog.py via the instance .env file."
  type        = string
  sensitive   = true
}

variable "repo_url" {
  description = "Git repository URL to clone on the node during bootstrap."
  type        = string
  default     = "https://github.com/OWASP/Honeypot-Project.git"
}

variable "volume_size_gb" {
  description = "Root EBS volume size in GB. 30 GB gives enough headroom for Docker images and logs."
  type        = number
  default     = 30
}

variable "vpc_cidr" {
  description = "CIDR block for the dedicated honeypot VPC. A /24 is plenty for a single sensor node."
  type        = string
  default     = "10.0.0.0/24"
}

variable "subnet_cidr" {
  description = "CIDR block for the public subnet inside the honeypot VPC. Must be a subset of vpc_cidr."
  type        = string
  default     = "10.0.0.0/28"
}

variable "honeypot_persona" {
  description = "Starting application persona for the honeypot node. persona_watchdog.py can rotate this at runtime based on Shodan Honeyscore."
  type        = string
  default     = "apache-2.2-php5"
}

variable "honeypot_profile" {
  description = "Industry segment profile (education, financial, general). Controls detection thresholds and export settings."
  type        = string
  default     = "general"
}
