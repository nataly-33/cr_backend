# 🚀 GUÍA DE ACCESO RÁPIDO - CliniDocs Backend

## ✅ Estado Actual

| Componente | Estado | Detalles |
|-----------|--------|---------|
| **Base de Datos** | ✅ PostgreSQL | Conectada y configurada (`cr_db`) |
| **Migraciones** | ✅ Aplicadas | Todas las apps sincronizadas |
| **Autenticación JWT** | ✅ Funcional | Login y refresh tokens working |
| **Superusuario** | ✅ Activo | `superadmin@clinidocs.com` |
| **API Swagger** | ✅ Disponible | En `/api/docs/` |

---

## 🔐 Credenciales de Acceso

### ⭐ Superadmin (Admin Super Usuario)
```json
{
  "email": "superadmin@clinidocs.com",
  "password": "Superadmin123!"
}
```

**Características:**
- Acceso a TODOS los tenants (hospitales)
- Puede ver y gestionar múltiples tenants
- Sin tenant específico asignado
- ⚠️ **LIMITACIÓN**: No puede acceder a endpoints de pacientes (requieren tenant)

---

### 🏥 Hospital General Santa Cruz

#### Administrador TI (Recomendado para testing)
```json
{
  "email": "admin@hospital-santacruz.com",
  "password": "Password123!"
}
```

**Permisos:**
- ✅ CRUD completo de pacientes
- ✅ CRUD completo de historias clínicas
- ✅ CRUD completo de documentos
- ✅ Gestión de usuarios y roles
- ✅ Acceso a auditoría

#### Doctor
```json
{
  "email": "doctor1@hospital-santacruz.com",
  "password": "Password123!"
}
```

**Permisos:**
- ✅ CRUD de historias clínicas
- ✅ CRUD de documentos
- ✅ Lectura de pacientes

#### Paciente
```json
{
  "email": "paciente1@hospital-santacruz.com",
  "password": "Password123!"
}
```

**Permisos:**
- ✅ Lectura de SU propia historia clínica
- ✅ Lectura de SUS propios documentos

---

### 🏥 Clínica Médica La Paz

#### Administrador TI
```json
{
  "email": "admin@clinica-lapaz.com",
  "password": "Password123!"
}
```

#### Doctor
```json
{
  "email": "doctor1@clinica-lapaz.com",
  "password": "Password123!"
}
```

#### Paciente
```json
{
  "email": "paciente1@clinica-lapaz.com",
  "password": "Password123!"
}
```

---

## 🌐 Endpoints de Autenticación

### 1. Login - Obtener Tokens
```bash
POST /api/auth/login/

Body:
{
  "email": "superadmin@clinidocs.com",
  "password": "Superadmin123!"
}

Response:
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": "...",
    "email": "superadmin@clinidocs.com",
    "full_name": "Super Administrador",
    "is_active": true,
    ...
  }
}
```

### 2. Refresh Token - Obtener nuevo Access Token
```bash
POST /api/auth/refresh/

Body:
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}

Response:
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

---

## 🎯 Endpoints Principales

### Documentación Interactiva
- **Swagger UI**: http://localhost:8000/api/docs/
- **ReDoc**: http://localhost:8000/api/redoc/
- **Schema OpenAPI**: http://localhost:8000/api/schema/

### Rutas de API
| Módulo | Endpoint | Descripción |
|--------|----------|------------|
| Autenticación | `/api/auth/login/` | Login con email/password |
| Autenticación | `/api/auth/refresh/` | Refrescar token |
| Usuarios | `/api/auth/users/` | CRUD de usuarios |
| Roles | `/api/auth/roles/` | CRUD de roles |
| Pacientes | `/api/patients/` | CRUD de pacientes |
| Historias Clínicas | `/api/clinical-records/` | CRUD de historias |
| Documentos | `/api/documents/` | CRUD de documentos clínicos |
| Auditoría | `/api/audit/` | Logs de auditoría |
| Reportes | `/api/reports/` | Sistema de reportes |

---

## 🛠️ Comandos Útiles

### Activar Servidor de Desarrollo
```powershell
# Opción 1: Usar script PowerShell (recomendado)
cd cr_backend
.\runserver.ps1

# Opción 2: Usar script Batch (CMD)
runserver.bat

# Opción 3: Activar venv manualmente
& '.\.venv\Scripts\Activate.ps1'
python manage.py runserver

# Opción 4: Con puerto personalizado
.\runserver.ps1 -Port 8080
```

### Ver estado de la BD
```bash
python manage.py dbshell
```

### Crear migraciones
```bash
python manage.py makemigrations
python manage.py migrate
```

### Cargar datos de prueba (próximo paso)
```bash
python scripts/seed_data.py
```

---

## 📋 Próximos Pasos

1. ✅ **Datos de prueba cargados** - Ya ejecutado `seed_data.py`
   - ✅ 2 tenants creados (Hospital Santa Cruz + Clínica La Paz)
   - ✅ 3 roles por tenant (Admin TI, Doctor, Paciente)
   - ✅ 11 usuarios de prueba
   - ✅ 70 pacientes de ejemplo
   - ✅ 70 historias clínicas
   - ✅ 54 documentos de ejemplo

2. **Acceder a Swagger y probar endpoints**
   - Ir a http://localhost:8000/api/docs/
   - Usar credenciales del **Admin del Hospital Santa Cruz**:
     - Email: `admin@hospital-santacruz.com`
     - Password: `Password123!`
   - Hacer click en "Authorize" y paste el access token
   - Explorar endpoints disponibles

3. **Integrar con Frontend**
   - Frontend en `cr_frontend/`
   - URL base: `http://localhost:8000`
   - CORS configurado para puertos 3000 y 5173
   - Usar credenciales del Hospital para login

---

## ⚠️ Nota Importante Sobre Multi-Tenancy

El sistema está diseñado como **multi-tenant**:

- **Superusuario**: Puede ver info de TODOS los tenants pero NO puede acceder a endpoints de pacientes (por diseño)
- **Admin del Tenant**: Puede ver y gestionar todos los datos de SU tenant
- **Paciente**: Solo puede ver SUS propios datos

Para probar la API desde el frontend o Swagger, **usa las credenciales de un Admin de tenant** (no el superusuario)

---

## 🔧 Variables de Entorno (.env)

```
# Django
DEBUG=True
SECRET_KEY=django-insecure-dev-key-change-in-production
ALLOWED_HOSTS=localhost,127.0.0.1,testserver

# Database
DATABASE_ENGINE=postgresql
DATABASE_HOST=localhost
DATABASE_NAME=cr_db
DATABASE_USER=postgres
DATABASE_PASSWORD=Mipeluche123
DATABASE_PORT=5432

# Redis
REDIS_URL=redis://localhost:6379/0

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173

# JWT
JWT_ACCESS_TOKEN_LIFETIME=60
JWT_REFRESH_TOKEN_LIFETIME=1440
```

---

## 🚨 Troubleshooting

### Error: "La combinación de credenciales no tiene una cuenta activa"
**Solución:** Resetear contraseña del usuario
```bash
python manage.py shell
from apps.accounts.models import User
u = User.objects.get(email='superadmin@clinidocs.com')
u.set_password('Superadmin123!')
u.save()
```

### Error: "Invalid HTTP_HOST header"
**Solución:** Agregar host a `ALLOWED_HOSTS` en `.env`
```
ALLOWED_HOSTS=localhost,127.0.0.1,your-host
```

### Error: "No module named 'celery'"
**Solución:** Celery no está completamente configurado aún. Es opcional para desarrollo.

---

## 📖 Documentación

- [DEVELOPMENT_GUIDE.md](./DEVELOPMENT_GUIDE.md) - Guía completa de desarrollo
- [README.md](./README.md) - README del proyecto
- [db_schema_final.sql](./db_schema_final.sql) - Esquema de base de datos

---

**Última actualización:** 3 de Noviembre de 2025  
**Estado:** ✅ Backend Listo para Desarrollo

