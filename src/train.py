import os
import sys
import pandas as pd
import joblib
from sklearn.datasets import fetch_california_housing
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
import boto3
from botocore.exceptions import NoCredentialsError

def upload_model_to_s3(model_path, bucket, key):
    """Sube el modelo a S3, a menos que se indique saltar este paso."""
    if os.getenv("SKIP_S3_UPLOAD") == "true":
        print("MODO QA: Saltando subida a S3.")
        return True
    
    try:
        s3_client = boto3.client('s3')
        s3_client.upload_file(Filename=str(model_path), Bucket=bucket, Key=key)
        print(f"Modelo subido exitosamente a s3://{bucket}/{key}")
        return True
    except NoCredentialsError:
        print("Error: No se encontraron credenciales de AWS.")
        return False
    except Exception as e:
        print(f"Error al subir a S3: {e}")
        return False

def main():
    # 1. Cargar datos
    print("Cargando datos de California Housing...")
    data = fetch_california_housing()
    X = pd.DataFrame(data.data, columns=data.feature_names)
    y = data.target

    # 2. Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # 3. Entrenar
    print("Entrenando modelo...")
    model = RandomForestRegressor(n_estimators=10, random_state=42)
    model.fit(X_train, y_train)

    # 4. Guardar localmente
    model_filename = "model.joblib"
    joblib.dump(model, model_filename)
    print(f"Saved model to {model_filename}")

    # 5. Intentar subir a S3 (Las variables vienen del .env que cargue el entorno)
    bucket = os.getenv("S3_BUCKET_NAME", "3-12-bucket-chido")
    key = os.getenv("S3_MODEL_KEY", "models/model.joblib")
    
    success = upload_model_to_s3(model_filename, bucket, key)
    
    # Si estamos en QA y el archivo existe, salimos con éxito aunque no haya S3
    if os.getenv("SKIP_S3_UPLOAD") == "true" and os.path.exists(model_filename):
        return 0
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())