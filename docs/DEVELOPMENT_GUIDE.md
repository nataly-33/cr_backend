# 🛠️ Guía de Desarrollo - Backend (ClinicRecords)# 📚 BACKEND DEVELOPMENT GUIDE - CliniDocs

**Versión:** 1.0 ## 📋 Tabla de Contenidos

**Fecha:** 5 de Noviembre, 2025

**Autor:** Equipo ClinicRecords1. [Introducción](#introducción)

2. [Arquitectura del Backend](#arquitectura-del-backend)

---3. [Estructura del Proyecto](#estructura-del-proyecto)

4. [Multi-Tenancy](#multi-tenancy)

## 📋 Tabla de Contenidos5. [Sistema RBAC de Permisos](#sistema-rbac-de-permisos)

6. [Modelos y Base de Datos](#modelos-y-base-de-datos)

1. [Introducción](#introducción)7. [Serializers y Validaciones](#serializers-y-validaciones)

1. [Configuración del Entorno](#configuración-del-entorno)8. [Views y ViewSets](#views-y-viewsets)

1. [Estructura del Proyecto](#estructura-del-proyecto)9. [URLs y Routing](#urls-y-routing)

1. [Arquitectura Multi-tenant](#arquitectura-multi-tenant)10. [Servicios y Lógica de Negocio](#servicios-y-lógica-de-negocio)

1. [Sistema RBAC](#sistema-rbac)11. [Signals](#signals)

1. [Crear un Nuevo Módulo](#crear-un-nuevo-módulo)12. [Testing](#testing)

1. [Trabajar con Modelos](#trabajar-con-modelos)13. [Celery y Tareas Asíncronas](#celery-y-tareas-asíncronas)

1. [Crear Endpoints (ViewSets)](#crear-endpoints-viewsets)14. [APIs y Documentación](#apis-y-documentación)

1. [Serializers](#serializers)15. [Crear un Nuevo Módulo](#crear-un-nuevo-módulo)

1. [Permisos Personalizados](#permisos-personalizados)16. [Best Practices](#best-practices)

1. [Celery y Tareas Asíncronas](#celery-y-tareas-asíncronas)17. [Comandos Útiles](#comandos-útiles)

1. [Testing](#testing)

1. [Migraciones](#migraciones)---

1. [Mejores Prácticas](#mejores-prácticas)

1. [Debugging](#debugging)## 🎯 Introducción

1. [Comandos Útiles](#comandos-útiles)

Este documento es la guía completa y **ACTUALIZADA** para desarrollar el backend de CliniDocs. Refleja la estructura y arquitectura **REAL** del proyecto implementado.

---

### Principios Fundamentales

## 🎯 Introducción

1. **Multi-tenancy First**: Todo debe estar aislado por tenant

Esta guía está diseñada para desarrolladores que necesitan:2. **RBAC (Role-Based Access Control)**: Control granular de permisos por roles

- Agregar nuevos módulos al sistema3. **Seguridad por Defecto**: Validar siempre la propiedad de los recursos

- Modificar funcionalidades existentes4. **DRY (Don't Repeat Yourself)**: Reutilizar código común

- Entender la arquitectura multi-tenant5. **Testing**: Cada funcionalidad debe tener tests

- Implementar nuevos endpoints y modelos6. **Documentación**: APIs autodocumentadas con Swagger

- Seguir las mejores prácticas del proyecto

---

**Requisitos previos:**

- Python 3.11+## 🏗️ Arquitectura del Backend

- PostgreSQL 15+

- Redis### Stack Tecnológico

- Conocimientos de Django y Django REST Framework

````

---Django 4.2

├── Django REST Framework 3.14  (APIs)

## ⚙️ Configuración del Entorno├── PostgreSQL 14+              (Base de datos)

├── Redis                       (Cache + Celery - Pendiente)

### 1. Clonar el Repositorio├── Celery 5.3                  (Tareas asíncronas - Pendiente)

├── JWT                         (Autenticación)

```bash└── AWS S3                      (Storage)

git clone <repository-url>```

cd clinic_records/cr_backend

```### Flujo de Request



### 2. Crear Entorno Virtual```

Client Request

```bash    ↓

python -m venv venvNGINX (Reverse Proxy)

    ↓

# WindowsDjango WSGI (Gunicorn)

venv\Scripts\activate    ↓

Middleware Stack

# Linux/Mac    ├── SecurityMiddleware

source venv/bin/activate    ├── SessionMiddleware

```    ├── AuthenticationMiddleware

    ├── TenantMiddleware ← CRÍTICO

### 3. Instalar Dependencias    └── AuditMiddleware

    ↓

```bashURL Router

pip install -r requirements.txt    ↓

```View/ViewSet

    ├── IsTenantMember Check

### 4. Configurar Variables de Entorno    ├── RBAC Permissions Check

    ├── Tenant Validation

Copia `.env.example` a `.env` y configura:    └── Business Logic

    ↓

```envSerializer

# Database    ├── Validation

DATABASE_NAME=clinic_records    └── Data Transform

DATABASE_USER=postgres    ↓

DATABASE_PASSWORD=tu_passwordModel/ORM

DATABASE_HOST=localhost    ├── QuerySet (filtered by tenant)

DATABASE_PORT=5432    └── Database

    ↓

# DjangoResponse

SECRET_KEY=tu_secret_key_segura```

DEBUG=True

ALLOWED_HOSTS=localhost,127.0.0.1---



# AWS S3## 📁 Estructura del Proyecto

AWS_ACCESS_KEY_ID=tu_access_key

AWS_SECRET_ACCESS_KEY=tu_secret_key### Estructura Actual (REAL)

AWS_STORAGE_BUCKET_NAME=clinic-records-bucket

AWS_S3_REGION_NAME=us-east-1```

backend/

# Redis├── manage.py

REDIS_URL=redis://localhost:6379/0├── requirements.txt              # Un solo archivo de requirements

├── .env

# Celery├── .env.example

CELERY_BROKER_URL=redis://localhost:6379/0├── config/

CELERY_RESULT_BACKEND=redis://localhost:6379/0│   ├── settings/

│   │   ├── base.py

# Email (SendGrid)│   │   ├── development.py

SENDGRID_API_KEY=tu_sendgrid_key│   │   └── production.py

DEFAULT_FROM_EMAIL=noreply@clinicrecords.com│   ├── urls.py

```│   ├── wsgi.py

│   └── asgi.py

### 5. Crear Base de Datos└── apps/

    ├── core/               # Multi-tenancy base + permisos

```bash    │   ├── models.py      # Tenant, TenantAwareModel, get/set_current_tenant

# PostgreSQL    │   ├── middleware.py  # TenantMiddleware

createdb clinic_records    │   └── permissions.py # Sistema RBAC completo ← NUEVO

    ├── accounts/          # Usuarios, roles, permisos

# O con psql    ├── patients/          # Gestión de pacientes

psql -U postgres    ├── clinical_records/  # Historias clínicas

CREATE DATABASE clinic_records;    ├── documents/         # Documentos clínicos (services.py existe)

\q    ├── audit/             # Logs de auditoría

```    ├── reports/           # Sistema de reportes

    ├── backup/            # Sistema de backup (services.py existe)

### 6. Ejecutar Migraciones    └── tenants/           # Gestión de tenants

````

```bash

python manage.py migrate### Anatomía de una App (Estructura REAL)

```

````

### 7. Crear Superusuarioapps/my_app/

├── __init__.py

```bash├── apps.py              # Configuración de la app

python manage.py createsuperuser├── models.py            # Modelos de datos

```├── serializers.py       # Serializers DRF

├── views.py             # Views/ViewSets

### 8. Cargar Datos de Prueba├── urls.py              # URLs de la app

├── admin.py             # Admin de Django

```bash├── services.py          # ⚠️ Solo en: documents, backup

python scripts/seed_data.py├── filters.py           # ⚠️ Solo en: patients

```├── signals.py           # ⚠️ Solo en: accounts (básico)

├── tests/               # ⚠️ Solo en: audit, documents

### 9. Iniciar Servidor└── migrations/          # Migraciones de BD

````

```bash

python manage.py runserver**Nota importante**: No todas las apps tienen `services.py`, `filters.py` o `signals.py`. Solo agregar cuando sea necesario.

```

---

### 10. Iniciar Celery (opcional)

## 🏢 Multi-Tenancy

```bash

# Worker### Conceptos Clave

celery -A config worker -l info

El sistema usa **base de datos compartida** con aislamiento por `tenant_id`. Cada hospital/clínica es un tenant independiente.

# Beat (scheduler)

celery -A config beat -l info### TenantMiddleware

```

**Ubicación**: `apps/core/middleware.py`

---

El middleware determina el tenant actual en este orden:

## 📁 Estructura del Proyecto

````python

```# apps/core/middleware.py

cr_backend/

├── apps/                          # Aplicaciones Django1. Header X-Tenant-ID (UUID)

│   ├── accounts/                  # Usuarios, roles, autenticación   → Para APIs y servicios externos

│   │   ├── models.py              # User, Role, Permission

│   │   ├── serializers.py         # UserSerializer, RoleSerializer2. Subdomain

│   │   ├── views.py               # ViewSets y APIViews   → hospital1.clinidocs.com → tenant.subdomain = 'hospital1'

│   │   ├── urls.py                # Rutas del módulo

│   │   └── signals.py             # Señales de Django3. Usuario autenticado (session)

│   ├── audit/                     # Sistema de auditoría   → request.user.tenant_id

│   ├── backup/                    # Respaldos automáticos

│   ├── clinical_records/          # Historias clínicas4. JWT Token

│   ├── core/                      # Funcionalidad compartida   → Claims del token: { "tenant_id": "..." }

│   │   ├── models.py              # TenantAwareModel, Tenant```

│   │   ├── middleware.py          # TenantMiddleware

│   │   ├── permissions.py         # Sistema RBAC### Thread-Local Storage

│   │   └── managers.py            # TenantManager

│   ├── documents/                 # Documentos clínicos**Ubicación**: `apps/core/models.py` (NO en middleware)

│   ├── notifications/             # Notificaciones

│   ├── patients/                  # Pacientes```python

│   └── reports/                   # Reportesfrom apps/core.models import get_current_tenant, set_current_tenant

├── config/                        # Configuración Django

│   ├── settings/                  # Settings por entorno# Obtener tenant actual

│   │   ├── base.py                # Configuración basetenant = get_current_tenant()

│   │   ├── development.py         # Desarrollo

│   │   └── production.py          # Producción# Establecer tenant (solo en casos especiales como seeders)

│   ├── urls.py                    # URLs principalesset_current_tenant(tenant)

│   ├── celery.py                  # Configuración Celery```

│   ├── wsgi.py                    # WSGI

│   └── asgi.py                    # ASGI**Implementación**:

├── docs/                          # Documentación

│   ├── REVISION.md                # Estado del proyecto```python

│   ├── DOCUMENTATION_GUIDE.md     # Documentación técnica# apps/core/models.py

│   ├── DEVELOPMENT_GUIDE.md       # Esta guíaimport threading

│   ├── guides/                    # Guías específicas_thread_locals = threading.local()

│   ├── deployment/                # Deployment

│   └── advanced/                  # Temas avanzadosdef get_current_tenant():

├── media/                         # Archivos media    """Obtiene el tenant actual del contexto"""

│   ├── backups/                   # Respaldos locales    return getattr(_thread_locals, 'tenant', None)

│   └── reports/                   # Reportes generados

├── scripts/                       # Scripts utilitariosdef set_current_tenant(tenant):

│   ├── seed_data.py               # Seeder principal    """Establece el tenant actual en el contexto"""

│   └── reset_migrations.py        # Reset de migraciones    _thread_locals.tenant = tenant

├── manage.py                      # Comando Django```

├── requirements.txt               # Dependencias

└── .env                           # Variables de entorno### TenantAwareModel

````

**Base abstracta para modelos tenant-aware:**

---

```````python

## 🏢 Arquitectura Multi-tenantfrom apps.core.models import TenantAwareModel



### Conceptoclass Patient(TenantAwareModel):

    # NO agregar tenant manualmente, ya viene de TenantAwareModel

Cada cliente (hospital, clínica) tiene su propio **Tenant**. Los datos están aislados por `tenant_id`.    first_name = models.CharField(max_length=100)

    last_name = models.CharField(max_length=100)

### Componentes Clave

    # TenantAwareModel ya incluye:

#### 1. Modelo Tenant    # - id (UUID)

    # - tenant (ForeignKey)

```python    # - created_at

# apps/core/models.py    # - updated_at

class Tenant(models.Model):    # - deleted_at (soft delete)

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)

    name = models.CharField(max_length=255)    objects = TenantManager()  # Manager que filtra por tenant

    subdomain = models.CharField(max_length=100, unique=True)```

    domain = models.CharField(max_length=255, blank=True)

    is_active = models.BooleanField(default=True)### TenantManager

    created_at = models.DateTimeField(auto_now_add=True)

``````python

from apps.core.models import TenantManager

#### 2. TenantAwareModel (Modelo Base)

class MyModel(TenantAwareModel):

**TODOS los modelos deben heredar de TenantAwareModel:**    # ...

    objects = TenantManager()  # Filtra automáticamente por tenant

```python    all_objects = models.Manager()  # Sin filtro (para admin)

from apps.core.models import TenantAwareModel```



class Patient(TenantAwareModel):**Uso:**

    first_name = models.CharField(max_length=100)

    last_name = models.CharField(max_length=100)```python

    # ... otros campos# Automáticamente filtrado por tenant actual

    patients = Patient.objects.all()

    objects = TenantManager()  # Manager personalizado

    # Ver incluyendo soft-deleted

    class Meta:all_with_deleted = Patient.objects.all_with_deleted()

        db_table = 'patients'```

        unique_together = [['tenant', 'document_number']]

```---



**¿Qué incluye TenantAwareModel?**## 🔒 Sistema RBAC de Permisos



```python### ⚡ NUEVO - Sistema Completo Implementado

class TenantAwareModel(models.Model):

    tenant = models.ForeignKey('core.Tenant', on_delete=models.CASCADE)**Ubicación**: `apps/core/permissions.py`

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)El sistema implementa **RBAC (Role-Based Access Control)** completo con permisos granulares.

    deleted_at = models.DateTimeField(null=True, blank=True)

    ### Roles del Sistema

    objects = TenantManager()

    1. **ASU (Admin Super Usuario)**:

    class Meta:

        abstract = True   - Superusuario global

```   - NO pertenece a ningún tenant

   - Puede ver TODOS los tenants

#### 3. TenantManager   - Email: `superadmin@clinidocs.com`



**Filtra automáticamente por tenant:**2. **Administrador TI**:



```python   - Gestión completa de SU tenant

# apps/core/managers.py   - CRUD de usuarios, roles, pacientes, historias, documentos

class TenantManager(models.Manager):   - Acceso a auditoría

    def get_queryset(self):   - Email: `admin@{tenant}.com`

        tenant = get_current_tenant()

        if tenant:3. **Doctor**:

            return super().get_queryset().filter(

                tenant=tenant,    - CRUD completo de historias clínicas

                deleted_at__isnull=True   - CRUD completo de documentos

            )   - Puede firmar documentos

        return super().get_queryset().filter(deleted_at__isnull=True)   - Lectura y actualización de pacientes

```````

4. **Paciente**:

**Uso:**

- Solo lectura de SU propia historia clínica

```python - No puede ver historias de otros pacientes

# Automáticamente filtra por tenant actual   - Validación en `has_object_permission`

patients = Patient.objects.all()  # Solo pacientes del tenant actual

### Códigos de Permisos

# Sin filtro de tenant (usar con cuidado)

all_patients = Patient.objects.using('default').all()**Ubicación**: `apps/core/permissions.py` → clase `PermissionCodes`

```

````python

#### 4. TenantMiddlewarefrom apps.core.permissions import PermissionCodes



**Detecta el tenant automáticamente:**# Pacientes

PermissionCodes.PATIENT_CREATE  # 'patient.create'

```pythonPermissionCodes.PATIENT_READ    # 'patient.read'

# apps/core/middleware.pyPermissionCodes.PATIENT_UPDATE  # 'patient.update'

class TenantMiddleware:PermissionCodes.PATIENT_DELETE  # 'patient.delete'

    def __call__(self, request):PermissionCodes.PATIENT_EXPORT  # 'patient.export'

        tenant = self._get_tenant(request)

        set_current_tenant(tenant)# Historias Clínicas

        response = self.get_response(request)PermissionCodes.CLINICAL_RECORD_CREATE

        clear_current_tenant()PermissionCodes.CLINICAL_RECORD_READ

        return responsePermissionCodes.CLINICAL_RECORD_UPDATE

    PermissionCodes.CLINICAL_RECORD_DELETE

    def _get_tenant(self, request):PermissionCodes.CLINICAL_RECORD_EXPORT

        # 1. Header X-Tenant-ID

        tenant_id = request.headers.get('X-Tenant-ID')# Documentos

        if tenant_id:PermissionCodes.DOCUMENT_CREATE

            return Tenant.objects.get(id=tenant_id)PermissionCodes.DOCUMENT_READ

        PermissionCodes.DOCUMENT_UPDATE

        # 2. SubdomainPermissionCodes.DOCUMENT_DELETE

        host = request.get_host().split(':')[0]PermissionCodes.DOCUMENT_SIGN    # Solo documentos

        if '.' in host:PermissionCodes.DOCUMENT_EXPORT

            subdomain = host.split('.')[0]

            return Tenant.objects.get(subdomain=subdomain)# Usuarios

        PermissionCodes.USER_CREATE

        # 3. User's tenantPermissionCodes.USER_READ

        if request.user.is_authenticated:PermissionCodes.USER_UPDATE

            return request.user.tenantPermissionCodes.USER_DELETE



        return None# Roles

```PermissionCodes.ROLE_CREATE

PermissionCodes.ROLE_READ

**Métodos de detección (en orden):**PermissionCodes.ROLE_UPDATE

PermissionCodes.ROLE_DELETE

1. **Header HTTP:** `X-Tenant-ID: uuid-del-tenant`

2. **Subdomain:** `hospital-santacruz.clinicrecords.com`# Reportes

3. **Usuario autenticado:** `request.user.tenant`PermissionCodes.REPORT_CREATE

4. **Query param:** `?tenant=uuid` (deshabilitado por seguridad)PermissionCodes.REPORT_READ

PermissionCodes.REPORT_EXPORT

#### 5. Funciones Helper

# Auditoría

```pythonPermissionCodes.AUDIT_READ

from apps.core.middleware import get_current_tenant, set_current_tenantPermissionCodes.AUDIT_EXPORT

````

# Obtener tenant actual

tenant = get_current_tenant()### Clases de Permisos Disponibles

# Establecer tenant manualmente (en scripts)```python

set_current_tenant(tenant_obj)from apps.core.permissions import (

````IsTenantMember, # Base: usuario debe pertenecer al tenant

    IsSuperAdmin,                # Solo ASU (superusuarios)

### Ejemplo Completo: Crear Paciente    HasPermission,               # Genérico con resource_name

    PermissionByActionMixin,     # Mixin para ViewSets

```python

# El tenant se establece automáticamente    # Permisos específicos

patient = Patient.objects.create(    CanManageClinicalRecords,    # CRUD historias + validación pacientes

    first_name='Juan',    CanManageDocuments,          # CRUD documentos + firma

    last_name='Pérez',    CanManageUsers,              # CRUD usuarios (solo Admin TI)

    document_number='12345678'    CanManageRoles,              # CRUD roles (solo Admin TI)

)    CanViewAuditLogs,            # Ver auditoría (solo Admin TI)

    CanGenerateReports,          # Generar reportes

# El tenant ya está asignado gracias a TenantAwareModel)

print(patient.tenant)  # <Tenant: Hospital Santa Cruz>```

````

### Uso en ViewSets

---

#### Opción 1: HasPermission Genérico (Recomendado)

## 🔐 Sistema RBAC

`````python

### Roles Disponiblesfrom apps.core.permissions import (

    IsTenantMember,

```python    HasPermission,

# apps/accounts/constants.py    PermissionByActionMixin

ROLE_ASU = 'ASU'                    # Admin Super Usuario)

ROLE_ADMIN_TI = 'Administrador_TI'  # Admin del tenant

ROLE_DOCTOR = 'Doctor'              # Doctorclass PatientViewSet(PermissionByActionMixin, viewsets.ModelViewSet):

ROLE_PATIENT = 'Paciente'           # Paciente    """ViewSet para gestión de pacientes"""

ROLE_NURSE = 'Enfermera'            # Enfermera

```    permission_classes = [IsTenantMember, HasPermission]

    resource_name = 'patient'  # ← Importante: nombre del recurso

### Estructura de Permisos

    # HasPermission automáticamente mapea:

**Formato:** `<recurso>.<acción>`    # - list/retrieve → patient.read

    # - create → patient.create

**Recursos:**    # - update/partial_update → patient.update

- `patient`    # - destroy → patient.delete

- `clinical_record````

- `document`

- `user`#### Opción 2: Permisos Específicos

- `role`

- `report````python

- `audit`from apps.core.permissions import (

- `backup`    IsTenantMember,

    CanManageClinicalRecords

**Acciones:**)

- `create` - Crear

- `read` - Leerclass ClinicalRecordViewSet(viewsets.ModelViewSet):

- `update` - Actualizar    """ViewSet para historias clínicas"""

- `delete` - Eliminar

- `export` - Exportar    permission_classes = [IsTenantMember, CanManageClinicalRecords]

- `sign` - Firmar (documentos)

    # CanManageClinicalRecords incluye:

**Ejemplos:**    # - Validación de permisos por acción

- `patient.read` - Leer pacientes    # - has_object_permission para pacientes

- `document.sign` - Firmar documentos```

- `report.export` - Exportar reportes

- `audit.read` - Ver logs de auditoría### Validación en el Usuario



### Permisos por Rol```python

# En el modelo User (apps/accounts/models.py)

```pythondef has_permission(self, permission_code):

# ASU (Admin Super Usuario)    """Verifica si el usuario tiene un permiso específico"""

permisos = ['*.*']  # Acceso total    if self.is_superuser:

        return True

# Administrador TI    if not self.role:

permisos = [        return False

    'patient.*', 'clinical_record.*', 'document.*',    return self.role.permissions.filter(code=permission_code).exists()

    'user.*', 'role.*', 'report.*', 'audit.read', 'backup.*'

]# Uso en código

if request.user.has_permission('patient.create'):

# Doctor    # Usuario puede crear pacientes

permisos = [    pass

    'patient.read', 'patient.update',```

    'clinical_record.*', 'document.*',

    'report.read', 'report.export'### Función Auxiliar

]

```python

# Pacientefrom apps.core.permissions import check_permission

permisos = [

    'patient.read',  # Solo su propio perfil# En servicios o vistas

    'clinical_record.read',  # Solo su historiadef my_service(user, patient_id):

    'document.read'  # Solo sus documentos    check_permission(user, 'patient.update')  # Lanza PermissionDenied si no tiene

]    # Continuar con la lógica...

`````

# Enfermera

permisos = [---

    'patient.read', 'patient.create',

    'clinical_record.read', 'clinical_record.update',## 📊 Modelos y Base de Datos

    'document.read', 'document.create'

]### Crear un Modelo

````

**Reglas:**

### Usar Permisos en Views

1. **Tenant-Aware**: Heredar de `TenantAwareModel` si pertenece a un tenant

```python2. **Global**: Heredar de `models.Model` si es compartido entre todos

from apps.core.permissions import HasPermission3. **UUID**: Siempre usar UUID como PK (viene en TenantAwareModel)

4. **Soft Delete**: Usar `deleted_at` en lugar de borrar (viene en TenantAwareModel)

class PatientViewSet(viewsets.ModelViewSet):5. **Timestamps**: Siempre incluir `created_at` y `updated_at` (viene en TenantAwareModel)

    queryset = Patient.objects.all()

    serializer_class = PatientSerializer**Ejemplo:**

    permission_classes = [IsAuthenticated, HasPermission]

    required_permission = 'patient'  # Chequea patient.read, patient.create, etc.```python

    # apps/patients/models.py

    def get_queryset(self):from django.db import models

        # Los pacientes solo ven su propio perfilfrom apps.core.models import TenantAwareModel, TenantManager

        if self.request.user.has_role('Paciente'):

            return Patient.objects.filter(user=self.request.user)class Patient(TenantAwareModel):

        return super().get_queryset()    """Modelo de Paciente (tenant-aware)"""

````

    # Identificación

### Verificar Permisos Manualmente identity_document_type = models.CharField(

        max_length=50,

````python choices=[

# En views o serializers            ('CI', 'Cédula de Identidad'),

user = request.user            ('Pasaporte', 'Pasaporte'),

            ('DNI', 'DNI'),

# Verificar permiso específico            ('RUT', 'RUT'),

if user.has_permission('document.sign'):        ]

    # Usuario puede firmar documentos    )

    pass    identity_document = models.CharField(max_length=100)



# Verificar rol    # Información personal

if user.has_role('Doctor'):    first_name = models.CharField(max_length=100)

    # Usuario es doctor    last_name = models.CharField(max_length=100)

    pass    date_of_birth = models.DateField()

    gender = models.CharField(

# Verificar múltiples permisos        max_length=1,

if user.has_permissions(['patient.read', 'document.read']):        choices=[('M', 'Masculino'), ('F', 'Femenino'), ('O', 'Otro')]

    # Usuario puede leer pacientes Y documentos    )

    pass

```    # Contacto

    phone = models.CharField(max_length=50, blank=True)

---    email = models.EmailField(blank=True)

    address = models.TextField(blank=True)

## 📦 Crear un Nuevo Módulo

    # Metadata

Vamos a crear un módulo de ejemplo: **Appointments (Citas Médicas)**    created_by = models.ForeignKey(

        'accounts.User',

### Paso 1: Crear la App        on_delete=models.SET_NULL,

        null=True,

```bash        related_name='patients_created'

python manage.py startapp appointments apps/appointments    )

````

    # Manager

### Paso 2: Registrar en Settings objects = TenantManager()

````python class Meta:

# config/settings/base.py        db_table = 'patient'

INSTALLED_APPS = [        ordering = ['-created_at']

    # ... otras apps        indexes = [

    'apps.appointments',            models.Index(fields=['tenant', 'identity_document']),

]            models.Index(fields=['first_name', 'last_name']),

```        ]

        # IMPORTANTE: Unicidad por tenant

### Paso 3: Crear Modelo        unique_together = [['tenant', 'identity_document']]



```python    def __str__(self):

# apps/appointments/models.py        return f"{self.first_name} {self.last_name}"

from django.db import models

from apps.core.models import TenantAwareModel    def get_full_name(self):

from apps.core.managers import TenantManager        return f"{self.first_name} {self.last_name}"

from apps.patients.models import Patient```

from apps.accounts.models import User

### Modelo User - Caso Especial

class Appointment(TenantAwareModel):

    STATUS_CHOICES = [**IMPORTANTE**: El modelo `User` **NO hereda de TenantAwareModel** porque es un caso especial que hereda de `AbstractBaseUser` y `PermissionsMixin`.

        ('scheduled', 'Programada'),

        ('confirmed', 'Confirmada'),```python

        ('completed', 'Completada'),# apps/accounts/models.py

        ('cancelled', 'Cancelada'),class User(AbstractBaseUser, PermissionsMixin):

        ('no_show', 'No Asistió'),    """Modelo de Usuario personalizado"""

    ]

        id = models.UUIDField(primary_key=True, default=uuid.uuid4)

    patient = models.ForeignKey(    tenant = models.ForeignKey(

        Patient,        Tenant,

        on_delete=models.CASCADE,        on_delete=models.CASCADE,

        related_name='appointments'        related_name='users',

    )        null=True,  # ← Puede ser null para superusuarios

    doctor = models.ForeignKey(        blank=True

        User,    )

        on_delete=models.CASCADE,

        related_name='doctor_appointments',    email = models.EmailField(unique=True)

        limit_choices_to={'role__name': 'Doctor'}    first_name = models.CharField(max_length=100)

    )    last_name = models.CharField(max_length=100)

    appointment_date = models.DateTimeField()

    duration_minutes = models.PositiveIntegerField(default=30)    role = models.ForeignKey(

    status = models.CharField(        'Role',

        max_length=20,        on_delete=models.SET_NULL,

        choices=STATUS_CHOICES,        null=True,

        default='scheduled'        blank=True,

    )        related_name='users'

    reason = models.TextField()    )

    notes = models.TextField(blank=True)

        # ... más campos

    objects = TenantManager()

        objects = UserManager()

    class Meta:```

        db_table = 'appointments'

        ordering = ['-appointment_date']---

        indexes = [

            models.Index(fields=['tenant', 'appointment_date']),## 🔄 Serializers y Validaciones

            models.Index(fields=['tenant', 'status']),

            models.Index(fields=['patient', 'appointment_date']),(Esta sección se mantiene igual que en la versión original)

        ]

    ---

    def __str__(self):

        return f"{self.patient} - {self.appointment_date}"## 🎯 Views y ViewSets

````

### ModelViewSet con RBAC

### Paso 4: Crear Serializers

````python

```python# apps/patients/views.py

# apps/appointments/serializers.pyfrom rest_framework import viewsets, filters

from rest_framework import serializersfrom rest_framework.decorators import action

from .models import Appointmentfrom rest_framework.response import Response

from apps.patients.serializers import PatientSerializerfrom django_filters.rest_framework import DjangoFilterBackend

from apps.accounts.serializers import UserSerializerfrom drf_spectacular.utils import extend_schema



class AppointmentSerializer(serializers.ModelSerializer):from .models import Patient

    patient_name = serializers.CharField(from .serializers import PatientSerializer, PatientListSerializer

        source='patient.get_full_name',from .filters import PatientFilter

        read_only=Truefrom apps.core.permissions import (

    )    IsTenantMember,

    doctor_name = serializers.CharField(    HasPermission,

        source='doctor.get_full_name',    PermissionByActionMixin

        read_only=True)

    )



    class Meta:@extend_schema(tags=['Patients'])

        model = Appointmentclass PatientViewSet(PermissionByActionMixin, viewsets.ModelViewSet):

        fields = [    """

            'id', 'patient', 'patient_name', 'doctor', 'doctor_name',    ViewSet para gestión de pacientes.

            'appointment_date', 'duration_minutes', 'status',

            'reason', 'notes', 'created_at', 'updated_at'    Permisos requeridos:

        ]    - list/retrieve: patient.read

        read_only_fields = ['id', 'created_at', 'updated_at']    - create: patient.create

        - update: patient.update

    def validate_appointment_date(self, value):    - delete: patient.delete

        """Validar que la fecha sea futura"""    """

        from django.utils import timezone    queryset = Patient.objects.all()

        if value < timezone.now():    permission_classes = [IsTenantMember, HasPermission]

            raise serializers.ValidationError(    resource_name = 'patient'  # ← Para HasPermission

                "La fecha de la cita debe ser futura"

            )    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]

        return value    filterset_class = PatientFilter

    search_fields = ['first_name', 'last_name', 'identity_document']

class AppointmentDetailSerializer(AppointmentSerializer):    ordering_fields = ['created_at', 'last_name']

    patient = PatientSerializer(read_only=True)    ordering = ['-created_at']

    doctor = UserSerializer(read_only=True)

        def get_serializer_class(self):

    class Meta(AppointmentSerializer.Meta):        """Serializer según acción"""

        fields = AppointmentSerializer.Meta.fields        if self.action == 'list':

```            return PatientListSerializer

        return PatientSerializer

### Paso 5: Crear ViewSet

    def get_queryset(self):

```python        """Queryset filtrado por tenant"""

# apps/appointments/views.py        # TenantManager ya filtra por tenant automáticamente

from rest_framework import viewsets, status        return Patient.objects.all()

from rest_framework.decorators import action

from rest_framework.response import Response    def perform_create(self, serializer):

from rest_framework.permissions import IsAuthenticated        """Crear paciente asignando tenant y created_by"""

from apps.core.permissions import HasPermission        serializer.save(

from .models import Appointment            # tenant se asigna automáticamente en TenantAwareModel.save()

from .serializers import AppointmentSerializer, AppointmentDetailSerializer            created_by=self.request.user

        )

class AppointmentViewSet(viewsets.ModelViewSet):

    queryset = Appointment.objects.all()    def perform_destroy(self, instance):

    serializer_class = AppointmentSerializer        """Soft delete en lugar de borrado físico"""

    permission_classes = [IsAuthenticated, HasPermission]        from django.utils import timezone

    required_permission = 'appointment'        instance.deleted_at = timezone.now()

            instance.save()

    def get_serializer_class(self):

        if self.action == 'retrieve':    @action(detail=True, methods=['get'])

            return AppointmentDetailSerializer    def clinical_records(self, request, pk=None):

        return AppointmentSerializer        """Endpoint personalizado: GET /api/patients/{id}/clinical_records/"""

            patient = self.get_object()

    def get_queryset(self):        records = patient.clinicalrecord_set.filter(deleted_at__isnull=True)

        queryset = super().get_queryset()

                from apps.clinical_records.serializers import ClinicalRecordSerializer

        # Filtrar por paciente        serializer = ClinicalRecordSerializer(records, many=True)

        patient_id = self.request.query_params.get('patient_id')

        if patient_id:        return Response(serializer.data)

            queryset = queryset.filter(patient_id=patient_id)```



        # Filtrar por doctor### ViewSet con Permisos Específicos

        doctor_id = self.request.query_params.get('doctor_id')

        if doctor_id:```python

            queryset = queryset.filter(doctor_id=doctor_id)# apps/clinical_records/views.py

        from apps.core.permissions import (

        # Filtrar por estado    IsTenantMember,

        status = self.request.query_params.get('status')    CanManageClinicalRecords

        if status:)

            queryset = queryset.filter(status=status)

        class ClinicalRecordViewSet(viewsets.ModelViewSet):

        # Filtrar por fecha    """ViewSet para historias clínicas con validación especial para pacientes"""

        date = self.request.query_params.get('date')

        if date:    permission_classes = [IsTenantMember, CanManageClinicalRecords]

            queryset = queryset.filter(appointment_date__date=date)

            # CanManageClinicalRecords ya incluye:

        return queryset    # - has_permission: valida permisos por acción

        # - has_object_permission: valida que pacientes solo vean SU historia

    @action(detail=True, methods=['post'])```

    def confirm(self, request, pk=None):

        """Confirmar cita"""---

        appointment = self.get_object()

        appointment.status = 'confirmed'## 🛣️ URLs y Routing

        appointment.save()

        serializer = self.get_serializer(appointment)(Se mantiene igual)

        return Response(serializer.data)

    ---

    @action(detail=True, methods=['post'])

    def cancel(self, request, pk=None):## ⚙️ Servicios y Lógica de Negocio

        """Cancelar cita"""

        appointment = self.get_object()### ¿Cuándo usar Services?

        appointment.status = 'cancelled'

        appointment.save()**IMPORTANTE**: No todas las apps necesitan `services.py`. Solo crear cuando:

        serializer = self.get_serializer(appointment)

        return Response(serializer.data)- Lógica de negocio compleja

    - Operaciones que involucran múltiples modelos

    @action(detail=False, methods=['get'])- Integraciones con servicios externos (S3, OCR, etc.)

    def upcoming(self, request):- Lógica reutilizable

        """Citas próximas"""

        from django.utils import timezone### Apps con Services (REAL)

        upcoming = self.get_queryset().filter(

            appointment_date__gte=timezone.now(),```

            status__in=['scheduled', 'confirmed']apps/documents/services.py   # DocumentService, OCRService

        )[:10]apps/backup/services.py      # BackupService

        serializer = self.get_serializer(upcoming, many=True)```

        return Response(serializer.data)

```---



### Paso 6: Crear URLs## 📡 Signals



```python### Estado Actual

# apps/appointments/urls.py

from django.urls import path, include**IMPORTANTE**: Los signals NO están completamente implementados.

from rest_framework.routers import DefaultRouter

from .views import AppointmentViewSet**Apps con signals**:



router = DefaultRouter()- `apps/accounts/signals.py` - Básico/vacío

router.register(r'appointments', AppointmentViewSet, basename='appointment')

**Recomendación**: Implementar signals cuando sean necesarios para:

urlpatterns = [

    path('', include(router.urls)),- Side effects automáticos (auditoría, notificaciones)

]- Mantener consistencia entre modelos

````

---

### Paso 7: Registrar URLs en Config

## 🧪 Testing

````python

# config/urls.py### Estado Actual

from django.urls import path, include

**IMPORTANTE**: Los tests NO están implementados en la mayoría de apps.

urlpatterns = [

    # ... otras URLs**Apps con tests**:

    path('api/', include('apps.appointments.urls')),

]- `apps/audit/test/`

```- `apps/documents/test/`



### Paso 8: Crear Migración**Pendiente**: Implementar tests para todas las apps principales.



```bash---

python manage.py makemigrations appointments

python manage.py migrate## ⏰ Celery y Tareas Asíncronas

````

### Estado Actual

### Paso 9: Agregar Permisos

**IMPORTANTE**: Celery está en requirements pero **NO está configurado**.

````python

# apps/appointments/management/commands/create_appointment_permissions.py**Pendiente**:

from django.core.management.base import BaseCommand

from apps.accounts.models import Permission- Crear `config/celery.py`

- Configurar Redis

class Command(BaseCommand):- Implementar tareas asíncronas

    help = 'Crear permisos de citas'

    ---

    def handle(self, *args, **options):

        permissions = [## 📚 APIs y Documentación

            ('appointment.create', 'Crear citas'),

            ('appointment.read', 'Ver citas'),### Swagger/OpenAPI

            ('appointment.update', 'Actualizar citas'),

            ('appointment.delete', 'Eliminar citas'),**Configurado con drf-spectacular**

        ]

        ```python

        for codename, name in permissions:# Decoradores para documentación

            Permission.objects.get_or_create(from drf_spectacular.utils import extend_schema

                codename=codename,

                defaults={'name': name}@extend_schema(

            )    tags=['Patients'],

            summary="Listar pacientes",

        self.stdout.write(    description="Obtiene la lista de pacientes del tenant actual"

            self.style.SUCCESS('Permisos de citas creados'))

        )class PatientViewSet(viewsets.ModelViewSet):

```    # ...

````

```bash

python manage.py create_appointment_permissions### Acceder a Swagger

```

````

### Paso 10: Testinghttp://localhost:8000/api/docs/

http://localhost:8000/api/schema/

```python```

# apps/appointments/tests.py

from django.test import TestCase---

from django.utils import timezone

from datetime import timedelta## 🆕 Crear un Nuevo Módulo

from apps.core.models import Tenant

from apps.accounts.models import User, Role### Checklist Completo

from apps.patients.models import Patient

from .models import Appointment```bash

# 1. Crear app

class AppointmentModelTest(TestCase):python manage.py startapp my_module apps/my_module

    def setUp(self):

        self.tenant = Tenant.objects.create(# 2. Archivos básicos necesarios (SIEMPRE)

            name='Test Hospital',cd apps/my_module

            subdomain='test'# Ya existen: __init__.py, apps.py, models.py, views.py, admin.py, urls.py

        )

        self.doctor_role = Role.objects.create(# 3. Archivos opcionales (SOLO SI SON NECESARIOS)

            tenant=self.tenant,touch serializers.py    # ← SIEMPRE necesario

            name='Doctor'touch services.py       # ← Solo si hay lógica compleja

        )touch filters.py        # ← Solo si se necesitan filtros personalizados

        self.doctor = User.objects.create_user(touch signals.py        # ← Solo si se necesitan signals

            email='doctor@test.com',mkdir tests             # ← Solo cuando vayas a escribir tests

            password='test123',```

            tenant=self.tenant,

            role=self.doctor_role### Orden de Implementación

        )

        self.patient = Patient.objects.create(#### Paso 1: apps.py

            tenant=self.tenant,

            first_name='Juan',```python

            last_name='Pérez',# apps/my_module/apps.py

            document_number='12345678'from django.apps import AppConfig

        )

    class MyModuleConfig(AppConfig):

    def test_create_appointment(self):    default_auto_field = 'django.db.models.BigAutoField'

        appointment = Appointment.objects.create(    name = 'apps.my_module'

            tenant=self.tenant,    verbose_name = 'Mi Módulo'

            patient=self.patient,

            doctor=self.doctor,    def ready(self):

            appointment_date=timezone.now() + timedelta(days=1),        # Solo si tienes signals

            reason='Consulta general'        import apps.my_module.signals

        )```

        self.assertEqual(appointment.status, 'scheduled')

        self.assertEqual(str(appointment), f"{self.patient} - {appointment.appointment_date}")#### Paso 2: models.py

````

````python

---# apps/my_module/models.py

from apps.core.models import TenantAwareModel, TenantManager

## 🗄️ Trabajar con Modelos

class MyModel(TenantAwareModel):

### Soft Delete    name = models.CharField(max_length=255)

    # ...

**NUNCA usar `.delete()`**, siempre usar soft delete:

    objects = TenantManager()

```python

# ❌ MAL - Elimina del DB    class Meta:

patient.delete()        db_table = 'my_model'

        ordering = ['-created_at']

# ✅ BIEN - Soft delete```

from django.utils import timezone

patient.deleted_at = timezone.now()#### Paso 3: serializers.py

patient.save()

```python

# O usar el método personalizado# apps/my_module/serializers.py

patient.soft_delete()from rest_framework import serializers

```from .models import MyModel



### Queries Comunesclass MyModelSerializer(serializers.ModelSerializer):

    class Meta:

```python        model = MyModel

# Obtener todos (filtrado automático por tenant)        fields = '__all__'

patients = Patient.objects.all()        read_only_fields = ['id', 'tenant', 'created_at', 'updated_at']

````

# Con select_related (optimiza joins)

patients = Patient.objects.select_related('user').all()#### Paso 4: views.py con RBAC

# Con prefetch_related (optimiza reverse FK)```python

patients = Patient.objects.prefetch_related('appointments').all()# apps/my_module/views.py

from rest_framework import viewsets

# Filtrosfrom apps.core.permissions import (

patients = Patient.objects.filter( IsTenantMember,

    first_name__icontains='juan',    HasPermission,

    created_at__gte=timezone.now() - timedelta(days=30)    PermissionByActionMixin

))

# Ordenarfrom .models import MyModel

patients = Patient.objects.order_by('-created_at')from .serializers import MyModelSerializer

# Paginaciónclass MyModelViewSet(PermissionByActionMixin, viewsets.ModelViewSet):

from django.core.paginator import Paginator """ViewSet para MyModel con RBAC"""

paginator = Paginator(patients, 20) queryset = MyModel.objects.all()

page = paginator.get_page(1) serializer_class = MyModelSerializer

    permission_classes = [IsTenantMember, HasPermission]

# Contar resource_name = 'my_resource' # ← Importante para permisos

count = Patient.objects.count()```

# Existe#### Paso 5: urls.py

exists = Patient.objects.filter(document_number='12345678').exists()

````python

# Valores específicos# apps/my_module/urls.py

emails = Patient.objects.values_list('email', flat=True)from django.urls import path, include

from rest_framework.routers import DefaultRouter

# Agregaciónfrom .views import MyModelViewSet

from django.db.models import Count, Avg

stats = Patient.objects.aggregate(router = DefaultRouter()

    total=Count('id'),router.register(r'', MyModelViewSet, basename='mymodel')

    avg_age=Avg('date_of_birth')

)urlpatterns = [

```    path('', include(router.urls)),

]

### Transactions```



```python#### Paso 6: Registrar en config

from django.db import transaction

```python

# Opción 1: Context manager# config/settings/base.py

try:INSTALLED_APPS = [

    with transaction.atomic():    # ...

        patient = Patient.objects.create(...)    'apps.my_module',

        record = ClinicalRecord.objects.create(patient=patient, ...)]

        # Si algo falla, todo se revierte

except Exception as e:# config/urls.py

    # Manejar errorurlpatterns = [

    pass    # ...

    path('api/my-module/', include('apps.my_module.urls')),

# Opción 2: Decorator]

@transaction.atomic```

def create_patient_with_record(data):

    patient = Patient.objects.create(**data['patient'])#### Paso 7: Crear permisos en seeder

    record = ClinicalRecord.objects.create(

        patient=patient,```python

        **data['record']# En scripts/seed_data.py, agregar 'my_resource' a la lista de resources

    )resources = ['patient', 'clinical_record', 'document', 'user', 'role', 'report', 'audit', 'my_resource']

    return patient```

````

#### Paso 8: Migraciones

### Signals

````bash

```pythonpython manage.py makemigrations my_module

# apps/patients/signals.pypython manage.py migrate

from django.db.models.signals import post_save```

from django.dispatch import receiver

from .models import Patient---

from apps.clinical_records.models import ClinicalRecord

## ✅ Best Practices

@receiver(post_save, sender=Patient)

def create_clinical_record(sender, instance, created, **kwargs):### Do's ✅

    """Crear historia clínica automáticamente al crear paciente"""

    if created:1. **Siempre validar tenant**

        ClinicalRecord.objects.create(

            tenant=instance.tenant,```python

            patient=instanceif obj.tenant_id != request.tenant.id:

        )    raise PermissionDenied()

````

```````python2. **Usar soft delete**

# apps/patients/apps.py

from django.apps import AppConfig```python

from django.utils import timezone

class PatientsConfig(AppConfig):instance.deleted_at = timezone.now()

    default_auto_field = 'django.db.models.BigAutoField'instance.save()

    name = 'apps.patients'```



    def ready(self):3. **Definir resource_name en ViewSets con RBAC**

        import apps.patients.signals  # Importante!

``````python

class MyViewSet(viewsets.ModelViewSet):

---    resource_name = 'my_resource'  # ← Importante

    permission_classes = [IsTenantMember, HasPermission]

## 🌐 Crear Endpoints (ViewSets)```



### ViewSet Básico4. **Documentar APIs**



```python```python

from rest_framework import viewsets@extend_schema(summary="...", description="...")

from rest_framework.permissions import IsAuthenticated```

from apps.core.permissions import HasPermission

5. **Usar TenantManager**

class PatientViewSet(viewsets.ModelViewSet):

    queryset = Patient.objects.all()```python

    serializer_class = PatientSerializerclass MyModel(TenantAwareModel):

    permission_classes = [IsAuthenticated, HasPermission]    objects = TenantManager()  # ← Importante

    required_permission = 'patient'```



    # Acciones disponibles automáticamente:6. **Heredar de PermissionByActionMixin para RBAC**

    # - list()    GET    /api/patients/

    # - create()  POST   /api/patients/```python

    # - retrieve() GET   /api/patients/{id}/class MyViewSet(PermissionByActionMixin, viewsets.ModelViewSet):

    # - update()  PUT    /api/patients/{id}/    # ...

    # - partial_update() PATCH /api/patients/{id}/```

    # - destroy() DELETE /api/patients/{id}/

```### Don'ts ❌



### Serializers Dinámicos1. ❌ **NO crear `services.py` si no es necesario**

2. ❌ **NO crear `filters.py` si no hay filtros personalizados**

```python3. ❌ **NO crear `signals.py` si no hay signals**

def get_serializer_class(self):4. ❌ **NO hardcodear tenant_id en queries**

    if self.action == 'list':5. ❌ **NO ignorar permisos en viewsets**

        return PatientListSerializer6. ❌ **NO hacer borrado físico de datos críticos**

    elif self.action == 'retrieve':7. ❌ **NO olvidar definir `resource_name` en ViewSets con RBAC**

        return PatientDetailSerializer

    return PatientSerializer---

```````

## 🛠️ Comandos Útiles

### Filtros Personalizados

````bash

```python# Desarrollo

def get_queryset(self):python manage.py runserver

    queryset = super().get_queryset()python manage.py shell

    python manage.py dbshell

    # Filtro por query params

    search = self.request.query_params.get('search')# Migraciones

    if search:python manage.py makemigrations

        queryset = queryset.filter(python manage.py migrate

            Q(first_name__icontains=search) |python manage.py showmigrations

            Q(last_name__icontains=search) |

            Q(document_number__icontains=search)# Crear superusuario (ASU)

        )python manage.py createsuperuser



    # Filtro por fecha# Seeders

    start_date = self.request.query_params.get('start_date')python scripts/seed_data.py

    if start_date:

        queryset = queryset.filter(created_at__gte=start_date)# Tests (cuando estén implementados)

    python manage.py test

    return querysetpython manage.py test --keepdb

````

# Backup (cuando esté implementado)

### Acciones Personalizadaspython manage.py backup_database

```python# Otros

from rest_framework.decorators import actionpython manage.py collectstatic

from rest_framework.response import Responsepython manage.py check

```

class PatientViewSet(viewsets.ModelViewSet):

    # ... código anterior---



    @action(detail=True, methods=['get'])## 🔍 Debugging

    def medical_history(self, request, pk=None):

        """GET /api/patients/{id}/medical_history/"""### Django Shell - Probar Permisos

        patient = self.get_object()

        history = patient.clinical_record```python

        serializer = ClinicalRecordSerializer(history)python manage.py shell

        return Response(serializer.data)

    # Ver tenants

    @action(detail=False, methods=['get'])from apps.core.models import Tenant

    def statistics(self, request):Tenant.objects.all()

        """GET /api/patients/statistics/"""

        total = Patient.objects.count()# Establecer tenant actual

        by_gender = Patient.objects.values('gender').annotate(from apps.core.models import set_current_tenant

            count=Count('id')tenant = Tenant.objects.first()

        )set_current_tenant(tenant)

        return Response({

            'total': total,# Ver usuarios y sus roles

            'by_gender': list(by_gender)from apps.accounts.models import User

        })for user in User.objects.all():

        print(f"{user.email} - Rol: {user.role.name if user.role else 'Sin rol'}")

    @action(detail=True, methods=['post'])

    def send_notification(self, request, pk=None):# Probar permisos de un usuario

        """POST /api/patients/{id}/send_notification/"""user = User.objects.get(email='doctor1@hospital-santacruz.com')

        patient = self.get_object()user.has_permission('clinical_record.create')  # → True

        message = request.data.get('message')user.has_permission('user.create')  # → False

        # Lógica para enviar notificación

        return Response({'status': 'sent'})# Ver permisos de un rol

````from apps.accounts.models import Role

role = Role.objects.get(name='Doctor')

### Paginaciónfor perm in role.permissions.all():

    print(f"- {perm.code}: {perm.name}")

```python```

# config/settings/base.py

REST_FRAMEWORK = {---

    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',

    'PAGE_SIZE': 20## 📖 Recursos

}

### Documentación Oficial

# O personalizada

from rest_framework.pagination import PageNumberPagination- [Django](https://docs.djangoproject.com/)

- [Django REST Framework](https://www.django-rest-framework.org/)

class CustomPagination(PageNumberPagination):- [PostgreSQL](https://www.postgresql.org/docs/)

    page_size = 20

    page_size_query_param = 'page_size'### Archivos Importantes del Proyecto

    max_page_size = 100

- `apps/core/permissions.py` - Sistema RBAC completo

class PatientViewSet(viewsets.ModelViewSet):- `apps/core/models.py` - TenantAwareModel, get/set_current_tenant

    pagination_class = CustomPagination- `apps/core/middleware.py` - TenantMiddleware

```- `scripts/seed_data.py` - Datos de prueba con roles



### Filtros con django-filter---



```bash## 📌 Diferencias con la Versión Anterior

pip install django-filter

```### ✅ Corregido



```python1. ✅ Documentado sistema RBAC completo

# config/settings/base.py2. ✅ Aclarado ubicación de `get_current_tenant()` y `set_current_tenant()` → `apps/core/models.py`

INSTALLED_APPS = [3. ✅ Eliminadas referencias a app `ai` (no existe)

    'django_filters',4. ✅ Aclarado que solo hay un `requirements.txt`

]5. ✅ Documentado que `services.py` solo existe en `documents` y `backup`

6. ✅ Documentado que `filters.py` solo existe en `patients`

REST_FRAMEWORK = {7. ✅ Aclarado que `signals.py` y `tests` no están completamente implementados

    'DEFAULT_FILTER_BACKENDS': [8. ✅ Aclarado que Celery NO está configurado

        'django_filters.rest_framework.DjangoFilterBackend',9. ✅ Documentado que User NO hereda de TenantAwareModel

    ]10. ✅ Agregado rol ASU (Admin Super Usuario)

}11. ✅ Documentados 5 roles específicos del sistema

````

### ⚠️ Pendiente de Implementar

```python

# apps/patients/filters.py1. ⚠️ Tests completos

import django_filters2. ⚠️ Signals en todas las apps

from .models import Patient3. ⚠️ Configuración de Celery

4. ⚠️ Services en más apps (según necesidad)

class PatientFilter(django_filters.FilterSet):

    first_name = django_filters.CharFilter(lookup_expr='icontains')---

    last_name = django_filters.CharFilter(lookup_expr='icontains')

    gender = django_filters.ChoiceFilter(choices=Patient.GENDER_CHOICES)**Última actualización:** 2 de Noviembre de 2025

    created_after = django_filters.DateFilter(**Versión:** 2.0.0 (RBAC Implementation)

        field_name='created_at',

        lookup_expr='gte'---

    )

    class Meta:
        model = Patient
        fields = ['first_name', 'last_name', 'gender', 'created_after']

# apps/patients/views.py
class PatientViewSet(viewsets.ModelViewSet):
    filterset_class = PatientFilter
```

**Uso:**

```
GET /api/patients/?first_name=juan&gender=M&created_after=2024-01-01
```

---

## 📝 Serializers

### Serializer Básico

```python
from rest_framework import serializers
from .models import Patient

class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = ['id', 'first_name', 'last_name', 'email', 'created_at']
        read_only_fields = ['id', 'created_at']
```

### Serializers Anidados

```python
class PatientDetailSerializer(serializers.ModelSerializer):
    clinical_record = ClinicalRecordSerializer(read_only=True)
    appointments = AppointmentSerializer(many=True, read_only=True)

    class Meta:
        model = Patient
        fields = ['id', 'first_name', 'last_name', 'clinical_record', 'appointments']
```

### Campos Personalizados

```python
class PatientSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    age = serializers.SerializerMethodField()

    class Meta:
        model = Patient
        fields = ['id', 'first_name', 'last_name', 'full_name', 'age']

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"

    def get_age(self, obj):
        from datetime import date
        if obj.date_of_birth:
            today = date.today()
            return today.year - obj.date_of_birth.year
        return None
```

### Validaciones

```python
class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = '__all__'

    def validate_email(self, value):
        """Validar campo específico"""
        if not value.endswith('@example.com'):
            raise serializers.ValidationError(
                "Email debe ser del dominio @example.com"
            )
        return value

    def validate(self, data):
        """Validar múltiples campos"""
        if data.get('date_of_birth'):
            from datetime import date
            if data['date_of_birth'] > date.today():
                raise serializers.ValidationError({
                    'date_of_birth': 'La fecha de nacimiento no puede ser futura'
                })
        return data
```

### Create y Update Personalizados

```python
class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = '__all__'

    def create(self, validated_data):
        """Lógica personalizada al crear"""
        # Agregar tenant automáticamente
        from apps.core.middleware import get_current_tenant
        validated_data['tenant'] = get_current_tenant()
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Lógica personalizada al actualizar"""
        # No permitir cambiar el document_number
        validated_data.pop('document_number', None)
        return super().update(instance, validated_data)
```

---

## 🔒 Permisos Personalizados

### Crear Permiso Personalizado

```python
# apps/appointments/permissions.py
from rest_framework import permissions

class IsAppointmentParticipant(permissions.BasePermission):
    """
    Solo el paciente o el doctor de la cita pueden acceder
    """
    def has_object_permission(self, request, view, obj):
        return (
            obj.patient.user == request.user or
            obj.doctor == request.user or
            request.user.has_role('Administrador_TI')
        )

class CanConfirmAppointment(permissions.BasePermission):
    """
    Solo doctores y admin pueden confirmar citas
    """
    def has_permission(self, request, view):
        return request.user.has_role(['Doctor', 'Administrador_TI'])
```

### Usar Permiso en ViewSet

```python
class AppointmentViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsAppointmentParticipant]

    def get_permissions(self):
        """Permisos por acción"""
        if self.action == 'confirm':
            return [IsAuthenticated(), CanConfirmAppointment()]
        return super().get_permissions()
```

---

## ⚙️ Celery y Tareas Asíncronas

### Configuración

```python
# config/celery.py
from celery import Celery
from celery.schedules import crontab

app = Celery('clinic_records')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Tareas programadas
app.conf.beat_schedule = {
    'daily-backup': {
        'task': 'apps.backup.tasks.create_automatic_backup',
        'schedule': crontab(hour=2, minute=0),  # 2 AM diario
    },
    'cleanup-old-backups': {
        'task': 'apps.backup.tasks.cleanup_old_backups',
        'schedule': crontab(day_of_week=0, hour=3, minute=0),  # Domingos 3 AM
    },
}
```

### Crear Tarea

```python
# apps/appointments/tasks.py
from celery import shared_task
from django.core.mail import send_mail
from .models import Appointment

@shared_task
def send_appointment_reminder(appointment_id):
    """Enviar recordatorio de cita"""
    appointment = Appointment.objects.get(id=appointment_id)

    send_mail(
        subject=f'Recordatorio: Cita el {appointment.appointment_date}',
        message=f'Hola {appointment.patient.first_name}, recuerda tu cita...',
        from_email='noreply@clinicrecords.com',
        recipient_list=[appointment.patient.email],
    )

    return f'Reminder sent to {appointment.patient.email}'

@shared_task
def generate_monthly_report(tenant_id):
    """Generar reporte mensual"""
    from apps.core.models import Tenant
    from apps.reports.services import ReportService

    tenant = Tenant.objects.get(id=tenant_id)
    report = ReportService.generate_monthly_stats(tenant)

    return f'Report generated for {tenant.name}'
```

### Ejecutar Tarea

```python
# Inmediatamente
from apps.appointments.tasks import send_appointment_reminder
send_appointment_reminder.delay(appointment_id)

# Programada (5 minutos)
from datetime import timedelta
send_appointment_reminder.apply_async(
    args=[appointment_id],
    countdown=300
)

# En fecha específica
from datetime import datetime
send_appointment_reminder.apply_async(
    args=[appointment_id],
    eta=datetime(2025, 11, 10, 9, 0)
)
```

### Monitorear Tareas

```bash
# Ver tareas activas
celery -A config inspect active

# Ver tareas programadas
celery -A config inspect scheduled

# Ver workers
celery -A config inspect stats

# Flower (UI para Celery)
pip install flower
celery -A config flower
# http://localhost:5555
```

---

## 🧪 Testing

### Test Básico

```python
# apps/patients/tests.py
from django.test import TestCase
from apps.core.models import Tenant
from .models import Patient

class PatientModelTest(TestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(
            name='Test Clinic',
            subdomain='test'
        )

    def test_create_patient(self):
        patient = Patient.objects.create(
            tenant=self.tenant,
            first_name='Juan',
            last_name='Pérez',
            document_number='12345678',
            email='juan@test.com'
        )
        self.assertEqual(patient.first_name, 'Juan')
        self.assertEqual(str(patient), 'Juan Pérez')

    def test_patient_full_name(self):
        patient = Patient.objects.create(
            tenant=self.tenant,
            first_name='María',
            last_name='García'
        )
        self.assertEqual(patient.get_full_name(), 'María García')
```

### Test de API

```python
from rest_framework.test import APITestCase
from rest_framework import status

class PatientAPITest(APITestCase):
    def setUp(self):
        self.tenant = Tenant.objects.create(
            name='Test Clinic',
            subdomain='test'
        )
        self.user = User.objects.create_user(
            email='test@test.com',
            password='test123',
            tenant=self.tenant
        )
        self.client.force_authenticate(user=self.user)

    def test_list_patients(self):
        response = self.client.get('/api/patients/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_patient(self):
        data = {
            'first_name': 'Juan',
            'last_name': 'Pérez',
            'document_number': '12345678',
            'email': 'juan@test.com'
        }
        response = self.client.post('/api/patients/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Patient.objects.count(), 1)
```

### Ejecutar Tests

```bash
# Todos los tests
python manage.py test

# App específica
python manage.py test apps.patients

# Test específico
python manage.py test apps.patients.tests.PatientModelTest.test_create_patient

# Con coverage
pip install coverage
coverage run --source='.' manage.py test
coverage report
coverage html  # Genera reporte HTML
```

---

## 🗃️ Migraciones

### Crear Migración

```bash
# Detectar cambios en todos los modelos
python manage.py makemigrations

# App específica
python manage.py makemigrations patients

# Migración vacía (para data migrations)
python manage.py makemigrations --empty patients
```

### Aplicar Migraciones

```bash
# Aplicar todas
python manage.py migrate

# App específica
python manage.py migrate patients

# Migración específica
python manage.py migrate patients 0003

# Revertir
python manage.py migrate patients 0002
```

### Ver Migraciones

```bash
# Listar todas
python manage.py showmigrations

# Ver SQL de una migración
python manage.py sqlmigrate patients 0003
```

### Data Migration

```python
# apps/patients/migrations/0004_populate_clinical_records.py
from django.db import migrations

def create_clinical_records(apps, schema_editor):
    Patient = apps.get_model('patients', 'Patient')
    ClinicalRecord = apps.get_model('clinical_records', 'ClinicalRecord')

    for patient in Patient.objects.all():
        if not hasattr(patient, 'clinical_record'):
            ClinicalRecord.objects.create(
                tenant=patient.tenant,
                patient=patient
            )

def reverse_func(apps, schema_editor):
    pass

class Migration(migrations.Migration):
    dependencies = [
        ('patients', '0003_previous_migration'),
    ]

    operations = [
        migrations.RunPython(create_clinical_records, reverse_func),
    ]
```

---

## ✅ Mejores Prácticas

### 1. Estructura de Código

```python
# ✅ BIEN - Imports organizados
# Standard library
import os
from datetime import datetime

# Django
from django.db import models
from django.contrib.auth import get_user_model

# Third party
from rest_framework import serializers

# Local
from apps.core.models import TenantAwareModel
from .models import Patient
```

### 2. Nombres Descriptivos

```python
# ❌ MAL
def get_data(id):
    return Patient.objects.get(id=id)

# ✅ BIEN
def get_patient_by_id(patient_id: str) -> Patient:
    """
    Obtiene un paciente por su ID.

    Args:
        patient_id: UUID del paciente

    Returns:
        Instancia de Patient

    Raises:
        Patient.DoesNotExist: Si el paciente no existe
    """
    return Patient.objects.get(id=patient_id)
```

### 3. Evitar N+1 Queries

```python
# ❌ MAL - 1 query + N queries
patients = Patient.objects.all()
for patient in patients:
    print(patient.clinical_record.blood_type)  # Query por cada paciente

# ✅ BIEN - 1 query con join
patients = Patient.objects.select_related('clinical_record').all()
for patient in patients:
    print(patient.clinical_record.blood_type)
```

### 4. Use Indexes

```python
class Patient(TenantAwareModel):
    # ... campos

    class Meta:
        indexes = [
            models.Index(fields=['tenant', 'document_number']),
            models.Index(fields=['tenant', 'email']),
            models.Index(fields=['created_at']),
        ]
```

### 5. Manejo de Errores

```python
# ❌ MAL
patient = Patient.objects.get(id=patient_id)

# ✅ BIEN
from django.shortcuts import get_object_or_404
patient = get_object_or_404(Patient, id=patient_id)

# O con try/except
try:
    patient = Patient.objects.get(id=patient_id)
except Patient.DoesNotExist:
    return Response(
        {'error': 'Paciente no encontrado'},
        status=status.HTTP_404_NOT_FOUND
    )
```

### 6. Validación de Datos

```python
# ✅ BIEN - Validar en serializer
class PatientSerializer(serializers.ModelSerializer):
    def validate_email(self, value):
        if Patient.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email ya existe")
        return value
```

### 7. Logs

```python
import logging

logger = logging.getLogger(__name__)

def create_patient(data):
    try:
        patient = Patient.objects.create(**data)
        logger.info(f'Paciente creado: {patient.id}')
        return patient
    except Exception as e:
        logger.error(f'Error creando paciente: {str(e)}')
        raise
```

### 8. Constants

```python
# ❌ MAL - Magic numbers
if user.role == 'Doctor':
    ...

# ✅ BIEN - Constantes
# apps/accounts/constants.py
ROLE_DOCTOR = 'Doctor'
ROLE_ADMIN = 'Administrador_TI'

# views.py
from apps.accounts.constants import ROLE_DOCTOR
if user.role == ROLE_DOCTOR:
    ...
```

---

## 🐛 Debugging

### Django Debug Toolbar

```bash
pip install django-debug-toolbar
```

```python
# config/settings/development.py
INSTALLED_APPS += ['debug_toolbar']

MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']

INTERNAL_IPS = ['127.0.0.1']

# config/urls.py
if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]
```

### Django Shell

```bash
python manage.py shell
```

```python
# En el shell
from apps.patients.models import Patient
from apps.core.middleware import set_current_tenant
from apps.core.models import Tenant

# Establecer tenant
tenant = Tenant.objects.first()
set_current_tenant(tenant)

# Queries
patients = Patient.objects.all()
patient = patients.first()
print(patient.first_name)

# Ver SQL generado
from django.db import connection
print(connection.queries)
```

### Logging

```python
# config/settings/base.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'debug.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
        },
        'apps': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
        },
    },
}
```

---

## 📝 Comandos Útiles

### Django

```bash
# Servidor
python manage.py runserver
python manage.py runserver 0.0.0.0:8000

# Shell
python manage.py shell
python manage.py shell_plus  # Requiere django-extensions

# Migraciones
python manage.py makemigrations
python manage.py migrate
python manage.py showmigrations
python manage.py sqlmigrate app_name migration_number

# Superusuario
python manage.py createsuperuser

# Seeders
python scripts/seed_data.py

# Tests
python manage.py test
python manage.py test apps.patients

# Collectstatic (producción)
python manage.py collectstatic --noinput

# Comprobar proyecto
python manage.py check
```

### Celery

```bash
# Worker
celery -A config worker -l info

# Beat (scheduler)
celery -A config beat -l info

# Worker + Beat juntos
celery -A config worker -B -l info

# Purge (limpiar cola)
celery -A config purge

# Inspect
celery -A config inspect active
celery -A config inspect stats

# Flower (monitoring)
celery -A config flower
```

### PostgreSQL

```bash
# Conectar
psql -U postgres -d clinic_records

# Backup
pg_dump -U postgres clinic_records > backup.sql

# Restore
psql -U postgres clinic_records < backup.sql

# Drop database
dropdb clinic_records

# Create database
createdb clinic_records
```

### Git

```bash
# Estado
git status

# Agregar cambios
git add .
git add apps/patients/

# Commit
git commit -m "feat: agregar módulo de citas"

# Push
git push origin main

# Pull
git pull origin main

# Branch
git checkout -b feature/appointments
git checkout main
git merge feature/appointments
```

---

## 🚀 Próximos Pasos

Una vez domines estos conceptos, puedes:

1. **Agregar más módulos** (Facturación, Inventario, etc.)
2. **Implementar tests completos** (Unit, Integration, E2E)
3. **Optimizar performance** (Caching, Query optimization)
4. **Agregar CI/CD** (GitHub Actions, GitLab CI)
5. **Deploy a producción** (AWS, Docker, Kubernetes)

---

## 📚 Recursos Adicionales

- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Celery Documentation](https://docs.celeryq.dev/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

---

**¡Happy coding! 🎉**

---

**Última actualización:** 5 de Noviembre, 2025  
**Versión:** 1.0
