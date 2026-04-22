import numpy as np
import os
from unittest.mock import patch, MagicMock
from src.train import load_data, train_model, serialize_model, upload_model_to_s3
from sklearn.linear_model import LinearRegression

def test_serialize_model(tmp_path):
    model = LinearRegression()
    output_path = tmp_path / "model.joblib"
    path = serialize_model(model, output_path=output_path)
    assert path.exists()
    assert path.name == "model.joblib"

def test_load_data_csv(tmp_path):
    csv_file = tmp_path / "test.csv"
    with open(csv_file, "w") as f:
        f.write("MedHouseVal,feature1,feature2\n")
        f.write("1.0,0.5,0.2\n")
        f.write("2.0,0.8,0.4\n")
    features, target = load_data(str(csv_file))
    assert features.shape == (2, 2)
    assert target.shape == (2,)
    assert target[0] == 1.0

def test_train_model():
    X = np.array([[i, i+1] for i in range(10)])
    y = np.array([i*2 for i in range(10)])
    model, metrics = train_model(X, y, test_size=0.2, random_state=42)
    assert "rmse" in metrics
    assert "mae" in metrics
    assert "r2" in metrics
    assert model is not None

@patch("boto3.client")
def test_upload_model_to_s3(mock_boto):
    mock_s3 = MagicMock()
    mock_boto.return_value = mock_s3
    # Usamos SKIP_S3_UPLOAD=false para que entre a la función
    with patch.dict(os.environ, {"SKIP_S3_UPLOAD": "false"}):
        upload_model_to_s3(
            model_path="dummy_path.joblib",
            bucket="my-bucket",
            key="models/model.joblib",
            region_name="us-east-1"
        )
    assert mock_s3.upload_file.called