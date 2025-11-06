# 🚀 COMANDOS RÁPIDOS - DEPLOYMENT

## 📌 REFERENCIA RÁPIDA

### 🔌 Conectar a EC2

```bash
# Windows PowerShell
ssh -i "tu-archivo.pem" ubuntu@3.85.212.201

# Si da error de permisos en Windows:
icacls "tu-archivo.pem" /inheritance:r
icacls "tu-archivo.pem" /grant:r "$($env:USERNAME):(R)"
```

---

## 🐛 TROUBLESHOOTING

### Ver logs del backend en tiempo real

```bash
sudo journalctl -u clinidocs-backend -f
```

### Ver últimas 100 líneas de logs del backend

```bash
sudo journalctl -u clinidocs-backend -n 100
```

### Ver logs de Nginx

```bash
# Error log
sudo tail -f /var/log/nginx/error.log

# Access log
sudo tail -f /var/log/nginx/access.log
```

### Ver logs de Gunicorn

```bash
cd ~/clinic_records/cr_backend
tail -f logs/gunicorn-error.log
tail -f logs/gunicorn-access.log
```

---

## 🔄 REINICIAR SERVICIOS

### Reiniciar backend

```bash
sudo systemctl restart clinidocs-backend
```

### Reiniciar Nginx

```bash
sudo systemctl restart nginx
```

### Reiniciar ambos

```bash
sudo systemctl restart clinidocs-backend nginx
```

---

## 📊 VERIFICAR ESTADO

### Estado del backend

```bash
sudo systemctl status clinidocs-backend
```

### Estado de Nginx

```bash
sudo systemctl status nginx
```

### Estado de ambos

```bash
sudo systemctl status clinidocs-backend nginx
```

---

## 🔧 COMANDOS DJANGO

### Acceder al shell Django

```bash
cd ~/clinic_records/cr_backend
source venv/bin/activate
python manage.py shell
```

### Ejecutar migraciones

```bash
cd ~/clinic_records/cr_backend
source venv/bin/activate
python manage.py migrate
```

### Crear superusuario

```bash
cd ~/clinic_records/cr_backend
source venv/bin/activate
python manage.py createsuperuser
```

### Ejecutar seeder

```bash
cd ~/clinic_records/cr_backend
source venv/bin/activate
python run_seeder.py
```

### Recolectar archivos estáticos

```bash
cd ~/clinic_records/cr_backend
source venv/bin/activate
python manage.py collectstatic --noinput
```

---

## 📦 ACTUALIZAR CÓDIGO

### Actualizar backend

```bash
cd ~/clinic_records/cr_backend
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart clinidocs-backend
```

### Actualizar frontend

```bash
cd ~/clinic_records/cr_frontend
git pull origin main
npm install
npm run build
sudo systemctl restart nginx
```

### Actualizar ambos (script completo)

```bash
cd ~/clinic_records

# Pull latest
git pull origin main

# Backend
cd cr_backend
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput

# Frontend
cd ../cr_frontend
npm install
npm run build

# Restart services
sudo systemctl restart clinidocs-backend nginx

echo "✅ Actualización completada"
```

---

## 🗄️ BASE DE DATOS

### Conectar a PostgreSQL desde EC2

```bash
psql -h clinidocs-db.cexccmuycswr.us-east-1.rds.amazonaws.com \
     -U clinidocs_user \
     -d clinidocs_db
```

Password: `clinicdocs_pass_123*`

### Hacer backup de la base de datos

```bash
pg_dump -h clinidocs-db.cexccmuycswr.us-east-1.rds.amazonaws.com \
        -U clinidocs_user \
        -d clinidocs_db \
        -F c \
        -f backup_$(date +%Y%m%d_%H%M%S).dump
```

### Restaurar backup

```bash
pg_restore -h clinidocs-db.cexccmuycswr.us-east-1.rds.amazonaws.com \
           -U clinidocs_user \
           -d clinidocs_db \
           -c \
           backup_20250105_120000.dump
```

---

## 📁 ARCHIVOS Y PERMISOS

### Ver espacio en disco

```bash
df -h
```

### Ver uso de carpeta

```bash
du -sh ~/clinic_records/*
```

### Limpiar logs antiguos

```bash
# Limpiar logs de Nginx mayores a 7 días
sudo find /var/log/nginx -type f -mtime +7 -delete

# Limpiar logs de Gunicorn mayores a 7 días
find ~/clinic_records/cr_backend/logs -type f -mtime +7 -delete
```

### Permisos correctos para archivos

```bash
# Backend
cd ~/clinic_records/cr_backend
chmod 755 deploy.sh
chmod 644 .env

# Logs escribibles
chmod -R 755 logs/
```

---

## 🌐 NGINX

### Test de configuración

```bash
sudo nginx -t
```

### Recargar configuración sin downtime

```bash
sudo nginx -s reload
```

### Ver configuración activa

```bash
cat /etc/nginx/sites-enabled/clinidocs
```

### Editar configuración

```bash
sudo nano /etc/nginx/sites-available/clinidocs
sudo nginx -t
sudo systemctl restart nginx
```

---

## 🔐 SEGURIDAD

### Ver usuarios conectados

```bash
who
w
```

### Ver últimos logins

```bash
last -10
```

### Ver intentos fallidos de SSH

```bash
sudo grep "Failed password" /var/log/auth.log | tail -20
```

### Cambiar password de usuario ubuntu

```bash
sudo passwd ubuntu
```

---

## 📈 MONITOREO

### Ver uso de CPU y RAM en tiempo real

```bash
top
# Presionar 'q' para salir
```

### Ver procesos de Python/Gunicorn

```bash
ps aux | grep gunicorn
ps aux | grep python
```

### Ver conexiones de red

```bash
sudo netstat -tlnp
```

### Ver puertos abiertos

```bash
sudo ss -tulpn
```

---

## 🧹 LIMPIEZA Y MANTENIMIENTO

### Limpiar paquetes no usados

```bash
sudo apt autoremove -y
sudo apt autoclean
```

### Limpiar archivos temporales

```bash
sudo rm -rf /tmp/*
```

### Verificar actualizaciones disponibles

```bash
sudo apt update
sudo apt list --upgradable
```

### Aplicar actualizaciones de seguridad

```bash
sudo apt update
sudo apt upgrade -y
```

---

## 🚨 EMERGENCY

### Detener todo

```bash
sudo systemctl stop clinidocs-backend
sudo systemctl stop nginx
```

### Ver procesos que usan puerto 8000

```bash
sudo lsof -i :8000
```

### Matar proceso en puerto 8000

```bash
sudo kill -9 $(sudo lsof -t -i:8000)
```

### Reinicio completo del servidor

```bash
sudo reboot
# Esperar 1-2 minutos y reconectar
```

---

## 📊 MÉTRICAS RÁPIDAS

### Ver número de requests en última hora

```bash
sudo grep "$(date +%d/%b/%Y:%H)" /var/log/nginx/access.log | wc -l
```

### Ver errores 500 en última hora

```bash
sudo grep "$(date +%d/%b/%Y:%H)" /var/log/nginx/access.log | grep " 500 " | wc -l
```

### Ver IPs más activas

```bash
sudo awk '{print $1}' /var/log/nginx/access.log | sort | uniq -c | sort -rn | head -10
```

---

## 🔑 VARIABLES DE ENTORNO

### Ver variables del servicio

```bash
sudo systemctl show clinidocs-backend -p Environment
```

### Editar archivo .env

```bash
cd ~/clinic_records/cr_backend
nano .env
# Después de editar:
sudo systemctl restart clinidocs-backend
```

---

## 📝 CHECKLIST DE SALUD

```bash
# Ejecutar estos comandos para verificar que todo está OK

# 1. Servicios corriendo
sudo systemctl is-active clinidocs-backend
sudo systemctl is-active nginx

# 2. Puertos escuchando
sudo ss -tlnp | grep :8000
sudo ss -tlnp | grep :80
sudo ss -tlnp | grep :5173

# 3. Procesos activos
ps aux | grep gunicorn | grep -v grep
ps aux | grep nginx | grep -v grep

# 4. Test de conectividad
curl http://localhost:8000/api/docs/
curl http://localhost:5173

# 5. Logs sin errores recientes
sudo journalctl -u clinidocs-backend --since "5 minutes ago" | grep -i error
sudo tail -20 /var/log/nginx/error.log

# Si todos retornan OK: ✅ Sistema saludable
```

---

## 🆘 SOPORTE RÁPIDO

**Si algo no funciona:**

1. **Backend no responde:**

   ```bash
   sudo systemctl restart clinidocs-backend
   sudo journalctl -u clinidocs-backend -n 50
   ```

2. **Frontend no carga:**

   ```bash
   sudo systemctl restart nginx
   sudo tail -20 /var/log/nginx/error.log
   ```

3. **Error 502 Bad Gateway:**

   ```bash
   # Backend está caído
   sudo systemctl status clinidocs-backend
   sudo systemctl restart clinidocs-backend
   ```

4. **Error 404 en API:**

   ```bash
   # Verificar URLs en Nginx
   sudo nano /etc/nginx/sites-available/clinidocs
   sudo nginx -t
   sudo systemctl restart nginx
   ```

5. **Base de datos no conecta:**

   ```bash
   # Verificar .env
   cat ~/clinic_records/cr_backend/.env | grep DATABASE

   # Test de conexión
   psql -h clinidocs-db.cexccmuycswr.us-east-1.rds.amazonaws.com \
        -U clinidocs_user \
        -d clinidocs_db \
        -c "SELECT 1;"
   ```

---

**ÚLTIMA ACTUALIZACIÓN:** Noviembre 5, 2025  
**VERSIÓN:** 1.0
