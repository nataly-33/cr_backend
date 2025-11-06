# 🔌 ENDPOINTS API - REFERENCIA COMPLETA

## Base URL

```
http://localhost:8000/api
```

## ✅ Autenticación

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/login/` | Login con email/password |
| POST | `/logout/` | Logout (requiere token) |
| POST | `/refresh/` | Refresh access token |
| GET | `/users/me/` | Obtener usuario actual |

## 👥 Usuarios

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/users/` | Listar usuarios (paginado) |
| GET | `/users/{id}/` | Obtener usuario por ID |
| POST | `/users/` | Crear nuevo usuario |
| PUT | `/users/{id}/` | Actualizar usuario |
| DELETE | `/users/{id}/` | Eliminar usuario |
| POST | `/users/{id}/toggle-active/` | Activar/desactivar usuario |
| POST | `/users/{id}/change-password/` | Cambiar contraseña |
| GET | `/users/preferences/` | Obtener preferencias |
| PUT | `/users/preferences/` | Actualizar preferencias |

## 🎭 Roles

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/roles/` | Listar roles (paginado) |
| GET | `/roles/{id}/` | Obtener rol por ID |
| POST | `/roles/` | Crear nuevo rol |
| PUT | `/roles/{id}/` | Actualizar rol |
| DELETE | `/roles/{id}/` | Eliminar rol |

## 🔐 Permisos

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/permissions/` | Listar permisos (paginado) |
| GET | `/permissions/{id}/` | Obtener permiso por ID |
| POST | `/permissions/` | Crear nuevo permiso |
| PUT | `/permissions/{id}/` | Actualizar permiso |
| DELETE | `/permissions/{id}/` | Eliminar permiso |

## 🏥 Pacientes

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/patients/` | Listar pacientes (paginado) |
| GET | `/patients/{id}/` | Obtener paciente por ID |
| POST | `/patients/` | Crear nuevo paciente |
| PUT | `/patients/{id}/` | Actualizar paciente |
| DELETE | `/patients/{id}/` | Eliminar paciente |

## 📋 Historias Clínicas

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/clinical-records/` | Listar historias (paginado) |
| GET | `/clinical-records/{id}/` | Obtener historia por ID |
| POST | `/clinical-records/` | Crear nueva historia |
| PUT | `/clinical-records/{id}/` | Actualizar historia |
| DELETE | `/clinical-records/{id}/` | Eliminar historia |

## 📄 Documentos

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/documents/` | Listar documentos (paginado) |
| GET | `/documents/{id}/` | Obtener documento por ID |
| POST | `/documents/upload/` | Subir documento con OCR |
| GET | `/documents/{id}/download/` | Descargar documento |
| POST | `/documents/{id}/sign/` | Firmar documento |
| GET | `/documents/{id}/access-log/` | Ver log de accesos |

## 📊 Reportes

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/reports/` | Listar reportes |
| GET | `/reports/{id}/` | Obtener reporte por ID |
| POST | `/reports/generator/generate/` | Generar nuevo reporte |
| GET | `/reports/executions/` | Listar ejecuciones |

## 🔍 Auditoría

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/audit/` | Listar logs de auditoría |
| GET | `/audit/{id}/` | Obtener log por ID |
| GET | `/audit/stats/` | Estadísticas de auditoría |

## 📝 Formularios Clínicos

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/clinical-records/forms/` | Listar formularios |
| GET | `/clinical-records/forms/{id}/` | Obtener formulario |
| POST | `/clinical-records/forms/` | Crear formulario |
| PUT | `/clinical-records/forms/{id}/` | Actualizar formulario |
| DELETE | `/clinical-records/forms/{id}/` | Eliminar formulario |

## 🔔 Notificaciones

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/notifications/` | Listar notificaciones |
| POST | `/notifications/{id}/mark-read/` | Marcar como leída |
| GET | `/notifications/preferences/` | Obtener preferencias |
| PUT | `/notifications/preferences/` | Actualizar preferencias |

---

## 📍 Ejemplos de Uso

### Listar usuarios con paginación

```bash
GET /api/users/?page=1&page_size=10&search=john
```

**Query Parameters:**
- `page` - Número de página (default: 1)
- `page_size` - Items por página (default: 10)
- `search` - Buscar por nombre/email
- `ordering` - Campo para ordenar (ej: `-created_at`)
- `role` - Filtrar por rol
- `is_active` - Filtrar activos/inactivos

### Crear nuevo usuario

```bash
POST /api/users/
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePassword123",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+34912345678",
  "role": "role-id-uuid"
}
```

### Obtener usuario actual

```bash
GET /api/users/me/
Authorization: Bearer {access_token}
```

### Login

```bash
POST /api/login/
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePassword123"
}

Response:
{
  "access": "eyJhbGc...",
  "refresh": "eyJhbGc...",
  "user": {...}
}
```

### Crear rol con permisos

```bash
POST /api/roles/
Content-Type: application/json
Authorization: Bearer {access_token}

{
  "name": "Doctor",
  "description": "Rol para doctores",
  "permissions": ["perm-id-1", "perm-id-2"],
  "tenant_id": null
}
```

### Listar permisos

```bash
GET /api/permissions/?page=1&page_size=50
Authorization: Bearer {access_token}
```

### Subir documento

```bash
POST /api/documents/upload/
Content-Type: multipart/form-data
Authorization: Bearer {access_token}

FormData:
- file: [archivo PDF/imagen]
- clinical_record: [id-uuid]
- document_type: "medical_report"
```

---

## 🔑 Headers Requeridos

### Autenticación (después de login)

```
Authorization: Bearer {access_token}
```

### Content-Type

```
Content-Type: application/json
```

Para subidas de archivos:

```
Content-Type: multipart/form-data
```

---

## 🛡️ Códigos de Error

| Código | Significado |
|--------|------------|
| 200 | OK - Solicitud exitosa |
| 201 | Created - Recurso creado |
| 204 | No Content - Sin contenido |
| 400 | Bad Request - Datos inválidos |
| 401 | Unauthorized - No autenticado |
| 403 | Forbidden - Sin permisos |
| 404 | Not Found - Recurso no encontrado |
| 500 | Server Error - Error del servidor |

---

## 📊 Respuesta Paginada

```json
{
  "count": 100,
  "next": "http://localhost:8000/api/users/?page=2",
  "previous": null,
  "results": [
    { /* objeto 1 */ },
    { /* objeto 2 */ }
  ]
}
```

---

## 🔄 Flujo de Autenticación

```
1. POST /api/login/
   ├─ Email + Password
   └─ Response: access + refresh tokens

2. Usar access token en headers
   ├─ Authorization: Bearer {access_token}
   └─ Acceso a endpoints protegidos

3. Cuando access expira
   ├─ POST /api/refresh/
   ├─ Body: { refresh: {refresh_token} }
   └─ Response: nuevo access token

4. Logout
   └─ POST /api/logout/
```

---

## ⚠️ Notas Importantes

✅ **Todos los endpoints requieren autenticación** excepto:
- POST `/login/`

✅ **Multi-tenancy**: Los usuarios solo ven datos de su tenant

✅ **Permisos granulares**: Basados en roles y permisos RBAC

✅ **Paginación**: Todos los listados están paginados por defecto

✅ **Filtros**: Aplica a todos los endpoints GET de listado

---

**Última actualización:** Noviembre 2025  
**Versión:** 1.0.0  
**Status:** ✅ Actualizado
