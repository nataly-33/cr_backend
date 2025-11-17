# 📋 RESUMEN DE CAMBIOS Y RECOMENDACIONES - DEPLOY PRODUCCIÓN

**Fecha:** Noviembre 2025  
**Estado:** Listo para deploy con todas las funcionalidades

---

## ✅ CAMBIOS REALIZADOS

### 1. Archivos de Configuración

#### ✅ `.env.production` - ACTUALIZADO

- ✅ Agregadas todas las variables de Redis/Celery
- ✅ Agregadas variables de Stripe (modo test)
- ✅ Agregadas variables de Firebase (push notifications)
- ✅ Documentación clara de cada sección

#### ✅ `.env.example` - ACTUALIZADO

- ✅ Guía completa para desarrolladores
- ✅ Instrucciones de cómo obtener cada credencial
- ✅ Valores por defecto seguros
- ✅ Comentarios explicativos

#### ✅ `config/settings/production.py` - CONSOLIDADO

- ✅ Eliminada duplicación con `base.py`
- ✅ Solo contiene overrides específicos de producción:
  - Security settings
  - Redis cache
  - Celery override
  - Logging completo
  - Rate limiting
- ✅ Hereda configuraciones de servicios desde `base.py`

#### ✅ `config/settings/base.py` - CENTRALIZADO

- ✅ Configuraciones compartidas (dev + prod):
  - AWS S3 + Textract
  - SendGrid (Email)
  - Stripe (Pagos)
  - Firebase (Push)
  - Celery base

#### ❌ `config/settings/production_aws.py` - ELIMINADO

- Ya no es necesario, todo está en `production.py`

---

## 🎯 ARQUITECTURA FINAL

```
config/settings/
├── base.py              # Configuración compartida (dev + prod)
│   ├── Django core
│   ├── Apps
│   ├── Middleware
│   ├── REST Framework
│   ├── JWT
│   ├── Celery (base)
│   ├── AWS S3 + Textract
│   ├── SendGrid
│   ├── Stripe
│   └── Firebase
│
├── development.py       # Solo para desarrollo local
│   └── Override DEBUG=True
│
├── production.py        # Solo para producción
│   ├── Security headers
│   ├── Redis cache
│   ├── Celery (override)
│   ├── Logging completo
│   └── Rate limiting
│
└── logging.py          # Configuración de logs (dev)
```

---

## 🔧 NUEVOS SERVICIOS EN DEPLOY

### 1. Redis (NUEVO)

**¿Por qué?** Cache + Broker de Celery

**Instalación en EC2:**

```bash
sudo apt install -y redis-server
sudo systemctl enable redis-server
sudo systemctl start redis-server
```

**Variables en `.env`:**

```bash
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

**Costo:** ✅ GRATIS (instalado localmente en EC2)

---

### 2. Celery (NUEVO)

**¿Por qué?** Tareas asíncronas (backups, OCR, notificaciones)

**Servicios a crear:**

- `celery.service` → Worker (procesa tareas)
- `celerybeat.service` → Scheduler (tareas programadas)

**Comandos en consola:**

```bash
# Ver tareas activas
celery -A config inspect active

# Ver tareas programadas
celery -A config inspect scheduled

# Ejecutar tarea manual
celery -A config call apps.backup.tasks.crear_backup_automatico
```

**Costo:** ✅ GRATIS (usa recursos de EC2)

---

### 3. AWS Textract (NUEVO - OCR Automático)

**¿Por qué?** Extracción automática de texto de documentos

**Usuario IAM necesario:**

- Permisos: `AmazonTextractFullAccess` + `AmazonS3FullAccess`

**Variables en `.env`:**

```bash
ENABLE_OCR=True
AWS_TEXTRACT_REGION=us-east-1
```

**Cómo funciona:**

1. Usuario sube PDF/imagen
2. Se guarda en S3
3. Celery envía a Textract
4. Textract extrae texto
5. Se guarda en base de datos

**Costo:** ✅ GRATIS (1,000 páginas/mes en Free Tier)

---

### 4. Stripe (NUEVO - Pagos en Modo Test)

**¿Por qué?** Sistema de suscripciones y pagos

**Modo Test vs Producción:**

- ✅ **Modo Test (Proyecto Universitario):**
  - No requiere verificación de negocio
  - Tarjetas de prueba ilimitadas
  - Todos los features disponibles
  - **Sin comisiones**
- ❌ **Modo Live (Producción Real):**
  - Requiere verificación de negocio
  - Solo tarjetas reales
  - Comisión ~3% por transacción

**Variables en `.env`:**

```bash
STRIPE_ENABLED=True
STRIPE_SECRET_KEY=sk_test_XXXXX     # Modo test
STRIPE_PUBLISHABLE_KEY=pk_test_XXXXX
STRIPE_WEBHOOK_SECRET=whsec_XXXXX
```

**Webhooks - 2 Opciones:**

#### Opción A: Stripe CLI (Desarrollo)

```bash
# Instalar en EC2
wget https://github.com/stripe/stripe-cli/releases/download/v1.19.0/stripe_1.19.0_linux_x86_64.tar.gz
tar -xzf stripe_1.19.0_linux_x86_64.tar.gz
sudo mv stripe /usr/local/bin/

# Forward webhooks
stripe listen --forward-to http://52.0.69.138:8000/api/payments/stripe-webhook/
```

#### Opción B: Dashboard de Stripe (Recomendado)

1. Ir a https://dashboard.stripe.com/test/webhooks
2. Add endpoint → `http://52.0.69.138:8000/api/payments/stripe-webhook/`
3. Seleccionar eventos: `checkout.session.completed`, etc.
4. Copiar signing secret

**Costo:** ✅ GRATIS en modo test

---

### 5. Firebase (NUEVO - Notificaciones Push)

**¿Por qué?** Enviar notificaciones a app móvil

**Variables en `.env`:**

```bash
FIREBASE_SERVER_KEY=BAS4HqTdL-2sz-FAf5vvz8USFuGY0D_9adOjmoV9cfSsxt4xokoX_U2ZFYjj47FeDDHJ6lNVpjg7v33e04S3fjY

FIREBASE_SERVICE_ACCOUNT_KEY='{"type":"service_account",...}'
```

**Cómo obtener credenciales:**

1. Firebase Console → Project Settings
2. Service Accounts → Generate New Private Key
3. Copiar todo el JSON en una sola línea

**Costo:** ✅ GRATIS (Plan Spark)

---

## 🔐 HTTPS vs HTTP

### Estado Actual: HTTP

Tu deploy actual usa **HTTP** (puerto 80).

### ¿Necesitas HTTPS?

**SÍ necesitas HTTPS si:**

- ✅ Stripe webhooks (solo en producción real)
- ✅ PWA (Progressive Web App)
- ✅ Service Workers
- ⚠️ Algunos navegadores bloquean ciertas APIs sin HTTPS

**NO necesitas HTTPS para:**

- ✅ Desarrollo/testing
- ✅ Proyecto universitario
- ✅ Firebase (funciona con HTTP)
- ✅ Stripe modo test (funciona con HTTP)

### Opciones para HTTPS:

#### Opción 1: No-IP + Let's Encrypt (GRATIS)

```bash
# 1. Registrar dominio gratis en No-IP
#    Ejemplo: clinidocs.ddns.net → 52.0.69.138

# 2. Instalar certbot
sudo apt install -y certbot python3-certbot-nginx

# 3. Obtener certificado
sudo certbot --nginx -d clinidocs.ddns.net

# 4. Actualizar .env
ALLOWED_HOSTS=clinidocs.ddns.net,52.0.69.138
CORS_ALLOWED_ORIGINS=https://clinidocs.ddns.net

# 5. Actualizar production.py
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

#### Opción 2: Elastic IP + Route 53 (PAGO)

- Costo: ~$0.50/mes (Elastic IP) + $0.50/mes (Route 53)

#### Opción 3: Cloudflare (GRATIS)

- Proxy HTTPS gratis
- Pero necesitas dominio propio

### Recomendación:

**Para proyecto universitario:** Mantener HTTP está bien.  
**Si quieres HTTPS:** Usar No-IP + Let's Encrypt (100% gratis).

---

## 👤 USUARIOS IAM NECESARIOS

### Usuario Actual:

✅ Ya tienes: Usuario con permisos S3

### Usuario Requerido (Actualizar):

❗ **ACTUALIZAR** el usuario existente para agregar Textract

**Nombre sugerido:** `clinidocs-s3-textract-user`

**Permisos necesarios:**

1. `AmazonS3FullAccess`
2. `AmazonTextractFullAccess` ← AGREGAR ESTE

**Cómo actualizar:**

1. AWS Console → IAM → Users
2. Seleccionar tu usuario actual
3. Permissions → Add permissions
4. Attach policies → Buscar "Textract"
5. Marcar `AmazonTextractFullAccess`
6. Add permissions

**NO necesitas:**

- ❌ Usuario separado para cada servicio
- ❌ Usuario para Stripe (usa API keys)
- ❌ Usuario para SendGrid (usa API keys)
- ❌ Usuario para Firebase (usa Service Account)

---

## 📦 DEPENDENCIAS ACTUALIZADAS

### Agregado a `requirements.txt`:

```
django-redis==5.4.0  # NUEVO - Cache con Redis
```

### Ya existentes (verificar):

```
celery==5.3.4
django-celery-beat==2.5.0
django-celery-results==2.5.1
redis==5.0.1
boto3==1.34.0  # AWS S3
stripe==13.2.0
firebase-admin==6.5.0
```

---

## 🚀 COMANDOS PARA ACTUALIZAR DEPLOY EXISTENTE

Si ya tienes un deploy funcionando, ejecuta estos comandos:

```bash
# 1. Conectar a EC2
ssh -i "clinidocs-key.pem" ubuntu@52.0.69.138

# 2. Actualizar código
cd ~/clinic_records/cr_backend
git pull

# 3. Activar entorno virtual
source venv/bin/activate

# 4. Instalar nuevas dependencias
pip install -r requirements.txt

# 5. Actualizar .env con nuevas variables
nano .env
# Agregar:
# REDIS_URL=redis://localhost:6379/0
# CELERY_BROKER_URL=redis://localhost:6379/0
# CELERY_RESULT_BACKEND=redis://localhost:6379/0
# ENABLE_OCR=True
# STRIPE_ENABLED=True
# (y las demás del .env.production)

# 6. Instalar Redis
sudo apt install -y redis-server
sudo systemctl enable redis-server
sudo systemctl start redis-server

# 7. Crear servicios de Celery
# (ver sección PARTE 5 del DEPLOY_COMPLETO_ACTUALIZADO.md)
sudo nano /etc/systemd/system/celery.service
sudo nano /etc/systemd/system/celerybeat.service

# 8. Recargar systemd y iniciar servicios
sudo systemctl daemon-reload
sudo systemctl enable celery celerybeat
sudo systemctl start celery celerybeat

# 9. Ejecutar migraciones (si hay nuevas)
python manage.py migrate

# 10. Reiniciar servicios
sudo systemctl restart gunicorn
sudo systemctl restart celery
sudo systemctl restart celerybeat

# 11. Verificar todo funciona
sudo systemctl status redis-server
sudo systemctl status celery
sudo systemctl status celerybeat
sudo systemctl status gunicorn
```

---

## 📊 VERIFICACIÓN POST-DEPLOY

### Checklist de Funcionalidades:

```bash
# 1. Backend funcionando
curl http://52.0.69.138/api/health/
# Debe responder: 200 OK

# 2. Redis funcionando
redis-cli ping
# Debe responder: PONG

# 3. Celery Worker funcionando
sudo systemctl status celery
# Debe estar: active (running)

# 4. Celery Beat funcionando
sudo systemctl status celerybeat
# Debe estar: active (running)

# 5. Ver tareas en cola
cd ~/clinic_records/cr_backend
source venv/bin/activate
celery -A config inspect active
# Debe listar workers activos

# 6. Probar OCR (subir documento desde frontend)
# Verificar en logs:
tail -f logs/celery.log | grep textract

# 7. Probar notificación push
# Desde admin, crear notificación
# Verificar en logs:
tail -f logs/celery.log | grep firebase

# 8. Probar Stripe
# Ir a /planes → Seleccionar plan → Pagar con 4242 4242 4242 4242
# Verificar webhook:
tail -f logs/app.log | grep stripe
```

---

## 💡 RECOMENDACIONES FINALES

### 1. Monitoreo

```bash
# Crear script de monitoreo
nano ~/monitor.sh
```

```bash
#!/bin/bash
echo "=== Estado de Servicios ==="
sudo systemctl status redis-server --no-pager | grep Active
sudo systemctl status gunicorn --no-pager | grep Active
sudo systemctl status celery --no-pager | grep Active
sudo systemctl status celerybeat --no-pager | grep Active
sudo systemctl status nginx --no-pager | grep Active

echo ""
echo "=== Workers de Celery ==="
cd ~/clinic_records/cr_backend
source venv/bin/activate
celery -A config inspect active

echo ""
echo "=== Tareas Programadas ==="
celery -A config inspect scheduled

echo ""
echo "=== Uso de Recursos ==="
free -h
df -h | grep -E 'Filesystem|/$'
```

```bash
chmod +x ~/monitor.sh
~/monitor.sh
```

### 2. Backup Automático

Ya está configurado en Celery Beat:

- Se ejecuta diariamente a las 2:00 AM
- Guarda en S3
- Limpia backups antiguos los domingos

### 3. Logs

Todos los logs están en: `~/clinic_records/cr_backend/logs/`

- `app.log` - Aplicación general
- `errors.log` - Solo errores
- `celery.log` - Tareas asíncronas
- `django.log` - Django core
- `gunicorn-error.log` - Servidor Gunicorn

### 4. Rotación de Logs

Ya está configurada en `production.py`:

- Max 10 MB por archivo
- 5 archivos de backup
- Rotación automática

---

## 🎓 PARA TU PRESENTACIÓN

### Demo Script:

1. **Mostrar Dashboard**

   - Login como doctor
   - Ver estadísticas en tiempo real

2. **Subir Documento + OCR**

   - Ir a paciente → Documentos
   - Subir PDF médico
   - Mostrar extracción automática de texto
   - Verificar en S3 (consola AWS)

3. **Procesar Pago**

   - Ir a Planes
   - Seleccionar plan Premium
   - Pagar con tarjeta test: `4242 4242 4242 4242`
   - Mostrar webhook recibido en logs

4. **Notificación Push**

   - Desde admin, crear notificación
   - Mostrar en app móvil
   - Ver logs de Firebase

5. **Backup Automático**

   - Ejecutar backup manual
   - Verificar en S3
   - Mostrar schedule de Celery Beat

6. **Logs en Tiempo Real**
   - `tail -f logs/app.log`
   - Hacer alguna acción
   - Mostrar log inmediato

---

## 📞 CONTACTO Y SOPORTE

Si tienes dudas durante el deploy:

1. Revisar logs primero
2. Verificar estado de servicios: `sudo systemctl status`
3. Consultar documentación específica de cada servicio

**Documentación completa:** `docs/deployment/DEPLOY_COMPLETO_ACTUALIZADO.md`

---

## ✅ RESUMEN EJECUTIVO

### Lo que YA tienes:

- ✅ EC2 con IP elástica
- ✅ PostgreSQL (RDS o local)
- ✅ S3 bucket
- ✅ Usuario IAM con S3 (actualizar para Textract)
- ✅ Backend funcionando con Gunicorn + Nginx

### Lo que FALTA agregar:

- ⚠️ Redis (instalar)
- ⚠️ Celery Worker + Beat (configurar servicios)
- ⚠️ Permisos de Textract (actualizar IAM)
- ⚠️ Stripe CLI (opcional, para webhooks)
- ⚠️ Variables de entorno nuevas (actualizar .env)

### Tiempo estimado para actualizar:

- **30 minutos** (si ya tienes deploy funcionando)
- **2 horas** (si es deploy desde cero)

### Costo mensual:

- **$0** (todo en Free Tier)

---

**¡Todo listo para deploy completo! 🚀**
