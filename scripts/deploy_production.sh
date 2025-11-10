#!/bin/bash
# Script de deployment para producción AWS

set -e  # Exit on error

echo "🚀 Iniciando deployment en producción..."

# Variables
PROJECT_DIR="/opt/clinidocs/cr_backend"
VENV_DIR="$PROJECT_DIR/.venv"
DJANGO_SETTINGS_MODULE="config.settings.production_aws"

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

cd $PROJECT_DIR

echo "📦 Activando virtualenv..."
source $VENV_DIR/bin/activate

echo "🔄 Pulling latest code..."
git pull origin main

echo "📥 Instalando dependencias..."
pip install -r requirements.txt --quiet

echo "🗄️  Ejecutando migraciones..."
export DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE
python manage.py migrate --noinput

echo "📁 Recolectando archivos estáticos..."
python manage.py collectstatic --noinput

echo "🔄 Reiniciando Gunicorn..."
sudo systemctl restart gunicorn

echo "⏳ Esperando a que Gunicorn inicie..."
sleep 3

echo "🔄 Reiniciando Celery..."
sudo systemctl restart celery-worker
sudo systemctl restart celery-beat

echo "🔄 Reiniciando Nginx..."
sudo systemctl restart nginx

echo "✅ Health check..."
HEALTH_CHECK=$(curl -s -o /dev/null -w "%{http_code}" https://api.clinidocs.com/api/health/)

if [ "$HEALTH_CHECK" == "200" ]; then
    echo -e "${GREEN}✅ Deployment exitoso! Backend respondiendo correctamente.${NC}"
else
    echo -e "${RED}❌ Error: Backend no responde (HTTP $HEALTH_CHECK)${NC}"
    exit 1
fi

echo "📊 Estado de servicios:"
sudo systemctl status gunicorn --no-pager | grep Active
sudo systemctl status celery-worker --no-pager | grep Active
sudo systemctl status nginx --no-pager | grep Active

echo -e "${GREEN}🎉 Deployment completado!${NC}"
