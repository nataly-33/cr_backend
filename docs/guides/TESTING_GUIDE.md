# 🧪 TESTING GUIDE - API ENDPOINTS

## 📌 Herramientas Recomendadas

- **Postman** - GUI para testing de APIs
- **cURL** - CLI para testing
- **Thunder Client** - Extension VS Code
- **REST Client** - Extension VS Code
- **Insomnia** - Alternativa a Postman

---

## 🚀 QUICK START - TESTING BÁSICO

### 1. Login (Obtener Token)

**cURL:**
```bash
curl -X POST http://localhost:8000/api/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "password123"
  }'
```

**PowerShell:**
```powershell
$body = @{
    email = "admin@example.com"
    password = "password123"
} | ConvertTo-Json

$response = Invoke-WebRequest -Uri "http://localhost:8000/api/login/" `
  -Method POST `
  -ContentType "application/json" `
  -Body $body

$token = ($response.Content | ConvertFrom-Json).access
Write-Host "Token: $token"
```

### 2. Guardar Token en Variable

**PowerShell:**
```powershell
$token = "eyJhbGc..."  # Token obtenido del login
$headers = @{
    Authorization = "Bearer $token"
    "Content-Type" = "application/json"
}
```

### 3. Hacer Solicitud Autenticada

**cURL:**
```bash
curl -X GET http://localhost:8000/api/users/me/ \
  -H "Authorization: Bearer $token"
```

**PowerShell:**
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/users/me/" `
  -Method GET `
  -Headers $headers
```

---

## 📋 TESTING COMPLETO POR MÓDULO

### 🔐 AUTENTICACIÓN

#### 1. Login
```bash
curl -X POST http://localhost:8000/api/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "password123"
  }'
```
**Esperado:** `200 OK` + tokens (access, refresh) + datos usuario

#### 2. Obtener Usuario Actual
```bash
curl -X GET http://localhost:8000/api/users/me/ \
  -H "Authorization: Bearer {ACCESS_TOKEN}"
```
**Esperado:** `200 OK` + datos del usuario autenticado

#### 3. Refresh Token
```bash
curl -X POST http://localhost:8000/api/refresh/ \
  -H "Content-Type: application/json" \
  -d '{
    "refresh": "{REFRESH_TOKEN}"
  }'
```
**Esperado:** `200 OK` + nuevo access token

#### 4. Logout
```bash
curl -X POST http://localhost:8000/api/logout/ \
  -H "Authorization: Bearer {ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{}'
```
**Esperado:** `200 OK`

---

### 👥 USUARIOS

#### 1. Listar Usuarios
```bash
curl -X GET "http://localhost:8000/api/users/?page=1&page_size=10" \
  -H "Authorization: Bearer {ACCESS_TOKEN}"
```
**Esperado:** `200 OK` + lista paginada de usuarios

#### 2. Buscar Usuario
```bash
curl -X GET "http://localhost:8000/api/users/?search=john" \
  -H "Authorization: Bearer {ACCESS_TOKEN}"
```
**Esperado:** `200 OK` + usuarios que coincidan con "john"

#### 3. Obtener Usuario por ID
```bash
curl -X GET "http://localhost:8000/api/users/{USER_ID}/" \
  -H "Authorization: Bearer {ACCESS_TOKEN}"
```
**Esperado:** `200 OK` + datos del usuario

#### 4. Crear Usuario
```bash
curl -X POST http://localhost:8000/api/users/ \
  -H "Authorization: Bearer {ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@example.com",
    "password": "SecurePassword123",
    "first_name": "John",
    "last_name": "Doe",
    "role": "{ROLE_ID}"
  }'
```
**Esperado:** `201 Created` + datos del nuevo usuario

#### 5. Actualizar Usuario
```bash
curl -X PUT "http://localhost:8000/api/users/{USER_ID}/" \
  -H "Authorization: Bearer {ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Jane",
    "last_name": "Smith",
    "phone": "+34987654321"
  }'
```
**Esperado:** `200 OK` + datos actualizados

#### 6. Activar/Desactivar Usuario
```bash
curl -X POST "http://localhost:8000/api/users/{USER_ID}/toggle-active/" \
  -H "Authorization: Bearer {ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{}'
```
**Esperado:** `200 OK` + estado actualizado

#### 7. Cambiar Contraseña
```bash
curl -X POST "http://localhost:8000/api/users/{USER_ID}/change-password/" \
  -H "Authorization: Bearer {ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "old_password": "OldPassword123",
    "new_password": "NewPassword456"
  }'
```
**Esperado:** `200 OK`

#### 8. Obtener Preferencias
```bash
curl -X GET "http://localhost:8000/api/users/preferences/" \
  -H "Authorization: Bearer {ACCESS_TOKEN}"
```
**Esperado:** `200 OK` + preferencias del usuario

#### 9. Actualizar Preferencias
```bash
curl -X PUT "http://localhost:8000/api/users/preferences/" \
  -H "Authorization: Bearer {ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "language": "es",
    "theme": "dark",
    "notifications_enabled": true
  }'
```
**Esperado:** `200 OK` + preferencias actualizadas

#### 10. Eliminar Usuario
```bash
curl -X DELETE "http://localhost:8000/api/users/{USER_ID}/" \
  -H "Authorization: Bearer {ACCESS_TOKEN}"
```
**Esperado:** `204 No Content`

---

### 🎭 ROLES

#### 1. Listar Roles
```bash
curl -X GET "http://localhost:8000/api/roles/?page=1&page_size=20" \
  -H "Authorization: Bearer {ACCESS_TOKEN}"
```

#### 2. Obtener Rol por ID
```bash
curl -X GET "http://localhost:8000/api/roles/{ROLE_ID}/" \
  -H "Authorization: Bearer {ACCESS_TOKEN}"
```

#### 3. Crear Rol
```bash
curl -X POST http://localhost:8000/api/roles/ \
  -H "Authorization: Bearer {ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Doctor",
    "description": "Rol para doctores",
    "permissions": ["{PERMISSION_ID_1}", "{PERMISSION_ID_2}"]
  }'
```

#### 4. Actualizar Rol
```bash
curl -X PUT "http://localhost:8000/api/roles/{ROLE_ID}/" \
  -H "Authorization: Bearer {ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Senior Doctor",
    "description": "Doctores senior"
  }'
```

#### 5. Eliminar Rol
```bash
curl -X DELETE "http://localhost:8000/api/roles/{ROLE_ID}/" \
  -H "Authorization: Bearer {ACCESS_TOKEN}"
```

---

### 🔐 PERMISOS

#### 1. Listar Permisos
```bash
curl -X GET "http://localhost:8000/api/permissions/?page=1&page_size=50" \
  -H "Authorization: Bearer {ACCESS_TOKEN}"
```

#### 2. Obtener Permiso por ID
```bash
curl -X GET "http://localhost:8000/api/permissions/{PERMISSION_ID}/" \
  -H "Authorization: Bearer {ACCESS_TOKEN}"
```

#### 3. Crear Permiso
```bash
curl -X POST http://localhost:8000/api/permissions/ \
  -H "Authorization: Bearer {ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "view_patients",
    "description": "Ver pacientes",
    "codename": "view_patients"
  }'
```

---

### 🏥 PACIENTES

#### 1. Listar Pacientes
```bash
curl -X GET "http://localhost:8000/api/patients/?page=1&page_size=10" \
  -H "Authorization: Bearer {ACCESS_TOKEN}"
```

#### 2. Crear Paciente
```bash
curl -X POST http://localhost:8000/api/patients/ \
  -H "Authorization: Bearer {ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "María",
    "last_name": "González",
    "email": "maria@example.com",
    "phone": "+34912345678",
    "date_of_birth": "1990-05-15",
    "identification": "12345678A",
    "identification_type": "dni"
  }'
```

---

### 📄 DOCUMENTOS - Subir Archivo

```bash
# Primero obtener el ID del paciente o historia clínica
# Luego subir documento

curl -X POST http://localhost:8000/api/documents/upload/ \
  -H "Authorization: Bearer {ACCESS_TOKEN}" \
  -F "file=@/path/to/document.pdf" \
  -F "clinical_record={CLINICAL_RECORD_ID}" \
  -F "document_type=medical_report"
```

**En PowerShell:**
```powershell
$filePath = "C:\path\to\document.pdf"
$form = @{
    file = Get-Item -Path $filePath
    clinical_record = "{CLINICAL_RECORD_ID}"
    document_type = "medical_report"
}

Invoke-RestMethod -Uri "http://localhost:8000/api/documents/upload/" `
  -Method POST `
  -Form $form `
  -Headers @{ Authorization = "Bearer $token" }
```

---

## 🔍 TESTING AVANZADO

### Scenario: Flujo Completo

```bash
#!/bin/bash

BASE_URL="http://localhost:8000/api"

# 1. Login
echo "1. Login..."
LOGIN=$(curl -s -X POST "$BASE_URL/login/" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "password123"
  }')

TOKEN=$(echo $LOGIN | jq -r '.access')
USER_ID=$(echo $LOGIN | jq -r '.user.id')

echo "Token: $TOKEN"
echo "User ID: $USER_ID"

# 2. Obtener usuario actual
echo -e "\n2. Obtener usuario actual..."
curl -s -X GET "$BASE_URL/users/me/" \
  -H "Authorization: Bearer $TOKEN" | jq .

# 3. Listar usuarios
echo -e "\n3. Listar usuarios..."
curl -s -X GET "$BASE_URL/users/?page=1&page_size=5" \
  -H "Authorization: Bearer $TOKEN" | jq .

# 4. Listar roles
echo -e "\n4. Listar roles..."
curl -s -X GET "$BASE_URL/roles/" \
  -H "Authorization: Bearer $TOKEN" | jq .

# 5. Logout
echo -e "\n5. Logout..."
curl -s -X POST "$BASE_URL/logout/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}' | jq .
```

---

## 🛠️ TESTING EN POSTMAN

### Pasos para Configurar:

1. **Crear Collection**
   - File → New → Collection
   - Nombre: "API CR Backend"

2. **Crear Environment**
   - Environment → Create → "API Development"
   - Variables:
     ```
     base_url: http://localhost:8000/api
     token: (se llena después del login)
     user_id: (se llena después del login)
     ```

3. **Crear Request de Login**
   - Method: POST
   - URL: {{base_url}}/login/
   - Body (JSON):
     ```json
     {
       "email": "admin@example.com",
       "password": "password123"
     }
     ```
   - Tests (Script):
     ```javascript
     var jsonData = pm.response.json();
     pm.environment.set("token", jsonData.access);
     pm.environment.set("user_id", jsonData.user.id);
     ```

4. **Crear Request Autenticado**
   - Method: GET
   - URL: {{base_url}}/users/me/
   - Headers:
     ```
     Authorization: Bearer {{token}}
     ```

---

## ⚠️ ERRORES COMUNES Y SOLUCIONES

### Error 401 - Unauthorized
**Causa:** Token inválido o expirado
**Solución:** 
```bash
# Hacer login nuevamente
curl -X POST http://localhost:8000/api/login/ ...
```

### Error 403 - Forbidden
**Causa:** Usuario sin permisos
**Solución:**
- Verificar permisos del usuario
- Asignar rol con permisos adecuados

### Error 404 - Not Found
**Causa:** Endpoint o recurso no existe
**Solución:**
- Verificar URL en API_ENDPOINTS_REFERENCE.md
- Verificar que el ID del recurso existe

### Error 400 - Bad Request
**Causa:** Datos inválidos
**Solución:**
- Validar JSON
- Verificar tipos de datos requeridos
- Ver respuesta del servidor para detalles

### Error 500 - Internal Server Error
**Causa:** Error en el servidor
**Solución:**
- Verificar logs del backend: `.\watch_logs.ps1`
- Ver `logs/django.log`

---

## 📊 MONITOREO DURANTE TESTING

### Ver Logs en Tiempo Real

**PowerShell:**
```powershell
cd cr_backend
.\watch_logs.ps1
```

### Ver Últimas Líneas de Log

**PowerShell:**
```powershell
Get-Content logs\django.log -Tail 100
```

### Filtrar por Tipo de Error

**PowerShell:**
```powershell
Get-Content logs\django.log | Select-String "ERROR|404|403"
```

---

## ✅ CHECKLIST DE TESTING

- [ ] Autenticación (login/logout/refresh)
- [ ] Usuarios (CRUD completo)
- [ ] Roles (CRUD completo)
- [ ] Permisos (CRUD completo)
- [ ] Pacientes (CRUD completo)
- [ ] Documentos (upload/download)
- [ ] Preferencias de usuario
- [ ] Filtros y búsqueda
- [ ] Paginación
- [ ] Permisos y roles aplicados correctamente
- [ ] Errores apropriados en casos inválidos
- [ ] Logs registrando todas las operaciones

---

## 🔗 RECURSOS ÚTILES

- [Django REST Framework Documentation](https://www.django-rest-framework.org/)
- [Postman Learning Center](https://learning.postman.com/)
- [cURL Docs](https://curl.se/docs/)
- [Thunder Client VS Code](https://www.thunderclient.com/)

---

**Última actualización:** Noviembre 2025  
**Versión:** 1.0.0  
**Status:** ✅ Completo
