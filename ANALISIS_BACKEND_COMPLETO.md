# 🏥 Backend CliniDocs - Análisis Completo

## 📋 Descripción General

**CliniDocs Backend** es un sistema SaaS (Software as a Service) de gestión de historias clínicas y documentos médicos construido con **Django 4.2** y **Django REST Framework**. Implementa una arquitectura multi-tenant robusta que permite que múltiples hospitales/clínicas usen la plataforma con datos completamente aislados.

**Stack Tecnológico:**
- **Framework:** Django 4.2.7
- **API:** Django REST Framework 3.14.0
- **Base de Datos:** PostgreSQL 14+
- **Task Queue:** Celery 5.3.4 + Redis
- **Autenticación:** JWT (djangorestframework-simplejwt)
- **Documentación API:** Swagger/ReDoc (drf-spectacular)
- **Almacenamiento de Archivos:** AWS S3 (django-storages)
- **Procesamiento de OCR:** AWS Textract
- **Pagos:** Stripe (django-stripe-integration)

---

## 🏗️ Arquitectura Multi-Tenant

### Concepto Central

Cada **hospital/clínica** es un **Tenant** independiente:
- 🔒 Datos completamente aislados
- 👥 Múltiples usuarios por tenant
- 🛠️ Configuración personalizada por tenant
- 📊 Estadísticas y reportes independientes

### Modelo TenantAwareModel

Todos los modelos principales heredan de `TenantAwareModel`:

```python
class TenantAwareModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    tenant = models.ForeignKey(Tenant)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True)  # Soft delete
    
    objects = TenantManager()  # Filtra automáticamente por tenant
    
    class Meta:
        abstract = True
```

**Características:**
- ✅ Identificador único UUID
- ✅ Aislamiento de datos por tenant
- ✅ Soft delete (no elimina, marca como eliminado)
- ✅ Timestamps automáticos
- ✅ Manager personalizado que filtra por tenant

---

## 📁 Estructura de Carpetas

```
cr_backend/
├── config/                          ← Configuración central
│   ├── settings/
│   │   ├── base.py                  ← Configuración base
│   │   ├── development.py           ← Desarrollo local
│   │   ├── production.py            ← Producción
│   │   ├── production_aws.py        ← AWS específico
│   │   ├── staging.py               ← Staging
│   │   └── logging.py               ← Configuración de logs
│   ├── urls.py                      ← Enrutamiento principal
│   ├── wsgi.py                      ← WSGI para Gunicorn
│   ├── asgi.py                      ← ASGI para async
│   └── celery.py                    ← Configuración de Celery
│
├── apps/                            ← Aplicaciones Django
│   ├── accounts/                    ← Autenticación y usuarios
│   │   ├── models.py                ← User, Role, Permission
│   │   ├── serializers.py           ← Serializadores
│   │   ├── views.py                 ← Endpoints de auth
│   │   ├── signals.py               ← Signals de Django
│   │   └── urls.py                  ← Rutas
│   │
│   ├── tenants/                     ← Gestión de tenants
│   │   ├── models.py                ← Tenant, Subscription
│   │   ├── serializers.py
│   │   ├── views.py
│   │   └── urls.py
│   │
│   ├── patients/                    ← Gestión de pacientes
│   │   ├── models.py                ← Patient
│   │   ├── serializers.py
│   │   ├── views.py                 ← PatientViewSet
│   │   ├── filters.py               ← Filtros avanzados
│   │   └── urls.py
│   │
│   ├── clinical_records/            ← Historias clínicas
│   │   ├── models.py                ← ClinicalRecord, ClinicalForm
│   │   ├── serializers.py
│   │   ├── views.py                 ← ClinicalRecordViewSet
│   │   └── urls.py
│   │
│   ├── documents/                   ← Documentos médicos
│   │   ├── models.py                ← ClinicalDocument, MedicalImage
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── services.py              ← Lógica de documentos
│   │   └── urls.py
│   │
│   ├── audit/                       ← Auditoría y logs
│   │   ├── models.py                ← AuditLog
│   │   ├── middleware.py            ← Middleware de auditoría
│   │   └── views.py
│   │
│   ├── reports/                     ← Reportes y analytics
│   │   ├── models.py
│   │   ├── views.py                 ← Endpoints de reportes
│   │   ├── dashboard_views.py       ← Dashboard
│   │   └── services.py
│   │
│   ├── backup/                      ← Sistema de backups
│   │   ├── models.py
│   │   ├── services.py              ← Lógica de backup
│   │   └── views.py
│   │
│   ├── notifications/               ← Notificaciones
│   │   ├── models.py
│   │   ├── services.py
│   │   └── views.py
│   │
│   ├── payments/                    ← Pagos con Stripe
│   │   ├── models.py                ← Invoice, Payment
│   │   ├── services.py              ← Integración Stripe
│   │   └── views.py
│   │
│   ├── seed/                        ← Datos de prueba
│   │   └── views.py
│   │
│   └── core/                        ← Utilidades compartidas
│       ├── models.py                ← TenantAwareModel, TenantManager
│       ├── middleware.py            ← TenantMiddleware
│       ├── permissions.py           ← Permisos personalizados
│       ├── pagination.py            ← Paginación
│       ├── views/
│       │   └── health.py            ← Health checks
│       └── management/
│           └── commands/            ← Comandos personalizados
│
├── docs/                            ← Documentación técnica
├── scripts/                         ← Scripts de desarrollo
├── media/                           ← Archivos subidos
├── static/                          ← Archivos estáticos
├── requirements.txt                 ← Dependencias Python
├── manage.py                        ← Gestión de Django
└── README.md
```

---

## 📦 Apps Principales y Funcionalidad

### 1. **ACCOUNTS (Autenticación y Usuarios)**

**Ubicación:** `apps/accounts/`

**Responsabilidad:** Gestión de usuarios, autenticación JWT y control de acceso

**Modelos:**

```python
class User(AbstractUser, TenantAwareModel):
    # Campos personalizados
    employee_id = CharField()           # ID de empleado
    department = CharField()             # Departamento
    specialization = CharField()         # Especialidad médica
    is_active = BooleanField()           # Usuario activo
    is_verified = BooleanField()         # Email verificado
    
    # Relaciones
    role = ForeignKey('Role')            # Rol del usuario
    
class Role(TenantAwareModel):
    name = CharField()                   # 'Doctor', 'Admin', 'Secretary'
    permissions = ManyToManyField('Permission')
    
class Permission(TenantAwareModel):
    name = CharField()                   # 'can_create_patient'
    codename = CharField(unique=True)
```

**Endpoints:**

```
POST   /api/auth/login/                 # Login con email/password
POST   /api/auth/refresh/               # Renovar token JWT
POST   /api/auth/logout/                # Logout
POST   /api/auth/register/              # Registro (público)
GET    /api/users/me/                   # Perfil actual
POST   /api/users/                      # Crear usuario (admin)
GET    /api/users/                      # Listar usuarios
GET    /api/roles/                      # Listar roles
```

**Características:**
- ✅ JWT con refresh tokens
- ✅ Autenticación multi-tenant
- ✅ Control de acceso basado en roles (RBAC)
- ✅ Permisos granulares
- ✅ Verificación de email

---

### 2. **TENANTS (Gestión de Tenants/Suscripciones)**

**Ubicación:** `apps/tenants/`

**Responsabilidad:** Crear y gestionar tenants, planes de suscripción

**Modelos:**

```python
class Tenant(models.Model):
    id = UUIDField(primary_key=True)
    name = CharField()                   # "Hospital San Juan"
    domain = CharField(unique=True)      # "hospital-san-juan"
    logo = ImageField()
    
    # Suscripción
    subscription_plan = ForeignKey('SubscriptionPlan')
    subscription_start = DateField()
    subscription_end = DateField()
    is_active = BooleanField()
    
class SubscriptionPlan(models.Model):
    PLANS = [
        ('basic', 'Básico'),
        ('pro', 'Profesional'),
        ('enterprise', 'Empresarial')
    ]
    
    plan_type = CharField(choices=PLANS)
    price = DecimalField()
    max_users = IntegerField()
    max_patients = IntegerField()
    storage_gb = IntegerField()
    features = JSONField()               # Características por plan
```

**Endpoints:**

```
POST   /api/tenants/public/              # Crear tenant público
GET    /api/tenants/                     # Ver detalles del tenant
PATCH  /api/tenants/                     # Actualizar tenant
GET    /api/subscriptions/               # Ver suscripción actual
```

---

### 3. **PATIENTS (Gestión de Pacientes)**

**Ubicación:** `apps/patients/`

**Responsabilidad:** CRUD de pacientes, búsqueda avanzada, estadísticas

**Modelo:**

```python
class Patient(TenantAwareModel):
    # Identificación
    identity_document_type = CharField()  # 'CI', 'DNI', 'Pasaporte'
    identity_document = CharField()       # Número de documento
    
    # Información personal
    first_name = CharField()
    last_name = CharField()
    date_of_birth = DateField()
    gender = CharField()                  # 'M', 'F', 'O'
    
    # Contacto
    phone = CharField()
    email = EmailField()
    address = TextField()
    city = CharField()
    
    # Emergencia
    emergency_contact = JSONField()       # {"name": "...", "phone": "..."}
    
    # Metadata
    created_by = ForeignKey(User)
```

**Endpoints:**

```
GET    /api/patients/                    # Listar (con paginación)
POST   /api/patients/                    # Crear paciente
GET    /api/patients/{id}/               # Ver detalle
PATCH  /api/patients/{id}/               # Actualizar
DELETE /api/patients/{id}/               # Eliminar (soft delete)
GET    /api/patients/search/             # Búsqueda avanzada
GET    /api/patients/stats/              # Estadísticas
GET    /api/patients/{id}/clinical-records/  # Historias del paciente
```

**Filtros Disponibles:**
- Búsqueda por nombre, documento, email
- Filtro por género, rango de edad
- Ordenamiento por fecha de creación, nombre
- Paginación configurable

---

### 4. **CLINICAL_RECORDS (Historias Clínicas)**

**Ubicación:** `apps/clinical_records/`

**Responsabilidad:** CRUD de historias clínicas y formularios clínicos

**Modelos:**

```python
class ClinicalRecord(TenantAwareModel):
    """Historia Clínica única por paciente"""
    patient = OneToOneField(Patient)
    record_number = CharField(unique=True)  # HC-2025-000001 (auto)
    
    # Estado
    STATUS = [('active', 'Activa'), ('archived', 'Archivada'), ('closed', 'Cerrada')]
    status = CharField(choices=STATUS, default='active')
    
    # Información clínica
    blood_type = CharField()               # A+, B-, O+, etc.
    allergies = JSONField()                # [{"allergen": "Penicilina", ...}]
    chronic_conditions = JSONField()       # ["Diabetes", "Hipertensión"]
    medications = JSONField()              # [{"name": "...", "dose": "...", ...}]
    family_history = TextField()
    social_history = TextField()
    
    created_by = ForeignKey(User)


class ClinicalForm(TenantAwareModel):
    """Formularios asociados a una historia clínica"""
    clinical_record = ForeignKey(ClinicalRecord)
    
    # Tipo de formulario
    FORM_TYPES = [
        ('triage', 'Triaje'),
        ('consultation', 'Consulta Médica'),
        ('evolution', 'Nota de Evolución'),
        ('prescription', 'Receta Médica'),
        ('lab_order', 'Orden de Laboratorio'),
        ('imaging_order', 'Orden de Imagenología'),
        ('procedure', 'Procedimiento'),
        ('discharge', 'Alta Médica'),
        ('referral', 'Referencia'),
    ]
    form_type = CharField(choices=FORM_TYPES)
    
    # Contenido flexible (JSON)
    form_data = JSONField()                 # Datos del formulario
    doctor_name = CharField()
    form_date = DateTimeField()
    filled_by = ForeignKey(User)
```

**Endpoints:**

```
GET    /api/clinical-records/            # Listar historias
POST   /api/clinical-records/            # Crear historia
GET    /api/clinical-records/{id}/       # Ver detalle
PATCH  /api/clinical-records/{id}/       # Actualizar
DELETE /api/clinical-records/{id}/       # Eliminar

# Formularios
GET    /api/clinical-records/forms/      # Listar formularios
POST   /api/clinical-records/forms/      # Crear formulario
GET    /api/clinical-records/forms/{id}/ # Ver formulario
PATCH  /api/clinical-records/forms/{id}/ # Actualizar
DELETE /api/clinical-records/forms/{id}/ # Eliminar
```

---

### 5. **DOCUMENTS (Documentos Médicos)**

**Ubicación:** `apps/documents/`

**Responsabilidad:** Gestión de documentos clínicos, OCR, almacenamiento en S3

**Modelos:**

```python
class ClinicalDocument(TenantAwareModel):
    """Documento clínico - NÚCLEO del sistema"""
    clinical_record = ForeignKey(ClinicalRecord)
    
    # Clasificación
    TYPES = [
        ('consultation', 'Consulta'),
        ('lab_result', 'Resultado Lab'),
        ('imaging_report', 'Informe Imagen'),
        ('prescription', 'Receta'),
        ('surgical_note', 'Nota Quirúrgica'),
        ('discharge_summary', 'Resumen Alta'),
    ]
    document_type = CharField(choices=TYPES)
    
    title = CharField()
    description = TextField()
    document_date = DateTimeField()
    specialty = CharField()
    
    # Información del médico
    doctor_name = CharField()
    doctor_license = CharField()
    
    # Contenido
    content = JSONField()                  # Datos estructurados
    
    # Archivo
    file_path = CharField()                # Ruta en S3
    file_name = CharField()
    file_size_bytes = BigIntegerField()
    mime_type = CharField()
    file_hash = CharField()                # SHA-256
    
    # OCR (AWS Textract)
    ocr_text = TextField()                 # Texto extraído
    ocr_confidence = DecimalField()        # 0-100
    ocr_processed = BooleanField()
    ocr_job_id = CharField()
    
    # Firma digital
    is_signed = BooleanField()
    signed_at = DateTimeField()
    signed_by = ForeignKey(User)
    signature_hash = CharField()


class MedicalImage(TenantAwareModel):
    """Imágenes DICOM para radiología"""
    clinical_document = ForeignKey(ClinicalDocument)
    
    modality = CharField()                 # CT, MRI, X-RAY
    dicom_file_path = CharField()
    thumbnail_path = CharField()
    series_description = CharField()
```

**Endpoints:**

```
GET    /api/documents/                   # Listar documentos
POST   /api/documents/                   # Subir documento
GET    /api/documents/{id}/              # Descargar documento
PATCH  /api/documents/{id}/              # Actualizar metadata
DELETE /api/documents/{id}/              # Eliminar

GET    /api/documents/{id}/download/     # Descargar archivo
GET    /api/documents/{id}/sign/         # Firmar digitalmente
GET    /api/documents/search/            # Buscar documentos
```

**Features:**
- ✅ Almacenamiento en AWS S3
- ✅ OCR con AWS Textract (extrae texto de PDFs/imágenes)
- ✅ Firma digital
- ✅ Tracking de acceso
- ✅ Validación de integridad (hash SHA-256)
- ✅ Compresión y optimización

---

### 6. **AUDIT (Auditoría y Logs)**

**Ubicación:** `apps/audit/`

**Responsabilidad:** Registro de todas las acciones del sistema

**Modelo:**

```python
class AuditLog(models.Model):
    user = ForeignKey(User)
    tenant = ForeignKey(Tenant)
    
    # Acción
    action = CharField()                   # 'CREATE', 'UPDATE', 'DELETE', 'VIEW'
    content_type = CharField()             # Tipo de objeto modificado
    object_id = UUIDField()                # ID del objeto
    
    # Detalles
    description = TextField()
    changes = JSONField()                  # {"before": {...}, "after": {...}}
    ip_address = GenericIPAddressField()
    user_agent = CharField()
    
    timestamp = DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['tenant', 'timestamp']),
            models.Index(fields=['user', 'action']),
        ]
```

**Endpoints:**

```
GET    /api/audit/logs/                  # Ver logs de auditoría
GET    /api/audit/logs/{id}/             # Ver detalle de log
GET    /api/audit/activity/              # Actividad del usuario
GET    /api/audit/changes/{object_id}/   # Historial de cambios
```

---

### 7. **REPORTS (Reportes y Analytics)**

**Ubicación:** `apps/reports/`

**Responsabilidad:** Reportes, estadísticas, dashboards

**Endpoints:**

```
GET    /api/reports/dashboard/           # Dashboard general
GET    /api/reports/statistics/          # Estadísticas por período
GET    /api/reports/patients/stats/      # Estadísticas de pacientes
GET    /api/reports/documents/stats/     # Estadísticas de documentos
GET    /api/reports/export/              # Exportar datos (CSV, Excel)
GET    /api/reports/qbe/                 # Query By Example (consultas dinámicas)
```

---

### 8. **BACKUP (Sistema de Backups)**

**Ubicación:** `apps/backup/`

**Responsabilidad:** Backups automáticos y manuales, recuperación

**Endpoints:**

```
GET    /api/backup/status/               # Estado del último backup
POST   /api/backup/create/               # Crear backup manual
GET    /api/backup/list/                 # Listar backups
POST   /api/backup/restore/              # Restaurar desde backup
DELETE /api/backup/{id}/                 # Eliminar backup
```

---

### 9. **NOTIFICATIONS (Notificaciones)**

**Ubicación:** `apps/notifications/`

**Responsabilidad:** Notificaciones por email, SMS, push

**Endpoints:**

```
GET    /api/notifications/               # Listar notificaciones
POST   /api/notifications/read/          # Marcar como leído
POST   /api/notifications/settings/      # Configurar preferencias
```

---

### 10. **PAYMENTS (Pagos con Stripe)**

**Ubicación:** `apps/payments/`

**Responsabilidad:** Facturación, pagos, integración Stripe

**Modelos:**

```python
class Invoice(TenantAwareModel):
    tenant = ForeignKey(Tenant)
    invoice_number = CharField(unique=True)
    
    amount = DecimalField()
    currency = CharField()
    
    STATUS = [('draft', 'Borrador'), ('pending', 'Pendiente'), ('paid', 'Pagado')]
    status = CharField(choices=STATUS)
    
    issue_date = DateField()
    due_date = DateField()
    paid_at = DateTimeField()


class Payment(TenantAwareModel):
    invoice = ForeignKey(Invoice)
    stripe_payment_id = CharField()
    
    amount = DecimalField()
    method = CharField()                  # 'card', 'bank_transfer'
    status = CharField()                  # 'pending', 'completed', 'failed'
    
    timestamp = DateTimeField(auto_now_add=True)
```

---

## 🔐 Autenticación y Autorización

### JWT (JSON Web Tokens)

```python
# Login
POST /api/auth/login/
{
  "email": "doctor@hospital.com",
  "password": "secure_password"
}

# Response
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}

# Usar token en requests
Authorization: Bearer <access_token>

# Renovar token
POST /api/auth/refresh/
{
  "refresh": "<refresh_token>"
}
```

### Permisos por Rol

```python
# Roles disponibles
- SuperAdmin      → Acceso total
- TenantAdmin     → Admin del tenant
- Doctor          → Crear/ver historias clínicas
- Secretary       → Gestión de pacientes
- Viewer          → Solo lectura
```

### Middleware de Tenant

Cada request:
1. ✅ Extrae tenant del header o subdomain
2. ✅ Valida que el usuario pertenece al tenant
3. ✅ Filtra todas las queries por tenant automáticamente

---

## 🗄️ Base de Datos

### Diagrama de Relaciones (Simplificado)

```
Tenant (hospital/clínica)
  ├── User (usuarios del hospital)
  ├── SubscriptionPlan (plan contratado)
  ├── Patient (pacientes)
  │   └── ClinicalRecord (1:1 - una historia por paciente)
  │       ├── ClinicalForm (1:N - formularios)
  │       └── ClinicalDocument (1:N - documentos)
  │           └── MedicalImage (radiología)
  ├── Invoice (facturación)
  ├── Payment (pagos)
  ├── AuditLog (auditoría)
  └── Notification (notificaciones)
```

### Índices de Base de Datos

```python
# Para optimizar queries
Index: (tenant, patient_id)
Index: (tenant, created_at)
Index: (record_number)
Index: (status)
Index: (document_type)
Index: (user_id, timestamp)
```

---

## 📡 API Endpoints (Resumen)

| Módulo | Método | Endpoint | Descripción |
|--------|--------|----------|-------------|
| **Auth** | POST | `/api/auth/login/` | Autenticación |
| | POST | `/api/auth/refresh/` | Renovar token |
| **Users** | GET | `/api/users/me/` | Perfil actual |
| | POST | `/api/users/` | Crear usuario |
| **Patients** | GET | `/api/patients/` | Listar pacientes |
| | POST | `/api/patients/` | Crear paciente |
| **Clinical Records** | GET | `/api/clinical-records/` | Listar historias |
| | POST | `/api/clinical-records/` | Crear historia |
| **Documents** | POST | `/api/documents/` | Subir documento |
| | GET | `/api/documents/{id}/download/` | Descargar |
| **Audit** | GET | `/api/audit/logs/` | Ver logs |
| **Reports** | GET | `/api/reports/dashboard/` | Dashboard |
| **Backup** | POST | `/api/backup/create/` | Crear backup |

---

## 🔄 Celery - Task Queue

**Responsabilidad:** Procesar tareas asincrónicas

```python
# Tasks implementadas

# OCR (extrae texto de documentos)
@celery_app.task
def process_document_ocr(document_id):
    # Envía documento a AWS Textract
    # Almacena resultado en BD

# Email
@celery_app.task
def send_notification_email(user_id, subject, body):
    # Envía email asincronamente

# Backup
@celery_app.task
def create_backup_task(tenant_id):
    # Crea backup del tenant
    # Almacena en S3

# Reportes
@celery_app.task
def generate_report(tenant_id, report_type):
    # Genera reporte PDF
    # Envía por email
```

**Comando para ejecutar:**

```bash
# Worker
celery -A config worker -l info

# Beat (scheduler)
celery -A config beat -l info

# Flower (monitoring)
celery -A config flower
```

---

## 📊 Configuración por Entorno

### development.py
```python
DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1']
DATABASES = {'default': sqlite3}  # o PostgreSQL local
EMAIL_BACKEND = 'console'         # Imprime emails en terminal
```

### production.py
```python
DEBUG = False
ALLOWED_HOSTS = ['api.clinidocs.com']
DATABASES = {'default': PostgreSQL}
EMAIL_BACKEND = 'SendGrid'
SECURE_SSL_REDIRECT = True
```

### production_aws.py
```python
# Configuración AWS
AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID')
AWS_S3_REGION_NAME = 'us-east-1'
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
```

---

## 🚀 Deployment

### Con Gunicorn

```bash
gunicorn -c gunicorn_config.py config.wsgi:application
```

### Docker (si existe Dockerfile)

```bash
docker build -t clinidocs-backend .
docker run -p 8000:8000 clinidocs-backend
```

### AWS ECS / Lambda

- Configuración en `production_aws.py`
- ALB con health checks en `/api/health/`
- Auto-scaling basado en CPU/memoria

---

## 📈 Características Implementadas

- ✅ Multi-tenant con aislamiento de datos
- ✅ JWT authentication
- ✅ CRUD de pacientes
- ✅ CRUD de historias clínicas
- ✅ Gestión de documentos médicos
- ✅ OCR con AWS Textract
- ✅ Firma digital
- ✅ Auditoría completa
- ✅ Pagos con Stripe
- ✅ Backups automáticos
- ✅ Reportes y dashboards
- ✅ Notificaciones
- ✅ Rol-based access control (RBAC)
- ✅ Swagger/ReDoc documentation

---

## 🔧 Dependencias Principales

| Paquete | Versión | Propósito |
|---------|---------|----------|
| **Django** | 4.2.7 | Framework web |
| **DRF** | 3.14.0 | API REST |
| **djangorestframework-simplejwt** | 5.3.0 | JWT auth |
| **Celery** | 5.3.4 | Task queue |
| **psycopg2** | - | Driver PostgreSQL |
| **boto3** | 1.34.0 | AWS SDK |
| **stripe** | - | Pagos |
| **pillow** | - | Procesamiento de imágenes |
| **python-dotenv** | - | Variables de entorno |
| **drf-spectacular** | 0.26.5 | Swagger/ReDoc |

---

## 📝 Variables de Entorno Requeridas

```bash
# Django
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=api.clinidocs.com

# Database PostgreSQL
DATABASE_NAME=clinic_records_db
DATABASE_USER=clinic_admin
DATABASE_PASSWORD=secure_password
DATABASE_HOST=localhost
DATABASE_PORT=5432

# Redis
REDIS_URL=redis://localhost:6379/0

# AWS
AWS_ACCESS_KEY_ID=xxxxx
AWS_SECRET_ACCESS_KEY=xxxxx
AWS_S3_BUCKET_NAME=clinic-documents
AWS_REGION=us-east-1

# Stripe
STRIPE_SECRET_KEY=sk_live_xxxxx
STRIPE_PUBLIC_KEY=pk_live_xxxxx

# Email
EMAIL_BACKEND=SendGrid
SENDGRID_API_KEY=SG.xxxxx

# JWT
JWT_ALGORITHM=HS256
JWT_EXPIRATION_DELTA=3600
```

---

## 🧪 Testing

```bash
# Ejecutar todos los tests
python manage.py test

# Tests específicos
python manage.py test apps.patients.tests

# Con cobertura
coverage run --source='.' manage.py test
coverage report
```

---

## 📞 Health Checks

### Endpoints de Monitoreo

```
GET /api/health/       # Verificación básica
GET /api/readiness/    # Está listo para recibir tráfico
GET /api/liveness/     # Está vivo
```

**Respuesta:**
```json
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected",
  "version": "1.0.0"
}
```

---

## 🎯 Próximos Pasos

1. ✅ Completar integración Stripe
2. ⏳ Agregar autenticación 2FA
3. ⏳ Implementar WebSockets para notificaciones real-time
4. ⏳ Agregar más tipos de documentos DICOM
5. ⏳ Optimizar OCR con ML
6. ⏳ GraphQL API (alternativa REST)
7. ⏳ Mobile app sync mejorado

---

## 📞 Contacto & Soporte

**Proyecto:** CliniDocs Backend  
**Versión:** 1.0.0  
**Stack:** Django 4.2 + DRF + PostgreSQL  
**Estado:** ✅ En Producción

---

*Documento de análisis generado automáticamente. Última actualización: 16 de noviembre de 2025*
