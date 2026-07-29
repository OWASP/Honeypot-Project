variable "aws_profile" {
  description = "AWS CLI profile to use for authentication. Defaults to 'default'."
  type        = string
  default     = "default"
}

variable "key_name" {
  description = "EC2 key pair name. Must already exist in every target region before applying."
  type        = string
}

variable "admin_cidr" {
  description = "CIDR that is allowed SSH access (port 22). Restrict to your IP in production, e.g. '203.0.113.5/32'."
  type        = string
  default     = "0.0.0.0/0"
}

variable "logstash_host" {
  description = "host:port of the central Logstash instance (e.g. '10.0.0.5:5044'). Filebeat on each node ships here."
  type        = string
}

variable "shodan_api_key" {
  description = "Shodan API key for persona_watchdog.py. Marked sensitive so it never appears in plan output."
  type        = string
  sensitive   = true
}

variable "instance_type" {
  description = "EC2 instance type for all sensor nodes."
  type        = string
  default     = "t3.medium"
}

variable "volume_size_gb" {
  description = "Root EBS volume size in GB."
  type        = number
  default     = 30
}

variable "repo_url" {
  description = "Git repository URL to clone on each node during bootstrap."
  type        = string
  default     = "https://github.com/OWASP/Honeypot-Project.git"
}
