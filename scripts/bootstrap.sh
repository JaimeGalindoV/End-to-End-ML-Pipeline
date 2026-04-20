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
export S3_BUCKET_NAME="3-12-bucket-chido"

# ejecutar el script de entrenamiento
python3 src/train.py

# ejecutar la app
python3 src/app.py