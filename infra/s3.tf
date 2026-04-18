resource "aws_s3_bucket" "data_bucket" {
    bucket = "3-12-bucket-chido"
    tags = {
        Name = "MLOps 3.12 Pipeline Data Bucket"
    }
}