# 🔧 Guía de Configuración: Celery + Redis + Backup

Esta guía explica cómo configurar y ejecutar el sistema de tareas asíncronas (Celery) y backups automáticos.

---

## 📋 Requisitos Previos

### Windows:

1. **Redis** - Instalar y ejecutar Redis
2. **PostgreSQL** o **SQLite** - Base de datos
3. **Python 3.9+** con virtualenv activado

---

## 🚀 Instalación de Redis en Windows

### Opción 1: Usar Memurai (Recomendado para Windows)

```bash
# Descargar e instalar Memurai desde: https://www.memurai.com/
# Memurai es una versión de Redis optimizada para Windows
```

### Opción 2: Usar Redis en WSL

```bash
# En WSL (Ubuntu)
sudo apt update
sudo apt install redis-server
sudo service redis-server start
```

### Opción 3: Usar Docker

```bash
docker run -d -p 6379:6379 redis:alpine
```

---

## ⚙️ Configuración del Proyecto

### 1. Verificar Dependencias

Las dependencias ya están en `requirements.txt`:

```txt
celery==5.3.4
redis==5.0.1
boto3==1.34.0  # Para S3 (opcional)
```

Instalar si no están:

```bash
pip install celery redis boto3
```

### 2. Configurar Variables de Entorno

Editar `.env` o crear si no existe:

```env
# Redis (Celery broker)
REDIS_URL=redis://localhost:6379/0

# Opcional: Para backups en S3
USE_S3_BACKUP=False
# AWS_ACCESS_KEY_ID=tu_access_key
# AWS_SECRET_ACCESS_KEY=tu_secret_key
# AWS_STORAGE_BUCKET_NAME=tu_bucket
# AWS_S3_REGION_NAME=us-east-1

# Base de datos
DATABASE_ENGINE=sqlite  # o postgresql
DATABASE_NAME=db.sqlite3
```

---

## 🏃 Ejecutar Celery

Necesitas **3 terminales** simultáneas:

### Terminal 1: Django Server

```bash
cd cr_backend
python manage.py runserver
```

### Terminal 2: Celery Worker

```bash
cd cr_backend
celery -A config worker -l info --pool=solo
```

**Nota para Windows:** Usar `--pool=solo` en Windows. En Linux/Mac puedes omitirlo.

### Terminal 3: Celery Beat (Tareas Programadas)

```bash
cd cr_backend
celery -A config beat -l info
```

**Celery Beat** ejecuta las tareas programadas:
- Backup automático diario a las 2:00 AM
- Limpieza de backups antiguos los domingos a las 3:00 AM

---

## 🧪 Probar el Sistema

### 1. Verificar Celery

Desde Django shell:

```bash
python manage.py shell
```

```python
from config.celery import debug_task

# Ejecutar tarea de prueba
result = debug_task.delay()
print(f"Task ID: {result.id}")
print(f"Status: {result.status}")
```

### 2. Crear Backup Manual

```python
from apps.backup.tasks import crear_backup_automatico

# Ejecutar backup inmediatamente (sin Celery)
result = crear_backup_automatico()
print(result)
```

### 3. Crear Backup de Tenant Específico

```python
from apps.backup.tasks import crear_backup_tenant
from apps.tenants.models import Tenant

# Obtener primer tenant
tenant = Tenant.objects.first()

# Crear backup
result = crear_backup_tenant.delay(tenant.id)
print(f"Task ID: {result.id}")
```

### 4. Listar Backups

```python
from apps.backup.models import BackupJob

# Ver todos los backups
backups = BackupJob.objects.all().order_by('-created_at')

for backup in backups:
    print(f"ID: {backup.id}")
    print(f"Tenant: {backup.tenant.name if backup.tenant else 'Sistema'}")
    print(f"Estado: {backup.status}")
    print(f"Tamaño: {backup.backup_size_bytes / 1024 / 1024:.2f} MB")
    print(f"Ubicación: {backup.storage_location}")
    print("---")
```

### 5. Restaurar Backup

```python
from apps.backup.tasks import restaurar_backup

# Restaurar backup por ID
job_id = "uuid-del-backup"
result = restaurar_backup.delay(job_id)
print(result.get())
```

---

## 📊 API Endpoints para Backup

### Crear Backup

```http
POST /api/backup/jobs/
Content-Type: application/json
Authorization: Bearer {token}

{
  "backup_type": "full",
  "backup_scope": "tenant",
  "includes_files": true
}
```

### Listar Backups

```http
GET /api/backup/jobs/
Authorization: Bearer {token}
```

### Restaurar Backup

```http
POST /api/backup/jobs/{id}/restore/
Authorization: Bearer {token}
```

---

## 🔍 Monitoreo de Celery

### Ver Tareas en Ejecución

```bash
celery -A config inspect active
```

### Ver Tareas Registradas

```bash
celery -A config inspect registered
```

### Ver Estadísticas

```bash
celery -A config inspect stats
```

### Flower (UI Web para Celery) - Opcional

```bash
pip install flower
celery -A config flower
```

Abrir: http://localhost:5555

---

## 🐛 Troubleshooting

### Error: "Redis connection refused"

**Solución:** Verificar que Redis está corriendo

```bash
# Windows (Memurai)
# Abrir "Services" y buscar "Memurai"

# WSL
sudo service redis-server status
sudo service redis-server start

# Docker
docker ps | grep redis
```

### Error: "pg_dump command not found"

**Solución:** Agregar PostgreSQL a PATH

```bash
# Windows: Agregar a PATH
C:\Program Files\PostgreSQL\15\bin
```

### Error: "ModuleNotFoundError: No module named 'celery'"

**Solución:** Instalar dependencias

```bash
pip install -r requirements.txt
```

### Tareas no se ejecutan

**Solución:** Verificar que Celery worker está corriendo

```bash
# Ver logs del worker
celery -A config worker -l debug --pool=solo
```

---

## 📦 Configuración de S3 (Opcional)

Si quieres guardar backups en AWS S3:

### 1. Crear Bucket S3

- Ir a AWS Console → S3
- Crear nuevo bucket
- Habilitar encriptación

### 2. Crear IAM User

- Ir a IAM → Users → Create User
- Attach policy: `AmazonS3FullAccess` (o crear policy personalizada)
- Copiar Access Key ID y Secret Access Key

### 3. Configurar `.env`

```env
USE_S3_BACKUP=True
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_STORAGE_BUCKET_NAME=clinidocs-backups
AWS_S3_REGION_NAME=us-east-1
```

---

## ✅ Verificación Final

Checklist para confirmar que todo funciona:

- [ ] Redis está corriendo
- [ ] Celery worker está corriendo sin errores
- [ ] Celery beat está corriendo
- [ ] Se puede crear un backup manual
- [ ] El backup se guarda correctamente
- [ ] Se puede listar los backups desde la API
- [ ] Se puede restaurar un backup

---

## 📚 Tareas Programadas (Crontab)

Configuradas en `config/celery.py`:

| Tarea | Frecuencia | Horario |
|-------|------------|---------|
| `crear_backup_automatico` | Diario | 2:00 AM |
| `limpiar_backups_vencidos` | Semanal (Domingo) | 3:00 AM |

---

## 🎯 Próximos Pasos

1. **Producción:** Usar supervisor o systemd para mantener Celery corriendo
2. **Monitoreo:** Configurar Flower para monitoreo web
3. **Alertas:** Configurar notificaciones por email en caso de fallos
4. **S3:** Configurar backups automáticos a S3 para mayor seguridad

---

**Última actualización:** 3 de Noviembre de 2025
