# 🚀 CELERY + REDIS - QUICK START

## 🎯 ¿QUÉ SE IMPLEMENTÓ?

✅ **Celery 5.3** - Framework para tareas asincrónicas  
✅ **Redis** - Broker y result backend  
✅ **Celery Beat** - Scheduler para tareas programadas  
✅ **Flower** - Monitor UI para Celery  
✅ **Tasks para Notificaciones** - Envío de emails, push  
✅ **Tasks para Backup** - Backup automático, limpieza, restore  

---

## ⚡ INICIO RÁPIDO (5 minutos)

### Paso 1: Instalar Redis

**Windows (PowerShell):**
```powershell
# Opción A: Instalar con Chocolatey (si tienes)
choco install redis

# Opción B: Descargar desde GitHub
# https://github.com/microsoftarchive/redis/releases
# O usar WSL (Windows Subsystem for Linux)
```

**Linux/Mac:**
```bash
# Ubuntu/Debian
sudo apt install redis-server

# macOS
brew install redis
```

**Docker (recomendado):**
```bash
docker run -d -p 6379:6379 --name redis redis:latest
```

---

### Paso 2: Verificar que todo está configurado

```bash
# Test de Celery
python test_celery.py

# Output esperado:
# 1️⃣ Verificando conexión a Redis...
#    URL: redis://localhost:6379/0
#    ❌ Error: ... (Normal si Redis no está corriendo)
# 2️⃣ Verificando configuración de Celery...
#    ✅ Configuración de Celery cargada
# 3️⃣ Verificando tasks disponibles...
#    Total de tasks: 12+
```

---

### Paso 3: Ejecutar en 4 terminales diferentes

**Terminal 1 - Redis:**
```bash
redis-server
# O en Docker:
docker start redis
```

**Terminal 2 - Django Dev Server:**
```bash
python manage.py runserver
# Accede a: http://localhost:8000/api/
```

**Terminal 3 - Celery Worker:**
```powershell
# Windows PowerShell
.\run_celery_worker.ps1

# O manualmente:
celery -A config worker --loglevel=info --concurrency=4
```

**Terminal 4 - Celery Beat (opcional pero recomendado):**
```powershell
# Windows PowerShell
.\run_celery_beat.ps1

# O manualmente:
celery -A config beat --loglevel=info
```

**Terminal 5 - Celery Flower (monitor):**
```powershell
# Windows PowerShell
.\run_celery_flower.ps1

# O manualmente:
celery -A config flower --port=5555
```

Accede a: **http://localhost:5555** (Flower dashboard)

---

## 📊 ARQUITECTURA

```
┌─────────────────┐
│   Django Apps   │
│  (Vistas/APIs)  │
└────────┬────────┘
         │
         │ .delay() o .apply_async()
         │
         ▼
┌─────────────────────────────────┐
│      Celery Tasks Queue         │
│  (Redis como Broker)            │
└────────────┬────────────────────┘
             │
     ┌───────┴───────┐
     │               │
     ▼               ▼
┌──────────┐    ┌──────────┐
│ Worker 1 │    │ Worker N │
│(Process) │    │(Process) │
└──────────┘    └──────────┘
```

---

## 🎯 TAREAS IMPLEMENTADAS

### 📧 Notificaciones (apps/notifications/tasks.py)

```python
# Enviar email async
send_notification_email.delay(notification_id)

# Enviar push notification
send_notification_push.delay(notification_id)

# Batch de notificaciones
send_notifications_batch.delay([id1, id2], channel='email')

# Reintentar fallidas (cada 6 horas automático)
requeue_failed_notifications.delay()

# Limpiar antiguas (domingo 4:00 AM automático)
cleanup_old_notifications.delay()
```

### 💾 Backup (apps/backup/tasks.py)

```python
# Backup automático (diario 2:00 AM)
crear_backup_automatico.delay()

# Backup de un tenant
crear_backup_tenant.delay(tenant_id, includes_files=True)

# Limpiar backups vencidos (domingo 3:00 AM automático)
limpiar_backups_vencidos.delay()

# Restaurar backup
restaurar_backup.delay(job_id)
```

---

## 📅 TAREAS PROGRAMADAS (Beat Schedule)

Configuradas en `config/celery.py`:

| Tarea | Hora | Frecuencia |
|-------|------|-----------|
| Backup Sistema | 2:00 AM | Diarios |
| Limpiar Backups | 3:00 AM | Domingos |
| Reintentar Notificaciones | Cada 6h | Automático |
| Limpiar Notificaciones | 4:00 AM | Domingos |

---

## 🔍 MONITOREO

### Flower Dashboard
```
http://localhost:5555
```

**Funcionalidades:**
- ✓ Ver workers en vivo
- ✓ Historial de tareas ejecutadas
- ✓ Estadísticas y métricas
- ✓ Pool inspector
- ✓ Control de workers

### Comandos CLI

```bash
# Ver tasks en cola
celery -A config inspect active

# Ver workers conectados
celery -A config inspect active_queues

# Ver stats
celery -A config inspect stats

# Ver próximas tareas programadas
celery -A config inspect scheduled
```

---

## 🧪 PRUEBAS

### Test 1: Enviar email de prueba

```bash
python manage.py shell

from apps.notifications.models import Notification
from apps.notifications.tasks import send_notification_email
from apps.accounts.models import User

user = User.objects.first()
notif = Notification.objects.create(
    tenant=user.tenant,
    user=user,
    title="Test Email",
    body="This is a test notification",
    notification_type="system.alert",
    channel="email"
)

# Enviar async
result = send_notification_email.delay(str(notif.id))

# Ver resultado (esperar a que worker procese)
print(result.get(timeout=10))
```

### Test 2: Backup manual

```bash
python manage.py shell

from apps.backup.tasks import crear_backup_automatico

result = crear_backup_automatico.delay()
print(result.get(timeout=300))  # Esperar hasta 5 minutos
```

---

## ⚠️ TROUBLESHOOTING

### ❌ "Connection refused" (Redis no corre)

```bash
# Verificar que Redis está corriendo
redis-cli ping
# PONG = OK

# Si no funciona, inicia Redis
redis-server
```

### ❌ "No module named 'flower'"

```bash
pip install -r requirements.txt
# O específicamente:
pip install flower django-celery-beat
```

### ❌ Tasks no se ejecutan

1. ✓ Redis está corriendo (`redis-cli ping`)
2. ✓ Worker está corriendo (`celery -A config worker`)
3. ✓ Ver logs: agregar `--loglevel=debug`

### ❌ Beat schedule no funciona

1. ✓ Beat está corriendo (`celery -A config beat`)
2. ✓ Verificar schedule: `celery -A config inspect scheduled`
3. ✓ Worker debe estar corriendo también

---

## 📚 DOCUMENTACIÓN COMPLETA

- **Setup detallado:** `CELERY_SETUP_GUIDE.md`
- **Configuración de producción:** `CELERY_PRODUCTION_SETUP.md` (próximo)
- **Troubleshooting avanzado:** Ver logs con `--loglevel=debug`

---

## 🚀 PRÓXIMOS PASOS

1. ✅ **Celery + Redis funcionando** (COMPLETADO)
2. ⏳ **SendGrid para emails** (Sprint 2)
3. ⏳ **Backup a S3** (Sprint 2)
4. ⏳ **WebSockets para notificaciones RT** (Sprint 3)

---

**Última actualización:** 6 de Noviembre de 2025  
**Versión:** 1.0 - Production Ready  
**Estado:** ✅ COMPLETADO
