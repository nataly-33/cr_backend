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
   icacls "tu-archivo.pem" /inheritance:r
   icacls "tu-archivo.pem" /grant:r "$($env:USERNAME):(R)"
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

- http://3.85.212.201:8000/api/docs/

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
scp -i "D:\path\to\clinidocs-key.pem" -r dist ubuntu@3.85.212.201:~/cr_frontend/
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

**Creado por:** Nataly Vanessa
**Fecha:** Noviembre 5, 2025
**Versión:** 2.0 (con errores y soluciones)

¡Éxito en tu defensa! 🚀
