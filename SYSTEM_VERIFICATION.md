# ✅ SISTEMA VERIFICATION CHECKLIST

## 🔍 PRE-VERIFICACIÓN (Antes de Empezar)

### Requisitos del Sistema

- [ ] Windows 10/11 o Linux/Mac
- [ ] Python 3.9+ instalado: `python --version`
- [ ] Node.js 18+ instalado: `node --version`
- [ ] PostgreSQL 12+ corriendo
- [ ] Git configurado

### Verificar Instalaciones

```powershell
# Verificar Python
python --version  # Debe ser 3.9 o superior

# Verificar Node.js
node --version  # Debe ser 18 o superior
npm --version

# Verificar PostgreSQL
psql --version  # Debe estar instalado

# Verificar Git
git --version
```

---

## 🔧 SETUP INICIAL

### Backend Setup

- [ ] Crear virtual environment
```bash
python -m venv venv
```

- [ ] Activar virtual environment
```powershell
# Windows
.\venv\Scripts\Activate.ps1

# Linux/Mac
source venv/bin/activate
```

- [ ] Instalar dependencias
```bash
cd cr_backend
pip install -r requirements.txt
```

- [ ] Crear archivo `.env`
```
DEBUG=True
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://postgres:password@localhost:5432/cr_system
```

- [ ] Crear base de datos
```bash
python manage.py migrate
```

- [ ] Crear superusuario
```bash
python manage.py createsuperuser
```

- [ ] Correr seed data
```bash
python run_seeder.py
```

### Frontend Setup

- [ ] Instalar dependencias
```bash
cd cr_frontend
npm install
```

- [ ] Crear archivo `.env.local`
```
VITE_API_BASE_URL=http://localhost:8000/api
VITE_APP_NAME=CR System
```

- [ ] Verificar que no hay errores TypeScript
```bash
npm run type-check
```

---

## 🚀 SERVICIOS CORRIENDO

### Verificar Backend

- [ ] Servidor Django corriendo
```bash
cd cr_backend
python manage.py runserver
# Debe mostrar: "Starting development server at http://127.0.0.1:8000/"
```

- [ ] Accesible en http://localhost:8000
- [ ] API accesible en http://localhost:8000/api/
- [ ] Admin accesible en http://localhost:8000/admin/
- [ ] Logs creados en `logs/django.log`

### Verificar Frontend

- [ ] Servidor Vite corriendo
```bash
cd cr_frontend
npm run dev
# Debe mostrar: "Local: http://localhost:5173/"
```

- [ ] Accesible en http://localhost:5173
- [ ] No hay errores en consola (F12)

### Verificar PostgreSQL

- [ ] PostgreSQL corriendo
```powershell
Get-Service | Where-Object {$_.Name -like "*postgre*"}
# Debe mostrar: Status: Running
```

- [ ] Base de datos `cr_system` existe
```bash
psql -U postgres -l | grep cr_system
```

---

## 🔐 AUTENTICACIÓN

### Verificar Login

- [ ] Endpoint `/api/login/` responde
```bash
curl -X POST http://localhost:8000/api/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "admin123"}'
```

**Esperado:** Status 200 + tokens (access, refresh)

- [ ] Token se guarda en localStorage
```javascript
// Consola del navegador (F12)
console.log(localStorage.getItem('access_token'))
```

- [ ] Token se envía en requests
```bash
curl -X GET http://localhost:8000/api/users/me/ \
  -H "Authorization: Bearer {TOKEN}"
```

**Esperado:** Status 200 + datos del usuario

---

## 🎭 RBAC (Role-Based Access Control)

### Verificar Roles

- [ ] Roles existen en BD
```bash
python manage.py shell
>>> from core.models import Role
>>> Role.objects.all()
```

- [ ] Endpoint `/api/roles/` funciona
```bash
curl -X GET http://localhost:8000/api/roles/ \
  -H "Authorization: Bearer {TOKEN}"
```

- [ ] Al menos 3 roles exist: Admin, Doctor, Patient

### Verificar Permisos

- [ ] Permisos existen en BD
```bash
python manage.py shell
>>> from core.models import Permission
>>> Permission.objects.all()
```

- [ ] Endpoint `/api/permissions/` funciona
```bash
curl -X GET http://localhost:8000/api/permissions/ \
  -H "Authorization: Bearer {TOKEN}"
```

- [ ] Permisos asignados a roles
```bash
python manage.py shell
>>> from core.models import Role
>>> role = Role.objects.first()
>>> role.permissions.all()
```

### Verificar RBAC en Frontend

- [ ] `PermissionsService` está cargando permisos
```javascript
// Consola navegador (F12)
import { permissionsService } from '@/core/services';
permissionsService.hasPermission('users.view').then(console.log)
```

- [ ] Componentes respetan permisos
```typescript
// Debe mostrar solo si tiene permiso
<CanAccess permission="users.create">
  <button>Crear Usuario</button>
</CanAccess>
```

- [ ] Guards protegen rutas
```typescript
// Debe redirigir si no tiene permiso
<PermissionRoute permission="admin" fallback={<AccessDenied />}>
  <AdminPanel />
</PermissionRoute>
```

---

## 📊 API ENDPOINTS

### Autenticación

- [ ] GET `/api/login/` - POST login → Status 200
- [ ] GET `/api/logout/` - POST logout → Status 200
- [ ] GET `/api/refresh/` - POST refresh token → Status 200
- [ ] GET `/api/users/me/` - GET usuario actual → Status 200

### Usuarios

- [ ] GET `/api/users/` - Listar → Status 200
- [ ] POST `/api/users/` - Crear → Status 201
- [ ] GET `/api/users/{id}/` - Obtener → Status 200
- [ ] PUT `/api/users/{id}/` - Actualizar → Status 200
- [ ] DELETE `/api/users/{id}/` - Eliminar → Status 204

### Roles

- [ ] GET `/api/roles/` - Listar → Status 200
- [ ] POST `/api/roles/` - Crear → Status 201
- [ ] GET `/api/roles/{id}/` - Obtener → Status 200
- [ ] PUT `/api/roles/{id}/` - Actualizar → Status 200
- [ ] DELETE `/api/roles/{id}/` - Eliminar → Status 204

### Permisos

- [ ] GET `/api/permissions/` - Listar → Status 200
- [ ] POST `/api/permissions/` - Crear → Status 201
- [ ] GET `/api/permissions/{id}/` - Obtener → Status 200

---

## 🗄️ BASE DE DATOS

### Verificar Estructura

- [ ] Tabla `core_user` existe
```bash
python manage.py shell
>>> from django.apps import apps
>>> apps.get_models()
```

- [ ] Tabla `core_role` existe
- [ ] Tabla `core_permission` existe
- [ ] Tabla `core_role_permissions` existe (relación)

### Verificar Datos

- [ ] Al menos 1 usuario existe
```bash
python manage.py shell
>>> from core.models import User
>>> User.objects.count()
```

- [ ] Al menos 3 roles existen
- [ ] Al menos 5 permisos existen
- [ ] Usuario admin tiene todos los permisos

---

## 📝 LOGGING

### Verificar Logs

- [ ] Archivo `logs/django.log` existe
```powershell
Test-Path cr_backend\logs\django.log
```

- [ ] Logs se están escribiendo
```powershell
Get-Content cr_backend\logs\django.log | Measure-Object -Line
# Debe mostrar más de 0 líneas
```

- [ ] Script `watch_logs.ps1` funciona
```powershell
cd cr_backend
.\watch_logs.ps1
# Debe mostrar logs en tiempo real
```

### Verificar Contenido de Logs

- [ ] Contiene requests HTTP
```powershell
Get-Content cr_backend\logs\django.log | Select-String "GET|POST|PUT|DELETE"
```

- [ ] Contiene timestamps
- [ ] No tiene errores 500 recientes
```powershell
Get-Content cr_backend\logs\django.log | Select-String "ERROR" | Tail -10
```

---

## 🔌 INTEGRACIÓN FRONTEND-BACKEND

### CORS

- [ ] Sin errores CORS en consola (F12)
- [ ] Requests desde localhost:5173 → localhost:8000 funcionan

### Rutas API

- [ ] Frontend usa rutas correctas (sin `/auth/` prefix)
  - `/api/users/` ✅
  - `/api/roles/` ✅
  - `/api/permissions/` ✅
  - `/api/auth/users/` ❌ (antiguo)

- [ ] Archivo `users.service.ts` actualizado
```bash
grep -n "auth/users\|auth/roles" cr_frontend/src/modules/users/services/users.service.ts
# Debe retornar 0 resultados (sin coincidencias)
```

### Types/Interfaces

- [ ] No hay errores TypeScript en frontend
```bash
cd cr_frontend
npm run type-check
# Debe completar sin errores
```

- [ ] Interfaces son compatibles
  - Role interface compatible con RoleDetail
  - User interface tiene todos los campos requeridos

---

## ✨ CARACTERÍSTICAS PRINCIPALES

### US-1: Sistema de Notificaciones

- [ ] Notificaciones se crean en BD
- [ ] Endpoint `/api/notifications/` funciona
- [ ] Frontend muestra notificaciones
- [ ] Marcar como leída funciona
- [ ] Preferencias de notificaciones funciona

### US-2: RBAC (Roles y Permisos)

- [ ] Roles CRUD funciona
- [ ] Permisos CRUD funciona
- [ ] Asignar permisos a roles funciona
- [ ] Verificación de permisos funciona
- [ ] Frontend carga permisos dinámicamente
- [ ] Componentes respetan permisos
- [ ] Rutas protegidas funcionan

### US-3: Búsqueda Avanzada (Próximo)

- [ ] Filtros en backend implementados
- [ ] Paginación funciona
- [ ] Búsqueda por múltiples campos
- [ ] Ordenamiento funciona

---

## 🧪 TESTING MANUAL

### Flujo Completo: Crear Usuario

1. [ ] Ir a http://localhost:5173
2. [ ] Login con admin@example.com / admin123
3. [ ] Ir a Users
4. [ ] Click "Create User"
5. [ ] Llenar formulario:
   - Email: newuser@test.com
   - Name: Test User
   - Role: Doctor
6. [ ] Submit
7. [ ] Verificar en tabla
8. [ ] Verificar en BD: `SELECT * FROM core_user WHERE email='newuser@test.com';`

### Flujo Completo: Asignar Permiso

1. [ ] Ir a Admin → Roles
2. [ ] Editar rol "Doctor"
3. [ ] Agregar permiso "users.create"
4. [ ] Save
5. [ ] Verificar en BD
6. [ ] Verificar en frontend que el usuario ahora puede crear

### Flujo Completo: Documento

1. [ ] Crear paciente
2. [ ] Ir a paciente
3. [ ] Click "Upload Document"
4. [ ] Subir PDF
5. [ ] Verificar en tabla
6. [ ] Descargar documento
7. [ ] Verificar en BD: logs de acceso

---

## 🐛 PROBLEMAS CONOCIDOS

### Problema: "404 Not Found: /api/auth/users/"

**Estado:** ✅ RESUELTO
- Causa: Rutas antiguas en frontend
- Solución: Actualizar users.service.ts (hecho)
- Verificación: `grep -r "auth/users" cr_frontend/src/`

### Problema: "401 Unauthorized"

**Estado:** ⚠️ NORMAL (después de logout)
- Solución: Hacer login nuevamente
- Verificación: Token en localStorage

### Problema: "CORS error"

**Estado:** ⚠️ CONOCIDO si no está configurado
- Solución: django-cors-headers configurado
- Verificación: Ver `config/settings/development.py`

---

## 📋 DEPLOYMENT CHECKLIST

**Antes de pasar a producción:**

- [ ] DEBUG = False en settings
- [ ] SECRET_KEY es seguro (usar variables de entorno)
- [ ] ALLOWED_HOSTS configurado correctamente
- [ ] Database en servidor separado
- [ ] HTTPS habilitado
- [ ] Logs rotados periódicamente
- [ ] Backups configurados
- [ ] Errores 500 se envían por email
- [ ] Static files collectados
- [ ] Celery configurado para tasks asíncronas
- [ ] Redis configurado para cache

---

## 📞 VERIFICACIÓN FINAL

Ejecutar este script para verificación rápida:

```powershell
# script: quick_verify.ps1

Write-Host "=== QUICK VERIFICATION ===" -ForegroundColor Cyan

# 1. Backend
$backend = curl -s -X OPTIONS http://localhost:8000/api/login/
if ($backend) { Write-Host "✅ Backend OK" -ForegroundColor Green } 
else { Write-Host "❌ Backend FAIL" -ForegroundColor Red }

# 2. Frontend  
$frontend = curl -s http://localhost:5173/ 2>$null
if ($frontend) { Write-Host "✅ Frontend OK" -ForegroundColor Green }
else { Write-Host "❌ Frontend FAIL" -ForegroundColor Red }

# 3. Database
$db = psql -U postgres -l 2>$null | grep cr_system
if ($db) { Write-Host "✅ Database OK" -ForegroundColor Green }
else { Write-Host "❌ Database FAIL" -ForegroundColor Red }

# 4. Logs
$logs = Get-Item cr_backend\logs\django.log 2>$null
if ($logs) { Write-Host "✅ Logging OK" -ForegroundColor Green }
else { Write-Host "❌ Logging FAIL" -ForegroundColor Red }

Write-Host "`n=== END VERIFICATION ===" -ForegroundColor Cyan
```

---

## 🎯 ESTADO ACTUAL DEL PROYECTO

**Completado:**
- ✅ Backend API (90%)
- ✅ Authentication & JWT
- ✅ RBAC System (Dynamic)
- ✅ Multi-tenancy
- ✅ Logging Infrastructure
- ✅ Frontend Integration
- ✅ Type Safety (TypeScript)

**En Progreso:**
- 🔄 US-2: Notificaciones (90%)
- 🔄 US-3: Búsqueda Avanzada (planeado)

**Próximos:**
- 📋 US-4: Reportes Avanzados
- 📋 US-5: Exportación de Datos
- 📋 US-6: Analytics Dashboard

---

**Última actualización:** Noviembre 2025  
**Versión:** 1.0.0  
**Status:** ✅ Sistema Operacional

## ⭐ Feedback

Si encuentras problemas:
1. Ejecutar `quick_verify.ps1`
2. Ver `TROUBLESHOOTING_GUIDE.md`
3. Revisar logs en `logs/django.log`
4. Consultar `API_ENDPOINTS_REFERENCE.md`
5. Crear issue en GitHub
