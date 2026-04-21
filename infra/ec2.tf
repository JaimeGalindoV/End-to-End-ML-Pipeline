resource "aws_instance" "mlops_3_12_instance" {
    ami = "ami-0ec10929233384c7f"
    instance_type = "t2.micro"
    vpc_security_group_ids = [aws_security_group.mlops_sg.id]
    iam_instance_profile = aws_iam_instance_profile.ec2_instance_profile.name

    user_data = file("${path.module}/../scripts/bootstrap.sh")

    tags = {
        Name = "MLOps 3.12 EC2 Instance"
    }
}

resource "aws_security_group" "mlops_sg" {
    name = "mlops_sg"
    description = "allow SSH and HTTP access"

    ingress {
        from_port = 22
        to_port = 22
        protocol = "tcp"
        cidr_blocks = ["0.0.0.0/0"]
    }

    ingress {
        from_port = 8000
        to_port = 8000
        protocol = "tcp"
        cidr_blocks = ["0.0.0.0/0"]
    }

    egress {
        from_port = 0
        to_port = 0
        protocol = "-1"
        cidr_blocks = ["0.0.0.0/0"]
    }
}