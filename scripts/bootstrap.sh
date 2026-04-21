#!/bin/bash
set -e

exec > /var/log/bootstrap.log 2>&1

# actualizar el sistema
sudo apt-get update -y

# instalar python y pip
sudo apt-get install -y git python3 python3-pip

# clonar el repo
git clone "https://github.com/JaimeGalindoV/End-to-End-ML-Pipeline.git" /home

cd /home/End-to-End-ML-Pipeline

# instalar dependencias de requirements.txt
pip3 install -r requirements.txt

# exponer variables de entorno
TOKEN=$(curl -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")

INSTANCE_IP=$(curl -H "X-aws-ec2-metadata-token: $TOKEN" -s http://169.254.169.254/latest/meta-data/public-ipv4)

{
    echo 'S3_BUCKET_NAME="3-12-bucket-chido"'
    echo 'MODEL_FILENAME="model.joblib"'
    echo 'MODEL_LOCAL_DIR="/home/End-to-End-ML-Pipeline/models/"'
    echo "API_HOST=\"$INSTANCE_IP\""
    echo 'API_PORT="8000"'
    echo 'S3_MODEL_KEY="models/model.joblib"'
} | sudo tee -a /etc/environment

set -a
source /etc/environment
set +a


# ejecutar el script de entrenamiento
python3 src/train.py

# ejecutar la app
# nohup se usa para ejecutar el proceso en segundo plano, redirigiendo la salida
# a un archivo de log para poder revisar cualquier error o salida del proceso
nohup python3 src/app.py > /home/End-to-End-ML-Pipeline/app.log 2>&1 &
