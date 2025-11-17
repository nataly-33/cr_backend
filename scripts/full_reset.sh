#!/bin/bash
# ============================================================================
# SCRIPT DE RESET COMPLETO Y REINSTALACIÓN
# ============================================================================

echo "============================================================================"
echo "REINICIO COMPLETO DEL DEPLOYMENT"
echo "============================================================================"
echo ""
echo "ADVERTENCIA: Este script va a:"
echo "  1. Detener todos los servicios"
echo "  2. Eliminar archivos antiguos (BACKUP automático)"
echo "  3. Clonar repositorios frescos"
echo "  4. Reinstalar todo desde cero"
echo ""
read -p "¿Estás seguro? (escribe 'SI' para continuar): " confirm

if [ "$confirm" != "SI" ]; then
    echo "Operación cancelada"
    exit 0
fi

echo ""
echo "Iniciando reset completo..."
echo ""

# ============================================================================
# 1. DETENER TODOS LOS SERVICIOS
# ============================================================================
echo "[1/10] Deteniendo servicios..."
sudo systemctl stop celery celerybeat gunicorn nginx 2>/dev/null
pm2 delete all 2>/dev/null
echo "  [OK] Servicios detenidos"

# ============================================================================
# 2. BACKUP DE CONFIGURACIONES IMPORTANTES
# ============================================================================
echo "[2/10] Haciendo backup de configuraciones..."
mkdir -p ~/backup_$(date +%Y%m%d_%H%M%S)
BACKUP_DIR=~/backup_$(date +%Y%m%d_%H%M%S)

if [ -f ~/clinic_records/cr_backend/.env ]; then
    cp ~/clinic_records/cr_backend/.env $BACKUP_DIR/
    echo "  [OK] .env respaldado"
fi

if [ -f ~/clinic_records/cr_backend/logs/*.log ]; then
    cp ~/clinic_records/cr_backend/logs/*.log $BACKUP_DIR/ 2>/dev/null
    echo "  [OK] Logs respaldados"
fi

# ============================================================================
# 3. ELIMINAR CARPETAS ANTIGUAS
# ============================================================================
echo "[3/10] Eliminando instalación antigua..."
rm -rf ~/clinic_records
echo "  [OK] Carpeta clinic_records eliminada"

# ============================================================================
# 4. INSTALAR DEPENDENCIAS DEL SISTEMA
# ============================================================================
echo "[4/10] Actualizando sistema..."
sudo apt update -qq
sudo apt install -y python3.11 python3.11-venv python3-pip redis-server nginx git curl -qq
echo "  [OK] Dependencias instaladas"

# ============================================================================
# 5. CLONAR REPOSITORIOS
# ============================================================================
echo "[5/10] Clonando repositorios..."
cd ~
git clone https://github.com/nataly-33/cr_backend.git ~/clinic_records/cr_backend
git clone https://github.com/nataly-33/cr_frontend.git ~/clinic_records/cr_frontend
echo "  [OK] Repositorios clonados"

# ============================================================================
# 6. CONFIGURAR BACKEND
# ============================================================================
echo "[6/10] Configurando backend..."
cd ~/clinic_records/cr_backend

# Cambiar a rama correcta
git checkout nataly_martinez 2>/dev/null || git checkout main

# Crear virtualenv
python3.11 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install --upgrade pip -q
pip install -r requirements.txt -q

# Crear directorio de logs
mkdir -p logs
chmod 755 logs

# Restaurar .env si existe backup
if [ -f $BACKUP_DIR/.env ]; then
    cp $BACKUP_DIR/.env .env
    echo "  [OK] .env restaurado desde backup"
else
    echo "  [WARN] No hay .env en backup - deberás configurarlo manualmente"
fi

# Ejecutar migraciones
python manage.py migrate --noinput

# Collectstatic
python manage.py collectstatic --noinput

echo "  [OK] Backend configurado"

# ============================================================================
# 7. CONFIGURAR FRONTEND
# ============================================================================
echo "[7/10] Configurando frontend..."
cd ~/clinic_records/cr_frontend

# Cambiar a rama correcta
git checkout nataly 2>/dev/null || git checkout main

# Instalar dependencias
npm install -q

# Build
npm run build

echo "  [OK] Frontend configurado"

# ============================================================================
# 8. CONFIGURAR SERVICIOS SYSTEMD
# ============================================================================
echo "[8/10] Configurando servicios systemd..."

# Gunicorn
sudo tee /etc/systemd/system/gunicorn.service > /dev/null <<EOF
[Unit]
Description=Gunicorn daemon for CliniDocs
After=network.target

[Service]
Type=notify
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/clinic_records/cr_backend
Environment="PATH=/home/ubuntu/clinic_records/cr_backend/venv/bin"
Environment="DJANGO_SETTINGS_MODULE=config.settings.production"
ExecStart=/home/ubuntu/clinic_records/cr_backend/venv/bin/gunicorn \\
    --workers 4 \\
    --bind 0.0.0.0:8000 \\
    --timeout 120 \\
    --access-logfile /home/ubuntu/clinic_records/cr_backend/logs/gunicorn-access.log \\
    --error-logfile /home/ubuntu/clinic_records/cr_backend/logs/gunicorn-error.log \\
    --log-level info \\
    config.wsgi:application
ExecReload=/bin/kill -s HUP \$MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF

# Celery Worker
sudo mkdir -p /var/run/celery
sudo chown ubuntu:ubuntu /var/run/celery

sudo tee /etc/systemd/system/celery.service > /dev/null <<EOF
[Unit]
Description=Celery Worker for CliniDocs
After=network.target redis.service

[Service]
Type=forking
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/clinic_records/cr_backend
Environment="PATH=/home/ubuntu/clinic_records/cr_backend/venv/bin"
Environment="DJANGO_SETTINGS_MODULE=config.settings.production"
ExecStart=/home/ubuntu/clinic_records/cr_backend/venv/bin/celery -A config multi start worker1 \\
    --pidfile=/var/run/celery/worker1.pid \\
    --logfile=/home/ubuntu/clinic_records/cr_backend/logs/celery.log \\
    --loglevel=INFO \\
    --concurrency=4
ExecStop=/home/ubuntu/clinic_records/cr_backend/venv/bin/celery -A config multi stopwait worker1 \\
    --pidfile=/var/run/celery/worker1.pid
Restart=on-failure
RuntimeDirectory=celery
RuntimeDirectoryMode=0755

[Install]
WantedBy=multi-user.target
EOF

# Celery Beat
sudo tee /etc/systemd/system/celerybeat.service > /dev/null <<EOF
[Unit]
Description=Celery Beat Scheduler for CliniDocs
After=network.target redis.service

[Service]
Type=simple
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/clinic_records/cr_backend
Environment="PATH=/home/ubuntu/clinic_records/cr_backend/venv/bin"
Environment="DJANGO_SETTINGS_MODULE=config.settings.production"
ExecStart=/home/ubuntu/clinic_records/cr_backend/venv/bin/celery -A config beat \\
    --loglevel=INFO \\
    --pidfile=/var/run/celery/beat.pid \\
    --logfile=/home/ubuntu/clinic_records/cr_backend/logs/celerybeat.log \\
    --schedule=/home/ubuntu/clinic_records/cr_backend/celerybeat-schedule
Restart=on-failure
RuntimeDirectory=celery
RuntimeDirectoryMode=0755

[Install]
WantedBy=multi-user.target
EOF

echo "  [OK] Servicios systemd configurados"

# ============================================================================
# 9. CONFIGURAR NGINX
# ============================================================================
echo "[9/10] Configurando Nginx..."

sudo tee /etc/nginx/sites-available/clinidocs > /dev/null <<'EOF'
server {
    listen 80;
    server_name 52.44.135.19;
    client_max_body_size 100M;

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 120s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;
    }

    location /admin/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /static/ {
        alias /home/ubuntu/clinic_records/cr_backend/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /home/ubuntu/clinic_records/cr_backend/media/;
        expires 7d;
    }

    location / {
        alias /home/ubuntu/clinic_records/cr_frontend/dist/;
        try_files \$uri \$uri/ /index.html;
        expires 30d;
        add_header Cache-Control "public, max-age=31536000";
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/clinidocs /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t

echo "  [OK] Nginx configurado"

# ============================================================================
# 10. INICIAR TODOS LOS SERVICIOS
# ============================================================================
echo "[10/10] Iniciando servicios..."

sudo systemctl daemon-reload

# Iniciar servicios en orden
sudo systemctl start redis-server
sleep 2
sudo systemctl start gunicorn
sleep 2
sudo systemctl start celery
sleep 2
sudo systemctl start celerybeat
sleep 2
sudo systemctl restart nginx

# Habilitar servicios para auto-start
sudo systemctl enable redis-server gunicorn celery celerybeat nginx

echo "  [OK] Servicios iniciados"

# ============================================================================
# VERIFICACIÓN FINAL
# ============================================================================
echo ""
echo "============================================================================"
echo "VERIFICACIÓN FINAL"
echo "============================================================================"

services=("redis-server" "gunicorn" "celery" "celerybeat" "nginx")
ALL_OK=true

for service in "${services[@]}"; do
    if systemctl is-active --quiet $service; then
        echo "[OK] $service"
    else
        echo "[FAIL] $service NO ESTÁ ACTIVO"
        ALL_OK=false
    fi
done

echo ""
echo "Probando endpoint de salud..."
sleep 3
curl -s http://127.0.0.1:8000/api/health/ | head -3

echo ""
echo "============================================================================"
if [ "$ALL_OK" = true ]; then
    echo "INSTALACIÓN COMPLETADA EXITOSAMENTE"
    echo "============================================================================"
    echo ""
    echo "Próximos pasos:"
    echo "  1. Configurar .env con tus credenciales:"
    echo "     nano ~/clinic_records/cr_backend/.env"
    echo ""
    echo "  2. Reiniciar servicios:"
    echo "     sudo systemctl restart gunicorn celery celerybeat"
    echo ""
    echo "  3. Acceder a:"
    echo "     Frontend: http://52.44.135.19"
    echo "     Admin: http://52.44.135.19/admin"
    echo "     API: http://52.44.135.19/api/health/"
else
    echo "INSTALACIÓN COMPLETADA CON ADVERTENCIAS"
    echo "============================================================================"
    echo "Algunos servicios no iniciaron correctamente."
    echo "Revisa los logs en: ~/clinic_records/cr_backend/logs/"
fi

echo ""
echo "Backup de configuración anterior en: $BACKUP_DIR"
echo "============================================================================"
