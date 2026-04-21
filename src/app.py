import os
import boto3
import joblib
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
load_dotenv()  



MODEL_DIR = os.getenv("MODEL_LOCAL_DIR", "./")
MODEL_NAME = os.getenv("MODEL_FILENAME", "model.joblib")
MODEL_PATH = os.path.join(MODEL_DIR, MODEL_NAME)


app = FastAPI(
    title="California Housing ML API",
    description="API de Inferencia para la predicción de precios de casas",
    version="1.0" 
)


def download_model_from_s3():
    bucket = os.getenv("S3_BUCKET_NAME")
    s3_key = os.getenv("S3_MODEL_KEY", "models/model.joblib")
    
    
    if not bucket:
        return 

    s3 = boto3.client("s3")
    print(f"Descargando modelo desde s3://{bucket}/{s3_key}...")
    s3.download_file(bucket, s3_key, MODEL_PATH)
    print("Modelo descargado exitosamente.")


model = None

@app.on_event("startup")
def load_model():
    global model
    try:
        download_model_from_s3()
        model = joblib.load(MODEL_PATH)
        print(f"Modelo cargado exitosamente desde: {MODEL_PATH}")
    except Exception as e:
        print(f"Advertencia: No se pudo cargar el modelo en {MODEL_PATH}. Error: {e}")


class PredictionRequest(BaseModel):
    features: list[float]

@app.get("/health")
def health_check():
    
    if model is None:
        raise HTTPException(status_code=503, detail="Servidor activo, pero modelo no cargado.")
    return {"status": "healthy", "model_path": MODEL_PATH}

@app.post("/predict")
def predict(request: PredictionRequest):
    
    if model is None:
        raise HTTPException(status_code=503, detail="Modelo no disponible para inferencia.")
    
    if len(request.features) != 8:
        raise HTTPException(
            status_code=400, 
            detail=f"Se esperan 8 características, se recibieron {len(request.features)}."
        )
    
    try:
        input_data = np.array(request.features).reshape(1, -1)
        
        prediction = model.predict(input_data)
        
        return {"prediction": float(prediction[0])}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno al predecir: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    API_PORT=int(os.getenv("API_PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=API_PORT)
