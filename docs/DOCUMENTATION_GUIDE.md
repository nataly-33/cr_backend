# 📚 Guía de Documentación Completa - Clinic Records Backend

**Versión:** 1.0.0  
**Última actualización:** 5 de Noviembre, 2025

---

## 📖 Índice

1. [Visión General del Sistema](#visión-general-del-sistema)
2. [Arquitectura](#arquitectura)
3. [Modelo de Negocio SaaS](#modelo-de-negocio-saas)
4. [Sistema de Permisos (RBAC)](#sistema-de-permisos-rbac)
5. [Módulos del Sistema](#módulos-del-sistema)
6. [API Endpoints](#api-endpoints)
7. [Flujos de Trabajo](#flujos-de-trabajo)
8. [Base de Datos](#base-de-datos)
9. [Seguridad](#seguridad)
10. [Integraciones](#integraciones)

---

## 🎯 Visión General del Sistema

### ¿Qué es Clinic Records?

**Clinic Records** es un sistema **SaaS multi-tenant** para la gestión de historias clínicas electrónicas (EHR/EMR) diseñado para hospitales, clínicas y consultorios médicos.

### Características Principales

- 🏥 **Multi-tenancy**: Múltiples clínicas usando la misma aplicación con datos completamente aislados
- 📋 **Historias Clínicas Digitales**: Gestión completa de pacientes y documentos médicos
- 🔐 **Control de Acceso (RBAC)**: Permisos granulares por rol y usuario
- 📄 **Documentos Clínicos**: Almacenamiento seguro en S3 con firma digital
- 📊 **Reportes y Analytics**: Generación de reportes en PDF/Excel
- 🔄 **Backups Automáticos**: Respaldos diarios con Celery
- 🔍 **Auditoría Completa**: Trazabilidad de todas las acciones

### Stack Tecnológico

**Backend:**

- Python 3.11+
- Django 5.0+
- Django REST Framework
- PostgreSQL 15+
- Redis (Celery)
- AWS S3 (almacenamiento)

**Frontend:**

- React 18+ con TypeScript
- Vite
- TailwindCSS
- Zustand (estado global)
- React Router v6

---

## 🏗️ Arquitectura

### Arquitectura General

```
┌─────────────────────────────────────────────────────────────┐
│                        FRONTEND (React)                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Patients │  │Documents │  │ Reports  │  │  Admin   │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
└───────┼─────────────┼─────────────┼─────────────┼──────────┘
        │             │             │             │
        └─────────────┴─────────────┴─────────────┘
                          │
                    API REST (JWT)
                          │
┌─────────────────────────┴──────────────────────────────────┐
│                    BACKEND (Django)                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │             Middleware de Tenant                     │  │
│  │  - Identifica tenant por subdomain/header           │  │
│  │  - Aplica filtros automáticos a queries             │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ Tenants  │  │Accounts  │  │Patients  │  │Documents │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ Records  │  │ Reports  │  │  Audit   │  │ Backup   │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
└──────────────────────────┬──────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
   PostgreSQL          AWS S3            Redis
   (Base de Datos)   (Archivos)      (Celery Queue)
```

### Patrón Multi-Tenant

**Estrategia:** Shared Database, Shared Schema con filtros a nivel de aplicación

**Ventajas:**

- ✅ Costos reducidos (una sola base de datos)
- ✅ Fácil mantenimiento
- ✅ Backups centralizados

**Cómo funciona:**

1. Cada modelo hereda de `TenantAwareModel`
2. El middleware `TenantMiddleware` identifica el tenant actual
3. El manager `TenantManager` filtra automáticamente por tenant
4. Las queries solo retornan datos del tenant activo

```python
# Ejemplo de modelo con tenant
class Patient(TenantAwareModel):
    tenant = models.ForeignKey('core.Tenant', on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100)
    # ... otros campos

    objects = TenantManager()  # Filtra automáticamente por tenant

# Uso en código
set_current_tenant(mi_tenant)
patients = Patient.objects.all()  # Solo del tenant actual
```

---

## 💼 Modelo de Negocio SaaS

### Planes de Suscripción

| Plan             | Precio/Mes | Usuarios | Pacientes | Almacenamiento | Características                                     |
| ---------------- | ---------- | -------- | --------- | -------------- | --------------------------------------------------- |
| **Basic**        | $1         | 10       | 500       | 50 GB          | Funciones básicas, soporte por email                |
| **Professional** | $19        | 50       | 2,000     | 200 GB         | Reportes avanzados, API access, soporte prioritario |
| **Enterprise**   | $49        | 200      | 10,000    | 1 TB           | Backup diario, multi-sucursales, IA, soporte 24/7   |

### Estados de Suscripción

- **`trial`**: Período de prueba (30 días gratuitos)
- **`active`**: Suscripción pagada y activa
- **`past_due`**: Pago atrasado (gracia de 7 días)
- **`canceled`**: Cancelado por el usuario
- **`suspended`**: Suspendido por falta de pago

### Flujo de Onboarding

```
1. Usuario visita landing page
   ↓
2. Selecciona plan y crea cuenta (API pública /api/tenants/register/)
   ↓
3. Se crea tenant con estado "trial"
   ↓
4. Recibe email de bienvenida con credenciales
   ↓
5. Accede a su subdominio (ej: hospital-santacruz.clinidocs.com)
   ↓
6. Configura su cuenta (usuarios, pacientes, etc.)
   ↓
7. Después de 30 días, debe pagar para continuar
```

### Límites por Plan

Los límites se aplican en las vistas con validación:

```python
def perform_create(self, serializer):
    tenant = self.request.tenant

    # Verificar límite de pacientes
    if tenant.patients.count() >= tenant.max_patients:
        raise ValidationError("Límite de pacientes alcanzado")

    serializer.save(tenant=tenant)
```

---

## 🔐 Sistema de Permisos (RBAC)

### Roles del Sistema

#### 1. **Administrador TI** (`SystemRoles.ADMIN_TI`)

**Descripción:** Administrador completo del tenant (clínica/hospital)

**Permisos:**

- ✅ CRUD completo en TODOS los recursos
- ✅ Gestión de usuarios y roles
- ✅ Configuración del tenant
- ✅ Acceso a auditoría y reportes
- ✅ Backup y restauración

**Uso típico:** Director del hospital, Administrador del sistema

#### 2. **Doctor** (`Doctor`)

**Descripción:** Personal médico que atiende pacientes

**Permisos:**

- ✅ **Pacientes**: Leer y actualizar (no crear ni eliminar)
- ✅ **Historias Clínicas**: CRUD completo
- ✅ **Documentos Clínicos**: CRUD completo + Firma digital
- ✅ **Formularios Clínicos**: CRUD completo
- ✅ **Reportes**: Leer y generar

**Restricciones:**

- ❌ No puede gestionar usuarios
- ❌ No puede cambiar configuración del tenant
- ❌ No puede ver auditoría completa

**Uso típico:** Médicos, Enfermeras con permisos de registro

#### 3. **Paciente** (`Paciente`)

**Descripción:** Usuario final que consulta SU propia información

**Permisos:**

- ✅ **Historia Clínica**: Solo lectura de SU propia historia
- ✅ **Documentos**: Solo lectura de SUS propios documentos
- ✅ **Formularios**: Solo lectura de SUS propios formularios

**Restricciones:**

- ❌ No puede ver datos de otros pacientes
- ❌ No puede editar nada
- ❌ No puede crear documentos

**Uso típico:** Pacientes que acceden a su portal

### Estructura de Permisos

Los permisos se estructuran como: `<recurso>.<acción>`

**Recursos:**

- `patient`
- `clinical_record`
- `document`
- `user`
- `role`
- `report`
- `audit`

**Acciones:**

- `create` - Crear nuevos registros
- `read` - Ver registros
- `update` - Modificar registros existentes
- `delete` - Eliminar registros
- `export` - Exportar datos
- `sign` - Firmar documentos (solo para `document`)

**Ejemplos:**

- `patient.read` - Ver pacientes
- `document.create` - Crear documentos
- `document.sign` - Firmar documentos digitalmente
- `clinical_record.delete` - Eliminar historias clínicas

### Cómo se Aplican los Permisos

#### En el Backend (Django)

```python
# En las vistas
class ClinicalRecordViewSet(PermissionByActionMixin, viewsets.ModelViewSet):
    resource_name = 'clinical_record'  # Define el recurso

    permission_classes_by_action = {
        'list': [IsTenantMember],  # Solo miembro del tenant
        'create': [IsTenantMember, CanManageClinicalRecords],  # + permiso
        'update': [IsTenantMember, CanManageClinicalRecords],
        'destroy': [IsTenantMember, CanManageClinicalRecords],
    }
```

#### En el Frontend (React)

```typescript
// Hook de permisos
import { usePermissions } from "@core/hooks";

function ClinicalRecordPage() {
  const { can } = usePermissions();

  return (
    <>
      {can("clinical_record", "create") && (
        <Button onClick={handleCreate}>Crear Historia</Button>
      )}

      {can("clinical_record", "update") && (
        <Button onClick={handleEdit}>Editar</Button>
      )}
    </>
  );
}
```

### Creación de Roles y Permisos

Los roles y permisos se crean automáticamente por el seeder para cada tenant:

```python
# En el seeder
def create_permissions_and_roles(tenant):
    # 1. Crear todos los permisos
    permissions = []
    for resource in ['patient', 'clinical_record', 'document', ...]:
        for action in ['create', 'read', 'update', 'delete']:
            perm = Permission.objects.create(
                tenant=tenant,
                code=f'{resource}.{action}',
                name=f'{action.title()} {resource}',
                resource=resource,
                action=action
            )
            permissions.append(perm)

    # 2. Crear roles y asignar permisos
    doctor_role = Role.objects.create(
        tenant=tenant,
        name='Doctor',
        description='Doctor con CRUD de historias clínicas'
    )
    doctor_role.permissions.set([
        # Permisos específicos del doctor
    ])
```

---

## 📦 Módulos del Sistema

### 1. Tenants (Multi-tenancy)

**Ruta:** `apps/tenants/`

**Propósito:** Gestionar los "clientes" del SaaS (hospitales, clínicas)

**Modelos:**

- `SubscriptionPlan` - Planes (Basic, Pro, Enterprise)
- `Tenant` - Cada cliente (hospital/clínica)

**Endpoints:**

```
POST   /api/tenants/register/          # Registro público (no requiere auth)
GET    /api/tenants/public/plans/      # Listar planes disponibles
GET    /api/tenants/me/                # Info del tenant actual
PATCH  /api/tenants/me/                # Actualizar tenant
```

**Flujo de Registro:**

```python
# POST /api/tenants/register/
{
  "name": "Hospital General",
  "subdomain": "hospital-general",  # Único globalmente
  "email": "admin@hospital.com",
  "password": "SecurePass123!",
  "plan": "professional",
  "first_name": "Juan",
  "last_name": "Pérez"
}

# Respuesta
{
  "tenant": { "id": "...", "name": "...", "subdomain": "..." },
  "user": { "id": "...", "email": "..." },
  "access_token": "eyJ...",
  "refresh_token": "eyJ..."
}
```

---

### 2. Accounts (Usuarios y Permisos)

**Ruta:** `apps/accounts/`

**Propósito:** Autenticación, autorización y gestión de usuarios

**Modelos:**

- `User` - Usuarios del sistema
- `Role` - Roles (Admin TI, Doctor, Paciente)
- `Permission` - Permisos individuales

**Endpoints:**

```
# Autenticación
POST   /api/auth/login/                # Login
POST   /api/auth/refresh/              # Refresh token
POST   /api/auth/logout/               # Logout
POST   /api/auth/password/reset/       # Solicitar reset
POST   /api/auth/password/confirm/     # Confirmar reset

# Usuarios
GET    /api/users/                     # Listar usuarios
POST   /api/users/                     # Crear usuario
GET    /api/users/{id}/                # Ver usuario
PATCH  /api/users/{id}/                # Actualizar usuario
DELETE /api/users/{id}/                # Eliminar usuario
GET    /api/users/me/                  # Usuario actual

# Roles y Permisos
GET    /api/roles/                     # Listar roles
POST   /api/roles/                     # Crear rol
GET    /api/permissions/               # Listar permisos
```

**Ejemplo de Login:**

```python
# POST /api/auth/login/
{
  "email": "doctor@hospital.com",
  "password": "MyPassword123!"
}

# Respuesta
{
  "access_token": "eyJhbGci...",
  "refresh_token": "eyJhbGci...",
  "user": {
    "id": "uuid",
    "email": "doctor@hospital.com",
    "first_name": "Juan",
    "last_name": "Pérez",
    "role": {
      "name": "Doctor",
      "permissions": ["patient.read", "clinical_record.create", ...]
    },
    "tenant": {
      "id": "uuid",
      "name": "Hospital General",
      "subdomain": "hospital-general"
    }
  }
}
```

---

### 3. Patients (Pacientes)

**Ruta:** `apps/patients/`

**Propósito:** Gestión de pacientes

**Modelo:**

```python
class Patient(TenantAwareModel):
    tenant = ForeignKey(Tenant)
    identity_document = CharField()      # CI, DNI, Pasaporte
    identity_document_type = CharField()
    first_name = CharField()
    last_name = CharField()
    date_of_birth = DateField()
    gender = CharField(choices=['M', 'F', 'O'])
    blood_type = CharField()
    phone = CharField()
    email = EmailField()
    address = TextField()
    city = CharField()
    emergency_contact_name = CharField()
    emergency_contact_phone = CharField()
```

**Endpoints:**

```
GET    /api/patients/                  # Listar (con paginación)
POST   /api/patients/                  # Crear
GET    /api/patients/{id}/             # Ver detalle
PATCH  /api/patients/{id}/             # Actualizar
DELETE /api/patients/{id}/             # Eliminar (soft delete)
GET    /api/patients/search/?q=juan    # Buscar por nombre
```

**Filtros disponibles:**

- `?identity_document=12345678`
- `?gender=M`
- `?city=La Paz`
- `?search=Juan Pérez`

---

### 4. Clinical Records (Historias Clínicas)

**Ruta:** `apps/clinical_records/`

**Propósito:** Gestión de historias clínicas y formularios

**Modelos:**

#### **ClinicalRecord** (Historia Clínica)

```python
class ClinicalRecord(TenantAwareModel):
    tenant = ForeignKey(Tenant)
    patient = OneToOneField(Patient)  # UNA historia por paciente
    record_number = CharField(unique=True)  # HC-2025-000001
    status = CharField(choices=['active', 'inactive', 'archived'])
    blood_type = CharField()  # A+, B-, O+, etc.
    allergies = JSONField(default=list)  # ["Penicilina", "Polen"]
    chronic_conditions = JSONField(default=list)  # ["Hipertensión"]
    medications = JSONField(default=list)  # [{"name": "Losartán", ...}]
    family_history = TextField()
    surgical_history = TextField()
    notes = TextField()
```

#### **ClinicalForm** (Formulario Clínico)

```python
class ClinicalForm(TenantAwareModel):
    tenant = ForeignKey(Tenant)
    clinical_record = ForeignKey(ClinicalRecord)
    form_type = CharField(choices=[
        ('triage', 'Triaje'),
        ('consultation', 'Consulta'),
        ('prescription', 'Receta'),
        ('lab_order', 'Orden Lab'),
        ...
    ])
    form_data = JSONField()  # Estructura flexible
    filled_by = ForeignKey(User)
    form_date = DateTimeField()
```

**Endpoints:**

```
# Historias Clínicas
GET    /api/clinical-records/                 # Listar
POST   /api/clinical-records/                 # Crear
GET    /api/clinical-records/{id}/            # Ver
PATCH  /api/clinical-records/{id}/            # Actualizar
DELETE /api/clinical-records/{id}/            # Eliminar

# Formularios Clínicos
GET    /api/clinical-records/forms/           # Listar formularios
POST   /api/clinical-records/forms/           # Crear formulario
GET    /api/clinical-records/forms/{id}/      # Ver formulario
GET    /api/clinical-records/forms/types/     # Tipos disponibles
```

**Ejemplo de Formulario de Triaje:**

```json
{
  "clinical_record": "uuid-historia-clinica",
  "form_type": "triage",
  "form_data": {
    "vital_signs": {
      "temperature": 36.5,
      "blood_pressure_systolic": 120,
      "blood_pressure_diastolic": 80,
      "heart_rate": 72,
      "respiratory_rate": 16,
      "oxygen_saturation": 98,
      "weight": 70.5,
      "height": 175
    },
    "chief_complaint": "Dolor de cabeza",
    "initial_assessment": "Paciente alerta y orientado",
    "triage_level": {
      "level": 4,
      "name": "Semi-urgente",
      "color": "green"
    }
  },
  "filled_by": "uuid-usuario",
  "form_date": "2025-11-05T10:30:00Z"
}
```

---

### 5. Documents (Documentos Clínicos)

**Ruta:** `apps/documents/`

**Propósito:** Almacenar documentos médicos (PDFs, imágenes, contenido estructurado)

**Modelos:**

#### **ClinicalDocument**

```python
class ClinicalDocument(TenantAwareModel):
    tenant = ForeignKey(Tenant)
    clinical_record = ForeignKey(ClinicalRecord)
    document_type = CharField(choices=[
        ('consultation', 'Consulta'),
        ('lab_result', 'Resultado Lab'),
        ('imaging_report', 'Informe Imagen'),
        ('prescription', 'Receta'),
        ('surgical_note', 'Nota Quirúrgica'),
        ('discharge_summary', 'Resumen Alta'),
        ...
    ])
    title = CharField()
    description = TextField()
    document_date = DateTimeField()
    specialty = CharField()
    doctor_name = CharField()
    doctor_license = CharField()

    # Contenido
    content = JSONField(default=dict)  # Contenido estructurado
    file_path = CharField()  # Ruta en S3 (opcional)
    file_name = CharField()
    file_size_bytes = BigIntegerField()
    mime_type = CharField()
    file_hash = CharField()  # SHA-256 para integridad

    # OCR
    ocr_text = TextField()
    ocr_confidence = DecimalField()
    ocr_processed = BooleanField(default=False)

    # Firma Digital
    is_signed = BooleanField(default=False)
    signed_at = DateTimeField()
    signed_by = ForeignKey(User)
    digital_signature = TextField()
    is_locked = BooleanField(default=False)

    # Metadata
    tags = JSONField(default=list)
    created_by = ForeignKey(User)
```

**Endpoints:**

```
GET    /api/documents/                    # Listar
POST   /api/documents/                    # Crear
GET    /api/documents/{id}/               # Ver
PATCH  /api/documents/{id}/               # Actualizar
DELETE /api/documents/{id}/               # Eliminar
POST   /api/documents/upload/             # Subir archivo
GET    /api/documents/{id}/download/      # Descargar
POST   /api/documents/{id}/sign/          # Firmar digitalmente
GET    /api/documents/{id}/access_log/    # Log de accesos
GET    /api/documents/search/?q=diabetes  # Búsqueda (incluye OCR)
```

**Ejemplo - Crear Documento con Contenido JSON:**

```json
{
  "clinical_record": "uuid-historia",
  "document_type": "consultation",
  "title": "Consulta Médica - Control",
  "description": "Consulta de control mensual",
  "document_date": "2025-11-05T14:00:00Z",
  "specialty": "Cardiología",
  "doctor_name": "Dr. Juan Pérez",
  "doctor_license": "MED-12345",
  "content": {
    "chief_complaint": "Control de presión arterial",
    "vital_signs": {
      "blood_pressure": "130/85",
      "heart_rate": 78,
      "temperature": 36.7
    },
    "diagnosis": "Hipertensión arterial controlada",
    "treatment_plan": "Continuar con Losartán 50mg/día"
  },
  "tags": ["cardiologia", "control", "hipertension"]
}
```

**Ejemplo - Subir Documento PDF:**

```python
# POST /api/documents/upload/
Content-Type: multipart/form-data

{
  "clinical_record": "uuid-historia",
  "document_type": "lab_result",
  "title": "Hemograma Completo",
  "document_date": "2025-11-05",
  "specialty": "Laboratorio",
  "file": <archivo-pdf>
}
```

**Firma Digital:**

```python
# POST /api/documents/{id}/sign/
# (No requiere body, usa el usuario autenticado)

# Respuesta
{
  "message": "Documento firmado exitosamente",
  "signed_at": "2025-11-05T15:30:00Z",
  "signed_by": "Dr. Juan Pérez",
  "digital_signature": "a1b2c3d4e5f6..."
}
```

---

### 6. Reports (Reportes)

**Ruta:** `apps/reports/`

**Propósito:** Generación de reportes estadísticos

**Modelo:**

```python
class ReportTemplate(TenantAwareModel):
    tenant = ForeignKey(Tenant)
    name = CharField()
    description = TextField()
    report_type = CharField()
    category = CharField()
    output_formats = JSONField()  # ['pdf', 'excel']
    is_public = BooleanField()
    allowed_roles = JSONField()
```

**Endpoints:**

```
GET    /api/reports/templates/          # Plantillas disponibles
POST   /api/reports/generate/           # Generar reporte
GET    /api/reports/history/            # Historial de reportes
GET    /api/reports/{id}/download/      # Descargar reporte
```

**Tipos de Reportes:**

- `documents_by_type` - Documentos agrupados por tipo
- `patients_summary` - Estadísticas de pacientes
- `activity_log` - Log de actividad
- `usage_statistics` - Métricas de uso del sistema

**Ejemplo:**

```json
# POST /api/reports/generate/
{
  "template_id": "uuid-plantilla",
  "format": "pdf",  # o "excel"
  "filters": {
    "start_date": "2025-01-01",
    "end_date": "2025-11-05",
    "document_type": "consultation"
  }
}

# Respuesta
{
  "report_id": "uuid-reporte",
  "status": "completed",
  "download_url": "https://s3.../reporte.pdf",
  "generated_at": "2025-11-05T16:00:00Z"
}
```

---

### 7. Audit (Auditoría)

**Ruta:** `apps/audit/`

**Propósito:** Trazabilidad completa de acciones

**Modelo:**

```python
class AuditLog(models.Model):
    tenant = ForeignKey(Tenant)
    user = ForeignKey(User)
    action = CharField(choices=[
        ('CREATE', 'Create'),
        ('READ', 'Read'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
    ])
    model_name = CharField()  # 'Patient', 'ClinicalRecord', etc.
    object_id = UUIDField()
    changes = JSONField()  # {"before": {...}, "after": {...}}
    ip_address = GenericIPAddressField()
    user_agent = TextField()
    timestamp = DateTimeField(auto_now_add=True)
```

**Endpoints:**

```
GET    /api/audit/logs/                 # Listar logs
GET    /api/audit/logs/?model=Patient   # Filtrar por modelo
GET    /api/audit/logs/?user={id}       # Filtrar por usuario
GET    /api/audit/logs/?action=DELETE   # Filtrar por acción
```

**Ejemplo de Log:**

```json
{
  "id": "uuid",
  "user": "doctor@hospital.com",
  "action": "UPDATE",
  "model_name": "Patient",
  "object_id": "uuid-paciente",
  "changes": {
    "before": { "phone": "123456" },
    "after": { "phone": "789012" }
  },
  "ip_address": "192.168.1.100",
  "timestamp": "2025-11-05T17:00:00Z"
}
```

---

### 8. Backup (Respaldos)

**Ruta:** `apps/backup/`

**Propósito:** Backups automáticos de la base de datos

**Modelo:**

```python
class BackupJob(TenantAwareModel):
    tenant = ForeignKey(Tenant)
    backup_type = CharField(choices=[
        ('manual', 'Manual'),
        ('automatic', 'Automatic'),
    ])
    status = CharField(choices=[
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ])
    file_path = CharField()  # Ruta en S3
    file_size_bytes = BigIntegerField()
    started_at = DateTimeField()
    completed_at = DateTimeField()
    error_message = TextField()
```

**Endpoints:**

```
GET    /api/backup/jobs/                # Listar backups
POST   /api/backup/jobs/                # Crear backup manual
GET    /api/backup/jobs/{id}/           # Ver detalle
POST   /api/backup/jobs/{id}/restore/   # Restaurar backup
DELETE /api/backup/jobs/{id}/           # Eliminar backup
```

**Configuración de Celery:**

```python
# Backup automático diario a las 2 AM
@shared_task
def create_automatic_backup():
    for tenant in Tenant.objects.filter(subscription_status='active'):
        BackupService().create_backup(tenant, backup_type='automatic')

# En celery beat schedule
CELERY_BEAT_SCHEDULE = {
    'daily-backup': {
        'task': 'apps.backup.tasks.create_automatic_backup',
        'schedule': crontab(hour=2, minute=0),  # 02:00 AM
    },
}
```

---

### 9. Notifications (Notificaciones)

**Ruta:** `apps/notifications/`

**Propósito:** Notificaciones in-app y por email

**Modelo:**

```python
class Notification(TenantAwareModel):
    tenant = ForeignKey(Tenant)
    user = ForeignKey(User)
    notification_type = CharField(choices=[
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('success', 'Success'),
    ])
    title = CharField()
    message = TextField()
    link = CharField()  # URL para "Ver más"
    is_read = BooleanField(default=False)
    read_at = DateTimeField()
    created_at = DateTimeField(auto_now_add=True)
```

**Endpoints:**

```
GET    /api/notifications/              # Listar notificaciones
POST   /api/notifications/              # Crear notificación
PATCH  /api/notifications/{id}/read/    # Marcar como leída
PATCH  /api/notifications/read_all/     # Marcar todas como leídas
DELETE /api/notifications/{id}/         # Eliminar notificación
GET    /api/notifications/unread_count/ # Cantidad no leídas
```

**Ejemplo - Enviar Notificación:**

```python
from apps.notifications.services import NotificationService

# Notificación in-app
NotificationService.send_notification(
    user=doctor_user,
    title="Nuevo documento disponible",
    message="Se ha agregado un resultado de laboratorio para Juan Pérez",
    notification_type="info",
    link="/documents/123"
)

# Notificación por email
NotificationService.send_email(
    to=doctor_user.email,
    subject="Nuevo documento disponible",
    template="new_document",
    context={"patient_name": "Juan Pérez"}
)
```

---

## 🔌 API Endpoints - Referencia Rápida

### Autenticación

```
POST   /api/auth/login/                # Login
POST   /api/auth/refresh/              # Refresh token
POST   /api/auth/logout/               # Logout
POST   /api/auth/password/reset/       # Solicitar reset
POST   /api/auth/password/confirm/     # Confirmar reset
```

### Usuarios

```
GET    /api/users/                     # Listar
POST   /api/users/                     # Crear
GET    /api/users/{id}/                # Ver
PATCH  /api/users/{id}/                # Actualizar
DELETE /api/users/{id}/                # Eliminar
GET    /api/users/me/                  # Usuario actual
```

### Pacientes

```
GET    /api/patients/                  # Listar
POST   /api/patients/                  # Crear
GET    /api/patients/{id}/             # Ver
PATCH  /api/patients/{id}/             # Actualizar
DELETE /api/patients/{id}/             # Eliminar
GET    /api/patients/search/?q=texto   # Buscar
```

### Historias Clínicas

```
GET    /api/clinical-records/          # Listar
POST   /api/clinical-records/          # Crear
GET    /api/clinical-records/{id}/     # Ver
PATCH  /api/clinical-records/{id}/     # Actualizar
DELETE /api/clinical-records/{id}/     # Eliminar
```

### Formularios Clínicos

```
GET    /api/clinical-records/forms/    # Listar
POST   /api/clinical-records/forms/    # Crear
GET    /api/clinical-records/forms/{id}/ # Ver
GET    /api/clinical-records/forms/types/ # Tipos
```

### Documentos

```
GET    /api/documents/                 # Listar
POST   /api/documents/                 # Crear
GET    /api/documents/{id}/            # Ver
PATCH  /api/documents/{id}/            # Actualizar
DELETE /api/documents/{id}/            # Eliminar
POST   /api/documents/upload/          # Subir archivo
GET    /api/documents/{id}/download/   # Descargar
POST   /api/documents/{id}/sign/       # Firmar
```

### Reportes

```
GET    /api/reports/templates/         # Plantillas
POST   /api/reports/generate/          # Generar
GET    /api/reports/history/           # Historial
GET    /api/reports/{id}/download/     # Descargar
```

### Auditoría

```
GET    /api/audit/logs/                # Listar logs
```

### Backups

```
GET    /api/backup/jobs/               # Listar
POST   /api/backup/jobs/               # Crear
POST   /api/backup/jobs/{id}/restore/  # Restaurar
```

### Notificaciones

```
GET    /api/notifications/             # Listar
PATCH  /api/notifications/{id}/read/   # Marcar leída
GET    /api/notifications/unread_count/ # Cantidad no leídas
```

---

## 🔄 Flujos de Trabajo

### Flujo 1: Registro de un Nuevo Paciente

```
1. Doctor hace login
   POST /api/auth/login/

2. Crea un paciente
   POST /api/patients/
   {
     "identity_document": "12345678",
     "first_name": "Juan",
     "last_name": "Pérez",
     ...
   }

3. Se crea automáticamente una historia clínica
   (Triggered en el backend con signals)

4. Se registra en auditoría
   AuditLog: CREATE Patient
```

### Flujo 2: Atención Médica Completa

```
1. Enfermera registra Triaje
   POST /api/clinical-records/forms/
   {
     "form_type": "triage",
     "form_data": {
       "vital_signs": {...},
       "chief_complaint": "Dolor de cabeza"
     }
   }

2. Doctor consulta historia clínica
   GET /api/clinical-records/?patient={id}

3. Doctor registra consulta médica
   POST /api/clinical-records/forms/
   {
     "form_type": "consultation",
     "form_data": {
       "diagnosis": "Cefalea tensional",
       "treatment_plan": "..."
     }
   }

4. Doctor crea documento con diagnóstico
   POST /api/documents/
   {
     "document_type": "consultation",
     "title": "Consulta Médica",
     "content": {
       "diagnosis": "...",
       "treatment": "..."
     }
   }

5. Doctor firma el documento
   POST /api/documents/{id}/sign/

6. Paciente recibe notificación
   Notification: "Nuevo documento disponible"
```

### Flujo 3: Gestión de Resultados de Laboratorio

```
1. Doctor solicita exámenes
   POST /api/clinical-records/forms/
   {
     "form_type": "lab_order",
     "form_data": {
       "tests": ["Hemograma", "Glucemia"],
       "urgency": "routine"
     }
   }

2. Laboratorio procesa y sube resultados
   POST /api/documents/upload/
   {
     "document_type": "lab_result",
     "title": "Hemograma Completo",
     "file": <pdf-con-resultados>
   }

3. Sistema extrae texto con OCR (Celery task)
   Task: process_document_ocr(document_id)

4. Doctor es notificado
   Notification: "Resultados de laboratorio disponibles"

5. Doctor revisa y firma
   GET /api/documents/{id}/
   POST /api/documents/{id}/sign/

6. Paciente puede ver su resultado
   GET /api/documents/{id}/ (con permisos de paciente)
```

---

## 🗄️ Base de Datos

### Diagrama de Relaciones Principal

```
┌─────────────┐
│   Tenant    │
└──────┬──────┘
       │
       ├──────────┬──────────┬──────────┬──────────┐
       │          │          │          │          │
       ▼          ▼          ▼          ▼          ▼
   ┌──────┐  ┌──────┐  ┌────────┐  ┌────────┐  ┌────────┐
   │ User │  │Patient│ │Clinical│  │Document│  │ Report │
   └──────┘  └───┬───┘ │ Record │  └────────┘  └────────┘
                 │     └────┬───┘
                 │          │
                 └──────────┴─── One-to-One

   ┌────────────────┐
   │ ClinicalForm   │
   │ (Many-to-One)  │
   └────────────────┘
        │
        └─── ClinicalRecord
```

### Modelos Principales

#### Tenant

```sql
CREATE TABLE core_tenant (
    id UUID PRIMARY KEY,
    name VARCHAR(255),
    subdomain VARCHAR(63) UNIQUE,  -- Identifica al tenant
    subscription_plan VARCHAR(50),
    subscription_status VARCHAR(50),
    max_users INTEGER,
    max_patients INTEGER,
    max_storage_gb INTEGER,
    created_at TIMESTAMP,
    deleted_at TIMESTAMP  -- Soft delete
);
```

#### User

```sql
CREATE TABLE accounts_user (
    id UUID PRIMARY KEY,
    tenant_id UUID REFERENCES core_tenant(id),
    email VARCHAR(255) UNIQUE,
    password VARCHAR(128),  -- Hashed con bcrypt
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    role_id UUID REFERENCES accounts_role(id),
    is_active BOOLEAN DEFAULT TRUE,
    email_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP
);
```

#### Patient

```sql
CREATE TABLE patients_patient (
    id UUID PRIMARY KEY,
    tenant_id UUID REFERENCES core_tenant(id),
    identity_document VARCHAR(50),
    identity_document_type VARCHAR(20),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    date_of_birth DATE,
    gender VARCHAR(1),
    blood_type VARCHAR(5),
    phone VARCHAR(20),
    email VARCHAR(255),
    address TEXT,
    created_at TIMESTAMP,
    deleted_at TIMESTAMP,
    UNIQUE(tenant_id, identity_document)  -- Único por tenant
);

CREATE INDEX idx_patient_tenant ON patients_patient(tenant_id);
CREATE INDEX idx_patient_identity ON patients_patient(identity_document);
```

#### ClinicalRecord

```sql
CREATE TABLE clinical_records_clinicalrecord (
    id UUID PRIMARY KEY,
    tenant_id UUID REFERENCES core_tenant(id),
    patient_id UUID UNIQUE REFERENCES patients_patient(id),  -- One-to-One
    record_number VARCHAR(50) UNIQUE,
    status VARCHAR(20),
    blood_type VARCHAR(5),
    allergies JSONB DEFAULT '[]',  -- ["Penicilina", "Polen"]
    chronic_conditions JSONB DEFAULT '[]',
    medications JSONB DEFAULT '[]',
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE INDEX idx_clinicalrecord_patient ON clinical_records_clinicalrecord(patient_id);
```

#### ClinicalForm

```sql
CREATE TABLE clinical_records_clinicalform (
    id UUID PRIMARY KEY,
    tenant_id UUID REFERENCES core_tenant(id),
    clinical_record_id UUID REFERENCES clinical_records_clinicalrecord(id),
    form_type VARCHAR(100),  -- 'triage', 'consultation', etc.
    form_data JSONB,  -- Estructura flexible
    filled_by_id UUID REFERENCES accounts_user(id),
    form_date TIMESTAMP,
    created_at TIMESTAMP
);

CREATE INDEX idx_clinicalform_record ON clinical_records_clinicalform(clinical_record_id);
CREATE INDEX idx_clinicalform_type ON clinical_records_clinicalform(form_type);
```

#### ClinicalDocument

```sql
CREATE TABLE clinical_document (
    id UUID PRIMARY KEY,
    tenant_id UUID REFERENCES core_tenant(id),
    clinical_record_id UUID REFERENCES clinical_records_clinicalrecord(id),
    document_type VARCHAR(100),
    title VARCHAR(255),
    description TEXT,
    document_date TIMESTAMP,
    content JSONB DEFAULT '{}',  -- Contenido estructurado
    file_path VARCHAR(500),  -- Ruta en S3 (opcional)
    file_name VARCHAR(255),
    file_size_bytes BIGINT,
    is_signed BOOLEAN DEFAULT FALSE,
    signed_at TIMESTAMP,
    signed_by_id UUID,
    digital_signature TEXT,
    created_at TIMESTAMP,
    deleted_at TIMESTAMP
);

CREATE INDEX idx_document_record ON clinical_document(clinical_record_id);
CREATE INDEX idx_document_type ON clinical_document(document_type);
CREATE INDEX idx_document_date ON clinical_document(document_date);
```

### Queries Comunes

#### Obtener pacientes con su historia clínica

```sql
SELECT p.*, cr.record_number, cr.blood_type, cr.allergies
FROM patients_patient p
LEFT JOIN clinical_records_clinicalrecord cr ON p.id = cr.patient_id
WHERE p.tenant_id = :tenant_id
  AND p.deleted_at IS NULL
ORDER BY p.created_at DESC;
```

#### Documentos de un paciente

```sql
SELECT d.*
FROM clinical_document d
INNER JOIN clinical_records_clinicalrecord cr ON d.clinical_record_id = cr.id
INNER JOIN patients_patient p ON cr.patient_id = p.id
WHERE p.id = :patient_id
  AND d.tenant_id = :tenant_id
  AND d.deleted_at IS NULL
ORDER BY d.document_date DESC;
```

#### Buscar pacientes por texto

```sql
SELECT *
FROM patients_patient
WHERE tenant_id = :tenant_id
  AND deleted_at IS NULL
  AND (
    LOWER(first_name) LIKE LOWER(:query)
    OR LOWER(last_name) LIKE LOWER(:query)
    OR identity_document LIKE :query
  )
LIMIT 20;
```

---

## 🔒 Seguridad

### Autenticación JWT

**Tokens:**

- **Access Token**: Expira en 1 hora
- **Refresh Token**: Expira en 7 días

**Headers requeridos:**

```
Authorization: Bearer <access_token>
X-Tenant: <subdomain>  (opcional, se puede inferir del token)
```

**Renovación:**

```python
# POST /api/auth/refresh/
{
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}

# Respuesta
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."  # Nuevo refresh opcional
}
```

### Validación de Permisos

**En cada request:**

1. Verificar autenticación (JWT válido)
2. Identificar tenant (del token o header)
3. Verificar que el usuario pertenece al tenant
4. Validar permisos para la acción solicitada
5. Aplicar filtros de tenant en queries

**Código ejemplo:**

```python
class PermissionByActionMixin:
    def check_permissions(self, request):
        # 1. Autenticación
        if not request.user.is_authenticated:
            raise AuthenticationFailed()

        # 2. Tenant
        tenant = get_current_tenant()
        if request.user.tenant != tenant:
            raise PermissionDenied("No perteneces a este tenant")

        # 3. Permisos
        required_permission = f'{self.resource_name}.{self.action_to_permission()}'
        if not request.user.has_permission(required_permission):
            raise PermissionDenied("No tienes permisos para esta acción")
```

### Protección de Datos

**Soft Delete:**

- Todos los modelos tienen `deleted_at`
- Los registros "eliminados" se marcan con timestamp
- Los managers filtran automáticamente registros eliminados
- Solo el Admin TI puede recuperar registros eliminados

**Aislamiento por Tenant:**

- Todos los queries filtran automáticamente por tenant
- Imposible acceder a datos de otro tenant
- Validación doble: middleware + manager

**Auditoría:**

- Todas las acciones CRUD se registran
- Almacena before/after de cambios
- IP y user agent del usuario

---

## 🔌 Integraciones

### AWS S3 (Almacenamiento)

**Configuración:**

```python
# settings.py
AWS_ACCESS_KEY_ID = env('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = env('AWS_STORAGE_BUCKET_NAME')
AWS_S3_REGION_NAME = env('AWS_S3_REGION_NAME', default='us-east-1')
```

**Estructura de carpetas:**

```
clinic-records-bucket/
├── {tenant_id}/
│   ├── documents/
│   │   ├── {year}/
│   │   │   ├── {month}/
│   │   │   │   └── {document_id}.pdf
│   └── backups/
│       └── backup-{timestamp}.sql.gz
```

**URLs firmadas:**

```python
from apps.documents.storage import S3Storage

storage = S3Storage()
url = storage.get_presigned_url(file_path, expiration=300)  # 5 minutos
```

### SendGrid (Emails)

**Configuración:**

```python
# settings.py
SENDGRID_API_KEY = env('SENDGRID_API_KEY')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='noreply@clinidocs.com')
```

**Uso:**

```python
from apps.notifications.services import EmailService

EmailService.send_email(
    to='doctor@hospital.com',
    subject='Nuevo resultado de laboratorio',
    template='lab_result_available',
    context={
        'patient_name': 'Juan Pérez',
        'document_url': 'https://...'
    }
)
```

### Celery + Redis (Tareas Asíncronas)

**Configuración:**

```python
# celery.py
CELERY_BROKER_URL = env('CELERY_BROKER_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND', default='redis://localhost:6379/0')
```

**Tareas disponibles:**

```python
# Backup automático
@shared_task
def create_automatic_backup():
    # ...

# OCR de documentos
@shared_task
def process_document_ocr(document_id):
    # ...

# Envío de emails
@shared_task
def send_email_async(to, subject, template, context):
    # ...
```

**Ejecutar Celery:**

```bash
# Worker
celery -A config worker -l info

# Beat (tareas programadas)
celery -A config beat -l info
```

---

## 📊 Mejores Prácticas

### Paginación

Todas las listas están paginadas por defecto:

```python
# Request
GET /api/patients/?page=2&page_size=50

# Response
{
  "count": 250,
  "next": "http://api.../patients/?page=3",
  "previous": "http://api.../patients/?page=1",
  "results": [...]
}
```

### Filtrado

```python
# Por campo exacto
GET /api/patients/?gender=M

# Por campo parcial (icontains)
GET /api/patients/?search=juan

# Por fecha
GET /api/documents/?document_date__gte=2025-01-01

# Múltiples filtros
GET /api/patients/?gender=M&city=La Paz
```

### Ordenamiento

```python
# Ascendente
GET /api/patients/?ordering=first_name

# Descendente
GET /api/patients/?ordering=-created_at

# Múltiples campos
GET /api/patients/?ordering=last_name,first_name
```

### Manejo de Errores

```json
// Error 400 - Validación
{
  "error": "validation_error",
  "details": {
    "email": ["Este campo es requerido"],
    "phone": ["Formato inválido"]
  }
}

// Error 401 - No autenticado
{
  "detail": "Authentication credentials were not provided."
}

// Error 403 - Sin permisos
{
  "detail": "No tienes permisos para esta acción"
}

// Error 404 - No encontrado
{
  "detail": "Not found."
}

// Error 500 - Error del servidor
{
  "error": "internal_server_error",
  "message": "Ha ocurrido un error inesperado"
}
```

---

## 🚀 Comandos Útiles

### Gestión de Base de Datos

```bash
# Crear migraciones
python manage.py makemigrations

# Aplicar migraciones
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser

# Ejecutar seeder completo
python scripts/seed_data.py

# Reset completo de base de datos
python manage.py reset_db --noinput
python manage.py migrate
python scripts/seed_data.py
```

### Servidor de Desarrollo

```bash
# Iniciar servidor
python manage.py runserver

# Iniciar en puerto específico
python manage.py runserver 8080

# Accesible desde red local
python manage.py runserver 0.0.0.0:8000
```

### Celery

```bash
# Worker
celery -A config worker -l info

# Beat (scheduler)
celery -A config beat -l info

# Flower (monitoring)
celery -A config flower
```

### Tests

```bash
# Ejecutar todos los tests
python manage.py test

# Tests de una app específica
python manage.py test apps.patients

# Con cobertura
coverage run --source='.' manage.py test
coverage report
coverage html
```

### Shell Django

```bash
# Shell interactivo
python manage.py shell

# Ejemplos útiles
>>> from apps.core.models import set_current_tenant, Tenant
>>> tenant = Tenant.objects.first()
>>> set_current_tenant(tenant)
>>> from apps.patients.models import Patient
>>> Patient.objects.all()  # Solo del tenant actual
```

---

## 📖 Recursos Adicionales

- **API Documentation (Swagger):** http://localhost:8000/api/docs/
- **API Documentation (Redoc):** http://localhost:8000/api/redoc/
- **Django Admin:** http://localhost:8000/admin/
- **Development Guide:** [DEVELOPMENT_GUIDE.md](./DEVELOPMENT_GUIDE.md)
- **Deployment Guide:** [deployment/DEPLOY_GUIDE.md](./deployment/DEPLOY_GUIDE.md)

---

**¿Preguntas? ¿Sugerencias?**  
Contacta al equipo de desarrollo o abre un issue en el repositorio.
