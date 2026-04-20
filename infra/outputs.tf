output "ec2_instance_public_ip" {
    description = "IP Pública de la instancia de EC2"
    value = aws_instance.mlops_3_12_instance.public_ip
}

output "s3_bucket_name" {
    description = "Nombre del bucket de S3"
    value = aws_s3_bucket.data_bucket.bucket
}

output "s3_bucket_url" {
    description = "URL del bucket de S3"
    value = "s3://${aws_s3_bucket.data_bucket.bucket}/"