# 🔌 ENDPOINTS API - REFERENCIA COMPLETA

**Última actualización**: 17/11/2025  
**Status**: ✅ Sincronizado (Backend Django + Frontend React + Flutter)

---

## 📍 Base URL

```
http://localhost:8000/api
```

**⚠️ IMPORTANTE**:

- Todos los endpoints están bajo `/api/` **SIN** `/auth/` prefix
- Backend, Frontend y Flutter usan las mismas rutas
- Endpoints públicos: `/login/`, `/register/`, `/refresh/`, `/tenants/public/*`

---

## ✅ Autenticación

| Método | Endpoint     | Descripción                | Público |
| ------ | ------------ | -------------------------- | ------- |
| POST   | `/login/`    | Login con email/password   | ✅ Sí   |
| POST   | `/register/` | Registro público de tenant | ✅ Sí   |
| POST   | `/refresh/`  | Refresh access token       | ✅ Sí   |
| GET    | `/users/me/` | Obtener usuario actual     | ❌ No   |

**Ejemplo Login**:

```bash
POST /api/login/
Content-Type: application/json

{
  "email": "admin@hospital.com",
  "password": "SecurePassword123"
}

# Response 200 OK:
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "uuid-here",
    "email": "admin@hospital.com",
    "full_name": "Admin User",
    "role": "Administrador TI",
    "tenant_id": "tenant-uuid"
  }
}
```

**Headers requeridos** (después de login):

```
Authorization: Bearer {access_token}
Content-Type: application/json
```

---

## 👥 Usuarios

| Método | Endpoint                       | Descripción                             |
| ------ | ------------------------------ | --------------------------------------- |
| GET    | `/users/`                      | Listar usuarios (paginado)              |
| GET    | `/users/{id}/`                 | Obtener usuario por ID                  |
| GET    | `/users/me/`                   | Obtener usuario actual                  |
| GET    | `/users/me/preferences/`       | Obtener preferencias del usuario actual |
| PUT    | `/users/me/preferences/`       | Actualizar preferencias                 |
| POST   | `/users/`                      | Crear nuevo usuario                     |
| PUT    | `/users/{id}/`                 | Actualizar usuario completo             |
| PATCH  | `/users/{id}/`                 | Actualizar usuario parcial              |
| DELETE | `/users/{id}/`                 | Eliminar usuario                        |
| POST   | `/users/{id}/toggle_active/`   | Activar/desactivar usuario              |
| POST   | `/users/{id}/change_password/` | Cambiar contraseña                      |
| GET    | `/users/get_preferences/`      | Alias para preferencias                 |
| GET    | `/users/preferences/`          | Alias para preferencias                 |
| PUT    | `/users/preferences/`          | Alias para actualizar preferencias      |

**Query Parameters** (GET `/users/`):

- `page` - Número de página (default: 1)
- `page_size` - Items por página (default: 10)
- `search` - Buscar por nombre/email
- `ordering` - Campo para ordenar (ej: `-created_at`, `email`)
- `role` - Filtrar por rol UUID
- `is_active` - Filtrar activos/inactivos (`true`/`false`)

**Ejemplo Crear Usuario**:

```bash
POST /api/users/
Authorization: Bearer {token}
Content-Type: application/json

{
  "email": "doctor@hospital.com",
  "password": "SecurePassword123",
  "first_name": "Juan",
  "last_name": "Pérez",
  "phone": "+34912345678",
  "role": "role-uuid-here",
  "is_active": true
}
```

---

## 🎭 Roles

| Método | Endpoint       | Descripción             |
| ------ | -------------- | ----------------------- |
| GET    | `/roles/`      | Listar roles (paginado) |
| GET    | `/roles/{id}/` | Obtener rol por ID      |
| POST   | `/roles/`      | Crear nuevo rol         |
| PUT    | `/roles/{id}/` | Actualizar rol completo |
| PATCH  | `/roles/{id}/` | Actualizar rol parcial  |
| DELETE | `/roles/{id}/` | Eliminar rol            |

**Ejemplo Crear Rol**:

```bash
POST /api/roles/
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "Doctor",
  "description": "Rol para médicos",
  "permissions": ["permission-uuid-1", "permission-uuid-2"],
  "is_system_role": false
}
```

---

## 🔐 Permisos

| Método | Endpoint             | Descripción                 |
| ------ | -------------------- | --------------------------- |
| GET    | `/permissions/`      | Listar permisos (paginado)  |
| GET    | `/permissions/{id}/` | Obtener permiso por ID      |
| POST   | `/permissions/`      | Crear nuevo permiso         |
| PUT    | `/permissions/{id}/` | Actualizar permiso completo |
| PATCH  | `/permissions/{id}/` | Actualizar permiso parcial  |
| DELETE | `/permissions/{id}/` | Eliminar permiso            |

---

## 🏥 Pacientes

| Método | Endpoint                           | Descripción                  |
| ------ | ---------------------------------- | ---------------------------- |
| GET    | `/patients/`                       | Listar pacientes (paginado)  |
| GET    | `/patients/{id}/`                  | Obtener paciente por ID      |
| POST   | `/patients/`                       | Crear nuevo paciente         |
| PUT    | `/patients/{id}/`                  | Actualizar paciente completo |
| PATCH  | `/patients/{id}/`                  | Actualizar paciente parcial  |
| DELETE | `/patients/{id}/`                  | Eliminar paciente            |
| GET    | `/patients/{id}/clinical_records/` | Historias del paciente       |

---

## 📋 Historias Clínicas

| Método | Endpoint                            | Descripción                  |
| ------ | ----------------------------------- | ---------------------------- |
| GET    | `/clinical-records/`                | Listar historias (paginado)  |
| GET    | `/clinical-records/{id}/`           | Obtener historia por ID      |
| POST   | `/clinical-records/`                | Crear nueva historia         |
| PUT    | `/clinical-records/{id}/`           | Actualizar historia completa |
| PATCH  | `/clinical-records/{id}/`           | Actualizar historia parcial  |
| DELETE | `/clinical-records/{id}/`           | Eliminar historia            |
| GET    | `/clinical-records/{id}/documents/` | Documentos de la historia    |
| GET    | `/clinical-records/{id}/timeline/`  | Timeline de eventos          |
| POST   | `/clinical-records/{id}/archive/`   | Archivar historia            |
| POST   | `/clinical-records/{id}/close/`     | Cerrar historia              |

**Formularios Clínicos**:
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/clinical-records/forms/` | Listar formularios |
| GET | `/clinical-records/forms/{id}/` | Obtener formulario |
| POST | `/clinical-records/forms/` | Crear formulario |
| PUT | `/clinical-records/forms/{id}/` | Actualizar formulario |
| DELETE | `/clinical-records/forms/{id}/` | Eliminar formulario |
| GET | `/clinical-records/forms/form_types/` | Tipos de formularios |

**Query Parameters** (GET `/clinical-records/forms/`):

- `clinical_record_id` - Filtrar por historia clínica
- `form_type` - Filtrar por tipo de formulario

---

## 📄 Documentos

| Método | Endpoint                      | Descripción                  |
| ------ | ----------------------------- | ---------------------------- |
| GET    | `/documents/`                 | Listar documentos (paginado) |
| GET    | `/documents/{id}/`            | Obtener documento por ID     |
| POST   | `/documents/upload/`          | Subir documento con OCR      |
| GET    | `/documents/{id}/download/`   | Descargar documento          |
| POST   | `/documents/{id}/sign/`       | Firmar documento             |
| GET    | `/documents/{id}/access_log/` | Ver log de accesos           |
| GET    | `/documents/search/`          | Buscar documentos            |

**Ejemplo Upload**:

```bash
POST /api/documents/upload/
Authorization: Bearer {token}
Content-Type: multipart/form-data

FormData:
- file: [archivo PDF/imagen]
- clinical_record: "record-uuid"
- document_type: "medical_report"
- description: "Análisis de sangre"
```

---

## 📊 Reportes

| Método | Endpoint                                    | Descripción               |
| ------ | ------------------------------------------- | ------------------------- |
| GET    | `/reports/executions/`                      | Listar reportes generados |
| GET    | `/reports/executions/{id}/`                 | Obtener reporte por ID    |
| GET    | `/reports/executions/{id}/download/`        | Descargar reporte         |
| POST   | `/reports/generator/generate/`              | Generar nuevo reporte     |
| POST   | `/reports/generator/generate_dynamic/`      | Generar reporte dinámico  |
| GET    | `/reports/generator/available_types/`       | Tipos disponibles         |
| GET    | `/reports/executions/{id}/analyze/`         | Analizar reporte (AI)     |
| GET    | `/reports/executions/{id}/summarize/`       | Resumir reporte (AI)      |
| GET    | `/reports/executions/{id}/recommendations/` | Recomendaciones (AI)      |
| GET    | `/reports/executions/{id}/ai_insights/`     | Insights (AI)             |
| GET    | `/reports/templates/`                       | Plantillas de reportes    |

---

## 🔍 Auditoría

| Método | Endpoint                        | Descripción               |
| ------ | ------------------------------- | ------------------------- |
| GET    | `/audit/`                       | Listar logs de auditoría  |
| GET    | `/audit/{id}/`                  | Obtener log por ID        |
| GET    | `/audit/{id}/verify_integrity/` | Verificar integridad      |
| GET    | `/audit/stats/`                 | Estadísticas de auditoría |
| GET    | `/audit/recent_suspicious/`     | Actividad sospechosa      |

---

## 🔔 Notificaciones

| Método | Endpoint                           | Descripción           |
| ------ | ---------------------------------- | --------------------- |
| GET    | `/notifications/`                  | Listar notificaciones |
| GET    | `/notifications/{id}/`             | Obtener notificación  |
| POST   | `/notifications/{id}/read/`        | Marcar como leída     |
| POST   | `/notifications/mark_all_as_read/` | Marcar todas leídas   |
| GET    | `/notifications/unread_count/`     | Contador no leídas    |
| POST   | `/notifications/send/`             | Enviar notificación   |

---

## 🏢 Tenants (Multi-tenancy)

**Públicos** (sin autenticación):
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/tenants/public/register/` | Registrar nuevo tenant |
| POST | `/tenants/public/checkout/` | Crear sesión Stripe Checkout |
| POST | `/tenants/public/activate/` | Activar tenant con password |
| GET | `/tenants/public/plans/` | Listar planes disponibles |

**Protegidos**:
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/tenants/` | Listar tenants (admin) |
| GET | `/tenants/{id}/` | Obtener tenant por ID |
| PUT | `/tenants/{id}/` | Actualizar tenant |

---

## 💳 Pagos (Stripe)

| Método | Endpoint                   | Descripción                 |
| ------ | -------------------------- | --------------------------- |
| POST   | `/payments/webhook/`       | Webhook de Stripe (público) |
| GET    | `/payments/`               | Listar pagos                |
| GET    | `/payments/{id}/`          | Obtener pago por ID         |
| GET    | `/payments/invoices/`      | Listar facturas             |
| GET    | `/payments/invoices/{id}/` | Obtener factura             |

---

## 🌱 Seed Data (Development)

| Método | Endpoint          | Descripción             |
| ------ | ----------------- | ----------------------- |
| POST   | `/seed/generate/` | Generar datos de prueba |
| GET    | `/seed/list/`     | Listar datos generados  |

---

## 📦 Backup

| Método | Endpoint                 | Descripción      |
| ------ | ------------------------ | ---------------- |
| POST   | `/backup/create/`        | Crear backup     |
| GET    | `/backup/`               | Listar backups   |
| POST   | `/backup/{id}/restore/`  | Restaurar backup |
| GET    | `/backup/{id}/download/` | Descargar backup |

---

## 🏥 Dashboard

| Método | Endpoint                      | Descripción              |
| ------ | ----------------------------- | ------------------------ |
| GET    | `/dashboard/overview/`        | Vista general            |
| GET    | `/dashboard/activity/`        | Actividad reciente       |
| GET    | `/dashboard/documents_stats/` | Estadísticas documentos  |
| GET    | `/dashboard/forms_stats/`     | Estadísticas formularios |
| GET    | `/dashboard/users_activity/`  | Actividad usuarios       |

---

## 🛡️ Códigos de Estado HTTP

| Código | Significado  | Cuándo aparece                 |
| ------ | ------------ | ------------------------------ |
| 200    | OK           | Solicitud exitosa              |
| 201    | Created      | Recurso creado exitosamente    |
| 204    | No Content   | Acción exitosa sin contenido   |
| 400    | Bad Request  | Datos inválidos en la petición |
| 401    | Unauthorized | Token inválido o expirado      |
| 403    | Forbidden    | Sin permisos suficientes       |
| 404    | Not Found    | Recurso no encontrado          |
| 500    | Server Error | Error interno del servidor     |

---

## 📊 Formato de Respuesta Paginada

```json
{
  "count": 100,
  "next": "http://localhost:8000/api/users/?page=2",
  "previous": null,
  "results": [
    { /* objeto 1 */ },
    { /* objeto 2 */ },
    ...
  ]
}
```

---

## 🔄 Flujo de Autenticación JWT

```
1. POST /api/login/
   ├─ Enviar: { email, password }
   └─ Recibir: { access, refresh, user }

2. Guardar tokens en localStorage/secure storage

3. Usar access token en todas las peticiones:
   ├─ Header: Authorization: Bearer {access_token}
   └─ Acceso a endpoints protegidos

4. Cuando access expira (1 hora):
   ├─ POST /api/refresh/
   ├─ Body: { refresh: {refresh_token} }
   └─ Recibir: nuevo access token

5. Logout:
   └─ Limpiar tokens del storage
```

---

## 🔑 Permisos RBAC

Los permisos se verifican por:

1. **Autenticación**: Token JWT válido
2. **Tenant**: Usuario pertenece al tenant correcto
3. **Rol**: Usuario tiene el rol necesario
4. **Permisos**: Rol tiene permisos específicos

**Ejemplo**:

- Ver usuarios: `view_user`
- Crear usuarios: `add_user`
- Editar usuarios: `change_user`
- Eliminar usuarios: `delete_user`

---

## ⚠️ Notas Importantes

✅ **Multi-tenancy**: Los usuarios solo ven datos de su propio tenant  
✅ **Paginación**: Todos los listados están paginados (page, page_size)  
✅ **Filtros**: Disponibles en todos los GET de listado  
✅ **Ordenamiento**: Usar `ordering` parameter (ej: `-created_at`)  
✅ **Búsqueda**: Usar `search` parameter donde esté disponible  
✅ **CORS**: Configurado para `localhost:5173` (frontend) y `localhost:3000`

---

## 🎯 Sincronización Frontend/Backend/Flutter

| Plataforma         | Archivo              | Endpoint Login | Status |
| ------------------ | -------------------- | -------------- | ------ |
| **Backend**        | `config/urls.py`     | `/api/login/`  | ✅ OK  |
| **Frontend React** | `api.config.ts`      | `/api/login/`  | ✅ OK  |
| **Flutter**        | `api_constants.dart` | `/api/login/`  | ✅ OK  |

**Todos usan las mismas rutas** → Sin conflictos.

---

**Última verificación**: 17/11/2025  
**Versión**: 2.0.0  
**Status**: ✅ Sincronizado y funcional
