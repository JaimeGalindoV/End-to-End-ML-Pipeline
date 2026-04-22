# configuración de AWS
terraform {
    required_providers {
        aws = {
            source = "hashicorp/aws"
            version = "~> 5.0"
        }
    }

    backend "s3" {
        bucket = "backend-bucket-chido"
        key = "mlops-pipeline/terraform.tfstate"
        region = "us-east-1"
        # profile = "colaborador-mlops"
    }
}

provider "aws" {
    region = var.aws_region
    # profile = var.aws_profile
}