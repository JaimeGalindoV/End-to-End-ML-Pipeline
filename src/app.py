import os
import joblib
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

MODEL_DIR = os.getenv("MODEL_LOCAL_DIR", "./")
MODEL_NAME = os.getenv("MODEL_FILENAME", "model.joblib")
MODEL_PATH = os.path.join(MODEL_DIR, MODEL_NAME)


app = FastAPI(
    title="California Housing ML API",
    description="API de Inferencia para la predicción de precios de casas",
    version="1.0"
)


model = None

@app.on_event("startup")
def load_model():
    global model
    try:
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