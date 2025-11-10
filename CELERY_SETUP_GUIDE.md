# 🚀 CELERY + REDIS - GUÍA DE EJECUCIÓN

## 📋 Requisitos Previos

- ✅ Redis instalado y funcionando
- ✅ Dependencias: `celery==5.3.4` y `redis==5.0.1` (ya en requirements.txt)
- ✅ PostgreSQL o SQLite configurado
- ✅ Entorno virtual Python 3.11+

---

## 1️⃣ INSTALACIÓN

### 1.1 Redis (Windows)

**Opción A: WSL (Recomendado)**
```bash
# Dentro de WSL
sudo apt install redis-server
redis-server
```

**Opción B: Windows Native**
```powershell
# Descargar desde https://github.com/microsoftarchive/redis/releases
# O usar chocolatey:
choco install redis
redis-server
```

**Opción C: Docker**
```bash
docker run -d -p 6379:6379 redis:latest
```

### 1.2 Dependencias Python

```bash
pip install -r requirements.txt
# Ya incluye:
# - celery==5.3.4
# - redis==5.0.1
```

---

## 2️⃣ ESTRUCTURA DE CELERY

```
config/
├── celery.py          ← Configuración maestr
├── __init__.py        ← Importación automática
└── settings/
    └── base.py        ← CELERY_BROKER_URL, CELERY_RESULT_BACKEND

apps/
├── notifications/
│   └── tasks.py       ← 3 tasks: send_email, send_push, cleanup
├── backup/
│   └── tasks.py       ← 4 tasks: backup_auto, limpiar, restaurar, etc.
└── [otros]/
    └── tasks.py       ← Tus tasks personalizadas
```

---

## 3️⃣ EJECUCIÓN EN DESARROLLO

### 3.1 Terminal 1: Redis

```bash
# Windows (PowerShell)
redis-server

# Linux/Mac
redis-server

# Docker
docker run -d -p 6379:6379 redis:latest
```

**Verificar que funciona:**
```bash
redis-cli
> ping
PONG  ✓
> exit
```

### 3.2 Terminal 2: Django Dev Server

```bash
python manage.py runserver
# Accede a http://localhost:8000/api/
```

### 3.3 Terminal 3: Celery Worker

**Windows (PowerShell):**
```powershell
.\run_celery_worker.ps1
```

**Linux/Mac:**
```bash
celery -A config worker \
    --loglevel=info \
    --concurrency=4 \
    --queues=celery,backups,notifications
```

**Esperado:**
```
[2025-11-06 10:30:00,000: INFO/MainProcess] Connected to redis://localhost:6379/0
[2025-11-06 10:30:00,500: INFO/MainProcess] mingle: searching for executable celery script in /path/to/bin
[2025-11-06 10:30:00,600: WARNING/MainProcess] celery@DESKTOP-ABC ready.
 ---------- celery@DESKTOP-ABC v5.3.4 (emerald-rush)
--- ***** -----
-- ******* ----
- *** --- * ---
- ** ---------- [config]
- ** ----------
- ** ---------- Queues
  celery
  backups
  notifications
```

### 3.4 Terminal 4: Celery Beat (Scheduler)

```powershell
.\run_celery_beat.ps1
```

o

```bash
celery -A config beat \
    --loglevel=info \
    --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

**Esperado:**
```
[2025-11-06 10:30:05,000: INFO/MainProcess] beat: Initial
[2025-11-06 10:30:05,100: INFO/MainProcess] Scheduler: DatabaseScheduler
[2025-11-06 10:30:05,200: INFO/MainProcess] Celery Beat v5.3.4 is started.
[2025-11-06 10:30:05,300: INFO/MainProcess] Scheduler: Adding Entries
```

### 3.5 Terminal 5: Celery Flower (Monitor)

```powershell
.\run_celery_flower.ps1
```

o

```bash
celery -A config flower \
    --broker=redis://localhost:6379/0 \
    --port=5555
```

**Accede a:**
```
http://localhost:5555
```

---

## 4️⃣ PRUEBAS

### 4.1 Verificar que Celery funciona

**En Django shell:**
```bash
python manage.py shell

from config.celery import app
# Ver tasks disponibles
app.tasks
# Output: {
#   'apps.backup.tasks.crear_backup_automatico': <@task>,
#   'apps.notifications.tasks.send_notification_email': <@task>,
#   ...
# }
```

### 4.2 Enviar tarea de prueba

```bash
python manage.py shell

from apps.notifications.tasks import send_notification_email
from apps.notifications.models import Notification
from apps.accounts.models import User

# Crear notificación
user = User.objects.first()
notif = Notification.objects.create(
    tenant=user.tenant,
    user=user,
    title="Test",
    body="Test notification",
    notification_type="system.alert",
    channel="email"
)

# Enviar async con Celery
result = send_notification_email.delay(str(notif.id))

# Ver resultado
result.get(timeout=30)
# Output: {'success': True, 'notification_id': '...', 'recipient': 'user@example.com'}
```

### 4.3 Ver tasks en Flower

Abre **http://localhost:5555** y verás:
- ✅ Workers conectados
- ✅ Tasks ejecutadas
- ✅ Pool de workers
- ✅ Estadísticas en tiempo real

---

## 5️⃣ TAREAS DISPONIBLES

### 5.1 Notificaciones

```python
from apps.notifications.tasks import (
    send_notification_email,
    send_notification_push,
    send_notifications_batch,
    requeue_failed_notifications,
    cleanup_old_notifications
)

# Enviar email (async)
result = send_notification_email.delay(notification_id)

# Enviar batch
result = send_notifications_batch.delay([id1, id2, id3], channel='email')

# Reintentar fallidas (programada cada 6 horas)
result = requeue_failed_notifications.delay(max_age_hours=24)
```

### 5.2 Backup

```python
from apps.backup.tasks import (
    crear_backup_automatico,
    crear_backup_tenant,
    limpiar_backups_vencidos,
    restaurar_backup
)

# Backup automático del sistema (programado 2:00 AM)
result = crear_backup_automatico.delay()

# Backup de un tenant específico
result = crear_backup_tenant.delay(tenant_id, includes_files=True)

# Restaurar
result = restaurar_backup.delay(job_id)
```

---

## 6️⃣ TAREAS PROGRAMADAS (Beat Schedule)

Configuradas en `config/celery.py`:

| Tarea | Schedule | Descripción |
|-------|----------|-------------|
| `backup-sistema-diario` | 2:00 AM diarios | Backup completo del sistema |
| `limpiar-backups-vencidos` | Domingo 3:00 AM | Limpia backups expirados |
| `reintentar-notificaciones-fallidas` | Cada 6 horas | Reintenta emails fallidos |
| `limpiar-notificaciones-antiguas` | Domingo 4:00 AM | Archiva notificaciones viejas |

### Ejecutar manualmente (sin esperar schedule):

```bash
python manage.py shell

from apps.backup.tasks import crear_backup_automatico
result = crear_backup_automatico.delay()
result.get()  # Esperar resultado
```

---

## 7️⃣ TROUBLESHOOTING

### ❌ "Connection refused redis://localhost:6379"

```bash
# Verificar que Redis está corriendo
redis-cli ping
# Debería devolver: PONG

# Si no:
redis-server  # Iniciarlo
```

### ❌ "No module named 'celery'"

```bash
pip install celery redis
# O reinstalar todo
pip install -r requirements.txt
```

### ❌ Tasks no se ejecutan

1. Verificar que worker está corriendo (Terminal 3)
2. Verificar que broker está disponible (Redis)
3. Ver logs del worker: `--loglevel=debug`
4. Usar Flower para diagnosticar: http://localhost:5555

### ❌ Tareas programadas no se ejecutan

1. Verificar que Beat está corriendo (Terminal 4)
2. Ver logs de Beat: `--loglevel=debug`
3. Verificar schedule en `config/celery.py`
4. Usar: `celery -A config inspect scheduled` para ver próximas tareas

---

## 8️⃣ MONITOREO

### Comandos útiles

```bash
# Ver tasks disponibles
celery -A config inspect active

# Ver workers conectados
celery -A config inspect active_queues

# Ver estadísticas
celery -A config inspect stats

# Detener un worker
celery -A config control shutdown
```

### Flower UI

Accede a http://localhost:5555:
- **Tasks**: Ver tareas ejecutadas
- **Workers**: Estado de workers
- **Pool**: Inspeccionar pool de workers
- **Queues**: Ver colas y prioritarios
- **Settings**: Configuración de workers

---

## 9️⃣ CONFIGURACIÓN DE PRODUCCIÓN

Ver: `CELERY_PRODUCTION_SETUP.md` (próximo documento)

---

## 🔟 SIGUIENTE PASO

Una vez Celery esté funcionando:

1. ✅ Probar envío de emails con SendGrid
2. ✅ Configurar backup automático a S3
3. ✅ Integrar notificaciones en tiempo real (WebSockets)
4. ✅ Deploy en producción

---

**Última actualización:** 6 de Noviembre de 2025
**Versión:** 1.0 - Producción Ready
