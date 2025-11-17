# ⚡ COMANDOS RÁPIDOS - DEPLOY Y MANTENIMIENTO

**Copia y pega estos comandos directamente en tu terminal**

---

## 🚀 ACTUALIZAR DEPLOY EXISTENTE (30 MIN)

```bash
# ============================================================================
# CONECTAR A EC2
# ============================================================================
ssh -i "clinidocs-key.pem" ubuntu@52.0.69.138

# ============================================================================
# 1. INSTALAR REDIS
# ============================================================================
sudo apt update
sudo apt install -y redis-server
sudo systemctl enable redis-server
sudo systemctl start redis-server
redis-cli ping  # Debe responder: PONG

# ============================================================================
# 2. ACTUALIZAR CÓDIGO
# ============================================================================
cd ~/clinic_records/cr_backend
git pull
source venv/bin/activate
pip install -r requirements.txt

# ============================================================================
# 3. ACTUALIZAR .ENV
# ============================================================================
nano .env
# Agregar estas líneas al final:
#
# # Redis y Celery
# REDIS_URL=redis://localhost:6379/0
# CELERY_BROKER_URL=redis://localhost:6379/0
# CELERY_RESULT_BACKEND=redis://localhost:6379/0
#
# # OCR
# ENABLE_OCR=True
#
# # Stripe (modo test)
# STRIPE_ENABLED=True
# STRIPE_SECRET_KEY=sk_test_TU_KEY_AQUI
# STRIPE_PUBLISHABLE_KEY=pk_test_TU_KEY_AQUI
# STRIPE_WEBHOOK_SECRET=whsec_TU_SECRET_AQUI
#
# # Firebase
# FIREBASE_SERVER_KEY=TU_SERVER_KEY_AQUI
# FIREBASE_SERVICE_ACCOUNT_KEY='{"type":"service_account",...}'
#
# Guardar: Ctrl+O → Enter → Ctrl+X

# ============================================================================
# 4. CREAR SERVICIO CELERY WORKER
# ============================================================================
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
ExecStart=/home/ubuntu/clinic_records/cr_backend/venv/bin/celery -A config multi start worker1 \
    --pidfile=/var/run/celery/worker1.pid \
    --logfile=/home/ubuntu/clinic_records/cr_backend/logs/celery.log \
    --loglevel=INFO \
    --concurrency=4
ExecStop=/home/ubuntu/clinic_records/cr_backend/venv/bin/celery -A config multi stopwait worker1 \
    --pidfile=/var/run/celery/worker1.pid
ExecReload=/home/ubuntu/clinic_records/cr_backend/venv/bin/celery -A config multi restart worker1 \
    --pidfile=/var/run/celery/worker1.pid \
    --logfile=/home/ubuntu/clinic_records/cr_backend/logs/celery.log \
    --loglevel=INFO
Restart=on-failure
RuntimeDirectory=celery
RuntimeDirectoryMode=0755

[Install]
WantedBy=multi-user.target
EOF

# ============================================================================
# 5. CREAR SERVICIO CELERY BEAT
# ============================================================================
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
ExecStart=/home/ubuntu/clinic_records/cr_backend/venv/bin/celery -A config beat \
    --loglevel=INFO \
    --pidfile=/var/run/celery/beat.pid \
    --logfile=/home/ubuntu/clinic_records/cr_backend/logs/celerybeat.log \
    --schedule=/home/ubuntu/clinic_records/cr_backend/celerybeat-schedule
Restart=on-failure
RuntimeDirectory=celery
RuntimeDirectoryMode=0755

[Install]
WantedBy=multi-user.target
EOF

# ============================================================================
# 6. CREAR DIRECTORIO PARA PIDS
# ============================================================================
sudo mkdir -p /var/run/celery
sudo chown ubuntu:ubuntu /var/run/celery

# ============================================================================
# 7. INICIAR SERVICIOS
# ============================================================================
sudo systemctl daemon-reload
sudo systemctl enable celery celerybeat
sudo systemctl start celery celerybeat
sudo systemctl restart gunicorn

# ============================================================================
# 8. VERIFICAR TODO
# ============================================================================
echo "=== Verificando servicios ==="
sudo systemctl status redis-server --no-pager | grep Active
sudo systemctl status celery --no-pager | grep Active
sudo systemctl status celerybeat --no-pager | grep Active
sudo systemctl status gunicorn --no-pager | grep Active

echo ""
echo "=== Ver logs en tiempo real (Ctrl+C para salir) ==="
tail -f ~/clinic_records/cr_backend/logs/celery.log
```

---

## 🔍 MONITOREO Y VERIFICACIÓN

### Ver Estado de Todos los Servicios

```bash
sudo systemctl status redis-server gunicorn celery celerybeat nginx
```

### Ver Logs en Tiempo Real

```bash
# Todos los logs importantes
tail -f ~/clinic_records/cr_backend/logs/{app,errors,celery,gunicorn-error}.log

# Solo errores
tail -f ~/clinic_records/cr_backend/logs/errors.log

# Solo Celery
tail -f ~/clinic_records/cr_backend/logs/celery.log
```

### Ver Tareas de Celery

```bash
cd ~/clinic_records/cr_backend
source venv/bin/activate

# Tareas activas
celery -A config inspect active

# Tareas programadas
celery -A config inspect scheduled

# Workers registrados
celery -A config inspect registered

# Ver schedule de Beat
celery -A config beat --loglevel=debug
```

### Probar Celery Manualmente

```bash
cd ~/clinic_records/cr_backend
source venv/bin/activate
python manage.py shell
```

```python
# En el shell de Django:

# Probar tarea de debug
from celery import current_app
result = current_app.send_task('celery.debug')
print(result.get(timeout=10))

# Ejecutar backup manual
from apps.backup.tasks import crear_backup_automatico
result = crear_backup_automatico.delay()
print(result.get(timeout=60))

# Ver notificaciones pendientes
from apps.notifications.models import Notification
print(Notification.objects.filter(status='pending').count())

# Enviar notificación de prueba
from apps.notifications.tasks import send_push_notification
result = send_push_notification.delay(
    user_id=1,
    title="Test",
    body="Probando notificaciones"
)
print(result.get(timeout=30))
```

---

## 🔄 REINICIAR SERVICIOS

### Reiniciar Todo

```bash
sudo systemctl restart redis-server gunicorn celery celerybeat nginx
```

### Reiniciar Solo Backend

```bash
sudo systemctl restart gunicorn
```

### Reiniciar Solo Celery

```bash
sudo systemctl restart celery celerybeat
```

### Ver Estado Después de Reiniciar

```bash
sudo systemctl status redis-server gunicorn celery celerybeat nginx --no-pager
```

---

## 📦 ACTUALIZAR CÓDIGO

```bash
# Backend
cd ~/clinic_records/cr_backend
git pull
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart gunicorn celery celerybeat

# Frontend
cd ~/clinic_records/cr_frontend
git pull
npm install
pm2 restart frontend
```

---

## 🐛 TROUBLESHOOTING

### Redis no responde

```bash
sudo systemctl status redis-server
sudo systemctl restart redis-server
redis-cli ping
```

### Celery no procesa tareas

```bash
# Ver logs
tail -f ~/clinic_records/cr_backend/logs/celery.log

# Reiniciar
sudo systemctl restart celery

# Verificar que hay workers
cd ~/clinic_records/cr_backend
source venv/bin/activate
celery -A config inspect active
```

### Gunicorn con errores

```bash
# Ver logs
tail -f ~/clinic_records/cr_backend/logs/gunicorn-error.log

# Probar Django directamente
cd ~/clinic_records/cr_backend
source venv/bin/activate
python manage.py runserver 0.0.0.0:8001

# Si funciona, el problema es Gunicorn
sudo systemctl restart gunicorn
```

### Nginx no funciona

```bash
# Verificar configuración
sudo nginx -t

# Ver logs
sudo tail -f /var/log/nginx/error.log

# Reiniciar
sudo systemctl restart nginx
```

### OCR no funciona

```bash
# Verificar credenciales AWS
aws s3 ls  # Debe listar buckets

# Ver logs de Textract
tail -f ~/clinic_records/cr_backend/logs/celery.log | grep -i textract

# Probar manualmente
cd ~/clinic_records/cr_backend
source venv/bin/activate
python manage.py shell
```

```python
import boto3
client = boto3.client('textract', region_name='us-east-1')
response = client.detect_document_text(
    Document={'S3Object': {'Bucket': 'clinidocs-files-2025', 'Name': 'test.pdf'}}
)
print(response)
```

### Notificaciones Push no llegan

```bash
# Ver logs
tail -f ~/clinic_records/cr_backend/logs/celery.log | grep -i firebase

# Verificar Firebase
cd ~/clinic_records/cr_backend
source venv/bin/activate
python manage.py shell
```

```python
from firebase_admin import credentials, initialize_app, messaging
import firebase_admin

# Verificar que está inicializado
print(firebase_admin._apps)

# Si no hay apps, inicializar
if not firebase_admin._apps:
    from config.settings.base import get_firebase_credentials
    cred_dict = get_firebase_credentials()
    cred = credentials.Certificate(cred_dict)
    initialize_app(cred)
```

### Stripe webhook no recibe eventos

```bash
# Instalar Stripe CLI
wget https://github.com/stripe/stripe-cli/releases/download/v1.19.0/stripe_1.19.0_linux_x86_64.tar.gz
tar -xzf stripe_1.19.0_linux_x86_64.tar.gz
sudo mv stripe /usr/local/bin/

# Forward webhooks
stripe listen --forward-to http://52.0.69.138:8000/api/payments/stripe-webhook/

# En otra terminal, probar
stripe trigger checkout.session.completed

# Ver logs
tail -f ~/clinic_records/cr_backend/logs/app.log | grep -i stripe
```

---

## 📊 SCRIPTS ÚTILES

### Script de Monitoreo Completo

```bash
cat > ~/monitor.sh << 'EOF'
#!/bin/bash
echo "======================================"
echo "  MONITOREO CLINIDOCS"
echo "======================================"
echo ""
echo "=== Servicios ==="
sudo systemctl status redis-server --no-pager | grep Active
sudo systemctl status gunicorn --no-pager | grep Active
sudo systemctl status celery --no-pager | grep Active
sudo systemctl status celerybeat --no-pager | grep Active
sudo systemctl status nginx --no-pager | grep Active
echo ""
echo "=== Workers Celery ==="
cd ~/clinic_records/cr_backend
source venv/bin/activate
celery -A config inspect active 2>/dev/null | head -20
echo ""
echo "=== Tareas Programadas (próximas 3) ==="
celery -A config inspect scheduled 2>/dev/null | head -20
echo ""
echo "=== Memoria ==="
free -h | grep -E 'Mem|Swap'
echo ""
echo "=== Disco ==="
df -h | grep -E 'Filesystem|/$'
echo ""
echo "=== Últimos 5 errores ==="
tail -n 5 ~/clinic_records/cr_backend/logs/errors.log 2>/dev/null || echo "Sin errores recientes"
EOF

chmod +x ~/monitor.sh
```

### Ejecutar Monitoreo

```bash
~/monitor.sh
```

### Script de Backup Manual

```bash
cat > ~/backup_now.sh << 'EOF'
#!/bin/bash
cd ~/clinic_records/cr_backend
source venv/bin/activate
python manage.py shell << PYTHON
from apps.backup.tasks import crear_backup_automatico
result = crear_backup_automatico.delay()
print("Backup iniciado:", result.id)
print("Esperando resultado...")
try:
    output = result.get(timeout=120)
    print("✅ Backup completado:", output)
except Exception as e:
    print("❌ Error:", e)
PYTHON
EOF

chmod +x ~/backup_now.sh
```

### Ejecutar Backup Manual

```bash
~/backup_now.sh
```

### Script de Limpieza de Logs

```bash
cat > ~/clean_logs.sh << 'EOF'
#!/bin/bash
echo "Limpiando logs antiguos..."
cd ~/clinic_records/cr_backend/logs
find . -name "*.log" -mtime +30 -delete
echo "✅ Logs de más de 30 días eliminados"
EOF

chmod +x ~/clean_logs.sh
```

### Ejecutar Limpieza

```bash
~/clean_logs.sh
```

---

## 🔐 CONFIGURAR HTTPS CON NO-IP (OPCIONAL)

```bash
# 1. Registrar dominio gratis en No-IP.com
# Ejemplo: clinidocs.ddns.net → 52.0.69.138

# 2. Instalar certbot
sudo apt install -y certbot python3-certbot-nginx

# 3. Obtener certificado
sudo certbot --nginx -d clinidocs.ddns.net

# 4. Actualizar .env
nano ~/clinic_records/cr_backend/.env
# Cambiar:
# ALLOWED_HOSTS=clinidocs.ddns.net,52.0.69.138
# CORS_ALLOWED_ORIGINS=https://clinidocs.ddns.net

# 5. Actualizar production.py
nano ~/clinic_records/cr_backend/config/settings/production.py
# Cambiar a:
# SECURE_SSL_REDIRECT = True
# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SECURE = True

# 6. Reiniciar servicios
sudo systemctl restart gunicorn nginx

# 7. Renovación automática (certbot lo hace solo)
sudo certbot renew --dry-run
```

---

## 📱 PROBAR DESDE POSTMAN/CURL

### Health Check

```bash
curl http://52.0.69.138/api/health/
```

### Login

```bash
curl -X POST http://52.0.69.138/api/accounts/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@test.com",
    "password": "admin123"
  }'
```

### Listar Pacientes (con token)

```bash
TOKEN="tu_access_token_aqui"
curl http://52.0.69.138/api/patients/ \
  -H "Authorization: Bearer $TOKEN"
```

### Subir Documento (con OCR)

```bash
TOKEN="tu_access_token_aqui"
curl -X POST http://52.0.69.138/api/documents/ \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/ruta/a/documento.pdf" \
  -F "patient=1" \
  -F "document_type=LAB"
```

---

## 🎓 COMANDOS PARA DEMO/PRESENTACIÓN

### Ver Logs en Tiempo Real (3 terminales)

```bash
# Terminal 1: Logs de aplicación
tail -f ~/clinic_records/cr_backend/logs/app.log

# Terminal 2: Logs de Celery
tail -f ~/clinic_records/cr_backend/logs/celery.log

# Terminal 3: Monitoreo de servicios
watch -n 2 'sudo systemctl status redis-server gunicorn celery celerybeat --no-pager | grep Active'
```

### Forzar Backup Durante Demo

```bash
cd ~/clinic_records/cr_backend
source venv/bin/activate
python manage.py shell -c "from apps.backup.tasks import crear_backup_automatico; crear_backup_automatico.delay()"
```

### Ver Tareas de Celery Durante Demo

```bash
cd ~/clinic_records/cr_backend
source venv/bin/activate
watch -n 2 'celery -A config inspect active'
```

---

## 📞 AYUDA RÁPIDA

### ¿Algo no funciona?

```bash
# 1. Ver TODOS los logs de errores
tail -f ~/clinic_records/cr_backend/logs/errors.log

# 2. Ver estado de TODOS los servicios
sudo systemctl status redis-server gunicorn celery celerybeat nginx

# 3. Reiniciar TODO
sudo systemctl restart redis-server gunicorn celery celerybeat nginx

# 4. Si aún falla, revisar .env
nano ~/clinic_records/cr_backend/.env
```

### ¿Necesitas ayuda?

1. Copia el error exacto de los logs
2. Verifica que todas las variables de entorno estén configuradas
3. Revisa la documentación completa: `docs/deployment/DEPLOY_COMPLETO_ACTUALIZADO.md`

---

**¡Comandos listos para usar! 🚀**
