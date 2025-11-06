# 🏗️ ARQUITECTURA DE DEPLOYMENT - CLINIC RECORDS

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           INTERNET / USUARIOS                            │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ HTTP/HTTPS
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         EC2 (t3.micro - FREE TIER)                       │
│                        IP: 3.85.212.201                                  │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                         NGINX (Port 80)                          │   │
│  │                    (Reverse Proxy + Static)                      │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│            │                                        │                     │
│            │ Proxy Pass                            │ Serve Static        │
│            ▼                                        ▼                     │
│  ┌────────────────────────┐            ┌────────────────────────┐       │
│  │  BACKEND (Port 8000)   │            │  FRONTEND (Port 5173)  │       │
│  │  Django + Gunicorn     │            │  React + Vite          │       │
│  │  - API REST            │            │  - SPA Build           │       │
│  │  - Admin Panel         │            │  - Static Files        │       │
│  │  - 3 Workers           │            │  - index.html          │       │
│  └────────────────────────┘            └────────────────────────┘       │
│            │                                                              │
│            │ Reads .env                                                  │
│            ▼                                                              │
│  ┌────────────────────────────────────────────────────────────────┐     │
│  │                     Environment Variables                       │     │
│  │  - DATABASE_HOST, DATABASE_NAME, DATABASE_PASSWORD              │     │
│  │  - AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY                     │     │
│  │  - SENDGRID_API_KEY, CORS_ORIGINS, etc.                         │     │
│  └────────────────────────────────────────────────────────────────┘     │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘
         │                          │                         │
         │ PostgreSQL               │ S3 API                  │ SMTP
         ▼                          ▼                         ▼
┌──────────────────┐    ┌──────────────────────┐    ┌──────────────────┐
│   RDS PostgreSQL │    │    S3 Bucket         │    │    SendGrid      │
│  (db.t3.micro)   │    │ clinidocs-files-2025 │    │   Email Service  │
│  FREE TIER       │    │   FREE TIER (5GB)    │    │   (Opcional)     │
│                  │    │                      │    │                  │
│  - clinidocs_db  │    │  ├─ backups/        │    │  - Notificaciones│
│  - Historias     │    │  ├─ documents/      │    │  - Recuperación  │
│  - Pacientes     │    │  ├─ images/         │    │  - Alertas       │
│  - Usuarios      │    │  └─ temp/           │    │                  │
└──────────────────┘    └──────────────────────┘    └──────────────────┘
```

---

## 🔐 SECURITY GROUPS (Firewall)

```
┌─────────────────────────────────────────────────────────────────┐
│               EC2 Security Group - Inbound Rules                 │
├────────────────┬──────────┬─────────────┬────────────────────────┤
│ Type           │ Port     │ Source      │ Purpose                │
├────────────────┼──────────┼─────────────┼────────────────────────┤
│ SSH            │ 22       │ My IP       │ Administración         │
│ HTTP           │ 80       │ 0.0.0.0/0   │ Tráfico web            │
│ HTTPS          │ 443      │ 0.0.0.0/0   │ Tráfico web seguro     │
│ Custom TCP     │ 8000     │ 0.0.0.0/0   │ Backend Django         │
│ Custom TCP     │ 5173     │ 0.0.0.0/0   │ Frontend Vite          │
└────────────────┴──────────┴─────────────┴────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│               RDS Security Group - Inbound Rules                 │
├────────────────┬──────────┬─────────────┬────────────────────────┤
│ Type           │ Port     │ Source      │ Purpose                │
├────────────────┼──────────┼─────────────┼────────────────────────┤
│ PostgreSQL     │ 5432     │ EC2 SG      │ Desde EC2 solamente    │
└────────────────┴──────────┴─────────────┴────────────────────────┘
```

---

## 📊 FLUJO DE DATOS

### 1. Usuario accede a la aplicación

```
Usuario Browser
    │
    ├─→ http://3.85.212.201:5173
    │      │
    │      └─→ Nginx Port 5173 → Frontend React (SPA)
    │
    └─→ Frontend hace requests AJAX
           │
           └─→ http://3.85.212.201:8000/api/...
                  │
                  └─→ Nginx Port 80 → Proxy Pass → Backend Django
```

### 2. Backend procesa request

```
Backend Django (Gunicorn)
    │
    ├─→ Middleware
    │   ├─ TenantMiddleware (identifica tenant por JWT)
    │   ├─ AuthMiddleware (valida token)
    │   └─ CorsMiddleware (CORS headers)
    │
    ├─→ View
    │   └─ Procesa lógica de negocio
    │
    ├─→ Model
    │   └─→ PostgreSQL RDS
    │       └─ Query/Insert/Update datos
    │
    ├─→ Storage (si sube archivo)
    │   └─→ S3 Bucket
    │       └─ Upload documento/imagen
    │
    └─→ Serializer
        └─ JSON Response → Frontend
```

### 3. Frontend renderiza

```
Frontend React
    │
    ├─→ Recibe JSON del backend
    │
    ├─→ Store (Zustand)
    │   └─ Actualiza estado global
    │
    └─→ Components
        └─ Re-render UI
```

---

## 🔄 PROCESO DE DEPLOYMENT

```
┌────────────────┐
│  Local Machine │
│  (Windows)     │
└────────────────┘
        │
        │ 1. git push origin main
        ▼
┌────────────────┐
│  GitHub Repo   │
└────────────────┘
        │
        │ 2. git clone / git pull
        ▼
┌────────────────────────────────┐
│  EC2 Instance                  │
│                                │
│  3. ./deploy.sh                │
│     ├─ Create venv             │
│     ├─ Install dependencies    │
│     ├─ Migrate DB              │
│     ├─ Collect static          │
│     └─ Restart Gunicorn        │
│                                │
│  4. npm run build              │
│     └─ Generate dist/          │
│                                │
│  5. Restart Nginx              │
└────────────────────────────────┘
        │
        │ 6. Servir aplicación
        ▼
┌────────────────────────────┐
│  Users Access              │
│  http://3.85.212.201:5173  │
└────────────────────────────┘
```

## 🏗️ ARQUITECTURA DEL SISTEMA

```
┌─────────────────────────────────────────────────────────────┐
│                      INTERNET / USUARIOS                     │
└─────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                    EC2 (3.85.212.201)                        │
│  ┌─────────────┐           ┌──────────────┐                │
│  │   NGINX     │──────────▶│   Backend    │                │
│  │   (Port 80) │           │   (Port 8000)│                │
│  └─────────────┘           └──────────────┘                │
│         │                                                    │
│         └────────────▶ Frontend (Port 5173)                 │
└─────────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│   RDS       │      │     S3      │      │  SendGrid   │
│ PostgreSQL  │      │   Bucket    │      │   (Email)   │
└─────────────┘      └─────────────┘      └─────────────┘

---

## 🗂️ ESTRUCTURA DE ARCHIVOS EN EC2

```

/home/ubuntu/
└── clinic_records/
├── cr_backend/
│ ├── .env # ⚠️ Configuración de producción
│ ├── venv/ # Entorno virtual Python
│ ├── manage.py
│ ├── requirements.txt
│ ├── apps/
│ ├── config/
│ │ └── settings/
│ │ └── production.py # Settings de producción
│ ├── logs/
│ │ ├── django.log
│ │ ├── gunicorn-access.log
│ │ └── gunicorn-error.log
│ ├── staticfiles/ # Archivos estáticos recolectados
│ └── media/ # Backups locales (S3 es primario)
│
└── cr_frontend/
├── .env # ⚠️ Configuración de producción
├── dist/ # Build de producción (servido por Nginx)
│ ├── index.html
│ └── assets/
├── src/
├── package.json
└── vite.config.ts

```

---

## ⚙️ SERVICIOS SYSTEMD

```

/etc/systemd/system/
└── clinidocs-backend.service # Backend Django + Gunicorn

Comandos:
sudo systemctl start clinidocs-backend
sudo systemctl stop clinidocs-backend
sudo systemctl restart clinidocs-backend
sudo systemctl status clinidocs-backend
sudo journalctl -u clinidocs-backend -f

```

---

## 🌐 CONFIGURACIÓN NGINX

```

/etc/nginx/
├── sites-available/
│ └── clinidocs # Configuración principal
└── sites-enabled/
└── clinidocs → ../sites-available/clinidocs

Comandos:
sudo nginx -t # Test config
sudo systemctl restart nginx
sudo systemctl status nginx
sudo tail -f /var/log/nginx/error.log

````

---

## 🔑 VARIABLES DE ENTORNO CRÍTICAS

```env
# BACKEND (.env)
DJANGO_SETTINGS_MODULE=config.settings.production
SECRET_KEY=***                            # Django secret
DEBUG=False                               # SIEMPRE False en producción

DATABASE_HOST=clinidocs-db.cexcc...      # RDS endpoint
DATABASE_NAME=clinidocs_db
DATABASE_USER=clinidocs_user
DATABASE_PASSWORD=***

AWS_ACCESS_KEY_ID=AKIA***                # Usuario IAM
AWS_SECRET_ACCESS_KEY=***
AWS_STORAGE_BUCKET_NAME=clinidocs-files-2025

CORS_ALLOWED_ORIGINS=http://3.85.212.201:5173
FRONTEND_URL=http://3.85.212.201:5173

SENDGRID_API_KEY=SG.***
````

```env
# FRONTEND (.env)
VITE_API_URL=http://3.85.212.201:8000/api
```

---

## 💰 COSTOS MENSUALES (FREE TIER)

| Servicio      | Tipo        | Uso                 | Costo           |
| ------------- | ----------- | ------------------- | --------------- |
| EC2           | t3.micro    | 750h/mes            | $0 (año 1)      |
| RDS           | db.t3.micro | 750h/mes            | $0 (año 1)      |
| S3            | Storage     | 5 GB                | $0 (permanente) |
| S3            | Requests    | 2000 PUT, 20000 GET | $0 (permanente) |
| Data Transfer | Outbound    | 1 GB                | $0 (permanente) |
| **TOTAL**     |             |                     | **$0/mes** ✅   |

**Después del primer año:**

- EC2 t3.micro: ~$10/mes
- RDS db.t3.micro: ~$15/mes
- S3: ~$0.50/mes
- **Total: ~$25/mes**

---

## 📈 ESCALABILIDAD FUTURA

```
┌─────────────────────────────────────────────────────────┐
│              OPCIÓN 1: Agregar Load Balancer             │
│                                                           │
│  Internet → ALB → EC2-1 (Backend)                        │
│                 → EC2-2 (Backend)                        │
│                 → EC2-3 (Backend)                        │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│         OPCIÓN 2: Separar Frontend y Backend            │
│                                                           │
│  ├─ Frontend → S3 Static Hosting + CloudFront           │
│  └─ Backend  → EC2 + Auto Scaling                       │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│           OPCIÓN 3: Containerización (Docker)            │
│                                                           │
│  ├─ Backend  → ECS Fargate                              │
│  ├─ Frontend → ECS Fargate                              │
│  └─ Database → RDS (sin cambios)                        │
└─────────────────────────────────────────────────────────┘
```

---

## 🎯 URLS DE ACCESO

**Producción:**

- 🏠 Home/Login: http://3.85.212.201:5173
- 📋 Dashboard: http://3.85.212.201:5173/dashboard
- 👥 Pacientes: http://3.85.212.201:5173/patients
- 📄 Historias: http://3.85.212.201:5173/clinical-records
- 🔧 API Docs: http://3.85.212.201/api/docs/
- 👤 Admin: http://3.85.212.201/admin/

**Desarrollo:**

- Frontend: http://localhost:5173
- Backend: http://localhost:8000

---

**DIAGRAMA CREADO:** Noviembre 5, 2025  
**VERSIÓN:** 1.0
