# 📚 BACKEND DEVELOPMENT GUIDE - CliniDocs

## 📋 Tabla de Contenidos

1. [Introducción](#introducción)
2. [Arquitectura del Backend](#arquitectura-del-backend)
3. [Estructura del Proyecto](#estructura-del-proyecto)
4. [Multi-Tenancy](#multi-tenancy)
5. [Sistema RBAC de Permisos](#sistema-rbac-de-permisos)
6. [Modelos y Base de Datos](#modelos-y-base-de-datos)
7. [Serializers y Validaciones](#serializers-y-validaciones)
8. [Views y ViewSets](#views-y-viewsets)
9. [URLs y Routing](#urls-y-routing)
10. [Servicios y Lógica de Negocio](#servicios-y-lógica-de-negocio)
11. [Signals](#signals)
12. [Testing](#testing)
13. [Celery y Tareas Asíncronas](#celery-y-tareas-asíncronas)
14. [APIs y Documentación](#apis-y-documentación)
15. [Crear un Nuevo Módulo](#crear-un-nuevo-módulo)
16. [Best Practices](#best-practices)
17. [Comandos Útiles](#comandos-útiles)

---

## 🎯 Introducción

Este documento es la guía completa y **ACTUALIZADA** para desarrollar el backend de CliniDocs. Refleja la estructura y arquitectura **REAL** del proyecto implementado.

### Principios Fundamentales

1. **Multi-tenancy First**: Todo debe estar aislado por tenant
2. **RBAC (Role-Based Access Control)**: Control granular de permisos por roles
3. **Seguridad por Defecto**: Validar siempre la propiedad de los recursos
4. **DRY (Don't Repeat Yourself)**: Reutilizar código común
5. **Testing**: Cada funcionalidad debe tener tests
6. **Documentación**: APIs autodocumentadas con Swagger

---

## 🏗️ Arquitectura del Backend

### Stack Tecnológico

```
Django 4.2
├── Django REST Framework 3.14  (APIs)
├── PostgreSQL 14+              (Base de datos)
├── Redis                       (Cache + Celery - Pendiente)
├── Celery 5.3                  (Tareas asíncronas - Pendiente)
├── JWT                         (Autenticación)
└── AWS S3                      (Storage)
```

### Flujo de Request

```
Client Request
    ↓
NGINX (Reverse Proxy)
    ↓
Django WSGI (Gunicorn)
    ↓
Middleware Stack
    ├── SecurityMiddleware
    ├── SessionMiddleware
    ├── AuthenticationMiddleware
    ├── TenantMiddleware ← CRÍTICO
    └── AuditMiddleware
    ↓
URL Router
    ↓
View/ViewSet
    ├── IsTenantMember Check
    ├── RBAC Permissions Check
    ├── Tenant Validation
    └── Business Logic
    ↓
Serializer
    ├── Validation
    └── Data Transform
    ↓
Model/ORM
    ├── QuerySet (filtered by tenant)
    └── Database
    ↓
Response
```

---

## 📁 Estructura del Proyecto

### Estructura Actual (REAL)

```
backend/
├── manage.py
├── requirements.txt              # Un solo archivo de requirements
├── .env
├── .env.example
├── config/
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
└── apps/
    ├── core/               # Multi-tenancy base + permisos
    │   ├── models.py      # Tenant, TenantAwareModel, get/set_current_tenant
    │   ├── middleware.py  # TenantMiddleware
    │   └── permissions.py # Sistema RBAC completo ← NUEVO
    ├── accounts/          # Usuarios, roles, permisos
    ├── patients/          # Gestión de pacientes
    ├── clinical_records/  # Historias clínicas
    ├── documents/         # Documentos clínicos (services.py existe)
    ├── audit/             # Logs de auditoría
    ├── reports/           # Sistema de reportes
    ├── backup/            # Sistema de backup (services.py existe)
    └── tenants/           # Gestión de tenants
```

### Anatomía de una App (Estructura REAL)

```
apps/my_app/
├── __init__.py
├── apps.py              # Configuración de la app
├── models.py            # Modelos de datos
├── serializers.py       # Serializers DRF
├── views.py             # Views/ViewSets
├── urls.py              # URLs de la app
├── admin.py             # Admin de Django
├── services.py          # ⚠️ Solo en: documents, backup
├── filters.py           # ⚠️ Solo en: patients
├── signals.py           # ⚠️ Solo en: accounts (básico)
├── tests/               # ⚠️ Solo en: audit, documents
└── migrations/          # Migraciones de BD
```

**Nota importante**: No todas las apps tienen `services.py`, `filters.py` o `signals.py`. Solo agregar cuando sea necesario.

---

## 🏢 Multi-Tenancy

### Conceptos Clave

El sistema usa **base de datos compartida** con aislamiento por `tenant_id`. Cada hospital/clínica es un tenant independiente.

### TenantMiddleware

**Ubicación**: `apps/core/middleware.py`

El middleware determina el tenant actual en este orden:

```python
# apps/core/middleware.py

1. Header X-Tenant-ID (UUID)
   → Para APIs y servicios externos

2. Subdomain
   → hospital1.clinidocs.com → tenant.subdomain = 'hospital1'

3. Usuario autenticado (session)
   → request.user.tenant_id

4. JWT Token
   → Claims del token: { "tenant_id": "..." }
```

### Thread-Local Storage

**Ubicación**: `apps/core/models.py` (NO en middleware)

```python
from apps/core.models import get_current_tenant, set_current_tenant

# Obtener tenant actual
tenant = get_current_tenant()

# Establecer tenant (solo en casos especiales como seeders)
set_current_tenant(tenant)
```

**Implementación**:

```python
# apps/core/models.py
import threading
_thread_locals = threading.local()

def get_current_tenant():
    """Obtiene el tenant actual del contexto"""
    return getattr(_thread_locals, 'tenant', None)

def set_current_tenant(tenant):
    """Establece el tenant actual en el contexto"""
    _thread_locals.tenant = tenant
```

### TenantAwareModel

**Base abstracta para modelos tenant-aware:**

```python
from apps.core.models import TenantAwareModel

class Patient(TenantAwareModel):
    # NO agregar tenant manualmente, ya viene de TenantAwareModel
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)

    # TenantAwareModel ya incluye:
    # - id (UUID)
    # - tenant (ForeignKey)
    # - created_at
    # - updated_at
    # - deleted_at (soft delete)

    objects = TenantManager()  # Manager que filtra por tenant
```

### TenantManager

```python
from apps.core.models import TenantManager

class MyModel(TenantAwareModel):
    # ...
    objects = TenantManager()  # Filtra automáticamente por tenant
    all_objects = models.Manager()  # Sin filtro (para admin)
```

**Uso:**

```python
# Automáticamente filtrado por tenant actual
patients = Patient.objects.all()

# Ver incluyendo soft-deleted
all_with_deleted = Patient.objects.all_with_deleted()
```

---

## 🔒 Sistema RBAC de Permisos

### ⚡ NUEVO - Sistema Completo Implementado

**Ubicación**: `apps/core/permissions.py`

El sistema implementa **RBAC (Role-Based Access Control)** completo con permisos granulares.

### Roles del Sistema

1. **ASU (Admin Super Usuario)**:

   - Superusuario global
   - NO pertenece a ningún tenant
   - Puede ver TODOS los tenants
   - Email: `superadmin@clinidocs.com`

2. **Administrador TI**:

   - Gestión completa de SU tenant
   - CRUD de usuarios, roles, pacientes, historias, documentos
   - Acceso a auditoría
   - Email: `admin@{tenant}.com`

3. **Doctor**:

   - CRUD completo de historias clínicas
   - CRUD completo de documentos
   - Puede firmar documentos
   - Lectura y actualización de pacientes

4. **Paciente**:

   - Solo lectura de SU propia historia clínica
   - No puede ver historias de otros pacientes
   - Validación en `has_object_permission`

### Códigos de Permisos

**Ubicación**: `apps/core/permissions.py` → clase `PermissionCodes`

```python
from apps.core.permissions import PermissionCodes

# Pacientes
PermissionCodes.PATIENT_CREATE  # 'patient.create'
PermissionCodes.PATIENT_READ    # 'patient.read'
PermissionCodes.PATIENT_UPDATE  # 'patient.update'
PermissionCodes.PATIENT_DELETE  # 'patient.delete'
PermissionCodes.PATIENT_EXPORT  # 'patient.export'

# Historias Clínicas
PermissionCodes.CLINICAL_RECORD_CREATE
PermissionCodes.CLINICAL_RECORD_READ
PermissionCodes.CLINICAL_RECORD_UPDATE
PermissionCodes.CLINICAL_RECORD_DELETE
PermissionCodes.CLINICAL_RECORD_EXPORT

# Documentos
PermissionCodes.DOCUMENT_CREATE
PermissionCodes.DOCUMENT_READ
PermissionCodes.DOCUMENT_UPDATE
PermissionCodes.DOCUMENT_DELETE
PermissionCodes.DOCUMENT_SIGN    # Solo documentos
PermissionCodes.DOCUMENT_EXPORT

# Usuarios
PermissionCodes.USER_CREATE
PermissionCodes.USER_READ
PermissionCodes.USER_UPDATE
PermissionCodes.USER_DELETE

# Roles
PermissionCodes.ROLE_CREATE
PermissionCodes.ROLE_READ
PermissionCodes.ROLE_UPDATE
PermissionCodes.ROLE_DELETE

# Reportes
PermissionCodes.REPORT_CREATE
PermissionCodes.REPORT_READ
PermissionCodes.REPORT_EXPORT

# Auditoría
PermissionCodes.AUDIT_READ
PermissionCodes.AUDIT_EXPORT
```

### Clases de Permisos Disponibles

```python
from apps.core.permissions import (
    IsTenantMember,              # Base: usuario debe pertenecer al tenant
    IsSuperAdmin,                # Solo ASU (superusuarios)
    HasPermission,               # Genérico con resource_name
    PermissionByActionMixin,     # Mixin para ViewSets

    # Permisos específicos
    CanManageClinicalRecords,    # CRUD historias + validación pacientes
    CanManageDocuments,          # CRUD documentos + firma
    CanManageUsers,              # CRUD usuarios (solo Admin TI)
    CanManageRoles,              # CRUD roles (solo Admin TI)
    CanViewAuditLogs,            # Ver auditoría (solo Admin TI)
    CanGenerateReports,          # Generar reportes
)
```

### Uso en ViewSets

#### Opción 1: HasPermission Genérico (Recomendado)

```python
from apps.core.permissions import (
    IsTenantMember,
    HasPermission,
    PermissionByActionMixin
)

class PatientViewSet(PermissionByActionMixin, viewsets.ModelViewSet):
    """ViewSet para gestión de pacientes"""

    permission_classes = [IsTenantMember, HasPermission]
    resource_name = 'patient'  # ← Importante: nombre del recurso

    # HasPermission automáticamente mapea:
    # - list/retrieve → patient.read
    # - create → patient.create
    # - update/partial_update → patient.update
    # - destroy → patient.delete
```

#### Opción 2: Permisos Específicos

```python
from apps.core.permissions import (
    IsTenantMember,
    CanManageClinicalRecords
)

class ClinicalRecordViewSet(viewsets.ModelViewSet):
    """ViewSet para historias clínicas"""

    permission_classes = [IsTenantMember, CanManageClinicalRecords]

    # CanManageClinicalRecords incluye:
    # - Validación de permisos por acción
    # - has_object_permission para pacientes
```

### Validación en el Usuario

```python
# En el modelo User (apps/accounts/models.py)
def has_permission(self, permission_code):
    """Verifica si el usuario tiene un permiso específico"""
    if self.is_superuser:
        return True
    if not self.role:
        return False
    return self.role.permissions.filter(code=permission_code).exists()

# Uso en código
if request.user.has_permission('patient.create'):
    # Usuario puede crear pacientes
    pass
```

### Función Auxiliar

```python
from apps.core.permissions import check_permission

# En servicios o vistas
def my_service(user, patient_id):
    check_permission(user, 'patient.update')  # Lanza PermissionDenied si no tiene
    # Continuar con la lógica...
```

---

## 📊 Modelos y Base de Datos

### Crear un Modelo

**Reglas:**

1. **Tenant-Aware**: Heredar de `TenantAwareModel` si pertenece a un tenant
2. **Global**: Heredar de `models.Model` si es compartido entre todos
3. **UUID**: Siempre usar UUID como PK (viene en TenantAwareModel)
4. **Soft Delete**: Usar `deleted_at` en lugar de borrar (viene en TenantAwareModel)
5. **Timestamps**: Siempre incluir `created_at` y `updated_at` (viene en TenantAwareModel)

**Ejemplo:**

```python
# apps/patients/models.py
from django.db import models
from apps.core.models import TenantAwareModel, TenantManager

class Patient(TenantAwareModel):
    """Modelo de Paciente (tenant-aware)"""

    # Identificación
    identity_document_type = models.CharField(
        max_length=50,
        choices=[
            ('CI', 'Cédula de Identidad'),
            ('Pasaporte', 'Pasaporte'),
            ('DNI', 'DNI'),
            ('RUT', 'RUT'),
        ]
    )
    identity_document = models.CharField(max_length=100)

    # Información personal
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    gender = models.CharField(
        max_length=1,
        choices=[('M', 'Masculino'), ('F', 'Femenino'), ('O', 'Otro')]
    )

    # Contacto
    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)

    # Metadata
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='patients_created'
    )

    # Manager
    objects = TenantManager()

    class Meta:
        db_table = 'patient'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant', 'identity_document']),
            models.Index(fields=['first_name', 'last_name']),
        ]
        # IMPORTANTE: Unicidad por tenant
        unique_together = [['tenant', 'identity_document']]

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
```

### Modelo User - Caso Especial

**IMPORTANTE**: El modelo `User` **NO hereda de TenantAwareModel** porque es un caso especial que hereda de `AbstractBaseUser` y `PermissionsMixin`.

```python
# apps/accounts/models.py
class User(AbstractBaseUser, PermissionsMixin):
    """Modelo de Usuario personalizado"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name='users',
        null=True,  # ← Puede ser null para superusuarios
        blank=True
    )

    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)

    role = models.ForeignKey(
        'Role',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users'
    )

    # ... más campos

    objects = UserManager()
```

---

## 🔄 Serializers y Validaciones

(Esta sección se mantiene igual que en la versión original)

---

## 🎯 Views y ViewSets

### ModelViewSet con RBAC

```python
# apps/patients/views.py
from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema

from .models import Patient
from .serializers import PatientSerializer, PatientListSerializer
from .filters import PatientFilter
from apps.core.permissions import (
    IsTenantMember,
    HasPermission,
    PermissionByActionMixin
)


@extend_schema(tags=['Patients'])
class PatientViewSet(PermissionByActionMixin, viewsets.ModelViewSet):
    """
    ViewSet para gestión de pacientes.

    Permisos requeridos:
    - list/retrieve: patient.read
    - create: patient.create
    - update: patient.update
    - delete: patient.delete
    """
    queryset = Patient.objects.all()
    permission_classes = [IsTenantMember, HasPermission]
    resource_name = 'patient'  # ← Para HasPermission

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = PatientFilter
    search_fields = ['first_name', 'last_name', 'identity_document']
    ordering_fields = ['created_at', 'last_name']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """Serializer según acción"""
        if self.action == 'list':
            return PatientListSerializer
        return PatientSerializer

    def get_queryset(self):
        """Queryset filtrado por tenant"""
        # TenantManager ya filtra por tenant automáticamente
        return Patient.objects.all()

    def perform_create(self, serializer):
        """Crear paciente asignando tenant y created_by"""
        serializer.save(
            # tenant se asigna automáticamente en TenantAwareModel.save()
            created_by=self.request.user
        )

    def perform_destroy(self, instance):
        """Soft delete en lugar de borrado físico"""
        from django.utils import timezone
        instance.deleted_at = timezone.now()
        instance.save()

    @action(detail=True, methods=['get'])
    def clinical_records(self, request, pk=None):
        """Endpoint personalizado: GET /api/patients/{id}/clinical_records/"""
        patient = self.get_object()
        records = patient.clinicalrecord_set.filter(deleted_at__isnull=True)

        from apps.clinical_records.serializers import ClinicalRecordSerializer
        serializer = ClinicalRecordSerializer(records, many=True)

        return Response(serializer.data)
```

### ViewSet con Permisos Específicos

```python
# apps/clinical_records/views.py
from apps.core.permissions import (
    IsTenantMember,
    CanManageClinicalRecords
)

class ClinicalRecordViewSet(viewsets.ModelViewSet):
    """ViewSet para historias clínicas con validación especial para pacientes"""

    permission_classes = [IsTenantMember, CanManageClinicalRecords]

    # CanManageClinicalRecords ya incluye:
    # - has_permission: valida permisos por acción
    # - has_object_permission: valida que pacientes solo vean SU historia
```

---

## 🛣️ URLs y Routing

(Se mantiene igual)

---

## ⚙️ Servicios y Lógica de Negocio

### ¿Cuándo usar Services?

**IMPORTANTE**: No todas las apps necesitan `services.py`. Solo crear cuando:

- Lógica de negocio compleja
- Operaciones que involucran múltiples modelos
- Integraciones con servicios externos (S3, OCR, etc.)
- Lógica reutilizable

### Apps con Services (REAL)

```
apps/documents/services.py   # DocumentService, OCRService
apps/backup/services.py      # BackupService
```

---

## 📡 Signals

### Estado Actual

**IMPORTANTE**: Los signals NO están completamente implementados.

**Apps con signals**:

- `apps/accounts/signals.py` - Básico/vacío

**Recomendación**: Implementar signals cuando sean necesarios para:

- Side effects automáticos (auditoría, notificaciones)
- Mantener consistencia entre modelos

---

## 🧪 Testing

### Estado Actual

**IMPORTANTE**: Los tests NO están implementados en la mayoría de apps.

**Apps con tests**:

- `apps/audit/test/`
- `apps/documents/test/`

**Pendiente**: Implementar tests para todas las apps principales.

---

## ⏰ Celery y Tareas Asíncronas

### Estado Actual

**IMPORTANTE**: Celery está en requirements pero **NO está configurado**.

**Pendiente**:

- Crear `config/celery.py`
- Configurar Redis
- Implementar tareas asíncronas

---

## 📚 APIs y Documentación

### Swagger/OpenAPI

**Configurado con drf-spectacular**

```python
# Decoradores para documentación
from drf_spectacular.utils import extend_schema

@extend_schema(
    tags=['Patients'],
    summary="Listar pacientes",
    description="Obtiene la lista de pacientes del tenant actual"
)
class PatientViewSet(viewsets.ModelViewSet):
    # ...
```

### Acceder a Swagger

```
http://localhost:8000/api/docs/
http://localhost:8000/api/schema/
```

---

## 🆕 Crear un Nuevo Módulo

### Checklist Completo

```bash
# 1. Crear app
python manage.py startapp my_module apps/my_module

# 2. Archivos básicos necesarios (SIEMPRE)
cd apps/my_module
# Ya existen: __init__.py, apps.py, models.py, views.py, admin.py, urls.py

# 3. Archivos opcionales (SOLO SI SON NECESARIOS)
touch serializers.py    # ← SIEMPRE necesario
touch services.py       # ← Solo si hay lógica compleja
touch filters.py        # ← Solo si se necesitan filtros personalizados
touch signals.py        # ← Solo si se necesitan signals
mkdir tests             # ← Solo cuando vayas a escribir tests
```

### Orden de Implementación

#### Paso 1: apps.py

```python
# apps/my_module/apps.py
from django.apps import AppConfig

class MyModuleConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.my_module'
    verbose_name = 'Mi Módulo'

    def ready(self):
        # Solo si tienes signals
        import apps.my_module.signals
```

#### Paso 2: models.py

```python
# apps/my_module/models.py
from apps.core.models import TenantAwareModel, TenantManager

class MyModel(TenantAwareModel):
    name = models.CharField(max_length=255)
    # ...

    objects = TenantManager()

    class Meta:
        db_table = 'my_model'
        ordering = ['-created_at']
```

#### Paso 3: serializers.py

```python
# apps/my_module/serializers.py
from rest_framework import serializers
from .models import MyModel

class MyModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = MyModel
        fields = '__all__'
        read_only_fields = ['id', 'tenant', 'created_at', 'updated_at']
```

#### Paso 4: views.py con RBAC

```python
# apps/my_module/views.py
from rest_framework import viewsets
from apps.core.permissions import (
    IsTenantMember,
    HasPermission,
    PermissionByActionMixin
)

from .models import MyModel
from .serializers import MyModelSerializer

class MyModelViewSet(PermissionByActionMixin, viewsets.ModelViewSet):
    """ViewSet para MyModel con RBAC"""
    queryset = MyModel.objects.all()
    serializer_class = MyModelSerializer
    permission_classes = [IsTenantMember, HasPermission]
    resource_name = 'my_resource'  # ← Importante para permisos
```

#### Paso 5: urls.py

```python
# apps/my_module/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MyModelViewSet

router = DefaultRouter()
router.register(r'', MyModelViewSet, basename='mymodel')

urlpatterns = [
    path('', include(router.urls)),
]
```

#### Paso 6: Registrar en config

```python
# config/settings/base.py
INSTALLED_APPS = [
    # ...
    'apps.my_module',
]

# config/urls.py
urlpatterns = [
    # ...
    path('api/my-module/', include('apps.my_module.urls')),
]
```

#### Paso 7: Crear permisos en seeder

```python
# En scripts/seed_data.py, agregar 'my_resource' a la lista de resources
resources = ['patient', 'clinical_record', 'document', 'user', 'role', 'report', 'audit', 'my_resource']
```

#### Paso 8: Migraciones

```bash
python manage.py makemigrations my_module
python manage.py migrate
```

---

## ✅ Best Practices

### Do's ✅

1. **Siempre validar tenant**

```python
if obj.tenant_id != request.tenant.id:
    raise PermissionDenied()
```

2. **Usar soft delete**

```python
from django.utils import timezone
instance.deleted_at = timezone.now()
instance.save()
```

3. **Definir resource_name en ViewSets con RBAC**

```python
class MyViewSet(viewsets.ModelViewSet):
    resource_name = 'my_resource'  # ← Importante
    permission_classes = [IsTenantMember, HasPermission]
```

4. **Documentar APIs**

```python
@extend_schema(summary="...", description="...")
```

5. **Usar TenantManager**

```python
class MyModel(TenantAwareModel):
    objects = TenantManager()  # ← Importante
```

6. **Heredar de PermissionByActionMixin para RBAC**

```python
class MyViewSet(PermissionByActionMixin, viewsets.ModelViewSet):
    # ...
```

### Don'ts ❌

1. ❌ **NO crear `services.py` si no es necesario**
2. ❌ **NO crear `filters.py` si no hay filtros personalizados**
3. ❌ **NO crear `signals.py` si no hay signals**
4. ❌ **NO hardcodear tenant_id en queries**
5. ❌ **NO ignorar permisos en viewsets**
6. ❌ **NO hacer borrado físico de datos críticos**
7. ❌ **NO olvidar definir `resource_name` en ViewSets con RBAC**

---

## 🛠️ Comandos Útiles

```bash
# Desarrollo
python manage.py runserver
python manage.py shell
python manage.py dbshell

# Migraciones
python manage.py makemigrations
python manage.py migrate
python manage.py showmigrations

# Crear superusuario (ASU)
python manage.py createsuperuser

# Seeders
python scripts/seed_data.py

# Tests (cuando estén implementados)
python manage.py test
python manage.py test --keepdb

# Backup (cuando esté implementado)
python manage.py backup_database

# Otros
python manage.py collectstatic
python manage.py check
```

---

## 🔍 Debugging

### Django Shell - Probar Permisos

```python
python manage.py shell

# Ver tenants
from apps.core.models import Tenant
Tenant.objects.all()

# Establecer tenant actual
from apps.core.models import set_current_tenant
tenant = Tenant.objects.first()
set_current_tenant(tenant)

# Ver usuarios y sus roles
from apps.accounts.models import User
for user in User.objects.all():
    print(f"{user.email} - Rol: {user.role.name if user.role else 'Sin rol'}")

# Probar permisos de un usuario
user = User.objects.get(email='doctor1@hospital-santacruz.com')
user.has_permission('clinical_record.create')  # → True
user.has_permission('user.create')  # → False

# Ver permisos de un rol
from apps.accounts.models import Role
role = Role.objects.get(name='Doctor')
for perm in role.permissions.all():
    print(f"- {perm.code}: {perm.name}")
```

---

## 📖 Recursos

### Documentación Oficial

- [Django](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [PostgreSQL](https://www.postgresql.org/docs/)

### Archivos Importantes del Proyecto

- `apps/core/permissions.py` - Sistema RBAC completo
- `apps/core/models.py` - TenantAwareModel, get/set_current_tenant
- `apps/core/middleware.py` - TenantMiddleware
- `scripts/seed_data.py` - Datos de prueba con roles

---

## 📌 Diferencias con la Versión Anterior

### ✅ Corregido

1. ✅ Documentado sistema RBAC completo
2. ✅ Aclarado ubicación de `get_current_tenant()` y `set_current_tenant()` → `apps/core/models.py`
3. ✅ Eliminadas referencias a app `ai` (no existe)
4. ✅ Aclarado que solo hay un `requirements.txt`
5. ✅ Documentado que `services.py` solo existe en `documents` y `backup`
6. ✅ Documentado que `filters.py` solo existe en `patients`
7. ✅ Aclarado que `signals.py` y `tests` no están completamente implementados
8. ✅ Aclarado que Celery NO está configurado
9. ✅ Documentado que User NO hereda de TenantAwareModel
10. ✅ Agregado rol ASU (Admin Super Usuario)
11. ✅ Documentados 5 roles específicos del sistema

### ⚠️ Pendiente de Implementar

1. ⚠️ Tests completos
2. ⚠️ Signals en todas las apps
3. ⚠️ Configuración de Celery
4. ⚠️ Services en más apps (según necesidad)

---

**Última actualización:** 2 de Noviembre de 2025  
**Versión:** 2.0.0 (RBAC Implementation)

---
