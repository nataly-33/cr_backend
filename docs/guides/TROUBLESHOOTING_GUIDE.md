# 🔧 TROUBLESHOOTING GUIDE - RESOLUCIÓN DE PROBLEMAS

## 🚨 PROBLEMAS COMUNES

---

## 1️⃣ Error: "Not Found: /api/auth/users/"

### Síntomas
```
404 Not Found: /api/auth/users/
GET /api/auth/users/ HTTP/1.1" 404 10765
```

### Causa
La ruta cambió de `/api/auth/users/` a `/api/users/`. El frontend aún usa rutas antiguas.

### Solución
**Archivo:** `cr_frontend/src/modules/users/services/users.service.ts`

Verificar que las rutas sean:
```typescript
// ✅ CORRECTO
getAllUsers: async (): Promise<PaginatedResponse<User>> => {
  return await apiService.get<PaginatedResponse<User>>("/users/");
};

getRoles: async (): Promise<PaginatedResponse<Role>> => {
  return await apiService.get<PaginatedResponse<Role>>("/roles/");
};

getPermissions: async (): Promise<PaginatedResponse<Permission>> => {
  return await apiService.get<PaginatedResponse<Permission>>("/permissions/");
};

// ❌ INCORRECTO (uso antiguo)
// return await apiService.get<PaginatedResponse<User>>("/auth/users/");
// return await apiService.get<PaginatedResponse<Role>>("/auth/roles/");
```

---

## 2️⃣ Error: "401 Unauthorized"

### Síntomas
```
401 Unauthorized: /api/users/me/
```
En el navegador: Login fallido, redirige a login infinitamente

### Causa
- Token expirado
- Token inválido
- Headers de autorización incorrectos
- Token no está siendo enviado

### Solución Paso a Paso

1. **Verificar token en localStorage**
```javascript
// En la consola del navegador (F12)
console.log(localStorage.getItem('access_token'));
console.log(localStorage.getItem('refresh_token'));
```

2. **Hacer login nuevamente**
```bash
curl -X POST http://localhost:8000/api/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "password123"
  }'
```

3. **Verificar formato de header**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiI...
```

4. **Comprobar credenciales**
- Email correcto
- Contraseña correcta
- Usuario activo en BD

---

## 3️⃣ Error: "403 Forbidden"

### Síntomas
```
403 Forbidden: /api/users/
POST /api/users/ HTTP/1.1" 403
```

### Causa
- Usuario sin permiso para la acción
- Rol sin permisos asignados
- Validación de permisos RBAC fallando

### Solución

1. **Verificar rol del usuario**
```bash
curl -X GET http://localhost:8000/api/users/me/ \
  -H "Authorization: Bearer {TOKEN}"
```

Buscar en respuesta: `"role": {...}`

2. **Verificar permisos del rol**
```bash
curl -X GET http://localhost:8000/api/roles/{ROLE_ID}/ \
  -H "Authorization: Bearer {TOKEN}"
```

Buscar: `"permissions": [...]`

3. **Asignar permisos al rol**
```bash
curl -X PUT http://localhost:8000/api/roles/{ROLE_ID}/ \
  -H "Authorization: Bearer {TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "permissions": ["{PERMISSION_ID_1}", "{PERMISSION_ID_2}"]
  }'
```

---

## 4️⃣ Error: "500 Internal Server Error"

### Síntomas
```
500 Internal Server Error: /api/users/
GET /api/users/ HTTP/1.1" 500
```

### Causa
- Error en el código del backend
- Problema con la base de datos
- Problema con librerías/dependencias
- Falta de configuración

### Solución

1. **Ver logs detallados**
```powershell
cd cr_backend
Get-Content logs\django.log -Tail 50
```

2. **Activar modo debug**

Editar `cr_backend/config/settings/development.py`:
```python
DEBUG = True
ALLOWED_HOSTS = ['*']
```

3. **Reiniciar servidor Django**
```powershell
cd cr_backend
python manage.py runserver
```

4. **Verificar base de datos**
```bash
# Hacer migraciones
python manage.py migrate

# Ver estado
python manage.py showmigrations
```

5. **Instalar dependencias faltantes**
```bash
cd cr_backend
pip install -r requirements.txt
```

---

## 5️⃣ Error: "TypeError: Cannot read properties of undefined"

### Síntomas
En consola del navegador (F12):
```
TypeError: Cannot read properties of undefined (reading 'access')
at Object.login (auth.service.ts:15)
```

### Causa
- Respuesta API no tiene estructura esperada
- API retorna error en lugar de datos
- Frontend espera estructura diferente

### Solución

1. **Verificar respuesta del servidor**
```bash
curl -X POST http://localhost:8000/api/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "password123"
  }' | jq .
```

Debería retornar:
```json
{
  "access": "eyJhbGc...",
  "refresh": "eyJhbGc...",
  "user": { ... }
}
```

2. **Verificar que el endpoint existe**
- Ver `API_ENDPOINTS_REFERENCE.md`
- Verificar URL exacta

3. **Revisar código que parsea respuesta**

Archivo: `cr_frontend/src/core/services/auth.service.ts`

Debe tener:
```typescript
const login = async (email: string, password: string) => {
  const response = await apiService.post<AuthResponse>('/login/', { email, password });
  const { access, refresh, user } = response.data; // ← Desestructuración correcta
  return { access, refresh, user };
};
```

---

## 6️⃣ Error de Conexión a Base de Datos

### Síntomas
```
psycopg2.OperationalError: could not connect to server: Connection refused
FATAL: remaining connection slots are reserved for non-replication superuser connections
```

### Causa
- PostgreSQL no está corriendo
- Credenciales incorrectas
- Puerto incorrecto

### Solución

1. **Verificar que PostgreSQL está corriendo**
```powershell
# En Windows, verificar servicios
Get-Service | Where-Object {$_.Name -like "*postgre*"}
```

2. **Verificar credenciales en settings**

Archivo: `cr_backend/config/settings/development.py`
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'cr_system',
        'USER': 'postgres',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

3. **Probar conexión directa**
```bash
psql -U postgres -h localhost -d cr_system
```

4. **Crear base de datos si no existe**
```sql
CREATE DATABASE cr_system;
```

---

## 7️⃣ Error: "CSRF token missing or incorrect"

### Síntomas
```
403 Forbidden - CSRF token missing or incorrect
POST /api/login/ HTTP/1.1" 403
```

### Causa
- Header CSRF-Token no enviado (en formularios)
- CSRF middleware activado

### Solución

Django REST Framework maneja CSRF automáticamente con tokens. Si usas fetch/axios:

```javascript
// Obtener token CSRF
const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;

// Enviar en header
headers: {
  'X-CSRFToken': csrfToken,
  'Content-Type': 'application/json'
}
```

O desactivar CSRF si es necesario (desarrollo):

Archivo: `cr_backend/config/settings/development.py`
```python
MIDDLEWARE = [
    # ... otros middleware
    # 'django.middleware.csrf.CsrfViewMiddleware',  # Comentar si es necesario
]
```

---

## 8️⃣ Error: "CORS error - Access-Control-Allow-Origin"

### Síntomas
En consola del navegador:
```
Access to XMLHttpRequest at 'http://localhost:8000/api/login/' from origin 
'http://localhost:5173' has been blocked by CORS policy
```

### Causa
- CORS no está configurado
- Frontend y backend en diferentes puertos
- Headers CORS incorrectos

### Solución

1. **Instalar django-cors-headers**
```bash
pip install django-cors-headers
```

2. **Configurar en settings**

Archivo: `cr_backend/config/settings/development.py`
```python
INSTALLED_APPS = [
    # ...
    'corsheaders',
]

MIDDLEWARE = [
    'corsheaders.CorsMiddleware',  # Debe estar al inicio
    'django.middleware.common.CommonMiddleware',
    # ...
]

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

CORS_ALLOW_CREDENTIALS = True
```

3. **Reiniciar servidor**
```bash
python manage.py runserver
```

---

## 9️⃣ Error: "Port already in use"

### Síntomas
```
Address already in use (:8000)
Port 8000 is already in use
```

### Causa
- Puerto 8000 ya está en uso
- Otra instancia del servidor sigue corriendo

### Solución

1. **Encontrar proceso en puerto 8000** (Windows PowerShell)
```powershell
Get-NetTCPConnection -LocalPort 8000 | Get-Process
```

2. **Matar proceso**
```powershell
Stop-Process -Id {PID} -Force
```

O usar un puerto diferente:
```bash
python manage.py runserver 8001
```

---

## 🔟 Error: "Module not found"

### Síntomas
```
ModuleNotFoundError: No module named 'rest_framework'
```

### Causa
- Dependencia no instalada
- Virtual environment no activado

### Solución

1. **Verificar virtual environment activo**
```powershell
# Debe mostrar el nombre del env entre paréntesis
# (venv) C:\path\to\project>
```

2. **Activar virtual environment**
```powershell
# Windows
.\venv\Scripts\Activate.ps1

# Linux/Mac
source venv/bin/activate
```

3. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

4. **Verificar instalación**
```bash
pip list | grep -i django
pip list | grep -i rest
```

---

## 🟫 Frontend Build Errors

### Error: "Cannot find module"

**Síntoma:**
```
error TS2307: Cannot find module '@/core/services'
```

**Causa:**
- Path alias no configurado
- Import incorrecto

**Solución:**

Verificar `cr_frontend/tsconfig.json`:
```json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"]
    }
  }
}
```

---

## 🟪 Problemas de Autenticación en Frontend

### Token no persiste después de refresh

**Causa:**
- localStorage no funciona
- Token se pierde al recargar

**Solución:**

Archivo: `cr_frontend/src/core/services/auth.service.ts`
```typescript
// Guardar token
localStorage.setItem('access_token', response.data.access);
localStorage.setItem('refresh_token', response.data.refresh);

// Recuperar token
const token = localStorage.getItem('access_token');

// Limpiar token
localStorage.removeItem('access_token');
localStorage.removeItem('refresh_token');
```

---

## 🟩 Problemas de Permisos

### Usuario no ve opciones permitidas

**Checklist:**
- [ ] Usuario tiene rol asignado
- [ ] Rol tiene permisos asignados
- [ ] Frontend está cargando permisos correctamente
- [ ] Cache de permisos no está viejo (máx 5 minutos)
- [ ] No está usando superadmin bypass cuando no debería

**Verificar permisos en BD:**
```bash
# En pgAdmin o psql
SELECT * FROM core_role WHERE id = '{role_id}';
SELECT * FROM core_permission WHERE id IN (...);
SELECT * FROM core_role_permissions WHERE role_id = '{role_id}';
```

---

## 🟨 Problemas de Logs

### No veo logs del backend

**Solución:**
```powershell
# Ver último logs
cd cr_backend
Get-Content logs\django.log -Tail 100

# Ver en tiempo real
.\watch_logs.ps1

# Ver específicamente errores
Get-Content logs\django.log | Select-String "ERROR"
```

### Logs muy grandes

```powershell
# Limpiar logs
Clear-Content logs\django.log

# O eliminar y dejar que se recreen
Remove-Item logs\django.log
```

---

## 🔴 DIAGNÓSTICO RÁPIDO

Usa este script para diagnosticar problemas:

**PowerShell Script - `diagnose.ps1`:**
```powershell
Write-Host "=== DIAGNÓSTICO DEL SISTEMA ===" -ForegroundColor Cyan

# 1. Verificar backend corriendo
Write-Host "`n1. Backend Status:" -ForegroundColor Yellow
$backend = curl -s http://localhost:8000/api/login/ -Method OPTIONS -ErrorAction SilentlyContinue
if ($backend) {
    Write-Host "✅ Backend corriendo" -ForegroundColor Green
} else {
    Write-Host "❌ Backend NO está corriendo" -ForegroundColor Red
}

# 2. Verificar frontend corriendo
Write-Host "`n2. Frontend Status:" -ForegroundColor Yellow
$frontend = curl -s http://localhost:5173/ -ErrorAction SilentlyContinue
if ($frontend) {
    Write-Host "✅ Frontend corriendo" -ForegroundColor Green
} else {
    Write-Host "❌ Frontend NO está corriendo" -ForegroundColor Red
}

# 3. Verificar PostgreSQL
Write-Host "`n3. PostgreSQL Status:" -ForegroundColor Yellow
$postgres = Get-Service | Where-Object {$_.Name -like "*postgre*"}
if ($postgres.Status -eq "Running") {
    Write-Host "✅ PostgreSQL corriendo" -ForegroundColor Green
} else {
    Write-Host "❌ PostgreSQL NO está corriendo" -ForegroundColor Red
}

# 4. Verificar logs
Write-Host "`n4. Recent Errors:" -ForegroundColor Yellow
$errors = Get-Content logs\django.log 2>/dev/null | Select-String "ERROR" | Tail -5
if ($errors) {
    Write-Host "⚠️  Errores encontrados:" -ForegroundColor Yellow
    $errors
} else {
    Write-Host "✅ No hay errores recientes" -ForegroundColor Green
}

Write-Host "`n=== FIN DEL DIAGNÓSTICO ===" -ForegroundColor Cyan
```

---

## 📞 CÓMO PEDIR AYUDA

Al reportar un problema, incluye:

1. **Error exacto** (copiar desde logs o consola)
2. **Pasos para reproducir**
3. **Logs relevantes** (últimas 50 líneas)
4. **Información del sistema:**
   - SO (Windows, Linux, Mac)
   - Python version
   - Node version
   - Versión de Django

---

## 🔗 RECURSOS DE AYUDA

- **Django Docs:** https://docs.djangoproject.com/
- **DRF Docs:** https://www.django-rest-framework.org/
- **React Docs:** https://react.dev/
- **PostgreSQL Docs:** https://www.postgresql.org/docs/
- **Stack Overflow:** tag `django` + `django-rest-framework`

---

**Última actualización:** Noviembre 2025  
**Versión:** 1.0.0  
**Status:** ✅ Completo
