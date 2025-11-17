# 🚀 GUÍA COMPLETA DE DEPLOYMENT - CLINIC RECORDS 2.0

**Proyecto:** CliniDocs - Sistema de Gestión de Historias Clínicas  
**Actualizado:** Noviembre 2025  
**Funcionalidades:** Django + PostgreSQL + Redis + Celery + S3 + OCR + Stripe + Push Notifications  
**Tiempo estimado:** 2 horas  
**Costo:** AWS Free Tier + Servicios gratuitos

---

## 📋 TABLA DE CONTENIDOS

1. [Resumen de Arquitectura](#resumen-de-arquitectura)
2. [Prerequisitos y Checklist](#prerequisitos-y-checklist)
3. [PARTE 1: Infraestructura AWS](#parte-1-infraestructura-aws)
4. [PARTE 2: Instalación en EC2](#parte-2-instalación-en-ec2)
5. [PARTE 3: Configuración de Servicios](#parte-3-configuración-de-servicios)
6. [PARTE 4: Deploy del Backend](#parte-4-deploy-del-backend)
7. [PARTE 5: Configurar Celery + Redis](#parte-5-configurar-celery--redis)
8. [PARTE 6: Stripe en Modo Test](#parte-6-stripe-en-modo-test)
9. [PARTE 7: Nginx y Gunicorn](#parte-7-nginx-y-gunicorn)
10. [PARTE 8: Deploy del Frontend](#parte-8-deploy-del-frontend)
11. [PARTE 9: Pruebas y Verificación](#parte-9-pruebas-y-verificación)
12. [PARTE 10: Monitoreo y Logs](#parte-10-monitoreo-y-logs)
13. [Troubleshooting](#troubleshooting)
14. [Comandos Rápidos](#comandos-rápidos)

---

## 🏗️ RESUMEN DE ARQUITECTURA

### Componentes Principales:

```
┌─────────────────────────────────────────────────────────────┐
│                      CLIENTE (Browser/App)                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              AWS EC2 (IP: 52.0.69.138)                     │
│  ┌────────────┐  ┌────────────┐  ┌─────────────────────┐  │
│  │   Nginx    │  │  Gunicorn  │  │  Frontend (Vite)   │  │
│  │   :80      │─▶│   :8000    │  │      :5173         │  │
│  └────────────┘  └────────────┘  └─────────────────────┘  │
│  ┌────────────┐  ┌────────────┐  ┌─────────────────────┐  │
│  │   Redis    │◀─│   Celery   │  │   Celery Beat      │  │
│  │   :6379    │  │  Worker    │  │   (Scheduler)      │  │
│  └────────────┘  └────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    SERVICIOS EXTERNOS                        │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────┐   │
│  │ PostgreSQL   │ │    AWS S3    │ │  AWS Textract   │   │
│  │  RDS/Local   │ │ (Archivos)   │ │      (OCR)      │   │
│  └──────────────┘ └──────────────┘ └──────────────────┘   │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────┐   │
│  │   SendGrid   │ │    Stripe    │ │    Firebase     │   │
│  │   (Email)    │ │   (Pagos)    │ │     (Push)      │   │
│  └──────────────┘ └──────────────┘ └──────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Flujos de Datos:

1. **Requests HTTP** → Nginx → Gunicorn (Django)
2. **Tareas Asíncronas** → Celery Worker (via Redis)
3. **Archivos** → AWS S3
4. **OCR** → AWS Textract (automático al subir documento)
5. **Emails** → SendGrid
6. **Pagos** → Stripe (modo test)
7. **Notificaciones** → Firebase Cloud Messaging

---

## ✅ PREREQUISITOS Y CHECKLIST

### Cuentas Necesarias:

- [ ] Cuenta AWS (con tarjeta, pero Free Tier)
- [ ] Cuenta SendGrid (100 emails/día gratis)
- [ ] Cuenta Stripe (modo test, gratis)
- [ ] Cuenta Firebase (plan gratuito Spark)
- [ ] Repositorio Git (GitHub/GitLab)

### Información Actual:

```bash
# EC2
IP Pública: 52.44.135.19
IP Privada: 172.31.0.X

# RDS PostgreSQL
Endpoint: 172.31.0.117:5432
Database: clinidocs_db
User: clinidocs_user
Password: clinicdocs_pass_123*

# S3
Bucket: clinidocs-files-2025
Region: us-east-1
```

---

## 🎯 PARTE 1: INFRAESTRUCTURA AWS

### 1.1. Usuarios IAM Necesarios

Necesitarás **DOS usuarios IAM** con permisos específicos:

#### Usuario 1: `clinidocs-s3-textract-user`

```bash
# Permisos:
- AmazonS3FullAccess
- AmazonTextractFullAccess
```

**Pasos para crear:**

1. AWS Console → IAM → Users → Create User
2. Nombre: `clinidocs-s3-textract-user`
3. Access type: Programmatic access
4. Attach policies:
   - `AmazonS3FullAccess`
   - `AmazonTextractFullAccess`
5. Crear Access Keys
6. **COPIAR Y GUARDAR:**
   ```
   AWS_ACCESS_KEY_ID=AKIAXXXXXXXXX
   AWS_SECRET_ACCESS_KEY=xxxxxxxxxxxxxxxxx
   ```

### 1.2. Security Groups de EC2

Asegúrate de tener estos puertos abiertos:

```bash
# Inbound Rules:
SSH          | TCP | 22    | Tu IP (o 0.0.0.0/0)
HTTP         | TCP | 80    | 0.0.0.0/0
HTTPS        | TCP | 443   | 0.0.0.0/0
Custom TCP   | TCP | 8000  | 0.0.0.0/0  # Django
Custom TCP   | TCP | 5173  | 0.0.0.0/0  # Frontend
```

### 1.3. Verificar Infraestructura Existente

```bash
# Desde tu PC, conectar a EC2:
ssh -i "smartsales-key.pem" ubuntu@52.44.135.19

# Verificar PostgreSQL (puede ser RDS o local):
psql -h 172.31.0.117 -U clinidocs_user -d clinidocs_db

# Verificar S3:
aws s3 ls s3://clinidocs-files-2025/
```

---

## 🖥️ PARTE 2: INSTALACIÓN EN EC2

### 2.1. Conectar a EC2

```bash
# Desde PowerShell en Windows:
cd ~
ssh -i "smartsales-key.pem" ubuntu@52.44.135.19
```

### 2.2. Actualizar Sistema e Instalar Dependencias

```bash
# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Python 3.11
sudo apt install -y python3.11 python3.11-venv python3-pip

# Instalar PostgreSQL client
sudo apt install -y postgresql-client

# Instalar Redis (NUEVO - Requerido para Celery)
sudo apt install -y redis-server

# Iniciar y habilitar Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Verificar Redis
redis-cli ping  # Debe responder: PONG

# Instalar Nginx y otras herramientas
sudo apt install -y nginx git curl supervisor

# Instalar Node.js 20 (para frontend)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Verificar instalaciones
python3.11 --version
redis-cli --version
nginx -v
node --version
npm --version
```

### 2.3. Configurar Firewall (UFW)

```bash
# Permitir tráfico necesario
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 8000/tcp  # Django
sudo ufw allow 5173/tcp  # Frontend

# Activar firewall
sudo ufw --force enable
sudo ufw status


###
–
sgr-0703c5c0dcf24bf39
IPv4
HTTPS
TCP
443
0.0.0.0/0
–
–
sgr-02fd7b6d43a798747
IPv4
HTTP
TCP
80
0.0.0.0/0
–
–
sgr-0e2863ce45a7266d7
IPv4
PostgreSQL
TCP
5432
172.31.0.0/16
RDS Connection
–
sgr-063ef77f58e5301ad
IPv4
TCP personalizado
TCP
587
0.0.0.0/0
SendGridSMTP


```

---

## 🔧 PARTE 3: CONFIGURACIÓN DE SERVICIOS

### 3.1. Clonar Repositorio

```bash
# Ir a home
cd ~

# Clonar (reemplaza con tu repo)
git clone https://github.com/TU_USUARIO/clinic_records.git
cd clinic_records
```

### 3.2. Configurar Backend

```bash
# Ir a carpeta backend
cd cr_backend

# Crear entorno virtual con Python 3.11
python3.11 -m venv venv

# Activar entorno
source venv/bin/activate

# Actualizar pip
pip install --upgrade pip

# Instalar dependencias
pip install -r requirements.txt

# Crear directorio para logs
mkdir -p logs
chmod 755 logs
```

### 3.3. Configurar Variables de Entorno

```bash
# Copiar .env.production como .env
cp .env.production .env

# Editar .env con las credenciales reales
nano .env
```

**Contenido del `.env` en producción:**

```bash
# Django Core
DJANGO_SETTINGS_MODULE=config.settings.production
SECRET_KEY=prod-clinic-2025-super-secret-key-CAMBIAR-ESTO
DEBUG=False
ALLOWED_HOSTS=52.0.69.138,172.31.0.0/16,localhost,127.0.0.1

# Database
DATABASE_NAME=clinidocs_db
DATABASE_USER=clinidocs_user
DATABASE_PASSWORD=clinicdocs_pass_123*
DATABASE_HOST=172.31.0.117
DATABASE_PORT=5432

# Redis (NUEVO)
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# AWS S3 + Textract (ACTUALIZADO con usuario IAM)
USE_S3=True
USE_S3_BACKUP=True
AWS_ACCESS_KEY_ID=TU_ACCESS_KEY_AQUI
AWS_SECRET_ACCESS_KEY=TU_SECRET_KEY_AQUI
AWS_STORAGE_BUCKET_NAME=clinidocs-files-2025
AWS_S3_REGION_NAME=us-east-1
AWS_TEXTRACT_REGION=us-east-1
ENABLE_OCR=True

# CORS & Frontend
CORS_ALLOWED_ORIGINS=http://52.0.69.138,http://localhost:5173
FRONTEND_URL=http://52.0.69.138
BASE_DOMAIN=.com

# JWT
JWT_ACCESS_TOKEN_LIFETIME=60
JWT_REFRESH_TOKEN_LIFETIME=1440

# SendGrid (Email)
SENDGRID_ENABLED=True
SENDGRID_API_KEY=TU_SENDGRID_API_KEY
DEFAULT_FROM_EMAIL=tu_email@gmail.com

# Stripe (Modo Test)
STRIPE_ENABLED=True
STRIPE_SECRET_KEY=sk_test_XXXXXX
STRIPE_PUBLISHABLE_KEY=pk_test_XXXXXX
STRIPE_WEBHOOK_SECRET=whsec_XXXXXX

# Firebase (Push Notifications)
FIREBASE_SERVER_KEY=TU_SERVER_KEY
FIREBASE_SERVICE_ACCOUNT_KEY='{"type":"service_account","project_id":"tu-project",...}'
```

**Guardar:** `Ctrl+O` → `Enter` → `Ctrl+X`

### 3.4. Ejecutar Migraciones

```bash
# Asegúrate de estar en cr_backend con venv activado
source venv/bin/activate

# Ejecutar migraciones
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser

# Recolectar archivos estáticos
python manage.py collectstatic --noinput

# Probar que funciona
python manage.py check --deploy
```

---

## 🔄 PARTE 5: CONFIGURAR CELERY + REDIS

Celery maneja tareas asíncronas: backups, OCR, notificaciones push, etc.

### 5.1. Crear Archivo de Servicio para Celery Worker

```bash
sudo nano /etc/systemd/system/celery.service
```

**Contenido:**

```ini
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
```

### 5.2. Crear Archivo de Servicio para Celery Beat

```bash
sudo nano /etc/systemd/system/celerybeat.service
```

**Contenido:**

```ini
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
```

### 5.3. Crear Directorio para PIDs

```bash
sudo mkdir -p /var/run/celery
sudo chown ubuntu:ubuntu /var/run/celery
```

### 5.4. Iniciar Servicios Celery

```bash
# Recargar systemd
sudo systemctl daemon-reload

# Habilitar servicios
sudo systemctl enable celery
sudo systemctl enable celerybeat
sudo systemctl enable redis-server

# Iniciar servicios
sudo systemctl start redis-server
sudo systemctl start celery
sudo systemctl start celerybeat

# Verificar estado
sudo systemctl status redis-server
sudo systemctl status celery
sudo systemctl status celerybeat
```

### 5.5. Verificar que Celery Funciona

```bash
# Ver logs en tiempo real
tail -f ~/clinic_records/cr_backend/logs/celery.log

# Probar una tarea de prueba
cd ~/clinic_records/cr_backend
source venv/bin/activate
python manage.py shell

# En el shell:
from celery import current_app
result = current_app.send_task('celery.debug')
print(result.get(timeout=10))
# Debe mostrar: {'status': 'ok', 'message': 'Celery funcionando correctamente'}
```

---

## 💳 PARTE 6: STRIPE EN MODO TEST

Para webhooks de Stripe en producción, necesitamos el Stripe CLI.

### 6.1. Instalar Stripe CLI

```bash
# Descargar Stripe CLI
wget https://github.com/stripe/stripe-cli/releases/download/v1.19.0/stripe_1.19.0_linux_x86_64.tar.gz

# Descomprimir
tar -xzf stripe_1.19.0_linux_x86_64.tar.gz

# Mover a /usr/local/bin
sudo mv stripe /usr/local/bin/

# Verificar
stripe --version
```

### 6.2. Autenticar Stripe CLI

```bash
# Login (abrirá browser para autenticar)
stripe login

# Si no tienes browser, usa modo restricted key:
stripe login --api-key sk_test_TU_SECRET_KEY
```

### 6.3. Configurar Webhook en Modo Test

Tenemos dos opciones:

#### Opción A: Webhook Local (Desarrollo/Testing)

```bash
# Reenviar eventos a tu backend local
stripe listen --forward-to http://52.0.69.138:8000/api/payments/stripe-webhook/

# Copiar el webhook secret que aparece (whsec_...)
# Actualizar en .env:
STRIPE_WEBHOOK_SECRET=whsec_XXXXXX
```

#### Opción B: Webhook Configurado en Dashboard (Recomendado)

1. Ir a: https://dashboard.stripe.com/test/webhooks
2. Click "Add endpoint"
3. Endpoint URL: `http://52.0.69.138:8000/api/payments/stripe-webhook/`
4. Eventos a escuchar:
   - `checkout.session.completed`
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`
5. Copiar el "Signing secret" (whsec\_...)
6. Actualizar en `.env`

### 6.4. Crear Servicio para Stripe CLI (Opcional)

Si quieres que Stripe CLI se ejecute automáticamente:

```bash
sudo nano /etc/systemd/system/stripe-webhook.service
```

```ini
[Unit]
Description=Stripe Webhook Forwarder
After=network.target

[Service]
Type=simple
User=ubuntu
ExecStart=/usr/local/bin/stripe listen --forward-to http://52.0.69.138:8000/api/payments/stripe-webhook/
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable stripe-webhook
sudo systemctl start stripe-webhook
```

---

## 🌐 PARTE 7: NGINX Y GUNICORN

### 7.1. Crear Archivo de Servicio para Gunicorn

```bash
sudo nano /etc/systemd/system/gunicorn.service
```

**Contenido:**

```ini
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
ExecStart=/home/ubuntu/clinic_records/cr_backend/venv/bin/gunicorn \
    --workers 4 \
    --bind 0.0.0.0:8000 \
    --timeout 120 \
    --access-logfile /home/ubuntu/clinic_records/cr_backend/logs/gunicorn-access.log \
    --error-logfile /home/ubuntu/clinic_records/cr_backend/logs/gunicorn-error.log \
    --log-level info \
    config.wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

### 7.2. Configurar Nginx

```bash
sudo nano /etc/nginx/sites-available/clinidocs
```

**Contenido:**

```nginx
server {
    listen 80;
    server_name 52.0.69.138;
    client_max_body_size 100M;

    # Backend Django
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 120s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;
    }

    # Admin Django
    location /admin/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Archivos estáticos Django
    location /static/ {
        alias /home/ubuntu/clinic_records/cr_backend/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Archivos media (si no usas S3)
    location /media/ {
        alias /home/ubuntu/clinic_records/cr_backend/media/;
        expires 7d;
    }

    # Frontend (React/Vite)
    location / {
        proxy_pass http://127.0.0.1:5173;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support (para Vite HMR)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### 7.3. Activar Configuración Nginx

```bash
# Crear symlink
sudo ln -s /etc/nginx/sites-available/clinidocs /etc/nginx/sites-enabled/

# Eliminar default si existe
sudo rm /etc/nginx/sites-enabled/default

# Verificar configuración
sudo nginx -t

# Reiniciar Nginx
sudo systemctl restart nginx
```

### 7.4. Iniciar Gunicorn

```bash
# Habilitar e iniciar
sudo systemctl enable gunicorn
sudo systemctl start gunicorn

# Verificar estado
sudo systemctl status gunicorn

# Ver logs
tail -f ~/clinic_records/cr_backend/logs/gunicorn-error.log
```

---

## 🎨 PARTE 8: DEPLOY DEL FRONTEND

### 8.1. Configurar Frontend

```bash
cd ~/clinic_records/cr_frontend

# Instalar dependencias
npm install

# Crear archivo .env.production
nano .env.production
```

**Contenido:**

```bash
VITE_API_URL=http://52.0.69.138/api
VITE_STRIPE_PUBLIC_KEY=pk_test_XXXXXX
VITE_FIREBASE_CONFIG='{"apiKey":"...","projectId":"..."}'
```

### 8.2. Build de Producción (Opcional)

Si quieres servir con build estático en lugar de dev server:

```bash
# Build
npm run build

# Los archivos estarán en dist/
```

### 8.3. Ejecutar Frontend en Modo Dev (Temporal)

```bash
# Instalar pm2 (process manager)
sudo npm install -g pm2

# Iniciar frontend con pm2
pm2 start npm --name "frontend" -- run dev -- --host 0.0.0.0 --port 5173

# Guardar configuración de pm2
pm2 save

# Auto-start en reboot
pm2 startup
# Copiar y ejecutar el comando que aparece
```

---

## ✅ PARTE 9: PRUEBAS Y VERIFICACIÓN

### 9.1. Verificar Todos los Servicios

```bash
# Redis
sudo systemctl status redis-server
redis-cli ping

# Celery Worker
sudo systemctl status celery
tail -f ~/clinic_records/cr_backend/logs/celery.log

# Celery Beat
sudo systemctl status celerybeat
tail -f ~/clinic_records/cr_backend/logs/celerybeat.log

# Gunicorn
sudo systemctl status gunicorn
tail -f ~/clinic_records/cr_backend/logs/gunicorn-error.log

# Nginx
sudo systemctl status nginx
sudo nginx -t

# Frontend
pm2 status
pm2 logs frontend
```

### 9.2. Probar Endpoints

```bash
# Health check
curl http://52.0.69.138/api/health/

# Login (debe devolver tokens)
curl -X POST http://52.0.69.138/api/accounts/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@test.com","password":"admin123"}'
```

### 9.3. Probar Funcionalidades

#### A. Subir Documento y OCR

1. Ir a `http://52.0.69.138`
2. Login como doctor
3. Ir a paciente → Documentos → Subir archivo
4. Verificar que se sube a S3:
   ```bash
   aws s3 ls s3://clinidocs-files-2025/media/documents/
   ```
5. Ver logs de OCR:
   ```bash
   tail -f ~/clinic_records/cr_backend/logs/celery.log | grep textract
   ```

#### B. Notificaciones Push

1. Registrar FCM token desde la app móvil
2. Crear una notificación desde admin
3. Verificar logs:
   ```bash
   tail -f ~/clinic_records/cr_backend/logs/celery.log | grep firebase
   ```

#### C. Backup Automático

```bash
# Forzar ejecución de backup
cd ~/clinic_records/cr_backend
source venv/bin/activate
python manage.py shell

# En shell:
from apps.backup.tasks import crear_backup_automatico
result = crear_backup_automatico.delay()
print(result.get(timeout=60))
```

#### D. Stripe Checkout

1. Ir a Planes → Seleccionar plan
2. Click "Suscribirse"
3. Usar tarjeta de prueba: `4242 4242 4242 4242`
4. Ver webhook logs:
   ```bash
   stripe logs tail
   ```

---

## 📊 PARTE 10: MONITOREO Y LOGS

### 10.1. Ver Todos los Logs en Tiempo Real

```bash
# Crear script de monitoreo
nano ~/watch_all_logs.sh
```

```bash
#!/bin/bash
tail -f \
  ~/clinic_records/cr_backend/logs/app.log \
  ~/clinic_records/cr_backend/logs/errors.log \
  ~/clinic_records/cr_backend/logs/celery.log \
  ~/clinic_records/cr_backend/logs/gunicorn-error.log
```

```bash
chmod +x ~/watch_all_logs.sh
~/watch_all_logs.sh
```

### 10.2. Comandos de Monitoreo

```bash
# Estado de servicios
sudo systemctl status redis-server gunicorn celery celerybeat nginx

# Uso de recursos
htop  # (instalar: sudo apt install htop)

# Uso de disco
df -h

# Procesos de Celery
ps aux | grep celery

# Conexiones a Redis
redis-cli INFO | grep connected_clients

# Logs de Django en tiempo real
tail -f ~/clinic_records/cr_backend/logs/app.log

# Logs de errores
tail -f ~/clinic_records/cr_backend/logs/errors.log
```

### 10.3. Tareas de Celery Programadas

Ver el schedule de Celery Beat:

```bash
cd ~/clinic_records/cr_backend
source venv/bin/activate
python manage.py shell

# En shell:
from config.celery import app
print(app.conf.beat_schedule)
```

**Tareas programadas:**

- `backup-sistema-diario`: 2:00 AM diario
- `limpiar-backups-vencidos`: Domingo 3:00 AM
- `reintentar-notificaciones-fallidas`: Cada 6 horas
- `verificar-ocr-asincrono`: Cada 10 minutos

---

## 🛠️ TROUBLESHOOTING

### Error: "Connection refused" a Redis

```bash
# Verificar que Redis está corriendo
sudo systemctl status redis-server

# Reiniciar Redis
sudo systemctl restart redis-server

# Verificar conexión
redis-cli ping
```

### Error: Celery no procesa tareas

```bash
# Ver logs de Celery
tail -f ~/clinic_records/cr_backend/logs/celery.log

# Reiniciar worker
sudo systemctl restart celery

# Verificar workers activos
cd ~/clinic_records/cr_backend
source venv/bin/activate
celery -A config inspect active
```

### Error: OCR no funciona

```bash
# Verificar credenciales AWS
aws s3 ls  # Debe listar tus buckets

# Verificar permisos IAM
# El usuario debe tener TextractFullAccess

# Ver logs de Textract
tail -f ~/clinic_records/cr_backend/logs/celery.log | grep textract
```

### Error: Webhook de Stripe no recibe eventos

```bash
# Verificar Stripe CLI
stripe listen --forward-to http://52.0.69.138:8000/api/payments/stripe-webhook/

# Probar webhook manualmente
stripe trigger checkout.session.completed

# Ver logs
tail -f ~/clinic_records/cr_backend/logs/app.log | grep stripe
```

### Error: Notificaciones Push no llegan

```bash
# Verificar credenciales Firebase
cd ~/clinic_records/cr_backend
source venv/bin/activate
python manage.py shell

# En shell:
from firebase_admin import credentials, initialize_app
cred = credentials.Certificate('path/to/serviceAccountKey.json')
initialize_app(cred)  # No debe dar error

# Ver logs
tail -f ~/clinic_records/cr_backend/logs/celery.log | grep firebase
```

---

## ⚡ COMANDOS RÁPIDOS

### Reiniciar Todo

```bash
sudo systemctl restart redis-server
sudo systemctl restart gunicorn
sudo systemctl restart celery
sudo systemctl restart celerybeat
sudo systemctl restart nginx
pm2 restart frontend
```

### Ver Estado de Todo

```bash
sudo systemctl status redis-server gunicorn celery celerybeat nginx
pm2 status
```

### Actualizar Código

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

### Logs Importantes

```bash
# Aplicación
tail -f ~/clinic_records/cr_backend/logs/app.log

# Errores
tail -f ~/clinic_records/cr_backend/logs/errors.log

# Celery
tail -f ~/clinic_records/cr_backend/logs/celery.log

# Gunicorn
tail -f ~/clinic_records/cr_backend/logs/gunicorn-error.log

# Nginx
sudo tail -f /var/log/nginx/error.log
```

---

## 🎓 NOTAS PARA PROYECTO UNIVERSITARIO

### Stripe en Modo Test

- ✅ No requiere verificación de negocio
- ✅ Tarjetas de prueba ilimitadas
- ✅ Todos los features disponibles
- ✅ No se cobran comisiones
- ⚠️ Los pagos no son reales

### Mantener Costos en $0

- ✅ EC2: t2.micro (750 hrs/mes gratis)
- ✅ RDS: db.t2.micro (750 hrs/mes gratis)
- ✅ S3: 5GB gratis
- ✅ Textract: 1,000 páginas/mes gratis
- ✅ SendGrid: 100 emails/día gratis
- ✅ Stripe: Modo test gratis
- ✅ Firebase: Plan Spark gratis

### Demostración

Para tu presentación:

1. Mostrar dashboard en vivo
2. Subir documento → demostrar OCR automático
3. Procesar pago con Stripe test
4. Enviar notificación push a móvil
5. Mostrar backup automático en S3
6. Mostrar logs en tiempo real

---

## 📞 SOPORTE

Si tienes problemas:

1. Revisar logs: `~/clinic_records/cr_backend/logs/`
2. Verificar servicios: `sudo systemctl status`
3. Revisar .env: `nano ~/clinic_records/cr_backend/.env`
4. Documentación oficial de cada servicio

---

**¡Deployment Completo! 🎉**

Tu aplicación ahora está corriendo con:
✅ Django + Gunicorn + Nginx  
✅ PostgreSQL  
✅ Redis + Celery (workers + beat)  
✅ AWS S3 + Textract (OCR automático)  
✅ SendGrid (emails)  
✅ Stripe (pagos en modo test)  
✅ Firebase (notificaciones push)  
✅ Frontend en Vite

**URL:** http://52.0.69.138
