import requests
import os
import pytest
from dotenv import load_dotenv

load_dotenv()
BASE_URL = os.getenv("API_IP")

def test_endpoint_prediction():
    """Prueba el endpoint enviando los datos en el formato 'features' que pide la API."""
    
    # Formato corregido según el error 422:
    # La API espera una llave "features" con una lista de valores
    sample_payload = {
        "features": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0] 
    }
    
    try:
        response = requests.post(f"{BASE_URL}/predict", json=sample_payload)
        
        if response.status_code != 200:
            print(f"\nRespuesta del servidor: {response.text}")
            
        assert response.status_code == 200
        assert "prediction" in response.json()
        
    except requests.exceptions.ConnectionError:
        pytest.fail(f"No se pudo conectar a la IP {BASE_URL}")