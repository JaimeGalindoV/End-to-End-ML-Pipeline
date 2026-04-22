"""Training script for the California Housing regression model.

This module keeps the training workflow self-contained so it can run both
locally and inside the EC2 bootstrap step. It loads the dataset, trains a
LinearRegression model, and serializes the fitted artifact to disk.
"""

from __future__ import annotations

import argparse
import csv
import math
import os
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import boto3
from sklearn.datasets import fetch_california_housing
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from dotenv import load_dotenv

load_dotenv()

# --- Valores por defecto (Constantes) ---
DEFAULT_TEST_SIZE = 0.2
DEFAULT_RANDOM_STATE = 42

# --- Variables de entorno (Configurables) ---
MODEL_DIR = os.getenv("MODEL_LOCAL_DIR", "./")
MODEL_NAME = os.getenv("MODEL_FILENAME", "model.joblib")
DEFAULT_MODEL_PATH = os.path.join(MODEL_DIR, MODEL_NAME)
DEFAULT_S3_MODEL_KEY = os.getenv("S3_MODEL_KEY", "models/model.joblib")
DEFAULT_S3_BUCKET = os.getenv("S3_BUCKET_NAME")
DEFAULT_AWS_REGION = os.getenv("AWS_REGION", "us-east-1")


def load_data(data_path: str | Path | None = None) -> tuple[np.ndarray, np.ndarray]:
    """Load training data."""
    if data_path is None:
        dataset = fetch_california_housing(as_frame=False)
        return dataset.data, dataset.target

    path = Path(data_path)
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {path}")

    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)

    if not rows:
        raise ValueError(f"Data file is empty: {path}")

    fieldnames = reader.fieldnames or []
    target_candidates = ("MedHouseVal", "target", "median_house_value")
    target_column = next((name for name in target_candidates if name in fieldnames), None)
    if target_column is None:
        raise ValueError("CSV data must include a target column")

    feature_columns = [name for name in fieldnames if name != target_column]
    features = np.asarray([[float(row[column]) for column in feature_columns] for row in rows], dtype=float)
    target = np.asarray([float(row[target_column]) for row in rows], dtype=float)
    return features, target


def train_model(features, target, *, test_size=DEFAULT_TEST_SIZE, random_state=DEFAULT_RANDOM_STATE):
    """Train a linear regression model and compute holdout metrics."""
    X_train, X_test, y_train, y_test = train_test_split(features, target, test_size=test_size, random_state=random_state)
    model = LinearRegression()
    model.fit(X_train, y_train)
    predictions = model.predict(X_test)
    metrics = {
        "rmse": float(math.sqrt(mean_squared_error(y_test, predictions))),
        "mae": float(mean_absolute_error(y_test, predictions)),
        "r2": float(r2_score(y_test, predictions)),
    }
    return model, metrics


def serialize_model(model: Any, output_path: str | Path = DEFAULT_MODEL_PATH) -> Path:
    """Persist the trained model to disk using joblib."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, path)
    return path


def upload_model_to_s3(model_path, bucket, key, region_name):
    """Upload the model to S3. INCLUDES QA BYPASS."""
    # --- CAMBIO PARA QA: Si detecta la variable del test, no intenta conectar a AWS ---
    if os.getenv("SKIP_S3_UPLOAD") == "true":
        print("MODO QA: Saltando conexión real a AWS S3.")
        return

    if not bucket:
        raise ValueError("S3_BUCKET environment variable is required for S3 upload")

    s3_client = boto3.client("s3", region_name=region_name)
    s3_client.upload_file(Filename=str(model_path), Bucket=bucket, Key=key)


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Train a California Housing model")
    parser.add_argument("--data-path", type=str, default=None)
    parser.add_argument("--model-path", type=str, default=str(DEFAULT_MODEL_PATH))
    parser.add_argument("--test-size", type=float, default=DEFAULT_TEST_SIZE)
    parser.add_argument("--random-state", type=int, default=DEFAULT_RANDOM_STATE)
    parser.add_argument("--s3-bucket", type=str, default=DEFAULT_S3_BUCKET)
    parser.add_argument("--s3-model-key", type=str, default=DEFAULT_S3_MODEL_KEY)
    parser.add_argument("--aws-region", type=str, default=DEFAULT_AWS_REGION)
    parser.add_argument("--skip-upload", action="store_true")
    return parser


def main() -> int:
    parser = build_argument_parser()
    args = parser.parse_args()

    features, target = load_data(args.data_path)
    model, metrics = train_model(features, target, test_size=args.test_size, random_state=args.random_state)
    model_path = serialize_model(model, args.model_path)

    print(f"Saved model to {model_path}")

    # --- Lógica de subida respetando el modo QA ---
    if args.skip_upload or os.getenv("SKIP_S3_UPLOAD") == "true":
        print("Skipped S3 upload (Manual or QA Mode)")
    else:
        upload_model_to_s3(model_path, args.s3_bucket, args.s3_model_key, args.aws_region)
        print(f"Uploaded model to s3://{args.s3_bucket}/{args.s3_model_key}")

    print(f"Evaluation metrics: rmse={metrics['rmse']:.4f}, mae={metrics['mae']:.4f}, r2={metrics['r2']:.4f}")
    return 0


if __name__ == "__main__":
    try:
        sys_exit_code = main()
        os._exit(sys_exit_code)
    except SystemExit as e:
        os._exit(e.code)
    except Exception:
        os._exit(1)