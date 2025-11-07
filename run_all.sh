#!/bin/bash
# Script para ejecutar TODO (Django + Celery Worker + Celery Beat + Flower)
# Uso: ./run_all.sh

set -e

echo "======================================================================"
echo "CliniDocs - Startup Script"
echo "======================================================================"
echo ""

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# Verificar si venv existe
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creando entorno virtual...${NC}"
    python -m venv venv
fi

# Activar venv
echo -e "${YELLOW}Activando entorno virtual...${NC}"
source venv/bin/activate

# Instalar dependencias
echo -e "${YELLOW}Verificando dependencias...${NC}"
pip install -q -r requirements.txt

# Verificar Redis
echo -e "${YELLOW}Verificando Redis...${NC}"
if ! command -v redis-server &> /dev/null; then
    echo -e "${RED}✗ Redis no está instalado${NC}"
    echo -e "${CYAN}Instala Redis desde: https://redis.io/download${NC}"
    exit 1
fi

# Iniciar Redis en background
echo -e "${YELLOW}Iniciando Redis (si no está corriendo)...${NC}"
redis-server --daemonize yes --logfile redis.log

# Migrar BD
echo -e "${YELLOW}Aplicando migraciones...${NC}"
python manage.py migrate

# Crear superusuario si no existe
python manage.py shell << END
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@clinidocs.local', 'admin123')
    print("✓ Superusuario creado: admin / admin123")
else:
    print("✓ Superusuario ya existe")
END

echo ""
echo -e "${GREEN}======================================================================"
echo "✓ Configuración completada"
echo "======================================================================"
echo ""
echo -e "${CYAN}Inicia estos servicios en terminales separadas:${NC}"
echo ""
echo -e "${GREEN}Terminal 1 - Django Dev Server:${NC}"
echo "  python manage.py runserver"
echo ""
echo -e "${GREEN}Terminal 2 - Celery Worker:${NC}"
echo "  celery -A config worker --loglevel=info"
echo ""
echo -e "${GREEN}Terminal 3 - Celery Beat (Scheduler):${NC}"
echo "  celery -A config beat --loglevel=info"
echo ""
echo -e "${GREEN}Terminal 4 - Celery Flower (Monitor UI):${NC}"
echo "  celery -A config flower --port=5555"
echo ""
echo -e "${CYAN}URLs de acceso:${NC}"
echo "  - API: http://localhost:8000/api/"
echo "  - Swagger: http://localhost:8000/api/docs/"
echo "  - Admin: http://localhost:8000/admin/ (user: admin, pass: admin123)"
echo "  - Flower: http://localhost:5555"
echo ""
