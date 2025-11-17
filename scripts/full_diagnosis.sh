#!/bin/bash
# ============================================================================
# DIAGNÓSTICO COMPLETO DEL SERVIDOR EC2
# ============================================================================

echo "============================================================================"
echo "DIAGNÓSTICO COMPLETO DEL SISTEMA - $(date)"
echo "============================================================================"
echo ""

# ============================================================================
# 1. INFORMACIÓN DEL SISTEMA
# ============================================================================
echo "1. INFORMACIÓN DEL SISTEMA"
echo "----------------------------------------------------------------------------"
echo "Hostname: $(hostname)"
echo "IP Privada: $(hostname -I | awk '{print $1}')"
echo "Sistema: $(lsb_release -d | cut -f2)"
echo "Uptime: $(uptime -p)"
echo "Memoria libre: $(free -h | grep Mem | awk '{print $4}')"
echo "Disco usado: $(df -h / | tail -1 | awk '{print $5}')"
echo ""

# ============================================================================
# 2. SERVICIOS CRÍTICOS
# ============================================================================
echo "2. ESTADO DE SERVICIOS CRÍTICOS"
echo "----------------------------------------------------------------------------"

services=("redis-server" "gunicorn" "celery" "celerybeat" "nginx")
for service in "${services[@]}"; do
    if systemctl is-active --quiet $service; then
        echo "[OK] $service está ACTIVO"
    else
        echo "[FAIL] $service está INACTIVO o NO EXISTE"
    fi
done
echo ""

# ============================================================================
# 3. PUERTOS Y PROCESOS
# ============================================================================
echo "3. PUERTOS EN USO"
echo "----------------------------------------------------------------------------"
echo "Puerto 8000 (Django/Gunicorn):"
sudo netstat -tlnp | grep :8000 || echo "  [FAIL] Nadie escuchando en 8000"
echo ""
echo "Puerto 80 (Nginx):"
sudo netstat -tlnp | grep :80 || echo "  [FAIL] Nadie escuchando en 80"
echo ""
echo "Puerto 6379 (Redis):"
sudo netstat -tlnp | grep :6379 || echo "  [FAIL] Nadie escuchando en 6379"
echo ""

# ============================================================================
# 4. ARCHIVOS Y DIRECTORIOS CLAVE
# ============================================================================
echo "4. VERIFICACIÓN DE ARCHIVOS"
echo "----------------------------------------------------------------------------"

check_file() {
    if [ -f "$1" ]; then
        echo "[OK] $1 existe"
    else
        echo "[FAIL] $1 NO EXISTE"
    fi
}

check_dir() {
    if [ -d "$1" ]; then
        echo "[OK] $1 existe ($(ls -A $1 | wc -l) archivos)"
    else
        echo "[FAIL] $1 NO EXISTE"
    fi
}

check_file "/home/ubuntu/clinic_records/cr_backend/.env"
check_file "/home/ubuntu/clinic_records/cr_backend/manage.py"
check_dir "/home/ubuntu/clinic_records/cr_backend/venv"
check_dir "/home/ubuntu/clinic_records/cr_backend/logs"
check_file "/etc/systemd/system/gunicorn.service"
check_file "/etc/systemd/system/celery.service"
check_file "/etc/nginx/sites-enabled/clinidocs"
check_dir "/home/ubuntu/clinic_records/cr_frontend/dist"
echo ""

# ============================================================================
# 5. LOGS DE ERRORES RECIENTES
# ============================================================================
echo "5. ÚLTIMOS ERRORES EN LOGS"
echo "----------------------------------------------------------------------------"

echo "--- Gunicorn Errors (últimas 10 líneas) ---"
if [ -f ~/clinic_records/cr_backend/logs/gunicorn-error.log ]; then
    tail -10 ~/clinic_records/cr_backend/logs/gunicorn-error.log
else
    echo "  [WARN] Log no existe"
fi
echo ""

echo "--- Celery Errors (últimas 10 líneas con ERROR) ---"
if [ -f ~/clinic_records/cr_backend/logs/celery.log ]; then
    grep -i error ~/clinic_records/cr_backend/logs/celery.log | tail -10 || echo "  No hay errores recientes"
else
    echo "  [WARN] Log no existe"
fi
echo ""

echo "--- Nginx Errors (últimas 10 líneas) ---"
sudo tail -10 /var/log/nginx/error.log 2>/dev/null || echo "  [WARN] Log no accesible"
echo ""

# ============================================================================
# 6. PRUEBAS DE CONECTIVIDAD
# ============================================================================
echo "6. PRUEBAS DE CONECTIVIDAD"
echo "----------------------------------------------------------------------------"

echo "Test 1: Redis PING"
redis-cli ping 2>/dev/null || echo "  [FAIL] Redis no responde"
echo ""

echo "Test 2: Django Health Check (directo a Gunicorn)"
curl -s http://127.0.0.1:8000/api/health/ | head -5 || echo "  [FAIL] Gunicorn no responde"
echo ""

echo "Test 3: Django Login (directo a Gunicorn)"
curl -s -X POST http://127.0.0.1:8000/api/login/ -H "Content-Type: application/json" -d '{}' | head -5
echo ""

echo "Test 4: Nginx → Backend"
curl -s http://localhost/api/health/ | head -5 || echo "  [FAIL] Nginx no reenvía correctamente"
echo ""

# ============================================================================
# 7. VARIABLES DE ENTORNO DJANGO
# ============================================================================
echo "7. CONFIGURACIÓN DJANGO"
echo "----------------------------------------------------------------------------"
cd ~/clinic_records/cr_backend
source venv/bin/activate 2>/dev/null

export DJANGO_SETTINGS_MODULE=config.settings.production

echo "SECRET_KEY: $(grep SECRET_KEY .env | cut -d= -f2 | head -c 20)..."
echo "DEBUG: $(grep ^DEBUG .env | cut -d= -f2)"
echo "ALLOWED_HOSTS: $(grep ALLOWED_HOSTS .env | cut -d= -f2)"
echo ""
echo "DATABASE_HOST: $(grep DATABASE_HOST .env | cut -d= -f2)"
echo "DATABASE_NAME: $(grep DATABASE_NAME .env | cut -d= -f2)"
echo ""
echo "REDIS_URL: $(grep REDIS_URL .env | cut -d= -f2)"
echo ""
echo "STRIPE_ENABLED: $(grep STRIPE_ENABLED .env | cut -d= -f2)"
echo "STRIPE_SECRET_KEY: $(grep STRIPE_SECRET_KEY .env | cut -d= -f2 | head -c 15)..."
echo ""

# ============================================================================
# 8. RUTAS DJANGO REGISTRADAS
# ============================================================================
echo "8. RUTAS DJANGO IMPORTANTES"
echo "----------------------------------------------------------------------------"
python -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
import django
django.setup()
from django.urls import get_resolver

resolver = get_resolver()
for pattern in resolver.url_patterns:
    p_str = str(pattern.pattern)
    if any(x in p_str for x in ['login', 'health', 'checkout']):
        print(f'  {p_str}')
" 2>/dev/null || echo "  [FAIL] No se pudo cargar Django"
echo ""

# ============================================================================
# 9. VERSIONES INSTALADAS
# ============================================================================
echo "9. VERSIONES DE SOFTWARE"
echo "----------------------------------------------------------------------------"
echo "Python: $(python3 --version 2>&1)"
echo "Django: $(python -c 'import django; print(django.get_version())' 2>/dev/null || echo 'N/A')"
echo "Celery: $(celery --version 2>/dev/null | head -1 || echo 'N/A')"
echo "Redis: $(redis-cli --version 2>/dev/null || echo 'N/A')"
echo "Nginx: $(nginx -v 2>&1)"
echo "Node: $(node --version 2>/dev/null || echo 'N/A')"
echo ""

# ============================================================================
# 10. ARCHIVOS DESACTUALIZADOS
# ============================================================================
echo "10. ESTADO DEL REPOSITORIO GIT"
echo "----------------------------------------------------------------------------"
cd ~/clinic_records/cr_backend
echo "Backend - Rama actual: $(git branch --show-current 2>/dev/null || echo 'N/A')"
echo "Backend - Último commit: $(git log -1 --oneline 2>/dev/null || echo 'N/A')"
echo "Backend - Archivos sin commitear:"
git status --short 2>/dev/null | head -10 || echo "  N/A"
echo ""

cd ~/clinic_records/cr_frontend
echo "Frontend - Rama actual: $(git branch --show-current 2>/dev/null || echo 'N/A')"
echo "Frontend - Último commit: $(git log -1 --oneline 2>/dev/null || echo 'N/A')"
echo ""

# ============================================================================
# RESUMEN
# ============================================================================
echo "============================================================================"
echo "RESUMEN Y RECOMENDACIONES"
echo "============================================================================"

ISSUES=0

# Verificar servicios
for service in "${services[@]}"; do
    if ! systemctl is-active --quiet $service; then
        echo "[ISSUE] Servicio $service no está activo - Ejecutar: sudo systemctl start $service"
        ISSUES=$((ISSUES+1))
    fi
done

# Verificar puertos
if ! sudo netstat -tlnp | grep -q :8000; then
    echo "[ISSUE] Puerto 8000 no está en uso - Gunicorn puede no estar corriendo"
    ISSUES=$((ISSUES+1))
fi

if ! redis-cli ping &>/dev/null; then
    echo "[ISSUE] Redis no responde - Ejecutar: sudo systemctl restart redis-server"
    ISSUES=$((ISSUES+1))
fi

if [ ! -f ~/clinic_records/cr_backend/.env ]; then
    echo "[ISSUE] Archivo .env no existe - Copiar desde .env.production"
    ISSUES=$((ISSUES+1))
fi

echo ""
if [ $ISSUES -eq 0 ]; then
    echo "[OK] No se detectaron problemas críticos"
else
    echo "[WARN] Se detectaron $ISSUES problemas que requieren atención"
fi

echo ""
echo "============================================================================"
echo "FIN DEL DIAGNÓSTICO - $(date)"
echo "============================================================================"
