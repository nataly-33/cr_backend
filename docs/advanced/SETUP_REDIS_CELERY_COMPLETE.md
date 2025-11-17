# 🚀 SETUP COMPLETO: Redis + Celery

**Para:** Windows (PowerShell) + Ubuntu (EC2/Deploy)  
**Propósito:** Instalar y ejecutar Redis + Celery para tareas async  
**Estado:** ✅ Ready to use

---

## 📋 ¿Qué necesitas?

| Componente      | Qué es                                    | Necesario |
| --------------- | ----------------------------------------- | --------- |
| **Redis**       | Base de datos que almacena tareas en cola | ✅ SÍ     |
| **Celery**      | Worker que ejecuta las tareas             | ✅ SÍ     |
| **Celery Beat** | Scheduler de tareas programadas           | ✅ SÍ     |

**Sin esto NO funcionan:**

- ❌ Notificaciones push (FCM)
- ❌ OCR automático
- ❌ Backups automáticos
- ❌ Envío de emails

---

## 🪟 WINDOWS - PowerShell

### Paso 1: Instalar Redis (Opción A: Directo en Windows)

**Descargar:**

```
https://github.com/tporadowski/redis/releases
↓
Buscar: Redis-x64-5.0.14.1.zip
↓
Descargar y extraer a: C:\Redis
```

**Verificar que funciona:**

```powershell
C:\Redis\redis-server.exe
# Debería mostrar: Ready to accept connections
```

### Paso 2: Instalar Redis (Opción B: Docker - más fácil)

Si prefieres no instalar nada en Windows:

```powershell
# Instalar Docker desde: https://www.docker.com/products/docker-desktop

# Luego ejecutar Redis en Docker:
docker run -d --name redis -p 6379:6379 redis:latest

# Verificar:
docker ps
```

### Paso 3: Iniciar Redis

**Opción A (Instalación directa):**

```powershell
C:\Redis\redis-server.exe
```

**Opción B (Docker):**

```powershell
docker start redis
```

**Verificar en otra terminal:**

```powershell
redis-cli ping
# Debería responder: PONG
```

### Paso 4: Instalar dependencias Python

Ya están en `requirements.txt`, pero instalalas:

```powershell
cd d:\1NATALY\Proyectos\clinic_records\cr_backend
pip install redis celery
```

### Paso 5: Ejecutar Celery Worker

**En terminal nueva:**

```powershell
cd d:\1NATALY\Proyectos\clinic_records\cr_backend
.\venv\Scripts\Activate.ps1

celery -A config worker -l info --pool=solo
```

**⚠️ IMPORTANTE:** Usa `--pool=solo` en Windows (requerido)

### Paso 6: Ejecutar Celery Beat (Tareas programadas)

**En terminal OTRA:**

```powershell
cd d:\1NATALY\Proyectos\clinic_records\cr_backend
.\venv\Scripts\Activate.ps1

celery -A config beat -l info
```

### Verificar todo funciona:

```powershell
python test_firebase_quick.py
# Debería mostrar: ✅ ALL TESTS PASSED
```

---

## 🐧 UBUNTU (EC2 Deploy)

### Paso 1: Instalar Redis

```bash
sudo apt update
sudo apt install redis-server -y
```

### Paso 2: Iniciar Redis (permanente)

```bash
sudo systemctl start redis-server
sudo systemctl enable redis-server   # Inicia automáticamente

# Verificar:
sudo systemctl status redis-server
```

### Paso 3: Instalar Python + dependencias

```bash
sudo apt install python3-pip python3-venv -y

cd /home/ubuntu/clinic_records/cr_backend
python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
```

### Paso 4: Crear servicio Systemd para Celery Worker

**Archivo:** `/etc/systemd/system/celery-worker.service`

```bash
sudo nano /etc/systemd/system/celery-worker.service
```

**Copiar y pegar:**

```ini
[Unit]
Description=Celery Worker for ClinIDocs
After=network.target redis-server.service

[Service]
Type=forking
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/clinic_records/cr_backend
Environment="PATH=/home/ubuntu/clinic_records/cr_backend/venv/bin"
ExecStart=/home/ubuntu/clinic_records/cr_backend/venv/bin/celery -A config worker \
    --logfile=/var/log/celery/worker.log \
    --pidfile=/var/run/celery/worker.pid \
    --loglevel=info \
    --concurrency=4

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Crear directorios de logs:**

```bash
sudo mkdir -p /var/log/celery
sudo mkdir -p /var/run/celery
sudo chown ubuntu:ubuntu /var/log/celery
sudo chown ubuntu:ubuntu /var/run/celery
```

**Habilitar y iniciar:**

```bash
sudo systemctl daemon-reload
sudo systemctl enable celery-worker
sudo systemctl start celery-worker

# Verificar:
sudo systemctl status celery-worker
```

### Paso 5: Crear servicio Systemd para Celery Beat

**Archivo:** `/etc/systemd/system/celery-beat.service`

```bash
sudo nano /etc/systemd/system/celery-beat.service
```

**Copiar y pegar:**

```ini
[Unit]
Description=Celery Beat Scheduler for ClinIDocs
After=network.target redis-server.service

[Service]
Type=simple
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/clinic_records/cr_backend
Environment="PATH=/home/ubuntu/clinic_records/cr_backend/venv/bin"
ExecStart=/home/ubuntu/clinic_records/cr_backend/venv/bin/celery -A config beat \
    --logfile=/var/log/celery/beat.log \
    --loglevel=info \
    --scheduler django_celery_beat.schedulers:DatabaseScheduler

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Habilitar y iniciar:**

```bash
sudo systemctl daemon-reload
sudo systemctl enable celery-beat
sudo systemctl start celery-beat

# Verificar:
sudo systemctl status celery-beat
```

### Paso 6: Ver logs

```bash
# Worker logs
tail -f /var/log/celery/worker.log

# Beat logs
tail -f /var/log/celery/beat.log
```

---

## ✅ CHECKLIST de Verificación

### Windows:

- [ ] Redis corriendo (`redis-cli ping` → `PONG`)
- [ ] Terminal 1: Django corriendo (`python manage.py runserver`)
- [ ] Terminal 2: Celery Worker corriendo (`celery -A config worker...`)
- [ ] Terminal 3: Celery Beat corriendo (`celery -A config beat...`)
- [ ] Test pasa: `python test_firebase_quick.py` ✅

### Ubuntu:

- [ ] Redis enabled: `sudo systemctl status redis-server`
- [ ] Worker service: `sudo systemctl status celery-worker`
- [ ] Beat service: `sudo systemctl status celery-beat`
- [ ] Logs visible: `tail -f /var/log/celery/worker.log`

---

## 🧪 Test Rápido

Verificar que todo funciona:

```bash
cd cr_backend
python manage.py shell
```

```python
from config.celery import app

# Test 1: Ver tareas
print(f"Total tareas: {len(app.tasks)}")

# Test 2: Enviar tarea de prueba
result = app.send_task('celery.debug')
print(f"Task ID: {result.id}")
print("Debería haber ejecutado en Celery Worker")
```

Si ves `✅ ALL TESTS PASSED`, todo funciona.

---

## 🚨 Troubleshooting

| Error                                                 | Solución                                                           |
| ----------------------------------------------------- | ------------------------------------------------------------------ |
| `redis.exceptions.ConnectionError`                    | Redis no está corriendo. Ejecuta: `redis-server`                   |
| `Connection refused`                                  | Verifica que Redis esté en puerto 6379: `netstat -an \| grep 6379` |
| `[Errno 10048] Only one usage of each socket address` | Puerto ya está en uso. Cambia a otro puerto o mata el proceso      |
| `ModuleNotFoundError: celery`                         | Instala: `pip install celery`                                      |
| Tareas no se ejecutan                                 | Verifica que Celery Worker está corriendo en otra terminal         |

---

## 📊 Diagrama de Flujo

```
┌─────────────────────────────────────────────────┐
│           FLUJO DE TAREAS ASYNC                 │
└─────────────────────────────────────────────────┘

Django App
  ↓
  send_task('nombre_tarea')
  ↓
Redis (almacena en cola)
  ↓
Celery Worker (procesa)
  ↓
Ejecuta tarea (OCR, email, push, etc)
  ↓
Resultado guardado en Redis
  ↓
Frontend obtiene resultado
```

---

## 🎯 Próximas tareas

Después de instalar Redis + Celery:

1. **Verificar que funcionan las notificaciones FCM** (con Luis)
2. **Verificar que funciona el OCR automático**
3. **Verificar que se crean backups automáticos**
4. **Configurar Flower para monitoreo** (opcional en producción)

---

## 📚 Comandos Útiles

### Windows (PowerShell)

```powershell
# Ver si Redis está corriendo
redis-cli ping

# Ver si Celery está procesando tareas
celery -A config inspect active

# Ver todas las tareas registradas
celery -A config inspect registered
```

### Ubuntu

```bash
# Ver estado de Redis
sudo systemctl status redis-server

# Ver estado de Celery Worker
sudo systemctl status celery-worker

# Ver logs en tiempo real
tail -f /var/log/celery/worker.log

# Reiniciar servicios
sudo systemctl restart celery-worker
sudo systemctl restart celery-beat
```

---

## ✨ Diagrama de lo que pasará

```
Tu PC (Windows)
│
├── Redis ✅ (almacena tareas en cola)
│   │
│   └─ PORT 6379
│
├── Django API ✅ (localhost:8000)
│   │
│   └─ Envia tareas a Redis
│
├── Celery Worker ✅ (procesa)
│   │
│   └─ Toma tareas de Redis
│
├── Celery Beat ✅ (programador)
│   │
│   └─ Ejecuta tareas a horarios
│
└─ RESULTADO ✅
   ├─ Notificaciones push funcionan
   ├─ OCR automático funciona
   ├─ Backups automáticos funcionan
   └─ Tareas programadas funcionan
```

## ✨ Estado Final

Una vez completado:

✅ Redis corriendo  
✅ Celery Worker procesando tareas  
✅ Celery Beat ejecutando tareas programadas  
✅ Notificaciones FCM funcionando  
✅ OCR automático funcionando  
✅ Backups automáticos funcionando

**Listo para producción** 🚀

---

_Última actualización: 17 Nov 2025_  
_Compatible: Windows + Ubuntu EC2_  
_Estado: Production Ready_
