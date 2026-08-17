output "elastic_ip" {
  description = "Public Elastic IP of this sensor. This is the stable address registered with Shodan."
  value       = aws_eip.sensor.public_ip
}

output "instance_id" {
  description = "EC2 instance ID."
  value       = aws_instance.sensor.id
}

output "public_dns" {
  description = "Public DNS name assigned by AWS to this instance."
  value       = aws_instance.sensor.public_dns
}
