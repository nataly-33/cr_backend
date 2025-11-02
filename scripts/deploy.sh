#!/bin/bash
echo "🚀 Iniciando deploy de CliniDocs..."

# Actualizar código
cd /home/ubuntu/clinidocs/cr_backend
git pull origin main

# Activar virtualenv
source /home/ubuntu/clinidocs/venv/bin/activate

# Instalar dependencias
pip install -r requirements/production.txt

# Migraciones
python manage.py migrate --noinput

# Collectstatic
python manage.py collectstatic --noinput

# Reiniciar Gunicorn
sudo systemctl restart gunicorn
sudo systemctl restart nginx

echo "✅ Deploy completado!"