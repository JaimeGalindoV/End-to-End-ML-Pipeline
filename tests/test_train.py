import os
import pytest
import subprocess

def test_train_script_results():
    """
    Valida que el entrenamiento genere el archivo localmente.
    Pasamos una variable de entorno para evitar la subida a S3.
    """
    # Creamos una copia de las variables de entorno actuales y añadimos una marca de TEST
    env = os.environ.copy()
    env["SKIP_S3_UPLOAD"] = "true"
    
    # Ejecutamos el script de entrenamiento
    result = subprocess.run(
        ["python3", "src/train.py"], 
        capture_output=True, 
        text=True,
        env=env
    )
    
    # Verificamos que el script terminó con éxito
    assert result.returncode == 0, f"Error en train.py: {result.stderr}"
    
    # Verificamos que el modelo exista
    assert os.path.exists("model.joblib"), "El entrenamiento terminó pero no se encontró model.joblib"

    print("\n¡Test de entrenamiento exitoso! Modelo generado localmente.")