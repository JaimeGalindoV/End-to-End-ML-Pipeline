"""Training script for the California Housing regression model.

This module keeps the training workflow self-contained so it can run both
locally and inside the EC2 bootstrap step. It loads the dataset, trains a
LinearRegression model, and serializes the fitted artifact to disk.
"""

from __future__ import annotations

import argparse
import csv
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


def load_dotenv_file(dotenv_path: str | Path = ".env") -> None:
    """Load simple KEY=VALUE pairs from a local `.env` file if it exists.

    Existing environment variables win, so GitHub Actions or EC2 variables
    can override local development settings.
    """

    path = Path(dotenv_path)
    if not path.is_absolute():
        path = Path.cwd() / path

    if not path.exists():
        return

    with path.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key:
                os.environ.setdefault(key, value)


load_dotenv_file()

DEFAULT_MODEL_PATH = Path(os.getenv("models/model.joblib"))
DEFAULT_TEST_SIZE = float(os.getenv("0.2"))
DEFAULT_RANDOM_STATE = int(os.getenv("42"))
DEFAULT_S3_BUCKET = os.getenv("S3_BUCKET")
DEFAULT_S3_MODEL_KEY = os.getenv("models/model.joblib")
DEFAULT_AWS_REGION = os.getenv("AWS_REGION")


def load_data(data_path: str | Path | None = None) -> tuple[np.ndarray, np.ndarray]:
    """Load training data.

    If `data_path` is provided, the file must be a CSV with a target column
    named `MedHouseVal`, `target`, or `median_house_value`. Otherwise, the
    built-in California Housing dataset from scikit-learn is used.
    """

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
        raise ValueError(
            "CSV data must include a target column named one of: "
            "MedHouseVal, target, median_house_value"
        )

    feature_columns = [name for name in fieldnames if name != target_column]
    if not feature_columns:
        raise ValueError("CSV data must include at least one feature column")

    features = np.asarray(
        [[float(row[column]) for column in feature_columns] for row in rows],
        dtype=float,
    )
    target = np.asarray([float(row[target_column]) for row in rows], dtype=float)
    return features, target


def train_model(
    features: np.ndarray,
    target: np.ndarray,
    *,
    test_size: float = DEFAULT_TEST_SIZE,
    random_state: int = DEFAULT_RANDOM_STATE,
) -> tuple[LinearRegression, dict[str, float]]:
    """Train a linear regression model and compute holdout metrics."""

    X_train, X_test, y_train, y_test = train_test_split(
        features,
        target,
        test_size=test_size,
        random_state=random_state,
    )

    model = LinearRegression()
    model.fit(X_train, y_train)

    predictions = model.predict(X_test)
    metrics = {
        "rmse": float(mean_squared_error(y_test, predictions, squared=False)),
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


def upload_model_to_s3(
    model_path: str | Path,
    bucket: str | None = DEFAULT_S3_BUCKET,
    key: str = DEFAULT_S3_MODEL_KEY,
    region_name: str | None = DEFAULT_AWS_REGION,
) -> None:
    """Upload the serialized model artifact to S3.

    The bucket name is required. The object key defaults to
    `models/model.joblib` so Person 2 can rely on a stable contract.
    """

    if not bucket:
        raise ValueError("S3_BUCKET environment variable is required for S3 upload")

    s3_client = boto3.client("s3", region_name=region_name)
    s3_client.upload_file(Filename=str(model_path), Bucket=bucket, Key=key)


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Train a California Housing model")
    parser.add_argument(
        "--data-path",
        type=str,
        default=None,
        help="Optional CSV file path. If omitted, the sklearn dataset is used.",
    )
    parser.add_argument(
        "--model-path",
        type=str,
        default=str(DEFAULT_MODEL_PATH),
        help="Where to save the trained joblib artifact.",
    )
    parser.add_argument(
        "--test-size",
        type=float,
        default=DEFAULT_TEST_SIZE,
        help="Fraction of the dataset to reserve for evaluation.",
    )
    parser.add_argument(
        "--random-state",
        type=int,
        default=DEFAULT_RANDOM_STATE,
        help="Random seed used for the train/test split.",
    )
    parser.add_argument(
        "--s3-bucket",
        type=str,
        default=DEFAULT_S3_BUCKET,
        help="S3 bucket where the serialized model will be uploaded. "
        "Set this from S3_BUCKET in your .env or environment.",
    )
    parser.add_argument(
        "--s3-model-key",
        type=str,
        default=DEFAULT_S3_MODEL_KEY,
        help="S3 object key for the serialized model artifact. "
        "Set this from S3_MODEL_KEY in your .env or environment.",
    )
    parser.add_argument(
        "--aws-region",
        type=str,
        default=DEFAULT_AWS_REGION,
        help="AWS region used by boto3. Set this from AWS_REGION in your .env.",
    )
    return parser


def main() -> int:
    parser = build_argument_parser()
    args = parser.parse_args()

    features, target = load_data(args.data_path)
    model, metrics = train_model(
        features,
        target,
        test_size=args.test_size,
        random_state=args.random_state,
    )
    model_path = serialize_model(model, args.model_path)
    upload_model_to_s3(
        model_path=model_path,
        bucket=args.s3_bucket,
        key=args.s3_model_key,
        region_name=args.aws_region,
    )

    print(f"Saved model to {model_path}")
    print(f"Uploaded model to s3://{args.s3_bucket}/{args.s3_model_key}")
    print(
        "Evaluation metrics: "
        f"rmse={metrics['rmse']:.4f}, mae={metrics['mae']:.4f}, r2={metrics['r2']:.4f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
