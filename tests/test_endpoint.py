import requests
import os
import pytest
from dotenv import load_dotenv

load_dotenv()

# Si no encuentra la variable, usa la IP que ya sabemos que funciona
API_HOST = os.getenv("API_HOST", "54.175.134.143")
API_PORT = os.getenv("API_PORT", "8000")
BASE_URL = f"http://{API_HOST}:{API_PORT}"

def test_endpoint_prediction():
    """Prueba el endpoint con la estructura solicitada en el PR."""
    # El payload debe coincidir con lo que la API espera
    sample_payload = {
        "features": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]
    }
    
    try:
        response = requests.post(f"{BASE_URL}/predict", json=sample_payload)
        assert response.status_code == 200
        assert "prediction" in response.json()
    except Exception as e:
        pytest.fail(f"Error de conexión a {BASE_URL}: {e}")