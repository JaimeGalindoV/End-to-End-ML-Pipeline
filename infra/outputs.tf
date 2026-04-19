output "ec2_public_ip" {
  description = "The public IP address of the EC2 instance"
  value       = aws_instance.mlops_3_12_instance.public_ip
}
