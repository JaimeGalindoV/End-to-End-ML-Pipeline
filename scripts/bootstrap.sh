#!/bin/bash
set -e

exec > /var/log/bootstrap.log 2>&1

# actualizar el sistema
sudo apt-get update -y
sudo apt-get install -y git python3 python3-pip python3-venv

# clonar el repo
cd /home/
git clone "https://github.com/JaimeGalindoV/End-to-End-ML-Pipeline.git"
cd /home/End-to-End-ML-Pipeline

# Crear un entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias en  del venv
pip install -r requirements.txt

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
venv/bin/python src/train.py

sudo chown -R ubuntu:ubuntu /home/End-to-End-ML-Pipeline

sudo apt-get install -y nginx

# Crear configuración de Nginx (Reverse Proxy)
echo 'server {
    listen 80;
    server_name _; 
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}' | sudo tee /etc/nginx/sites-available/default

# Reiniciar Nginx
sudo systemctl restart nginx

# Crear y activar el servicio de Systemd
cat << 'EOF' | sudo tee /etc/systemd/system/mlops.service
[Unit]
Description=MLOps FastAPI Service
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/End-to-End-ML-Pipeline
EnvironmentFile=/etc/environment
ExecStart=/home/End-to-End-ML-Pipeline/venv/bin/python /home/End-to-End-ML-Pipeline/src/app.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable mlops
sudo systemctl start mlops

echo "Bootstrap script completed successfully."