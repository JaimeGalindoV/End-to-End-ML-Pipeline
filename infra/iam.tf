resource "aws_iam_role" "ec2_role" {
    name = "ec2-s3-access-role"

    assume_role_policy = jsonencode({
        Version = "2012-10-17"
        Statement = [{
            Action = "sts:AssumeRole"
            Effect = "Allow"
            Principal = {
                Service = "ec2.amazonaws.com"
            }
        }]
    })
}

resource "aws_iam_policy" "ec2_s3_policy" {
    name = "ec2-s3-access-policy"
    description = "Permite a EC2 leer y escribir en S3"

    policy = jsonencode({
        Version = "2012-10-17"
        Statement = [{
            Effect = "Allow"
            Action = [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject",
                "s3:ListBucket"
            ]
            Resource = [
                "arn:aws:s3:::3-12-bucket-chido",
                "arn:aws:s3:::3-12-bucket-chido/*"
            ]
        }]
    })
}

resource "aws_iam_role_policy_attachment" "attach_ec2_s3" {
    role = aws_iam_role.ec2_role.name
    policy_arn = aws_iam_policy.ec2_s3_policy.arn
}

resource "aws_iam_instance_profile" "ec2_instance_profile" {
    name = "ec2-instance-profile"
    role = aws_iam_role.ec2_role.name
}