# 🏥 SISTEMA DE GESTIÓN DOCUMENTAL - HISTORIAS CLÍNICAS

## � DOCUMENTACIÓN (⭐ Empieza aquí)

### 🗺️ Índice de Guías

| Documento                                                      | Propósito                              | Tiempo   |
| -------------------------------------------------------------- | -------------------------------------- | -------- |
| **[DOCUMENTATION_INDEX.md](../DOCUMENTATION_INDEX.md)**        | Índice centralizado de todas las guías | 5 min    |
| **[SYSTEM_VERIFICATION.md](./SYSTEM_VERIFICATION.md)**         | Verificar que todo funciona            | 30 min   |
| **[API_ENDPOINTS_REFERENCE.md](./API_ENDPOINTS_REFERENCE.md)** | Referencia de todos los endpoints      | 15 min   |
| **[TESTING_GUIDE.md](./TESTING_GUIDE.md)**                     | Cómo testear la API                    | 20 min   |
| **[TROUBLESHOOTING_GUIDE.md](./TROUBLESHOOTING_GUIDE.md)**     | Resolver problemas comunes             | 5-30 min |
| **[LOGGING_GUIDE.md](./LOGGING_GUIDE.md)**                     | Cómo ver y monitorear logs             | 10 min   |
| **[DEVELOPMENT_GUIDE.md](./DEVELOPMENT_GUIDE.md)**             | Arquitectura y desarrollo              | 45 min   |
| **[RESUMEN_FINAL.md](./RESUMEN_FINAL.md)**                     | Resumen del proyecto                   | 20 min   |

**👉 Recomendación:** Comienza con [SYSTEM_VERIFICATION.md](./SYSTEM_VERIFICATION.md) para verificar que todo funciona.

# 🏥 ClinicRecords - Backend (Django + DRF)

**Sistema SaaS Multi-tenant para Gestión de Historias Clínicas y Documentos Médicos**

---

## 📘 Documentación Completa

**👉 Ver [docs/INDEX.md](./docs/INDEX.md) para el índice completo de documentación**

### 📖 Documentos Principales

| Documento                                                                | Propósito                                     | Audiencia       |
| ------------------------------------------------------------------------ | --------------------------------------------- | --------------- |
| **[docs/REVISION.md](./docs/REVISION.md)** ⭐                            | Estado del proyecto, sprints, funcionalidades | Todos           |
| **[docs/DOCUMENTATION_GUIDE.md](./docs/DOCUMENTATION_GUIDE.md)**         | Documentación técnica completa                | Desarrolladores |
| **[docs/DEVELOPMENT_GUIDE.md](./docs/DEVELOPMENT_GUIDE.md)**             | Guía para desarrollar nuevas funcionalidades  | Desarrolladores |
| **[docs/API_ENDPOINTS_REFERENCE.md](./docs/API_ENDPOINTS_REFERENCE.md)** | Referencia de endpoints                       | Todos           |

### 🔧 Guías Específicas

- **[docs/guides/QUICKSTART.md](./docs/guides/QUICKSTART.md)** - Guía rápida de inicio
- **[docs/guides/TROUBLESHOOTING_GUIDE.md](./docs/guides/TROUBLESHOOTING_GUIDE.md)** - Solución de problemas
- **[docs/guides/TESTING_GUIDE.md](./docs/guides/TESTING_GUIDE.md)** - Guía de testing
- **[docs/deployment/SAAS_SETUP_GUIDE.md](./docs/deployment/SAAS_SETUP_GUIDE.md)** - Configuración SaaS
- **[docs/advanced/CELERY_BACKUP_SETUP.md](./docs/advanced/CELERY_BACKUP_SETUP.md)** - Celery y backups

**👉 Recomendación:** Si eres nuevo, comienza con [docs/guides/QUICKSTART.md](./docs/guides/QUICKSTART.md)

---

## 📋 TABLA DE CONTENIDOS

1. [Visión General del Proyecto](#1-visión-general-del-proyecto)
2. [Stack Tecnológico](#2-stack-tecnológico)
3. [Arquitectura del Sistema](#3-arquitectura-del-sistema)
4. [Base de datos](#4-base-de-datos)

## 🚀 Quick Start / Guía rápida

### Prerrequisitos

- Python 3.10+
- PostgreSQL 14+ (opcional para desarrollo local; ver nota sobre tests)
- Redis (opcional)

### Instalación y puesta en marcha (Windows PowerShell)

1. Clonar el repositorio y entrar en la carpeta del backend:

```powershell
git clone <repo-url>
cd D:\1NATALY\Proyectos\clinic_records\cr_backend
```

2. Crear y activar un entorno virtual:

```powershell
python -m venv venv
# PowerShell
.\venv\Scripts\Activate.ps1
# CMD
# venv\Scripts\activate.bat
```

3. Instalar dependencias:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

4. Configurar variables de entorno:

```powershell
copy .env.example .env
# Edita .env con tus credenciales (DATABASE_URL, SECRET_KEY, REDIS_URL, etc.)
```

5. Ejecutar migraciones:

```powershell
python manage.py makemigrations
python manage.py migrate
```

6. Crear superusuario:

```powershell
python manage.py createsuperuser
```

7. Cargar datos de prueba (seeder):

```powershell
python scripts/seed_data.py
```

8. Ejecutar servidor de desarrollo:

```powershell
python manage.py runserver
```

### Documentación y endpoints útiles

- Swagger UI: http://localhost:8000/api/docs/
- ReDoc: http://localhost:8000/api/redoc/
- Django Admin: http://localhost:8000/admin/

### Tests

- Ejecutar todos los tests:

```powershell
pytest
```

- Si tu usuario de Postgres no puede crear bases de datos (error CREATE DATABASE), puedes ejecutar un test aislado usando SQLite:

```powershell
$env:DATABASE_URL = 'sqlite:///D:/1NATALY/Proyectos/clinic_records/cr_backend/db_test.sqlite3'
pytest apps/core/tests/test_tenant_isolation.py -v
```

### Credenciales de prueba

- Hospital Santa Cruz

  - URL: http://hospital-santacruz.localhost:8000
  - Email: admin@hospital-santacruz.com
  - Password: Password123!

- Clínica La Paz
  - URL: http://clinica-lapaz.localhost:8000
  - Email: admin@clinica-lapaz.com
  - Password: Password123!

## 1. VISIÓN GENERAL DEL PROYECTO

### 🎯 Objetivo

Desarrollar un **Sistema SaaS de Gestión Documental de Historias Clínicas** multi-tenant que permita a hospitales y clínicas gestionar de forma digital y segura los expedientes médicos de sus pacientes.

### ✅ 8 Puntos Obligatorios del Proyecto

1. **Multi-tenancy:** Base de datos compartida con `tenant_id`
2. **Sistema multiusuario:** Roles y permisos granulares (RBAC)
3. **Seguridad:** Autenticación JWT, 2FA, logs de auditoría
4. **Generación de reportes:** PDF, Excel, CSV con filtros dinámicos
5. **Stack tecnológico definido:** Django + React + PostgreSQL + AWS
6. **Usabilidad:** Responsive, PWA, multiplataforma
7. **Backup y restore:** Automatizado por tenant
8. **Asistente inteligente (IA):** OCR, mejora de imágenes, ML

### 🚀 Características Principales

- **SaaS Multi-Tenant:** Múltiples hospitales en una misma instancia
- **Gestión de Historias Clínicas:** Expedientes digitales completos
- **Upload de Documentos:** PDFs, imágenes, DICOM
- **OCR Inteligente:** Extracción de texto de documentos escaneados
- **Mejora de Imágenes:** Super-resolución con Real-ESRGAN
- **Reportes Dinámicos:** Generación bajo demanda con filtros
- **Auditoría Completa:** Logs inmutables tipo "caja negra"
- **Pagos con Stripe:** Sistema de suscripciones
- **App Móvil:** Acceso desde iOS y Android
- **Dashboard Analítico:** Estadísticas en tiempo real

---

## 2. STACK TECNOLÓGICO

### 🔧 Backend

- **Framework:** Django 4.2 + Django REST Framework 3.14
- **Base de Datos:** PostgreSQL 14+
- **ORM:** Django ORM (models.py por cada app)
- **Autenticación:** JWT con `djangorestframework-simplejwt`
- **Validaciones:** Serializers + Custom Validators
- **Tareas Asíncronas:** Celery 5.3 + Redis
- **Storage:** AWS S3 para archivos
- **Email:** SendGrid
- **Pagos:** Stripe API

### 🤖 Inteligencia Artificial

| Tecnología                       | Uso                                     | Link                                                                                            |
| -------------------------------- | --------------------------------------- | ----------------------------------------------------------------------------------------------- |
| OCR cn AWS Textract              | OCR de documentos médicos               | [Docs](https://cloud.google.com/vision/docs)                                                    |
| Real-ESRGAN + CLAHE              | Mejora de imágenes médicas              | [GitHub](https://github.com/xinntao/Real-ESRGAN)                                                |
| Scikit-learn (Árbol de Decisión) | Predicción de riesgos                   | [Docs](https://scikit-learn.org/stable/modules/tree.html)                                       |
| Scikit-learn (Isolation Forest)  | Detección de outliers en signos vitales | [Docs](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.IsolationForest.html) |

### 🔧 DevOps & Herramientas

- **Control de Versiones:** Git + GitHub
- **CI/CD:** GitHub Actions
- **Deploy:** AWS
- **Documentación API:** Swagger (drf-spectacular)
- **Testing:** pytest + pytest-django
- **Linting:** Black + Flake8 + isort
- **Gestión de Tareas:** Trello o Jira

---

## 3. ARQUITECTURA DEL SISTEMA

### 📦 Arquitectura de Apps Django

```
clinidocs/
├── apps/
│   ├── core/           → Multi-tenancy, modelos base
│   ├── accounts/       → Usuarios, roles, permisos
│   ├── tenants/        → Gestión de hospitales/clínicas
│   ├── patients/       → Pacientes
│   ├── clinical_records/ → Historias clínicas
│   ├── documents/      → Documentos clínicos (NÚCLEO)
│   ├── forms/          → Formularios clínicos dinámicos
│   ├── reports/        → Sistema de reportes
│   ├── audit/          → Logs de auditoría (caja negra)
│   ├── notifications/  → Notificaciones push/email
│   ├── payments/       → Integración Stripe
│   ├── backup/         → Sistema de backup
│   ├── analytics/      → Estadísticas y dashboards
│   └── ai/             → Servicios de IA (OCR, ML)
└── config/             → Configuración Django
```

## 4. BASE DE DATOS

### 📊 Diseño de Base de Datos

La base de datos PostgreSQL está completamente diseñada con **18 tablas** que cubren todas las funcionalidades del sistema.

#### Tablas Principales (por orden de dependencia):

1. **subscription_plan** - Planes de suscripción (Basic, Pro, Enterprise)
2. **tenant** - Hospitales/clínicas (multi-tenant)
3. **payment** - Pagos con Stripe
4. **invoice** - Facturas
5. **permission** - Permisos granulares por tenant
6. **role** - Roles por tenant
7. **role_permission** - Relación N:N
8. **user** - Usuarios del sistema
9. **user_preferences** - Configuración personalizada
10. **patient** - Pacientes
11. **clinical_record** - Historias clínicas
12. **clinical_document** - Documentos clínicos (NÚCLEO)
13. **document_access_log** - Tracking de accesos
14. **medical_image** - Imágenes DICOM
15. **clinical_form** - Formularios dinámicos
16. **audit_log** - Logs de auditoría inmutables
17. **report_template** - Plantillas de reportes
18. **report_execution** - Historial de reportes
19. **notification** - Notificaciones
20. **backup_job** - Jobs de backup
21. **tenant_usage_stats** - Estadísticas por tenant

### 🔑 Características Clave de la BD:

- ✅ **Multi-tenancy:** Todas las tablas tienen `tenant_id` (excepto tablas globales)
- ✅ **UUIDs:** Todas las PKs son UUID v4 para seguridad
- ✅ **Soft Deletes:** Campo `deleted_at` en tablas críticas
- ✅ **Timestamps:** `created_at` y `updated_at` automáticos
- ✅ **JSONB:** Campos flexibles para metadata
- ✅ **Índices:** Optimizados para queries frecuentes
- ✅ **Constraints:** Validaciones a nivel de BD
- ✅ **Extensiones:** uuid-ossp, pgcrypto

## 📡 APIs Disponibles

### Pacientes

- `GET /api/patients/` - Listar pacientes
- `POST /api/patients/` - Crear paciente
- `GET /api/patients/{id}/` - Detalle de paciente
- `PUT /api/patients/{id}/` - Actualizar paciente
- `DELETE /api/patients/{id}/` - Eliminar paciente
- `GET /api/patients/{id}/clinical-records/` - Historias del paciente

### Historias Clínicas

- `GET /api/clinical-records/` - Listar historias
- `POST /api/clinical-records/` - Crear historia
- `GET /api/clinical-records/{id}/documents/` - Documentos de la historia
- `GET /api/clinical-records/{id}/timeline/` - Timeline de eventos

### Documentos Clínicos

- `GET /api/documents/` - Listar documentos
- `POST /api/documents/upload/` - Upload con OCR automático
- `GET /api/documents/{id}/download/` - Descargar documento
- `POST /api/documents/{id}/sign/` - Firmar digitalmente
- `GET /api/documents/{id}/access-log/` - Log de accesos
- `GET /api/documents/search/?q=query` - Búsqueda avanzada

### Auditoría

- `GET /api/audit/` - Consultar logs (solo admin)
- `GET /api/audit/{id}/verify_integrity/` - Verificar integridad
- `POST /api/audit/verify_all/` - Verificar todos los logs
- `GET /api/audit/stats/` - Estadísticas de auditoría

## 🔒 Seguridad Implementada

- ✅ Hash SHA-256 inviolable en logs
- ✅ Firma digital de documentos
- ✅ Tracking de accesos a documentos
- ✅ Encriptación de archivos en S3 (AES-256)
- ✅ URLs firmadas temporales para descarga
- ✅ Audit log middleware automático
