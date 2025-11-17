# ✅ INSTRUCCIONES FINALES - Redis + Celery

**Estado:** Todo está listo para instalar  
**Plataforma:** Windows PowerShell  
**Tiempo estimado:** 15-20 minutos

---

## 🎯 Lo que necesitas hacer:

### 1️⃣ Instalar Redis (elige 1 opción)

**Opción A: Directo en Windows (recomendado)**

```
1. Ir a: https://github.com/tporadowski/redis/releases
2. Descargar: Redis-x64-5.0.14.1.zip
3. Extraer en: C:\Redis
```

**Opción B: Docker (si prefieres)**

```powershell
docker run -d --name redis -p 6379:6379 redis:latest
```

### 2️⃣ Verificar que Redis funciona

Abre **PowerShell** y ejecuta:

```powershell
C:\users\rodri\downloads\instaladores\redis\redis-cli.exe ping
```

**Debe responder:** `PONG`

Si no funciona, reemplaza la ruta con donde extrajiste Redis. Ejemplo:

- Si lo extrajiste en `C:\Redis`: `C:\Redis\redis-cli.exe ping`
- Si lo extrajiste en otro lado: `ruta-donde-lo-extrajiste\redis-cli.exe ping`

### 3️⃣ Instalar dependencias Python

```powershell
cd d:\1NATALY\Proyectos\clinic_records\cr_backend
pip install redis celery python-dotenv
```

### 4️⃣ Ahora tienes 3 terminales abiertas (necesitas 3):

**Terminal 1 - Django:**

```powershell
cd d:\1NATALY\Proyectos\clinic_records\cr_backend
python manage.py runserver
```

**Terminal 2 - Celery Worker:**

```powershell
cd d:\1NATALY\Proyectos\clinic_records\cr_backend
.\venv\Scripts\Activate.ps1
celery -A config worker -l info --pool=solo
```

**Terminal 3 - Celery Beat:**

```powershell
cd d:\1NATALY\Proyectos\clinic_records\cr_backend
.\venv\Scripts\Activate.ps1
celery -A config beat -l info
```

### 5️⃣ Verificar que TODO funciona

```powershell
python test_firebase_quick.py
```

**Debe mostrar:**

```
✅ ALL TESTS PASSED!
```

---

## 🐧 PARA CUANDO HAGAS DEPLOY (Ubuntu EC2)

Cuando estés en tu instancia EC2 con Ubuntu:

```bash
# Instalar Redis
sudo apt update
sudo apt install redis-server -y
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Instalar Python
sudo apt install python3-pip python3-venv -y

# Clonar proyecto
cd /home/ubuntu
git clone https://github.com/tu-repo.git clinic_records
cd clinic_records/cr_backend

# Crear venv
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Crear servicios systemd (ver archivo SETUP_REDIS_CELERY_COMPLETE.md para los detalles)
sudo nano /etc/systemd/system/celery-worker.service
# (copiar contenido del archivo)

sudo systemctl enable celery-worker
sudo systemctl start celery-worker
sudo systemctl enable celery-beat
sudo systemctl start celery-beat
```

---

## ✨ Resumen visual:

```
┌─────────────────────────────────┐
│    Redis (almacena tareas)      │
│  redis-server.exe corriendo     │
└──────────────────┬──────────────┘
                   │
                   ↓
┌─────────────────────────────────┐
│   Celery Worker (procesa)       │
│  celery -A config worker...     │
└──────────────────┬──────────────┘
                   │
                   ↓
┌─────────────────────────────────┐
│  Celery Beat (programa tareas)  │
│  celery -A config beat...       │
└──────────────────┬──────────────┘
                   │
                   ↓
┌─────────────────────────────────┐
│  Django API (entra datos)       │
│  localhost:8000                 │
└─────────────────────────────────┘

TODO EJECUTÁNDOSE = ✅ Notificaciones funcionan
```

---

## 🆘 Si algo sale mal:

| Error                              | Solución                                           |
| ---------------------------------- | -------------------------------------------------- |
| `redis.exceptions.ConnectionError` | Ejecuta `redis-server` en otra terminal            |
| `PONG` no responde                 | Redis no está corriendo                            |
| `ModuleNotFoundError: celery`      | `pip install celery`                               |
| Worker no procesa                  | Verifica que esté corriendo en otra terminal       |
| Tareas no se ejecutan              | Asegúrate de tener Redis + Worker + Beat corriendo |

---

## 📁 Archivos a tener a mano:

- ✅ **`SETUP_REDIS_CELERY_COMPLETE.md`** ← Guía completa (Windows + Ubuntu)
- ✅ **`test_firebase_quick.py`** ← Test rápido
- ✅ **`run_celery_worker.ps1`** ← Script para worker
- ✅ **`run_celery_beat.ps1`** ← Script para beat

---

## ✅ Confirmar que está todo:

Después de ejecutar los 3 comandos, deberías ver:

```
Terminal 1 (Django):
Starting development server at http://127.0.0.1:8000/

Terminal 2 (Worker):
celery@NOMBRE-PC ready

Terminal 3 (Beat):
Starting Scheduler: django_celery_beat.schedulers
```

Si ves eso, **¡TODO FUNCIONA!** 🎉

---

## 🚀 Listo para ir a producción

Cuando hayas confirmado que funciona en local, el paso a Ubuntu/EC2 es sencillo:

1. Instalar Redis (apt-get)
2. Crear servicios systemd (copy-paste)
3. Listo, todo automático

**Más detalles en:** `SETUP_REDIS_CELERY_COMPLETE.md`

---

¿Dudas? Revisa los archivos de test:

- `test_firebase_quick.py` - Test de Firebase
- `test_celery.py` - Test de Celery
- `test_celery_diagnosis.py` - Diagnóstico completo
