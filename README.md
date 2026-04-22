# End-to-End ML Pipeline

End-to-end MLOps project that trains a regression model (California Housing), stores the model artifact in S3, deploys an EC2-hosted FastAPI inference service, and validates the deployment with automated tests in GitHub Actions.

## Project structure

```text
End-to-End-ML-Pipeline/
├── infra/                    # Terraform IaC for AWS resources
│   ├── main.tf               # AWS provider + Terraform backend (S3 state)
│   ├── s3.tf                 # S3 bucket for model artifacts
│   ├── iam.tf                # IAM role/policy + instance profile for EC2
│   ├── ec2.tf                # EC2 instance + security group + user_data
│   ├── variables.tf          # Terraform input variables
│   └── outputs.tf            # Public IP and S3 outputs
├── src/
│   ├── train.py              # Train + evaluate + serialize + (optional) S3 upload
│   └── app.py                # FastAPI app that loads model and serves predictions
├── scripts/
│   └── bootstrap.sh          # EC2 startup script (clone, train, run API)
├── tests/
│   ├── test_train.py         # Unit tests for training pipeline
│   └── test_endpoint.py      # Smoke test for deployed API endpoint
├── .github/workflows/
│   └── deploy.yml            # CI/CD: lint, unit tests, terraform deploy, smoke test
└── requirements.txt          # Python dependencies
```

## Architecture summary

1. `src/train.py` trains a `LinearRegression` model using `sklearn.datasets.fetch_california_housing`.
2. The trained artifact is saved as `model.joblib` and uploaded to S3.
3. Terraform provisions S3, IAM, Security Group, and EC2.
4. EC2 `user_data` (`scripts/bootstrap.sh`) clones this repo, trains the model, and starts the FastAPI server.
5. `src/app.py` loads the model (from local path and/or S3) and serves `/health` and `/predict`.
6. GitHub Actions (`deploy.yml`) runs CI + deployment + post-deploy smoke validation.

## Prerequisites

- Python 3.12+ (project is tested in CI with 3.12)
- Terraform 1.x
- AWS account and credentials with permissions for S3, EC2, IAM
- A pre-existing S3 bucket for Terraform backend state (`infra/main.tf` currently uses `backend-bucket-chido`)
- GitHub repository secrets:
  - `AWS_ACCESS_KEY_ID`
  - `AWS_SECRET_ACCESS_KEY`

## Python setup (local)

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Environment variables

Used by training and API components:

- `S3_BUCKET_NAME` (required to upload/download model from S3)
- `S3_MODEL_KEY` (default: `models/model.joblib`)
- `MODEL_LOCAL_DIR` (default: `./`)
- `MODEL_FILENAME` (default: `model.joblib`)
- `AWS_REGION` (default: `us-east-1`)
- `API_HOST` (used by smoke test)
- `API_PORT` (default: `8000`)
- `SKIP_S3_UPLOAD` (`true` skips S3 upload in training)

You can place them in a `.env` file for local execution.

## Train the model

### Basic

```powershell
.\venv\Scripts\python src\train.py
```

### Useful options

```powershell
.\venv\Scripts\python src\train.py --help
```

Examples:

```powershell
# Train without uploading to S3
.\venv\Scripts\python src\train.py --skip-upload

# Train from CSV (must include target column: MedHouseVal, target, or median_house_value)
.\venv\Scripts\python src\train.py --data-path .\data\train.csv
```

## Run the API locally

```powershell
.\venv\Scripts\python src\app.py
```

API endpoints:

- `GET /health` -> health status and model path
- `POST /predict` -> expects:

```json
{
  "features": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]
}
```

The model expects exactly **8 features**.

## Tests

Unit tests:

```powershell
.\venv\Scripts\python -m pytest tests\test_train.py -v
```

Smoke test (against a running/deployed API):

```powershell
$env:API_HOST = "<ec2-public-ip>"
.\venv\Scripts\python -m pytest tests\test_endpoint.py -v
```

## Infrastructure deployment (Terraform)

From repository root:

```powershell
cd infra
terraform init
terraform apply -auto-approve
terraform output
```

Main resources provisioned:

- S3 bucket for model artifacts
- IAM role/policy + EC2 instance profile for S3 access
- EC2 instance (Ubuntu AMI) with bootstrap startup script
- Security Group allowing:
  - SSH `22/tcp`
  - API `8000/tcp`

## CI/CD workflow (`.github/workflows/deploy.yml`)

The workflow runs on pushes to `main` and `dev`:

1. **CI job**
   - Install dependencies
   - Lint (`flake8`)
   - Run unit tests (`tests/test_train.py`)
2. **Deploy job**
   - Configure AWS credentials from GitHub Secrets
   - Run Terraform apply
   - Export EC2 public IP as workflow output
3. **Validate job**
   - Wait for API readiness on `/health`
   - Run endpoint smoke test (`tests/test_endpoint.py`)

## Notes

- `scripts/bootstrap.sh` sets instance environment variables in `/etc/environment`, runs training, and starts API with `nohup`.
- Terraform backend and bucket names are hardcoded in current IaC files; adjust them to your environment if needed.
