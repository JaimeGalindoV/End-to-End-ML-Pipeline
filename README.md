```bash
End-to-End-ML-Pipeline/
├── infra/
│   ├── main.tf            # AWS provider, backend config
│   ├── s3.tf              # Bucket for data and model artifacts
│   ├── ec2.tf             # Instance definition + user_data bootstrap
│   ├── iam.tf             # Role and instance profile for S3 access
│   ├── variables.tf       # Region, instance type, key pair, etc.
│   └── outputs.tf         # Public IP of the deployed instance
├── src/
│   ├── train.py           # Training script (sklearn + joblib)
│   └── app.py             # FastAPI inference server
├── tests/
│   ├── test_train.py      # Unit tests for training logic
│   └── test_endpoint.py   # Smoke test against deployed endpoint
├── scripts/
│   └── bootstrap.sh       # EC2 user_data script
├── requirements.txt
└── .github/workflows/
    └── deploy.yml         # CI/CD pipeline definition

```
