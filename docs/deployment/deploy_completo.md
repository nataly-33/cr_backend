# 🚀 GUÍA DE DEPLOYMENT PASO A PASO - CLINIC RECORDS

**Tiempo estimado:** 90 minutos (incluyendo creación de infraestructura)
**Costo:** FREE TIER (gratis)
**Fecha:** Noviembre 5, 2025
**Actualizado:** Con errores encontrados y soluciones

---

## 📋 ÍNDICE

1. [Checklist Previo](#checklist-previo)
2. [PARTE 0: Crear Infraestructura AWS desde Cero](#parte-0-crear-infraestructura-aws-15-minutos)
3. [PARTE 1: Crear Usuario IAM para S3](#parte-1-crear-usuario-iam-para-s3-10-minutos)
4. [PARTE 2: Configurar Security Groups](#parte-2-configurar-security-groups-5-minutos)
5. [PARTE 3: Deployment del Backend](#parte-3-deployment-del-backend-20-minutos)
6. [PARTE 4: Deployment del Frontend](#parte-4-deployment-del-frontend-15-minutos)
7. [PARTE 5: Pruebas Finales](#parte-5-pruebas-finales-5-minutos)
8. [PARTE 6: Ejecutar Seeders](#parte-6-ejecutar-seeders-5-minutos)
9. [🐛 ERRORES ENCONTRADOS Y SOLUCIONES](#-errores-encontrados-y-soluciones-detallados)
10. [Troubleshooting General](#troubleshooting)
11. [Pendientes y Mejoras Futuras](#-pendientes-y-mejoras-futuras)

---

## 📋 CHECKLIST PREVIO

### Si ya tienes infraestructura:

- ✅ EC2 Backend corriendo: `i-0360a2ff4775a86a4` (3.85.212.201)
- ✅ RDS PostgreSQL: `clinidocs-db.cexccmuycswr.us-east-1.rds.amazonaws.com`
- ✅ S3 Bucket: `clinidocs-files-2025`
- ✅ SendGrid API Key configurado
- ✅ Archivo `.pem` para conectar a EC2

### Si empiezas desde cero:

- [ ] Cuenta AWS creada y verificada
- [ ] Acceso a AWS Console
- [ ] Tarjeta de crédito registrada (no se cobrará en Free Tier)

---

## 🏗️ PARTE 0: CREAR INFRAESTRUCTURA AWS (15 minutos)

**⚠️ Si ya tienes EC2, RDS y S3 creados, SALTA a [PARTE 1](#parte-1-crear-usuario-iam-para-s3-10-minutos)**

### 0.1. Crear Instancia EC2

1. Ve a: https://console.aws.amazon.com/ec2
2. Haz clic en **"Launch Instance"** (Lanzar instancia)
3. **Configuración:**
   - **Name:** `clinidocs-backend`
   - **AMI:** Ubuntu Server 22.04 LTS (Free Tier eligible)
   - **Instance type:** `t3.micro` (1 vCPU, 1 GB RAM) - Free Tier
   - **Key pair:**
     - Clic en "Create new key pair"
     - Name: `clinidocs-key`
     - Type: RSA
     - Format: `.pem`
     - **Descarga el archivo `.pem` y guárdalo en un lugar seguro**
   - **Network settings:**
     - Allow SSH traffic from: My IP
     - Allow HTTP traffic from the internet: ✅
     - Allow HTTPS traffic from the internet: ✅
   - **Storage:** 8 GB (Free Tier incluye hasta 30 GB)
4. Haz clic en **"Launch instance"**
5. **Anota la IP pública** que se asigna (ej: `3.85.212.201`)

### 0.2. Crear Base de Datos RDS PostgreSQL

1. Ve a: https://console.aws.amazon.com/rds
2. Haz clic en **"Create database"**
3. **Configuración:**
   - **Engine:** PostgreSQL
   - **Version:** PostgreSQL 14.19 (o la última disponible)
   - **Templates:** Free tier
   - **DB instance identifier:** `clinidocs-db`
   - **Master username:** `clinidocs_user`
   - **Master password:** `clinicdocs_pass_123*` (anótalo)
   - **DB instance class:** db.t3.micro (Free Tier)
   - **Storage:** 20 GB GP2 (Free Tier incluye hasta 20 GB)
   - **Storage autoscaling:** Deshabilitado
   - **Connectivity:**
     - **Publicly accessible:** ⚠️ **Sí** (importante para este tutorial)
     - **VPC:** Default VPC
     - **VPC security group:** Crear nuevo → `clinidocs-db-sg`
   - **Database authentication:** Password authentication
   - **Initial database name:** ⚠️ **DEJAR VACÍO** (lo crearemos manualmente)
4. Haz clic en **"Create database"**
5. **Espera 5-10 minutos** que se cree
6. **Anota el endpoint** (ej: `clinidocs-db.cexccmuycswr.us-east-1.rds.amazonaws.com`)

### 0.3. Crear Bucket S3

1. Ve a: https://console.aws.amazon.com/s3
2. Haz clic en **"Create bucket"**
3. **Configuración:**
   - **Bucket name:** `clinidocs-files-2025` (debe ser único globalmente)
   - **AWS Region:** us-east-1
   - **Block all public access:** ✅ **Activado** (bucket privado)
   - **Bucket Versioning:** Deshabilitado
   - **Default encryption:** Server-side encryption (SSE-S3)
4. Haz clic en **"Create bucket"**

### 0.4. Crear Base de Datos en RDS (Manualmente)

Una vez que RDS esté disponible:

**Desde tu PC (PowerShell en Windows) o Mac/Linux:**

```bash
# Instalar PostgreSQL client si no lo tienes
# Windows: https://www.postgresql.org/download/windows/
# Mac: brew install postgresql

# Conectar a RDS (sin especificar base de datos)
psql -h clinidocs-db.cexccmuycswr.us-east-1.rds.amazonaws.com -U clinidocs_user -d postgres
```

Password: `clinicdocs_pass_123*`

**Dentro de psql:**

```sql
-- Crear la base de datos
CREATE DATABASE clinidocs_db;

-- Verificar que se creó
\l

-- Salir
\q
```

---

## 🎯 PARTE 1: CREAR USUARIO IAM PARA S3 (10 minutos)

### 1.1. Ir a AWS Console → IAM

1. Abre tu navegador
2. Ve a: https://console.aws.amazon.com/iam
3. Haz login con tu cuenta AWS

### 1.2. Crear nuevo usuario IAM

1. En el menú izquierdo, haz clic en **"Users"** (Usuarios)
2. Haz clic en el botón naranja **"Create user"** (Crear usuario)
3. En **"User name"**, escribe: `clinidocs-s3-user`
4. **NO marques** "Provide user access to the AWS Management Console"
5. Haz clic en **"Next"** (Siguiente)

### 1.3. Asignar permisos S3

1. Selecciona **"Attach policies directly"** (Adjuntar políticas directamente)
2. En el buscador, escribe: `S3`
3. Marca el checkbox de **"AmazonS3FullAccess"**
4. Haz clic en **"Next"** (Siguiente)
5. Haz clic en **"Create user"** (Crear usuario)

### 1.4. Crear Access Keys

1. Haz clic en el usuario recién creado: `clinidocs-s3-user`
2. Ve a la pestaña **"Security credentials"** (Credenciales de seguridad)
3. Baja hasta la sección **"Access keys"**
4. Haz clic en **"Create access key"** (Crear clave de acceso)
5. Selecciona **"Application running outside AWS"**
6. Haz clic en **"Next"**
7. (Opcional) En "Description tag", escribe: `clinidocs-backend`
8. Haz clic en **"Create access key"**

### 1.5. ⚠️ GUARDAR LAS KEYS (MUY IMPORTANTE)

Se mostrará una pantalla con:

- **Access key ID**: Algo como `AKIAIOSFODNN7EXAMPLE`
- **Secret access key**: Algo como `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY`

**COPIA ESTAS KEYS INMEDIATAMENTE** y guárdalas en un lugar seguro. **NO SE VOLVERÁN A MOSTRAR**.

📝 **ANOTA AQUÍ:**

```
AWS_ACCESS_KEY_ID=PEGAR_AQUI_TU_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY=PEGAR_AQUI_TU_SECRET_ACCESS_KEY
```

Haz clic en **"Done"** (Listo)

---

## 🔐 PARTE 2: CONFIGURAR SECURITY GROUPS (5 minutos)

### 2.1. Ir a EC2 Security Groups

1. Ve a: https://console.aws.amazon.com/ec2
2. En el menú izquierdo, haz clic en **"Security Groups"** (Grupos de seguridad)
3. Busca el security group de tu EC2 `clinidocs-backend`
4. Haz clic en el **ID del security group**

### 2.2. Agregar reglas de entrada (Inbound Rules)

1. Ve a la pestaña **"Inbound rules"** (Reglas de entrada)
2. Haz clic en **"Edit inbound rules"** (Editar reglas de entrada)
3. Haz clic en **"Add rule"** (Agregar regla) para cada una de estas:

**Regla 1 - SSH (ya debería estar):**

- Type: `SSH`
- Protocol: `TCP`
- Port range: `22`
- Source: `My IP` (tu IP actual) o `0.0.0.0/0` (cualquier IP - menos seguro)
- Description: `SSH access`

**Regla 2 - HTTP:**

- Type: `HTTP`
- Protocol: `TCP`
- Port range: `80`
- Source: `0.0.0.0/0`
- Description: `HTTP public access`

**Regla 3 - HTTPS:**

- Type: `HTTPS`
- Protocol: `TCP`
- Port range: `443`
- Source: `0.0.0.0/0`
- Description: `HTTPS public access`

**Regla 4 - Backend Django:**

- Type: `Custom TCP`
- Protocol: `TCP`
- Port range: `8000`
- Source: `0.0.0.0/0`
- Description: `Django backend`

**Regla 5 - Frontend Vite:**

- Type: `Custom TCP`
- Protocol: `TCP`
- Port range: `5173`
- Source: `0.0.0.0/0`
- Description: `Vite frontend`

4. Haz clic en **"Save rules"** (Guardar reglas)

---

## 🖥️ PARTE 3: DEPLOYMENT DEL BACKEND (20 minutos)

### 3.1. Conectar a EC2 por SSH

**En Windows PowerShell:**

1. Abre PowerShell
2. Ve a la carpeta donde tienes tu archivo `.pem`:

   ```powershell
   cd "D:\1NATALY\SISTEMAS DE INFORMACIÓN II\nuevo GESTION_DOCUMENTAL"
   ```

3. Conecta a EC2:

   ```powershell
    ssh -i "clinidocs-key.pem" ubuntu@3.85.212.201
   ```

   Si te da error de permisos, ejecuta primero:

   ```powershell
   icacls "smartsales-key.pem" /reset
   icacls "smartsales-key.pem" /inheritance:r
   icacls "smartsales-key.pem" /grant:r "$($env:USERNAME):(R)"
   ```

### 3.2. Instalar dependencias en EC2

Una vez conectado a EC2, ejecuta estos comandos **uno por uno**:

```bash
# Actualizar el sistema
sudo apt update && sudo apt upgrade -y

# Instalar Python 3.11 y herramientas
sudo apt install -y python3.11 python3.11-venv python3-pip git postgresql-client nginx

# Instalar Node.js 20 (para el frontend)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Verificar instalaciones
python3.11 --version
node --version
npm --version
```

### 3.3. Clonar el repositorio

```bash
# Ir a home
cd ~

# Clonar el backend
git clone https://github.com/TU_USUARIO/clinic_records.git
cd clinic_records
```

**⚠️ IMPORTANTE:** Si el repositorio es privado, necesitarás:

1. Generar un Personal Access Token en GitHub
2. Usarlo como password al hacer `git clone`

### 3.4. Configurar el backend

```bash
# Ir a la carpeta del backend
cd ~/clinic_records/cr_backend

# Crear entorno virtual
python3.11 -m venv venv

# Activar entorno virtual
source venv/bin/activate

# Instalar dependencias
pip install --upgrade pip
pip install -r requirements.txt

# Instalar boto3 para S3
pip install boto3 django-storages
```

### 3.5. Crear archivo .env en EC2

````bash
# Crear archivo .env (copia del .env.production pero con las AWS keys reales)
nano .env

**Para guardar en nano:**

1. Presiona `Ctrl + X`
2. Presiona `Y` (Yes)
3. Presiona `Enter`

### 3.6. Ejecutar migraciones y recolectar estáticos

```bash
# Asegúrate de estar en el entorno virtual
source venv/bin/activate

# Crear carpeta de logs
mkdir -p logs

#Problemas con la BASE DE DATOS no conecta
#"Publicly Accessible" (MÁS RÁPIDO - 5 min)
Ve a: https://console.aws.amazon.com/rds
Selecciona "clinidocs-db"
Clic en "Modify" (botón naranja arriba)
Baja hasta "Connectivity" → "Additional configuration"
Marca "Publicly accessible: Yes"
Baja hasta el final → "Continue"
Selecciona "Apply immediately"
Clic en "Modify DB instance"
#Security groups en RDS
PostgreSQL   TCP       5432  172.31.19.164/32   EC2 Backend Instance
PostgreSQL   TCP       5432  172.31.0.0/16      VPC Range (backup)

#Modificar Security Group de EC2:
Type: PostgreSQL
Protocol: TCP
Port range: 5432
Destination: 54.243.78.191/32 (la IP pública de RDS)
Description: RDS Connection


# Ejecutar migraciones
python manage.py migrate

# Recolectar archivos estáticos
python manage.py collectstatic --noinput

# Crear superusuario (opcional, puedes usar el del seeder)
# python manage.py createsuperuser
````

### 3.7. Probar el backend manualmente

```bash
# Ejecutar servidor de desarrollo (solo para probar)
python manage.py runserver 0.0.0.0:8000
```

**Abre tu navegador y ve a:**

- http://http://52.0.69.138/api/docs

Si ves la documentación de Swagger, **¡funciona!** ✅

**Presiona Ctrl + C** en la terminal para detener el servidor.

### 3.8. Configurar Gunicorn (servidor de producción)

```bash
# Crear archivo de servicio systemd
sudo nano /etc/systemd/system/clinidocs-backend.service
```

**PEGA ESTE CONTENIDO:**

```ini
[Unit]
Description=Clinic Records Backend (Django + Gunicorn)
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/home/ubuntu/cr_backend
Environment="PATH=/home/ubuntu/cr_backend/venv/bin"
EnvironmentFile=/home/ubuntu/cr_backend/.env
ExecStart=/home/ubuntu/cr_backend/venv/bin/gunicorn \
    --workers 3 \
    --bind 0.0.0.0:8000 \
    --timeout 120 \
    config.wsgi:application

[Install]
WantedBy=multi-user.target
```

Guardar: `Ctrl + X` → `Y` → `Enter`

```bash
# Habilitar y arrancar el servicio
sudo systemctl daemon-reload
sudo systemctl enable clinidocs-backend
sudo systemctl start clinidocs-backend

# Verificar estado
sudo systemctl status clinidocs-backend
```

Deberías ver **"active (running)"** en verde. ✅

---

## 🎨 PARTE 4: DEPLOYMENT DEL FRONTEND (15 minutos)

### 4.1. Construir el frontend localmente

**En tu máquina Windows (PowerShell):**

```powershell
# Ir a la carpeta del frontend
cd d:\1NATALY\Proyectos\clinic_records\cr_frontend

# Crear archivo .env.production (ya está creado)
# Verificar que tenga: VITE_API_URL=http://3.85.212.201:8000/api

# Instalar dependencias si no lo has hecho
npm install

# Construir para producción
npm run build
```

Esto creará la carpeta `dist/` con los archivos compilados.

### 4.2. Subir el frontend a EC2

**Opción A: Usando SCP (más fácil)**

```powershell
# Desde PowerShell en Windows
scp -i "tu-archivo.pem" -r dist ubuntu@3.85.212.201:~/clinic_records/cr_frontend/
```

**Opción B: Clonar y compilar en EC2**

```bash
# En la conexión SSH a EC2
cd ~/clinic_records/cr_frontend

# Crear archivo .env
nano .env
```

Pegar:

```
VITE_APP_TITLE=Clinic Records
VITE_API_URL=http://3.85.212.201:8000/api
VITE_STRIPE_PUBLISHABLE_KEY=disabled
```

```bash
# Instalar dependencias
npm install

# Compilar
npm run build
```

### 4.3. Configurar Nginx

```bash
# Crear configuración de Nginx
sudo nano /etc/nginx/sites-available/clinidocs
```

**PEGA ESTE CONTENIDO:**

```nginx
# Backend (Django en puerto 8000)
server {
    listen 80;
    server_name 3.85.212.201;

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /admin/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /static/ {
        alias /home/ubuntu/clinic_records/cr_backend/staticfiles/;
    }

    location /media/ {
        # Los archivos están en S3, pero si hay locales:
        alias /home/ubuntu/clinic_records/cr_backend/media/;
    }
}

# Frontend (Vite en puerto 5173)
server {
    listen 5173;
    server_name 3.85.212.201;
    root /home/ubuntu/clinic_records/cr_frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

```bash
# Habilitar el sitio
sudo ln -s /etc/nginx/sites-available/clinidocs /etc/nginx/sites-enabled/

# Probar configuración
sudo nginx -t

# Si todo está OK, reiniciar Nginx
sudo systemctl restart nginx
```

---

## 🎉 PARTE 5: PRUEBAS FINALES (5 minutos)

### 5.1. Verificar servicios

```bash
# Verificar backend
sudo systemctl status clinidocs-backend

# Verificar Nginx
sudo systemctl status nginx
```

### 5.2. Acceder desde el navegador

1. **Backend API:**

   - http://3.85.212.201/api/docs/
   - Deberías ver Swagger UI ✅

2. **Frontend:**

   - http://3.85.212.201:5173
   - Deberías ver la página de login ✅

3. **Hacer login:**

   - Email: `admin@clinica-lapaz.com`
   - Password: `Password123!`

4. **Probar funcionalidades:**
   - Ver pacientes
   - Ver historias clínicas
   - Subir un documento (se guardará en S3)

---

## 🐛 TROUBLESHOOTING

### Error: No se puede conectar al backend

```bash
# Ver logs del backend
sudo journalctl -u clinidocs-backend -f

# Ver logs de Nginx
sudo tail -f /var/log/nginx/error.log
```

### Error: Migraciones de base de datos

```bash
cd ~/clinic_records/cr_backend
source venv/bin/activate
python manage.py migrate --fake-initial
```

### Error: S3 Access Denied

- Verifica que las AWS keys estén correctas en `.env`
- Verifica que el usuario IAM tenga permisos `AmazonS3FullAccess`
- Verifica que el bucket `clinidocs-files-2025` exista

### Reiniciar servicios después de cambios

```bash
# Reiniciar backend
sudo systemctl restart clinidocs-backend

# Reiniciar Nginx
sudo systemctl restart nginx
```

---

## 📊 COSTOS ESTIMADOS (FREE TIER)

- **EC2 t3.micro:** Gratis 750 horas/mes (primer año)
- **RDS db.t3.micro:** Gratis 750 horas/mes (primer año)
- **S3:** 5 GB gratis permanentemente
- **Total:** **$0/mes** durante el primer año ✅

---

## 🔄 ACTUALIZACIONES FUTURAS

Para actualizar el código después del deployment:

```bash
# SSH a EC2
ssh -i "tu-archivo.pem" ubuntu@3.85.212.201

# Actualizar backend
cd ~/clinic_records
git pull origin main

cd cr_backend
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart clinidocs-backend

# Actualizar frontend
cd ~/clinic_records/cr_frontend
git pull origin main
npm install
npm run build
sudo systemctl restart nginx
```

---

---

## 📦 PARTE 6: EJECUTAR SEEDERS (5 minutos)

### 6.1. Ejecutar el script de datos de prueba

```bash
# Conectar por SSH a EC2
ssh -i "clinidocs-key.pem" ubuntu@3.85.212.201

# Ir a la carpeta del backend
cd ~/cr_backend

# Activar entorno virtual
source venv/bin/activate

# Ejecutar seeders
python scripts/seed_data.py
```

### 6.2. Verificar que se crearon los datos

Deberías ver mensajes como:

```
✓ Creando tenant: Clínica La Paz
✓ Creando 3 usuarios Admin TI
✓ Enviando emails de bienvenida...
✓ Creando 2 médicos
✓ Creando 2 recepcionistas
✓ Creando 10 pacientes ficticios
✓ Creando 15 historias clínicas
✓ Datos de prueba creados exitosamente!
```

### 6.3. Credenciales de prueba

**Usuario Admin TI:**

- Email: `admin@clinica-lapaz.com`
- Password: `Password123!`

**Usuario Médico:**

- Email: `medico1@clinica-lapaz.com`
- Password: `Password123!`

**Usuario Recepcionista:**

- Email: `recepcionista1@clinica-lapaz.com`
- Password: `Password123!`

---

## 🐛 ERRORES ENCONTRADOS Y SOLUCIONES (DETALLADOS)

### ❌ ERROR 1: RDS no accesible desde EC2

**Síntoma:**

```
psycopg2.OperationalError: connection to server at "clinidocs-db.cexccmuycswr.us-east-1.rds.amazonaws.com" (172.31.0.117), port 5432 failed: Connection timed out
```

**Causa:**

- RDS estaba en modo **"Publicly Accessible: No"**
- Security Group de RDS no permitía conexión desde EC2
- EC2 intentaba conectar por IP privada (`172.31.0.117`) sin éxito

**Solución:**

#### Paso 1: Cambiar RDS a Publicly Accessible

1. Ve a: https://console.aws.amazon.com/rds
2. Selecciona **"clinidocs-db"**
3. Clic en **"Modify"** (botón naranja)
4. Baja hasta **"Connectivity"** → **"Additional configuration"**
5. Marca **"Publicly accessible: Yes"**
6. Clic en **"Continue"** → **"Apply immediately"**
7. Espera 2-3 minutos

#### Paso 2: Configurar Security Group de RDS

1. Ve a RDS → clinidocs-db → **"Connectivity & security"**
2. Haz clic en el **Security Group** (ej: `clinidocs-db-sg`)
3. **Inbound rules** → **"Edit inbound rules"**
4. Agrega estas reglas:

| Type       | Protocol | Port | Source              | Description |
| ---------- | -------- | ---- | ------------------- | ----------- |
| PostgreSQL | TCP      | 5432 | `IP_PUBLICA_EC2/32` | EC2 Backend |
| PostgreSQL | TCP      | 5432 | `172.31.0.0/16`     | VPC Range   |
| PostgreSQL | TCP      | 5432 | `TU_IP_LOCAL/32`    | Dev Access  |

5. **Save rules**

#### Paso 3: Agregar regla Outbound en Security Group de EC2

1. Ve a EC2 → Security Groups → Security Group de EC2
2. **Outbound rules** → **"Edit outbound rules"**
3. Agrega:

| Type        | Protocol | Port | Destination         | Description           |
| ----------- | -------- | ---- | ------------------- | --------------------- |
| PostgreSQL  | TCP      | 5432 | `IP_PUBLICA_RDS/32` | RDS Connection        |
| All traffic | All      | All  | `0.0.0.0/0`         | General (recomendado) |

4. **Save rules**

#### Paso 4: Usar IP pública de RDS en .env

**Si EC2 sigue sin conectar**, edita el `.env`:

```bash
nano ~/cr_backend/.env
```

Cambia:

```bash
# ANTES:
DATABASE_HOST=clinidocs-db.cexccmuycswr.us-east-1.rds.amazonaws.com

# DESPUÉS (usa la IP pública que aparece en RDS):
DATABASE_HOST=54.243.78.191
```

Guarda y prueba de nuevo.

---

### ❌ ERROR 2: Base de datos `clinidocs_db` no existe

**Síntoma:**

```
psql: error: falló la conexión al servidor: FATAL:  database "clinidocs_db" does not exist
```

**Causa:**
Al crear RDS, no se especificó un nombre de base de datos inicial, solo se creó el servidor PostgreSQL.

**Solución:**

```bash
# Conectar a la base de datos por defecto (postgres)
psql -h clinidocs-db.cexccmuycswr.us-east-1.rds.amazonaws.com -U clinidocs_user -d postgres

# Password: clinicdocs_pass_123*

# Crear la base de datos
CREATE DATABASE clinidocs_db;

# Verificar
\l

# Salir
\q
```

Ahora sí:

```bash
psql -h clinidocs-db.cexccmuycswr.us-east-1.rds.amazonaws.com -U clinidocs_user -d clinidocs_db
```

Debería conectar correctamente. ✅

---

### ❌ ERROR 3: Gunicorn falla con error de logging

**Síntoma:**

```
[ERROR] Worker failed to boot.
ValueError: Unable to configure handler 'file'
```

**Causa:**

- Carpeta `logs/` no existe
- Configuración de logging en `production.py` apunta a un archivo que no puede crear

**Solución:**

#### Opción 1: Crear carpetas y dar permisos

```bash
cd ~/cr_backend

# Crear carpetas necesarias
mkdir -p logs static staticfiles

# Dar permisos
chmod -R 755 logs
sudo chown -R ubuntu:www-data logs

# Crear archivo de log vacío
touch logs/django.log
chmod 664 logs/django.log
```

#### Opción 2: Simplificar configuración de logging (RECOMENDADO)

Editar `~/cr_backend/config/settings/production.py`:

```bash
nano ~/cr_backend/config/settings/production.py
```

Buscar la sección `LOGGING` y cambiarla a:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
}
```

Eliminar o comentar cualquier handler de tipo `'file'`.

#### Opción 3: Usar runserver en background (TEMPORAL)

Si Gunicorn sigue fallando:

```bash
# Detener el servicio systemd
sudo systemctl stop clinidocs-backend

# Ejecutar Django en background
cd ~/cr_backend
source venv/bin/activate
nohup python manage.py runserver 0.0.0.0:8000 > /tmp/django.log 2>&1 &

# Verificar que está corriendo
ps aux | grep runserver
```

⚠️ **Nota:** `runserver` es para desarrollo. En producción real, usa Gunicorn o uWSGI.

---

### ❌ ERROR 4: Nginx 500 Internal Server Error (frontend)

**Síntoma:**

```
2025/11/05 18:02:57 [crit] 12920#12920: *4 stat() "/home/ubuntu/cr_frontend/dist/index.html" failed (13: Permission denied)
```

**Causa:**
Permisos incorrectos en la carpeta `dist/` que impiden que Nginx (que corre como `www-data`) lea los archivos.

**Solución:**

```bash
# Dar permisos correctos a TODAS las carpetas padre
chmod 755 /home/ubuntu
chmod 755 /home/ubuntu/cr_frontend
chmod -R 755 /home/ubuntu/cr_frontend/dist

# Verificar permisos
ls -ld /home/ubuntu/cr_frontend/dist
# Debería mostrar: drwxr-xr-x (NO drwx---rwx)

# Reiniciar Nginx
sudo systemctl restart nginx
```

**Verificar:**

```bash
# Ver logs de error
sudo tail -20 /var/log/nginx/error.log

# No deberían aparecer más errores de "Permission denied"
```

---

### ❌ ERROR 5: Symlink de Nginx incorrecto

**Síntoma:**
Nginx configurado correctamente pero no se aplica. Frontend no responde en puerto 5173.

**Causa:**
Error de tipeo al crear el symlink (escribí `cinidocs` en vez de `clinidocs`).

**Solución:**

```bash
# Ver symlinks existentes
ls -la /etc/nginx/sites-enabled/

# Eliminar symlinks incorrectos
sudo rm /etc/nginx/sites-enabled/cinidocs
sudo rm /etc/nginx/sites-enabled/default  # Si existe

# Crear symlink CORRECTO (con espacio entre origen y destino)
sudo ln -s /etc/nginx/sites-available/clinidocs /etc/nginx/sites-enabled/

# Verificar sintaxis de Nginx
sudo nginx -t

# Si dice "syntax is ok" y "test is successful":
sudo systemctl restart nginx
```

---

### ❌ ERROR 6: `npm install` cuelga en EC2

**Síntoma:**
`npm install` se queda en spinner `⠼` por más de 5 minutos en la instancia EC2.

**Causa:**
Instancia `t3.micro` tiene solo 1 GB de RAM y 1 vCPU, lo que hace que `npm install` sea extremadamente lento (puede tomar 10-15 minutos).

**Solución (RECOMENDADA):**

#### Compilar localmente y subir `dist/`

**En tu PC Windows (PowerShell):**

```powershell
# Ir al frontend local
cd "D:\1NATALY\Proyectos\clinic_records\cr_frontend"

# Crear/verificar .env.production
nano .env.production
```

```
VITE_APP_TITLE=Clinic Records
VITE_API_URL=http://3.85.212.201:8000/api
VITE_STRIPE_PUBLISHABLE_KEY=disabled
```

```powershell
# Compilar (rápido en tu PC)
npm run build

# Subir carpeta dist/ a EC2 (2-3 minutos)
scp -i "D:\path\to\smartsales-key.pem" -r dist ubuntu@52.0.69.138:~/ss_frontend/

#ssh -i "smartsales-key.pem" ubuntu@52.0.69.138

```

Esto es **10x más rápido** que compilar en EC2.

---

### ❌ ERROR 7: Archivos estáticos no se sirven correctamente

**Síntoma:**

- Admin de Django sin CSS
- Errores 404 en `/static/` en logs de Nginx

**Causa:**
No se ejecutó `collectstatic` o las rutas en Nginx no coinciden.

**Solución:**

```bash
cd ~/cr_backend
source venv/bin/activate

# Recolectar archivos estáticos
python manage.py collectstatic --noinput

# Verificar que se creó la carpeta staticfiles
ls -la ~/cr_backend/staticfiles/

# Verificar configuración de Nginx
sudo nano /etc/nginx/sites-available/clinidocs
```

Asegúrate que tenga:

```nginx
location /static/ {
    alias /home/ubuntu/cr_backend/staticfiles/;
}
```

**NO** debería decir `/home/ubuntu/clinic_records/cr_backend/` (ruta incorrecta).

Reiniciar Nginx:

```bash
sudo systemctl restart nginx
```

---

## ✅ CHECKLIST FINAL

- [ ] Usuario IAM creado y AWS keys guardadas
- [ ] Security Groups configurados (puertos 22, 80, 443, 8000, 5173)
- [ ] RDS en modo "Publicly Accessible: Yes"
- [ ] Base de datos `clinidocs_db` creada manualmente
- [ ] Backend corriendo (runserver o Gunicorn)
- [ ] Frontend compilado y servido por Nginx
- [ ] Permisos correctos en carpetas (755)
- [ ] Seeders ejecutados
- [ ] Login funciona con `admin@clinica-lapaz.com`
- [ ] Historias clínicas se visualizan
- [ ] Documentos se suben a S3

---

**¡DEPLOYMENT COMPLETADO!** 🎉

**URLs de producción:**

- Frontend: http://3.85.212.201:5173
- Backend API: http://3.85.212.201/api/
- Swagger Docs: http://3.85.212.201/api/docs/
- Admin Django: http://3.85.212.201:8000/admin/

---

## 📝 PENDIENTES Y MEJORAS FUTURAS

### 🔴 Alta Prioridad

1. **Backups Automáticos en S3**

   - Configurar RDS Automated Backups (retención 7-30 días)
   - Script de backup incremental a S3 Glacier
   - Restauración de backups documentada

2. **Sistema de Logging Robusto**

   - CloudWatch Logs para centralizar logs
   - Rotación de logs con logrotate
   - Alertas de errores críticos por email/SMS

3. **Gunicorn/uWSGI Funcional**

   - Corregir configuración de Gunicorn
   - Workers según CPU (fórmula: 2\*CPU + 1)
   - Systemd service estable

4. **HTTPS con Let's Encrypt**
   - Instalar Certbot
   - Certificados SSL gratis
   - Redirección HTTP → HTTPS automática
   - Renovación automática de certificados

### 🟡 Media Prioridad

5. **Monitoring y Alertas**

   - CloudWatch metrics (CPU, memoria, disco)
   - Uptime Robot para monitoreo externo
   - Notificaciones si el servicio cae

6. **CI/CD Pipeline**

   - GitHub Actions para deployment automático
   - Tests automáticos antes de deploy
   - Rollback automático si falla

7. **Optimización de Costos**
   - Reserved Instances (descuento 30-50%)
   - S3 Lifecycle Policies (mover a Glacier)
   - Elastic IP para mantener IP fija

### 🟢 Baja Prioridad

8. **Docker y Docker Compose**

   - Containerizar backend y frontend
   - Facilitar desarrollo local
   - Preparar para Kubernetes

9. **Balanceador de Carga**

   - AWS Application Load Balancer
   - Múltiples instancias EC2
   - Auto Scaling Group

10. **CDN para Archivos Estáticos**
    - CloudFront para servir assets del frontend
    - Reducir latencia global
    - Cache de archivos de S3

---

## 📚 RECURSOS ADICIONALES

- **Documentación Django Deployment:** https://docs.djangoproject.com/en/5.1/howto/deployment/
- **Nginx Best Practices:** https://www.nginx.com/blog/nginx-best-practices/
- **AWS Free Tier Limits:** https://aws.amazon.com/free/
- **PostgreSQL Performance Tuning:** https://www.postgresql.org/docs/14/performance-tips.html
- **Let's Encrypt Certbot:** https://certbot.eff.org/

---

**Creado por:** Naataly Vanessa
**Fecha:** Noviembre 5, 2025
**Versión:** 2.0 (con errores y soluciones)

---

## 🚀 DEPLOYMENT RÁPIDO SMARTSALES365 (RESUMEN FUNCIONAL - NOVIEMBRE 9, 2025)

### ❌ PROBLEMA ENCONTRADO

El deployment inicial fallaba en dos puntos:

1. **Puerto 8000 en uso**: `runserver` local estaba corriendo en background
2. **S3 ACLs deshabilitado**: Django intentaba subir statics a S3 pero fallaba con `AccessControlListNotSupported`

### ✅ SOLUCIÓN IMPLEMENTADA

#### FASE 1: Preparación en EC2 (Terminal SSH)

```bash
# 1. Crear carpetas necesarias
cd ~/ss_backend
mkdir -p static staticfiles logs

# 2. Dar permisos correctos
sudo chown -R ubuntu:www-data .
chmod -R 755 .

# 3. Activar venv
source venv/bin/activate

# 4. Instalar Gunicorn (si no está)
pip install gunicorn
```

#### FASE 2: Desactivar S3 y usar almacenamiento LOCAL

```bash
# 1. Editar .env
nano .env
```

**Cambiar:**

```
USE_S3=True          ❌ ANTES
USE_S3=False         ✅ DESPUÉS
```

```bash
# 2. Ejecutar collectstatic (IMPORTANTE: --clear para limpiar antes)
python manage.py collectstatic --noinput --clear
```

**Deberías ver:**

```
X static files copied to '/home/ubuntu/ss_backend/staticfiles'
```

#### FASE 3: Liberar puerto 8000 y configurar Gunicorn

```bash
# 1. Detener servicio anterior
sudo systemctl stop smartsales-backend

# 2. Matar procesos en puerto 8000
sudo fuser -k 8000/tcp 2>/dev/null || true

# 3. Recargar systemd
sudo systemctl daemon-reload

# 4. Habilitar servicios
sudo systemctl enable smartsales-backend
sudo systemctl enable nginx

# 5. Iniciar servicios
sudo systemctl start smartsales-backend
sleep 2
sudo systemctl start nginx
sleep 2

# 6. Verificar estado
sudo systemctl status smartsales-backend
sudo systemctl status nginx
```

**Expected output:**

```
● smartsales-backend.service - SmartSales Backend (Django + Gunicorn)
     Active: active (running)

● nginx.service - A high performance web server
     Active: active (running)
```

#### FASE 4: Crear configuración de Nginx

```bash
# 1. Crear archivo
sudo nano /etc/nginx/sites-available/smartsales
```

**Contenido EXACTO:**

```nginx
upstream smartsales_backend {
    server 127.0.0.1:8000;
}

server {
    listen 80 default_server;
    server_name _;

    client_max_body_size 100M;

    access_log /var/log/nginx/smartsales_access.log;
    error_log /var/log/nginx/smartsales_error.log;

    # Backend API
    location /api/ {
        proxy_pass http://smartsales_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;

        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Admin de Django
    location /admin/ {
        proxy_pass http://smartsales_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Archivos estáticos
    location /static/ {
        alias /home/ubuntu/ss_backend/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Media files
    location /media/ {
        alias /home/ubuntu/ss_backend/media/;
        expires 7d;
    }
}
```

Guardar: `Ctrl+X` → `Y` → `Enter`

```bash
# 2. Limpiar configuraciones viejas
sudo rm -f /etc/nginx/sites-enabled/default
sudo rm -f /etc/nginx/sites-enabled/smartsales

# 3. Crear symlink
sudo ln -s /etc/nginx/sites-available/smartsales /etc/nginx/sites-enabled/

# 4. Probar sintaxis
sudo nginx -t
```

**Expected:**

```
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration will be successful
```

```bash
# 5. Reiniciar Nginx
sudo systemctl restart nginx
```

#### FASE 5: Verificación FINAL

```bash
# Ver logs de gunicorn (NO debería haber errores)
sudo journalctl -u smartsales-backend -n 20

# Ver logs de Nginx
sudo tail -20 /var/log/nginx/error.log

# Probar conectividad a backend
curl http://127.0.0.1:8000/api/
```

**Abre en navegador:**

```
http://52.0.69.138/api/docs
```

**Deberías ver:** ✅ **SWAGGER UI COMPLETO**

---

### 📋 RESUMEN DE COMANDOS PARA LA PRÓXIMA VEZ

```bash
# ========== SCRIPT COMPLETO PARA DESPLIEGUE RÁPIDO ==========

cd ~/ss_backend

# 1. Preparación
mkdir -p static staticfiles logs
sudo chown -R ubuntu:www-data .
chmod -R 755 .
source venv/bin/activate

# 2. Desactivar S3 (editar manualmente .env: USE_S3=False)
nano .env
# Cambiar USE_S3=True a USE_S3=False

# 3. Collectstatic
python manage.py collectstatic --noinput --clear

# 4. Servicios
sudo systemctl stop smartsales-backend
sudo fuser -k 8000/tcp 2>/dev/null || true
sudo systemctl daemon-reload
sudo systemctl enable smartsales-backend nginx
sudo systemctl start smartsales-backend
sleep 2
sudo systemctl start nginx

# 5. Nginx config (manual: sudo nano /etc/nginx/sites-available/smartsales)
# Luego:
sudo rm -f /etc/nginx/sites-enabled/default /etc/nginx/sites-enabled/smartsales
sudo ln -s /etc/nginx/sites-available/smartsales /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# 6. Verificar
sudo systemctl status smartsales-backend
sudo systemctl status nginx

# Resultado final:
# http://52.0.69.138/api/docs 🎉
```

---

### 🔑 PUNTOS CLAVE

| Problema            | Solución                                      |
| ------------------- | --------------------------------------------- |
| Puerto 8000 en uso  | `sudo fuser -k 8000/tcp`                      |
| S3 ACLs error       | `USE_S3=False` en .env                        |
| Collectstatic falla | Usar `--clear` flag                           |
| Nginx sin proxy     | Crear `/etc/nginx/sites-available/smartsales` |
| Permisos            | `sudo chown -R ubuntu:www-data .`             |
| Statics no sirven   | Verificar rutas en Nginx coincidan            |

---

¡Éxito en tu defensa! 🚀

---

---

# 🚀 DEPLOYMENT COMPLETO SMARTSALES365 - GUÍA OPERATIVA (NOVIEMBRE 9, 2025)

## 📌 TABLA DE CONTENIDOS

1. [Resumen Ejecutivo](#resumen-ejecutivo)
2. [Arquitectura Final](#arquitectura-final)
3. [Configuración de Security Groups](#configuración-de-security-groups)
4. [Guía Paso a Paso - BACKEND](#guía-paso-a-paso-backend)
5. [Guía Paso a Paso - FRONTEND](#guía-paso-a-paso-frontend)
6. [Errores Encontrados y Soluciones](#errores-encontrados-y-soluciones)
7. [Verificación Final](#verificación-final)
8. [Mantenimiento y Actualizaciones](#mantenimiento-y-actualizaciones)
9. [FAQ Git y Sincronización](#faq-git-y-sincronización)

---

## 📊 RESUMEN EJECUTIVO

**Proyecto:** SmartSales365 - E-commerce Backend + Frontend
**Infraestructura:** AWS EC2 (Ubuntu 22.04) + RDS PostgreSQL
**Stack:** Django 5.0.2 + React 19.1.1 + Nginx 1.18 + Gunicorn 23.0.0
**Fecha Deployment:** Noviembre 9, 2025
**Duración:** ~60 minutos (incluye troubleshooting)
**Costo:** $0 (Free Tier AWS)

**URLs Finales:**

- 🌐 Frontend: `http://52.0.69.138` (SPA - Single Page App)
- 🔌 Backend API: `http://52.0.69.138/api/` (Proxeado por Nginx)
- 📚 API Docs: `http://52.0.69.138/api/docs` (Swagger UI)
- 👨‍💼 Admin Django: `http://52.0.69.138/api/admin/`

---

## 🏗️ ARQUITECTURA FINAL

```
┌─────────────────────────────────────────────────────────────┐
│                    USUARIO INTERNET                          │
│              181.115.215.86 (ejemplo)                       │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP:80
                         ↓
        ┌────────────────────────────────────┐
        │    AWS EC2: 52.0.69.138            │
        │    Ubuntu 22.04 (t3.micro)         │
        ├────────────────────────────────────┤
        │                                    │
        │  ┌─ NGINX (Port 80) ──────┐       │
        │  │ ├─ / → /dist/index.html│       │
        │  │ ├─ /api → :8000        │       │
        │  │ ├─ /static → statics/  │       │
        │  │ └─ /media → media/     │       │
        │  └────────────────────────┘       │
        │           ↓                        │
        │  ┌─ GUNICORN (Port 8000) ─┐      │
        │  │  Django WSGI Server     │      │
        │  │  - 3 workers            │      │
        │  │  - Timeout: 120s        │      │
        │  └─────────────┬───────────┘      │
        │                │                   │
        │  ┌─────────────↓──────────────┐   │
        │  │  VITE Build (dist/)        │   │
        │  │  - React 19.1.1            │   │
        │  │  - TypeScript 5.9.3        │   │
        │  │  - SPA Routing             │   │
        │  └────────────────────────────┘   │
        │                                    │
        └────────────────────────────────────┘
                         │ TCP:5432
                         ↓
        ┌────────────────────────────────────┐
        │    AWS RDS PostgreSQL              │
        │    52.0.69.138 (IP interna)        │
        │    Port: 5432                      │
        │    Database: smartsales_db         │
        │    User: smartsales_user           │
        └────────────────────────────────────┘
```

---

## 🔐 CONFIGURACIÓN DE SECURITY GROUPS

### 1. Security Group de EC2 (smartsales-sg)

**Inbound Rules (Entrada):**

| Tipo       | Protocolo | Puerto | Origen      | Descripción                          |
| ---------- | --------- | ------ | ----------- | ------------------------------------ |
| SSH        | TCP       | 22     | `TU_IP/32`  | Tu PC - acceso SSH                   |
| HTTP       | TCP       | 80     | `0.0.0.0/0` | Público - navegadores                |
| HTTPS      | TCP       | 443    | `0.0.0.0/0` | Público - HTTPS                      |
| Custom TCP | TCP       | 8000   | `0.0.0.0/0` | Gunicorn (opcional - mejor proxeado) |
| Custom TCP | TCP       | 5173   | `0.0.0.0/0` | Vite dev server (solo desarrollo)    |

**Outbound Rules (Salida):**

| Tipo        | Protocolo | Puerto | Destino     | Descripción           |
| ----------- | --------- | ------ | ----------- | --------------------- |
| Custom TCP  | TCP       | 5432   | `RDS_SG_ID` | PostgreSQL en RDS     |
| HTTPS       | TCP       | 443    | `0.0.0.0/0` | AWS APIs, npm, pip    |
| HTTP        | TCP       | 80     | `0.0.0.0/0` | HTTP (APT updates)    |
| DNS         | UDP       | 53     | `0.0.0.0/0` | Resolución DNS        |
| All traffic | All       | All    | `0.0.0.0/0` | General (recomendado) |

**Configurar en AWS Console:**

1. Ir a: https://console.aws.amazon.com/ec2 → Security Groups
2. Buscar tu SG de EC2
3. Inbound rules → Edit inbound rules
4. Agregar reglas de la tabla anterior
5. Save rules

### 2. Security Group de RDS (smartsales-db-sg)

**Inbound Rules (Entrada):**

| Tipo       | Protocolo | Puerto | Origen          | Descripción               |
| ---------- | --------- | ------ | --------------- | ------------------------- |
| PostgreSQL | TCP       | 5432   | `SG_EC2` (ID)   | EC2 backend               |
| PostgreSQL | TCP       | 5432   | `172.31.0.0/16` | VPC range (backup)        |
| PostgreSQL | TCP       | 5432   | `TU_IP/32`      | Tu PC - psql remoto (dev) |

**Outbound Rules (Salida):**

| Tipo        | Protocolo | Puerto | Destino     | Descripción |
| ----------- | --------- | ------ | ----------- | ----------- |
| All traffic | All       | All    | `0.0.0.0/0` | General     |

**Configurar en AWS Console:**

1. Ir a: https://console.aws.amazon.com/rds → Databases
2. Seleccionar `smartsales-db`
3. Ir a "Connectivity & security"
4. Hacer clic en el Security Group (ej: `default`)
5. Editar inbound rules (mismo proceso que EC2)
6. Agregar reglas de la tabla anterior

---

## 📝 GUÍA PASO A PASO - BACKEND

### PASO 1: Preparación Inicial en EC2

```bash
# 1.1 Conectar por SSH (desde tu PC)
ssh -i "D:\ruta\a\smartsales-key.pem" ubuntu@52.0.69.138

# 1.2 Una vez en EC2, actualizar sistema
sudo apt update && sudo apt upgrade -y

# 1.3 Instalar dependencias
sudo apt install -y python3.11 python3.11-venv python3-pip git nginx postgresql-client

# 1.4 Verificar versiones
python3.11 --version  # Python 3.11.x
nginx -v              # nginx/1.18.0

# 1.5 Preparar directorios
cd ~
mkdir -p ss_backend
cd ss_backend

# 1.6 Crear entorno virtual
python3.11 -m venv venv

# 1.7 Activar entorno
source venv/bin/activate

# 1.8 Crear carpetas necesarias
mkdir -p logs static staticfiles media
```

### PASO 2: Clonar y Configurar Código

```bash
# 2.1 Si el repo es público
git clone https://github.com/nataly-33/smart_sales.git .
# o solo el backend:
git clone https://github.com/nataly-33/smart_sales.git --single-branch --branch main . && rm -rf ss_frontend .git && git init

# 2.2 Si es privado (necesita token GitHub)
# Opción: Descargar ZIP desde GitHub en tu PC y subir con SCP

# 2.3 Instalar dependencias
pip install --upgrade pip
pip install -r requirements.txt

# 2.4 Crear archivo .env (basado en .env.production)
cat > .env << 'EOF'
DEBUG=False
SECRET_KEY=tu-secret-key-aqui-cambiarlo
ALLOWED_HOSTS=52.0.69.138,52.0.69.138:8000

# Database
DATABASE_URL=postgresql://smartsales_user:smart_sales12345@smartsales-db.cexccmuycswr.us-east-1.rds.amazonaws.com:5432/smartsales_db

# JWT
JWT_ACCESS_TOKEN_LIFETIME=60
JWT_REFRESH_TOKEN_LIFETIME=1440

# CORS
CORS_ALLOWED_ORIGINS=http://52.0.69.138

# AWS S3 (DESHABILITADO - usar storage local)
USE_S3=False
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_STORAGE_BUCKET_NAME=

# Email
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
DEFAULT_FROM_EMAIL=noreply@smartsales365.com
EOF

# 2.5 Verificar que .env está correcto
cat .env
```

### PASO 3: Migraciones y Colección de Statics

```bash
# 3.1 Estar en venv activado
source venv/bin/activate

# 3.2 Ejecutar migraciones
python manage.py migrate

# ✅ Deberías ver:
# Running migrations:
#   Applying accounts.0001_initial... OK
#   Applying auth.0001_initial... OK
#   etc...

# 3.3 Recolectar archivos estáticos (MUY IMPORTANTE: --clear)
python manage.py collectstatic --noinput --clear

# ✅ Deberías ver:
# X static files copied to '/home/ubuntu/ss_backend/staticfiles', Y unmodified, Z post-processed.

# 3.4 Verificar que se creó staticfiles/
ls -la staticfiles/ | head -20
```

### PASO 4: Permisos y Directorio

```bash
# 4.1 Dar permisos correctos
sudo chown -R ubuntu:www-data ~/ss_backend
sudo chmod -R 755 ~/ss_backend
sudo chmod -R 775 ~/ss_backend/logs
sudo chmod -R 775 ~/ss_backend/media

# 4.2 Verificar permisos
ls -la ~/ss_backend/
```

### PASO 5: Configurar Gunicorn

```bash
# 5.1 Crear archivo de servicio systemd
sudo nano /etc/systemd/system/smartsales-backend.service
```

**PEGAR EXACTAMENTE ESTO:**

```ini
[Unit]
Description=SmartSales Backend (Django + Gunicorn)
After=network.target postgresql.service

[Service]
Type=notify
User=ubuntu
Group=www-data
WorkingDirectory=/home/ubuntu/ss_backend
Environment="PATH=/home/ubuntu/ss_backend/venv/bin"
EnvironmentFile=/home/ubuntu/ss_backend/.env
ExecStart=/home/ubuntu/ss_backend/venv/bin/gunicorn \
    --workers 3 \
    --worker-class sync \
    --bind 127.0.0.1:8000 \
    --timeout 120 \
    --access-logfile /home/ubuntu/ss_backend/logs/access.log \
    --error-logfile /home/ubuntu/ss_backend/logs/error.log \
    --log-level info \
    config.wsgi:application

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Guardar: `Ctrl+X` → `Y` → `Enter`

```bash
# 5.2 Recargar systemd
sudo systemctl daemon-reload

# 5.3 Habilitar servicio (inicia con el sistema)
sudo systemctl enable smartsales-backend

# 5.4 Iniciar servicio
sudo systemctl start smartsales-backend

# 5.5 Verificar estado
sudo systemctl status smartsales-backend

# ✅ Deberías ver: Active: active (running)

# 5.6 Ver logs
sudo journalctl -u smartsales-backend -n 20

# Si hay errores, revisar:
tail -50 ~/ss_backend/logs/error.log
```

### PASO 6: Configurar Nginx

```bash
# 6.1 Crear configuración
sudo nano /etc/nginx/sites-available/smartsales
```

**PEGAR EXACTAMENTE ESTO:**

```nginx
upstream smartsales_backend {
    server 127.0.0.1:8000;
}

server {
    listen 80 default_server;
    server_name _;

    client_max_body_size 100M;

    access_log /var/log/nginx/smartsales_access.log;
    error_log /var/log/nginx/smartsales_error.log;

    # Servir frontend (SPA - enviar todas las rutas a index.html)
    root /home/ubuntu/ss_frontend/dist;
    index index.html;

    # Frontend - SPA routing
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api/ {
        proxy_pass http://smartsales_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;

        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Admin de Django
    location /api/admin/ {
        proxy_pass http://smartsales_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Archivos estáticos del backend
    location /static/ {
        alias /home/ubuntu/ss_backend/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Media files
    location /media/ {
        alias /home/ubuntu/ss_backend/media/;
        expires 7d;
    }
}
```

Guardar: `Ctrl+X` → `Y` → `Enter`

```bash
# 6.2 Limpiar configuraciones viejas
sudo rm -f /etc/nginx/sites-enabled/default
sudo rm -f /etc/nginx/sites-enabled/smartsales

# 6.3 Crear symlink
sudo ln -s /etc/nginx/sites-available/smartsales /etc/nginx/sites-enabled/

# 6.4 Probar sintaxis
sudo nginx -t

# ✅ Deberías ver:
# nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
# nginx: configuration will be successful

# 6.5 Habilitar Nginx
sudo systemctl enable nginx

# 6.6 Iniciar Nginx
sudo systemctl start nginx

# 6.7 Verificar estado
sudo systemctl status nginx

# 6.8 Ver logs (sin errores)
sudo tail -20 /var/log/nginx/error.log
```

---

## 🎨 GUÍA PASO A PASO - FRONTEND

### PASO 1: Preparación Local (Tu PC)

```bash
# 1.1 Ir a carpeta frontend
cd d:\1NATALY\Proyectos\smart_sales\ss_frontend

# 1.2 Crear/actualizar .env.production
# CONTENIDO EXACTO:
cat > .env.production << 'EOF'
VITE_APP_TITLE=Smart Sales
VITE_API_URL=/api
VITE_STRIPE_PUBLISHABLE_KEY=disabled
EOF

# 1.3 Instalar dependencias
npm install

# 1.4 Compilar para producción
npm run build:prod

# ✅ Deberías ver:
# dist/ (carpeta creada)
# - assets/
# - images/
# - logo/
# - index.html

# 1.5 Verificar que index.html existe
ls dist/index.html
```

### PASO 2: Subir Frontend a EC2

```powershell
# 2.1 Desde PowerShell en tu PC
# (reemplaza ruta del .pem)

scp -i "D:\1NATALY\SISTEMAS DE INFORMACIÓN II\NUEVO GESTION_DOCUMENTAL\smartsales-key.pem" `
    -r dist ubuntu@52.0.69.138:~/ss_frontend/

# ✅ Deberías ver:
# Transferring file data.......................
# Sent X files
```

### PASO 3: Permisos en EC2

```bash
# 3.1 Conectar a EC2
ssh -i "D:\ruta\smartsales-key.pem" ubuntu@52.0.69.138

# 3.2 Dar permisos correctos a dist/
sudo chmod 755 /home/ubuntu/ss_frontend
sudo chmod -R 755 /home/ubuntu/ss_frontend/dist

# 3.3 Verificar
ls -la /home/ubuntu/ss_frontend/dist/ | head -5

# ✅ Deberías ver:
# drwxr-xr-x  5 ubuntu   ubuntu    4096 Nov  9 12:08 dist
```

### PASO 4: Verificar que todo funciona

```bash
# 4.1 En EC2, verificar servicios
sudo systemctl status smartsales-backend
sudo systemctl status nginx

# 4.2 Ver logs de nginx (sin errores)
sudo tail -10 /var/log/nginx/error.log
```

**Desde tu navegador:**

- 🌐 Frontend: `http://52.0.69.138`
- 📚 API Docs: `http://52.0.69.138/api/docs`

✅ ¡DEBE FUNCIONAR!

---

## 🐛 ERRORES ENCONTRADOS Y SOLUCIONES

### ❌ ERROR 1: "ERR_CONNECTION_REFUSED" en :8000

**Síntoma:**

```
POST http://52.0.69.138:8000/api/auth/login/ net::ERR_CONNECTION_REFUSED
```

**Causa:**
Frontend estaba intentando conectar directamente al puerto 8000, pero ese puerto no está expuesto públicamente.

**Solución:**

En `.env.production` del frontend:

```bash
# ❌ ANTES:
VITE_API_URL=http://52.0.69.138:8000/api

# ✅ DESPUÉS:
VITE_API_URL=/api
```

Esto hace que las llamadas se hagan localmente (`/api`) y Nginx las proxea a Gunicorn internamente.

**Comando rápido:**

```bash
# En EC2
sudo systemctl reload nginx
# Ya funciona sin cambiar nada del backend
```

---

### ❌ ERROR 2: "500 Internal Server Error" en frontend

**Síntoma:**

```
nginx: [crit] stat() "/home/ubuntu/ss_frontend/dist/index.html" failed (13: Permission denied)
```

**Causa:**
Permisos incorrectos. El directorio tiene `drwx---rwx` en lugar de `drwxr-xr-x`.

**Solución:**

```bash
# Limpiar dist viejo y crear nuevo con permisos correctos
sudo rm -rf /home/ubuntu/ss_frontend/dist
mkdir -p /home/ubuntu/ss_frontend/dist

# Desde tu PC, subir dist nuevamente
scp -i "ruta\smartsales-key.pem" -r dist ubuntu@52.0.69.138:~/ss_frontend/

# En EC2, dar permisos
sudo chmod -R 755 /home/ubuntu/ss_frontend/dist

# Reiniciar nginx
sudo systemctl reload nginx
```

---

### ❌ ERROR 3: "Port 8000 already in use"

**Síntoma:**

```
Address already in use
```

**Causa:**
Hay un proceso corriendo en el puerto 8000 (probablemente `python manage.py runserver` anterior).

**Solución:**

```bash
# Ver qué está en puerto 8000
sudo lsof -i :8000

# Matar el proceso
sudo fuser -k 8000/tcp

# O matar por PID específico
sudo kill -9 <PID>

# Reiniciar servicio
sudo systemctl restart smartsales-backend
```

---

### ❌ ERROR 4: S3 "AccessControlListNotSupported"

**Síntoma:**

```
botocore.exceptions.ClientError: An error occurred (AccessControlListNotSupported) when calling the PutObjectAcl operation
```

**Causa:**
El bucket S3 tiene ACLs deshabilitado pero Django intenta subir con ACLs.

**Solución:**

**OPCIÓN 1: Deshabilitar S3 (RECOMENDADA para dev/test)**

```bash
# En EC2, editar .env
nano .env

# Cambiar:
USE_S3=True   ❌
USE_S3=False  ✅

# Luego recolectar statics locales
python manage.py collectstatic --noinput --clear

# Reiniciar backend
sudo systemctl restart smartsales-backend
```

**OPCIÓN 2: Habilitar ACLs en S3**

1. Ir a: https://console.aws.amazon.com/s3
2. Seleccionar bucket
3. "Permissions" → "Block public access" → Editar
4. Desmarcar "Block all public access"
5. En "Access Control Lists (ACLs)", marcar "ACLs enabled"

---

### ❌ ERROR 5: TypeScript "Property not found"

**Síntoma:**

```
Property 'categoria_ids' does not exist on type 'CreateProductData'
```

**Causa:**
Frontend enviaba propiedades con nombres diferentes a las que esperaba el backend.

**Soluciones aplicadas:**

**En admin.service.ts:**

```typescript
// ❌ ANTES:
data.marca_id;
data.categoria_ids;
data.talla_ids;

// ✅ DESPUÉS:
data.marca; // sin "_id"
data.categorias; // plural, sin "_ids"
data.tallas_disponibles;
```

**En Address properties:**

```typescript
// ❌ ANTES:
address.calle;
address.numero_exterior;
address.estado;

// ✅ DESPUÉS:
address.direccion_linea1;
address.direccion_linea2;
address.departamento;
```

**En responses:**

```typescript
// ❌ ANTES:
setData(response.results || response);

// ✅ DESPUÉS:
setData(Array.isArray(response) ? response : response.results || []);
```

---

### ❌ ERROR 6: Nginx 404 en API Docs

**Síntoma:**

```
GET http://52.0.69.138/api/docs HTTP/1.1" 404 Not Found
```

**Causa:**
Nginx no estaba configurado para proxear `/api/` a Gunicorn.

**Solución:**

En `/etc/nginx/sites-available/smartsales`, agregar bloque:

```nginx
location /api/ {
    proxy_pass http://smartsales_backend;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

Luego:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

---

## ✅ VERIFICACIÓN FINAL

### Checklist de Funcionamiento

```bash
# En tu navegador:
✅ http://52.0.69.138              # Frontend debe cargar (React app)
✅ http://52.0.69.138/api/docs     # Swagger UI debe verse
✅ http://52.0.69.138/api/products # API debe responder JSON

# En terminal EC2:
✅ sudo systemctl status smartsales-backend  # Active: running
✅ sudo systemctl status nginx               # Active: running
✅ curl http://127.0.0.1:8000/api/docs      # 200 OK localmente
✅ curl http://127.0.0.1/api/docs           # 200 OK via Nginx

# Logs sin errores:
✅ sudo tail -20 /var/log/nginx/error.log   # Debe estar vacío o sin [crit]
✅ sudo journalctl -u smartsales-backend -n 10  # Debe estar limpio
```

---

## 🔄 MANTENIMIENTO Y ACTUALIZACIONES

### Actualizar código desde GitHub

```bash
# En EC2
cd ~/ss_backend
git pull origin main

# Instalar dependencias nuevas (si las hay)
source venv/bin/activate
pip install -r requirements.txt

# Ejecutar migraciones (si hay)
python manage.py migrate

# Recolectar statics
python manage.py collectstatic --noinput

# Reiniciar servicios
sudo systemctl restart smartsales-backend
sudo systemctl reload nginx
```

### Ver logs en tiempo real

```bash
# Backend
sudo journalctl -u smartsales-backend -f

# Nginx
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log

# Django errors
tail -f ~/ss_backend/logs/error.log
```

### Ejecutar scripts/management commands

```bash
# Desde tu PC (SSH remoto)
ssh -i "ruta\smartsales-key.pem" ubuntu@52.0.69.138 \
    "cd ~/ss_backend && source venv/bin/activate && python manage.py seed_data"

# O conectar SSH y ejecutar manual
ssh -i "ruta\smartsales-key.pem" ubuntu@52.0.69.138
cd ~/ss_backend
source venv/bin/activate
python manage.py seed_data
```

---

## 💬 FAQ Git y Sincronización

### ❓ ¿Debo hacer push desde EC2 a GitHub?

**❌ NO** - Razones:

1. EC2 tiene archivos `.env` con contraseñas que NO deben ir a GitHub
2. Crear conflictos entre tu PC local y EC2
3. Historial de Git se ensucia

**✅ FLUJO CORRECTO:**

```
Tu PC → git commit → git push origin main
    ↓
GitHub (main)
    ↓
EC2 → git pull origin main
```

### ❓ ¿Cómo configurar Git en EC2?

Si SOLO quieres leer (pull):

```bash
git config --global user.email "tu@email.com"
git config --global user.name "Tu Nombre"

# Solo eso es suficiente para git pull
```

### ❓ ¿Qué pasa si hago cambios en EC2?

**Opción 1: Crear rama local (no afecta GitHub)**

```bash
cd ~/ss_backend
git config user.email "tu@email.com"
git config user.name "Tu Nombre"

# Ver cambios
git status

# Crear rama local
git checkout -b deployment-nov-9-2025

# Commit local (nunca se sube)
git add .
git commit -m "Config de deployment"

# Verificar que está local
git branch
# * deployment-nov-9-2025
# main
```

**Opción 2: Ignorar archivos .env (mejor)**

En `.gitignore` del proyecto:

```
.env
.env.production
.env.local
```

Esto evita que `.env` se suba accidentalmente.

### ❓ ¿Y si necesito actualizar código en EC2?

```bash
# Descartar cambios locales (si existen)
git reset --hard

# Traer cambios nuevos de GitHub
git pull origin main

# Listo!
```

---

## 📋 SCRIPT RÁPIDO PARA PRÓXIMO DEPLOYMENT

```bash
#!/bin/bash
# Guardar como ~/deploy.sh
# Ejecutar: bash ~/deploy.sh

set -e

cd ~/ss_backend

echo "🔄 Actualizando código..."
git pull origin main

echo "🔧 Activando venv..."
source venv/bin/activate

echo "📦 Instalando dependencias..."
pip install -r requirements.txt -q

echo "🗄️ Ejecutando migraciones..."
python manage.py migrate --noinput

echo "📂 Recolectando statics..."
python manage.py collectstatic --noinput --clear -q

echo "🔄 Reiniciando servicios..."
sudo systemctl restart smartsales-backend
sleep 2
sudo systemctl reload nginx

echo "✅ Deployment completado!"
echo "🌐 Frontend: http://52.0.69.138"
echo "📚 API Docs: http://52.0.69.138/api/docs"
```

Usar:

```bash
chmod +x ~/deploy.sh
~/deploy.sh
```

---

## 🎓 CONCLUSIÓN

**Con esta guía:**

- ✅ Deployment reproducible y documentado
- ✅ Errores comunes y soluciones claras
- ✅ Security Groups correctamente configurados
- ✅ Frontend y Backend funcionando juntos
- ✅ Git sincronizado sin conflictos
- ✅ Listo para otros proyectos

**Próximos pasos para producción real:**

- HTTPS con Let's Encrypt
- Backups automáticos en S3
- Monitoreo con CloudWatch
- Auto-scaling groups
- RDS Multi-AZ (alta disponibilidad)

---

**Actualizado:** Noviembre 9, 2025
**Autor:** Deployment SmartSales365
**Status:** ✅ COMPLETADO Y TESTEADO
