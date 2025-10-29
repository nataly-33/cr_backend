# 🏥 SISTEMA DE GESTIÓN DOCUMENTAL - HISTORIAS CLÍNICAS

## RESUMEN COMPLETO FINAL - GUÍA MAESTRA DEL PROYECTO

**Versión:** 3.0 Final  
**Última actualización:** Octubre 2025  
**Duración total:** 14 días (2 semanas)  
**Equipo:** 3 personas  
**Stack:** Django + React + Flutter + PostgreSQL + AWS

---

## 📋 TABLA DE CONTENIDOS

1. [Visión General del Proyecto](#1-visión-general-del-proyecto)
2. [Stack Tecnológico](#2-stack-tecnológico)
3. [Arquitectura del Sistema](#3-arquitectura-del-sistema)
4. [Estructura Completa del Proyecto](#4-estructura-completa-del-proyecto)
5. [Base de Datos](#5-base-de-datos)
6. [Planificación de Sprints (14 días)](#6-planificación-de-sprints-14-días)
7. [Integraciones de IA](#7-integraciones-de-ia)
8. [Multi-Tenancy](#8-multi-tenancy)
9. [Seguridad y Auditoría](#9-seguridad-y-auditoría)
10. [APIs y Swagger](#10-apis-y-swagger)
11. [Deployment](#11-deployment)
12. [Roles del Equipo](#12-roles-del-equipo)

---

## 1. VISIÓN GENERAL DEL PROYECTO

### 🎯 Objetivo

Desarrollar un **Sistema SaaS de Gestión Documental de Historias Clínicas** multi-tenant que permita a hospitales y clínicas gestionar de forma digital y segura los expedientes médicos de sus pacientes.

### 🎓 Contexto Académico

Este proyecto se desarrolla en el marco de la materia de Ingeniería de Software, con una duración de **14 días naturales** divididos en:

- **Sprint Especial** (Días 1-3): Presentación de 8 puntos obligatorios
- **Sprint 1** (Días 4-7): Funcionalidad básica completa
- **Sprint 2** (Días 8-10): Módulos avanzados
- **Sprint 3** (Días 11-12): App móvil
- **Sprint 4** (Días 13-14): IA y refinamiento

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

### 🎨 Frontend Web

- **Framework:** React 18 + TypeScript
- **Build Tool:** Vite
- **UI Library:** Tailwind CSS + shadcn/ui
- **Estado Global:** Zustand o React Context
- **Peticiones HTTP:** Axios
- **Routing:** React Router v6
- **Formularios:** React Hook Form + Zod
- **Gráficos:** Recharts o Chart.js
- **Notificaciones:** React Toastify

### 📱 Frontend Móvil

- **Framework:** React Native + Expo
- **UI:** React Native Paper
- **Navegación:** React Navigation
- **Estado:** Zustand
- **Almacenamiento Local:** AsyncStorage
- **Notificaciones Push:** Expo Notifications
- **Cámara:** Expo Camera (para OCR)

### 🤖 Inteligencia Artificial

| Tecnología                       | Uso                                     | Link                                                                                            |
| -------------------------------- | --------------------------------------- | ----------------------------------------------------------------------------------------------- |
| AWS textract                     | OCR de documentos médicos               | [Docs](https://cloud.google.com/vision/docs)                                                    |
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

### 🏗️ Arquitectura General

```
┌────────────────────────────────────────────────────────────────┐
│                         FRONTEND LAYER                         │
├──────────────────────┬─────────────────────┬───────────────────┤
│   React Web App      │   Flutter           │   Admin Panel     │
│   (Responsive)       │   (iOS + Android)   │   (Django Admin)  │
└──────────────────────┴─────────────────────┴───────────────────┘
                              ▼ HTTPS
┌─────────────────────────────────────────────────────────────────┐
│                      API GATEWAY / NGINX                        │
└─────────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DJANGO REST FRAMEWORK                        │
├─────────────────────────────────────────────────────────────────┤
│  Tenant Middleware → Aislamiento por tenant_id                  │
│  Authentication (JWT) → Seguridad                               │
│  Permissions (RBAC) → Control de acceso                         │
└─────────────────────────────────────────────────────────────────┘
                              ▼
┌──────────────────┬───────────────────┬─────────────────────────┐
│   PostgreSQL     │   Redis           │   AWS S3                │
│   (Base Datos)   │   (Caché/Celery)  │   (Archivos)            │
└──────────────────┴───────────────────┴─────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SERVICIOS EXTERNOS                           │
├─────────────────────────────────────────────────────────────────┤
│  Stripe → Pagos  │  SendGrid → Email  │ AWS Textract  → OCR     │
└─────────────────────────────────────────────────────────────────┘
```

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

---

## 4. ESTRUCTURA COMPLETA DEL PROYECTO

### 📁 Estructura de Directorios (Final)

```
clinidocs-project/
│
├── backend/                          # Django Backend
│   ├── manage.py
│   ├── requirements.txt
│   ├── .env
│   ├── .env.example
│   ├── .gitignore
│   ├── pytest.ini
│   ├── docker-compose.yml
│   ├── Dockerfile
│   │
│   ├── config/                       # Configuración del proyecto
│   │   ├── __init__.py
│   │   ├── settings/
│   │   │   ├── __init__.py
│   │   │   ├── base.py              # Settings compartidos
│   │   │   ├── development.py       # Settings dev
│   │   │   ├── production.py        # Settings prod
│   │   │   └── testing.py           # Settings test
│   │   ├── urls.py
│   │   ├── wsgi.py
│   │   └── asgi.py
│   │
│   ├── apps/                         # Todas las apps
│   │   │
│   │   ├── core/                     # Multi-tenancy
│   │   │   ├── __init__.py
│   │   │   ├── apps.py
│   │   │   ├── models.py            # Tenant, BaseModel
│   │   │   ├── admin.py
│   │   │   ├── middleware.py        # TenantMiddleware
│   │   │   ├── permissions.py
│   │   │   ├── utils.py
│   │   │   ├── tests/
│   │   │   └── migrations/
│   │   │
│   │   ├── accounts/                 # Usuarios
│   │   │   ├── __init__.py
│   │   │   ├── apps.py
│   │   │   ├── models.py            # User, Role, Permission
│   │   │   ├── serializers.py
│   │   │   ├── views.py
│   │   │   ├── urls.py
│   │   │   ├── permissions.py
│   │   │   ├── signals.py
│   │   │   ├── services.py
│   │   │   ├── tests/
│   │   │   └── migrations/
│   │   │
│   │   ├── tenants/                  # Gestión de tenants
│   │   │   ├── __init__.py
│   │   │   ├── apps.py
│   │   │   ├── models.py            # SubscriptionPlan
│   │   │   ├── serializers.py
│   │   │   ├── views.py
│   │   │   ├── urls.py
│   │   │   ├── services.py
│   │   │   ├── tests/
│   │   │   └── migrations/
│   │   │
│   │   ├── patients/                 # Pacientes
│   │   │   ├── __init__.py
│   │   │   ├── apps.py
│   │   │   ├── models.py
│   │   │   ├── serializers.py
│   │   │   ├── views.py
│   │   │   ├── urls.py
│   │   │   ├── filters.py
│   │   │   ├── tests/
│   │   │   └── migrations/
│   │   │
│   │   ├── clinical_records/         # Historias clínicas
│   │   │   ├── __init__.py
│   │   │   ├── apps.py
│   │   │   ├── models.py
│   │   │   ├── serializers.py
│   │   │   ├── views.py
│   │   │   ├── urls.py
│   │   │   ├── services.py
│   │   │   ├── tests/
│   │   │   └── migrations/
│   │   │
│   │   ├── documents/                # Documentos (NÚCLEO)
│   │   │   ├── __init__.py
│   │   │   ├── apps.py
│   │   │   ├── models.py            # ClinicalDocument, MedicalImage
│   │   │   ├── serializers.py
│   │   │   ├── views.py
│   │   │   ├── urls.py
│   │   │   ├── services.py          # Upload, versioning
│   │   │   ├── storage.py           # S3 handler
│   │   │   ├── filters.py
│   │   │   ├── tests/
│   │   │   └── migrations/
│   │   │
│   │   ├── forms/                    # Formularios clínicos
│   │   │   ├── __init__.py
│   │   │   ├── apps.py
│   │   │   ├── models.py
│   │   │   ├── serializers.py
│   │   │   ├── views.py
│   │   │   ├── urls.py
│   │   │   ├── tests/
│   │   │   └── migrations/
│   │   │
│   │   ├── reports/                  # Reportes
│   │   │   ├── __init__.py
│   │   │   ├── apps.py
│   │   │   ├── models.py            # ReportTemplate, ReportExecution
│   │   │   ├── serializers.py
│   │   │   ├── views.py
│   │   │   ├── urls.py
│   │   │   ├── generators/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── pdf_generator.py
│   │   │   │   ├── excel_generator.py
│   │   │   │   └── csv_generator.py
│   │   │   ├── templates/
│   │   │   │   ├── report_base.html
│   │   │   │   └── document_report.html
│   │   │   ├── tests/
│   │   │   └── migrations/
│   │   │
│   │   ├── audit/                    # Auditoría (caja negra)
│   │   │   ├── __init__.py
│   │   │   ├── apps.py
│   │   │   ├── models.py            # AuditLog
│   │   │   ├── serializers.py
│   │   │   ├── views.py
│   │   │   ├── urls.py
│   │   │   ├── middleware.py
│   │   │   ├── signals.py
│   │   │   ├── tests/
│   │   │   └── migrations/
│   │   │
│   │   ├── notifications/            # Notificaciones
│   │   │   ├── __init__.py
│   │   │   ├── apps.py
│   │   │   ├── models.py
│   │   │   ├── serializers.py
│   │   │   ├── views.py
│   │   │   ├── urls.py
│   │   │   ├── services.py
│   │   │   ├── consumers.py         # WebSocket
│   │   │   ├── tests/
│   │   │   └── migrations/
│   │   │
│   │   ├── payments/                 # Stripe
│   │   │   ├── __init__.py
│   │   │   ├── apps.py
│   │   │   ├── models.py            # Payment, Invoice
│   │   │   ├── serializers.py
│   │   │   ├── views.py
│   │   │   ├── urls.py
│   │   │   ├── services.py          # Stripe API
│   │   │   ├── webhooks.py
│   │   │   ├── tests/
│   │   │   └── migrations/
│   │   │
│   │   ├── backup/                   # Backup
│   │   │   ├── __init__.py
│   │   │   ├── apps.py
│   │   │   ├── models.py
│   │   │   ├── serializers.py
│   │   │   ├── views.py
│   │   │   ├── urls.py
│   │   │   ├── services.py
│   │   │   ├── management/
│   │   │   │   └── commands/
│   │   │   │       ├── backup_database.py
│   │   │   │       └── restore_database.py
│   │   │   ├── tests/
│   │   │   └── migrations/
│   │   │
│   │   ├── analytics/                # Estadísticas
│   │   │   ├── __init__.py
│   │   │   ├── apps.py
│   │   │   ├── models.py
│   │   │   ├── serializers.py
│   │   │   ├── views.py
│   │   │   ├── urls.py
│   │   │   ├── services.py
│   │   │   ├── tests/
│   │   │   └── migrations/
│   │   │
│   │   └── ai/                       # Servicios de IA
│   │       ├── __init__.py
│   │       ├── apps.py
│   │       ├── views.py
│   │       ├── urls.py
│   │       ├── services/
│   │       │   ├── __init__.py
│   │       │   ├── ocr_service.py   # Google Vision
│   │       │   ├── image_enhancement.py # Real-ESRGAN
│   │       │   ├── outlier_detection.py # Isolation Forest
│   │       │   └── risk_prediction.py   # Decision Tree
│   │       ├── tests/
│   │       └── migrations/
│   │
│   ├── static/                       # Archivos estáticos
│   │   ├── css/
│   │   ├── js/
│   │   └── images/
│   │
│   ├── media/                        # Archivos subidos (local dev)
│   │   ├── documents/
│   │   ├── images/
│   │   └── backups/
│   │
│   ├── templates/                    # Templates HTML
│   │   ├── base.html
│   │   ├── emails/
│   │   └── reports/
│   │
│   ├── scripts/                      # Scripts útiles
│   │   ├── setup_dev.sh
│   │   ├── deploy.sh
│   │   └── seed_data.py
│   │
│   └── docs/                         # Documentación
│       ├── api.md
│       ├── architecture.md
│       └── deployment.md
│
├── frontend/                         # React Frontend
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── tailwind.config.js
│   ├── index.html
│   ├── .env
│   ├── .env.example
│   │
│   ├── public/
│   │   ├── favicon.ico
│   │   └── assets/
│   │
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── vite-env.d.ts
│       │
│       ├── components/               # Componentes reutilizables
│       │   ├── ui/                  # shadcn/ui components
│       │   ├── layout/
│       │   ├── forms/
│       │   └── common/
│       │
│       ├── pages/                    # Páginas
│       │   ├── auth/
│       │   ├── dashboard/
│       │   ├── patients/
│       │   ├── documents/
│       │   └── reports/
│       │
│       ├── services/                 # API calls
│       │   ├── api.ts
│       │   ├── auth.service.ts
│       │   ├── patients.service.ts
│       │   └── documents.service.ts
│       │
│       ├── hooks/                    # Custom hooks
│       │   ├── useAuth.ts
│       │   └── useTenant.ts
│       │
│       ├── store/                    # Estado global
│       │   └── useStore.ts
│       │
│       ├── utils/                    # Utilidades
│       │   ├── constants.ts
│       │   └── helpers.ts
│       │
│       ├── types/                    # TypeScript types
│       │   └── index.ts
│       │
│       └── styles/                   # Estilos globales
│           └── globals.css
│
├── mobile/                           # React Native App
│   ├── package.json
│   ├── app.json
│   ├── babel.config.js
│   ├── tsconfig.json
│   │
│   ├── App.tsx
│   │
│   └── src/
│       ├── screens/
│       ├── components/
│       ├── navigation/
│       ├── services/
│       ├── hooks/
│       ├── store/
│       ├── utils/
│       └── types/
│
├── database/                         # Scripts de DB
│   ├── schema.sql
│   └── seeders/
│       ├── tenants.sql
│       └── users.sql
│
└── docs/                             # Documentación del proyecto
    ├── RESUMEN_COMPLETO_FINAL.md    # Esta guía
    ├── PLAN_ACCION_SPRINT1.md       # Guía detallada Sprint 1
    ├── API_DOCUMENTATION.md
    └── DEPLOYMENT_GUIDE.md
```

---

## 5. BASE DE DATOS

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

### 📝 Script SQL

El script completo está en el archivo que me pasaste. Se ejecuta con:

```bash
psql -U postgres -d clinidocs -f database/schema.sql
```

---

## 6. PLANIFICACIÓN DE SPRINTS (14 DÍAS)

### 📅 Calendario General

| Sprint              | Días  | Duración | Objetivo                           |
| ------------------- | ----- | -------- | ---------------------------------- |
| **Sprint Especial** | 1-3   | 3 días   | Presentación 8 puntos obligatorios |
| **Sprint 1**        | 4-7   | 4 días   | Backend completo + Frontend básico |
| **Sprint 2**        | 8-10  | 3 días   | Módulos avanzados + Reportes       |
| **Sprint 3**        | 11-12 | 2 días   | App móvil                          |
| **Sprint 4**        | 13-14 | 2 días   | IA + Refinamiento final            |

---

### 🎯 SPRINT ESPECIAL (Días 1-3)

**Objetivo:** Demostrar que cumplimos los 8 puntos obligatorios

#### DÍA 1 - Fundación y Multi-Tenancy

**Entregables:**

- ✅ Proyecto Django configurado
- ✅ Base de datos PostgreSQL ejecutada
- ✅ Modelos: Tenant, User, Role, Permission
- ✅ TenantMiddleware funcionando
- ✅ Autenticación JWT
- ✅ 2 tenants de prueba con datos aislados

**Funcionalidades:**

- Multi-tenancy con aislamiento por `tenant_id`
- Login/logout con JWT
- Middleware que captura tenant del request
- Admin de Django configurado

#### DÍA 2 - Documentos y Seguridad

**Entregables:**

- ✅ Modelos: Patient, ClinicalRecord, ClinicalDocument
- ✅ AuditLog con hash SHA-256 inviolable
- ✅ Sistema RBAC (roles y permisos)
- ✅ Upload de documentos (S3 o local)
- ✅ OCR básico con AWS Textract
- ✅ APIs CRUD de pacientes y documentos

**Funcionalidades:**

- Gestión de pacientes por tenant
- Historias clínicas
- Upload de PDFs e imágenes
- OCR automático en documentos
- Audit logs capturando TODAS las acciones
- Sistema de permisos granular

#### DÍA 3 - Reportes, Backup y Finalización

**Entregables:**

- ✅ Sistema de reportes (PDF y Excel)
- ✅ Backup por tenant
- ✅ Swagger documentación
- ✅ Deploy en AWS
- ✅ Frontend React básico (login, dashboard, listas)
- ✅ Datos de demo (seeders)
- ✅ Presentación preparada

**Funcionalidades:**

- Generación de reportes en PDF con gráficos
- Exportación a Excel
- Script de backup de BD
- Documentación Swagger completa
- Frontend responsive básico
- Sistema deployado y accesible

---

### 🚀 SPRINT 1 (Días 4-7)

**Objetivo:** Sistema funcional completo con todas las funcionalidades core

#### Módulos a Implementar:

##### 1. Backend Completo (Django)

**Modelos Django por App:**

- ✅ **core:** Tenant, BaseModel
- ✅ **accounts:** User, Role, Permission, RolePermission, UserPreferences
- ✅ **tenants:** SubscriptionPlan (ya en core.Tenant)
- ✅ **patients:** Patient
- ✅ **clinical_records:** ClinicalRecord
- ✅ **documents:** ClinicalDocument, MedicalImage, DocumentAccessLog
- ✅ **forms:** ClinicalForm
- ✅ **reports:** ReportTemplate, ReportExecution
- ✅ **audit:** AuditLog
- ✅ **notifications:** Notification
- ✅ **payments:** Payment, Invoice
- ✅ **backup:** BackupJob
- ✅ **analytics:** TenantUsageStats

**APIs REST (45+ endpoints):**

**Autenticación:**

- POST `/api/auth/register/` - Registro de nuevo tenant
- POST `/api/auth/login/` - Login JWT
- POST `/api/auth/logout/` - Logout
- POST `/api/auth/refresh/` - Refresh token
- POST `/api/auth/verify-email/` - Verificar email
- POST `/api/auth/reset-password/` - Reset password

**Usuarios:**

- GET/POST `/api/users/` - Listar/crear usuarios
- GET/PUT/DELETE `/api/users/{id}/` - CRUD usuario
- POST `/api/users/{id}/change-password/` - Cambiar contraseña
- POST `/api/users/{id}/toggle-active/` - Activar/desactivar
- GET `/api/users/me/` - Usuario actual
- PUT `/api/users/me/preferences/` - Actualizar preferencias

**Roles y Permisos:**

- GET/POST `/api/roles/` - Listar/crear roles
- GET/PUT/DELETE `/api/roles/{id}/` - CRUD rol
- POST `/api/roles/{id}/assign-permissions/` - Asignar permisos
- GET `/api/permissions/` - Listar permisos disponibles

**Pacientes:**

- GET/POST `/api/patients/` - Listar/crear pacientes
- GET/PUT/DELETE `/api/patients/{id}/` - CRUD paciente
- GET `/api/patients/{id}/clinical-records/` - Historias del paciente
- GET `/api/patients/search/?q=` - Búsqueda

**Historias Clínicas:**

- GET/POST `/api/clinical-records/` - Listar/crear
- GET/PUT/DELETE `/api/clinical-records/{id}/` - CRUD
- GET `/api/clinical-records/{id}/documents/` - Documentos
- GET `/api/clinical-records/{id}/timeline/` - Línea de tiempo

**Documentos Clínicos (NÚCLEO):**

- GET/POST `/api/documents/` - Listar/crear
- GET/PUT/DELETE `/api/documents/{id}/` - CRUD
- POST `/api/documents/upload/` - Upload con OCR automático
- GET `/api/documents/{id}/download/` - Descargar
- POST `/api/documents/{id}/sign/` - Firmar digitalmente
- GET `/api/documents/{id}/access-log/` - Log de accesos
- GET `/api/documents/search/` - Búsqueda avanzada

**Reportes:**

- GET `/api/reports/templates/` - Plantillas disponibles
- POST `/api/reports/generate/` - Generar reporte
- GET `/api/reports/executions/` - Historial
- GET `/api/reports/executions/{id}/download/` - Descargar

**Auditoría:**

- GET `/api/audit/logs/` - Consultar logs (solo admin)
- GET `/api/audit/logs/{id}/` - Detalle de log
- GET `/api/audit/logs/verify-integrity/` - Verificar hashes

**Notificaciones:**

- GET `/api/notifications/` - Mis notificaciones
- PUT `/api/notifications/{id}/read/` - Marcar como leída
- DELETE `/api/notifications/{id}/` - Eliminar

**Analytics:**

- GET `/api/analytics/dashboard/` - Dashboard stats
- GET `/api/analytics/documents-by-type/` - Gráfico
- GET `/api/analytics/patients-trend/` - Tendencia
- GET `/api/analytics/usage-stats/` - Uso del sistema

**Backup:**

- POST `/api/backup/create/` - Crear backup
- GET `/api/backup/jobs/` - Listar backups
- POST `/api/backup/restore/{id}/` - Restaurar

**IA:**

- POST `/api/ai/ocr/` - Procesar OCR
- POST `/api/ai/enhance-image/` - Mejorar imagen
- POST `/api/ai/predict-risk/` - Predicción de riesgo
- POST `/api/ai/detect-outliers/` - Detectar anomalías

##### 2. Frontend Web (React)

**Páginas Principales:**

```
src/pages/
├── auth/
│   ├── LoginPage.tsx
│   ├── RegisterPage.tsx
│   └── ForgotPasswordPage.tsx
├── dashboard/
│   └── DashboardPage.tsx          # Stats, gráficos, accesos rápidos
├── patients/
│   ├── PatientsListPage.tsx       # Tabla con filtros
│   ├── PatientDetailPage.tsx      # Perfil + historias clínicas
│   └── PatientFormPage.tsx        # Crear/editar
├── clinical-records/
│   ├── ClinicalRecordDetailPage.tsx
│   └── ClinicalRecordFormPage.tsx
├── documents/
│   ├── DocumentsListPage.tsx      # Galería/lista de documentos
│   ├── DocumentViewerPage.tsx     # Visor de PDF/imágenes
│   └── DocumentUploadPage.tsx     # Upload con OCR
├── reports/
│   ├── ReportsPage.tsx            # Generador de reportes
│   └── ReportViewerPage.tsx       # Visualizar reporte
├── users/
│   ├── UsersListPage.tsx
│   └── UserFormPage.tsx
├── settings/
│   ├── ProfilePage.tsx
│   ├── PreferencesPage.tsx
│   └── SecurityPage.tsx
└── admin/
    ├── TenantsPage.tsx            # Solo super admin
    └── SystemLogsPage.tsx
```

**Componentes UI:**

- Navbar responsive con menú móvil
- Sidebar con navegación
- Tablas con paginación y filtros
- Formularios con validación
- Modal/Dialog components
- File uploader con preview
- PDF viewer integrado
- Gráficos (Recharts)
- Notificaciones toast
- Loading skeletons

**Funcionalidades Frontend:**

- ✅ Autenticación JWT con refresh automático
- ✅ Protección de rutas por roles
- ✅ Multi-idioma (ES/EN)
- ✅ Tema claro/oscuro
- ✅ Responsive mobile-first
- ✅ PWA (Service Worker)
- ✅ Notificaciones en tiempo real
- ✅ Upload con drag & drop
- ✅ Búsqueda con debounce
- ✅ Paginación infinita
- ✅ Exportar a PDF/Excel

#### Timeline Sprint 1:

**DÍA 4:**

- ✅ Completar todos los modelos Django
- ✅ Crear serializers con validaciones
- ✅ Implementar viewsets DRF
- ✅ Configurar URLs
- ✅ Testing básico de APIs

**DÍA 5:**

- ✅ Frontend: Estructura de proyecto
- ✅ Componentes UI base (navbar, sidebar, forms)
- ✅ Páginas de autenticación
- ✅ Dashboard básico
- ✅ Integración con API

**DÍA 6:**

- ✅ Páginas de pacientes (CRUD completo)
- ✅ Páginas de documentos (upload, viewer)
- ✅ Sistema de notificaciones
- ✅ Mejoras de UX

**DÍA 7:**

- ✅ Testing E2E
- ✅ Corrección de bugs
- ✅ Optimización de performance
- ✅ Documentación de código

---

### 📊 SPRINT 2 (Días 8-10)

**Objetivo:** Módulos avanzados, reportes complejos, analytics

#### Funcionalidades a Implementar:

##### 1. Sistema de Reportes Avanzado

**Tipos de Reportes:**

- 📋 Reporte de documentos por tipo/fecha/especialidad
- 👥 Reporte de pacientes activos/nuevos
- 📈 Estadísticas de uso del sistema
- 👨‍⚕️ Reporte de actividad por doctor
- 📊 Dashboard gerencial

**Características:**

- Query Builder dinámico
- Filtros personalizables (fecha, tipo, especialidad, doctor, etc.)
- Gráficos: barras, líneas, tortas
- Exportación: PDF (con gráficos), Excel (múltiples hojas), CSV
- Programación de reportes (Celery)
- Historial de reportes generados

##### 2. Dashboard Analítico

**Widgets:**

- Resumen de métricas (pacientes, documentos, usuarios)
- Gráfico de documentos por mes
- Top 5 especialidades
- Pacientes nuevos vs recurrentes
- Uso de almacenamiento
- Actividad reciente

##### 3. Sistema de Pagos Stripe (Completo)

**Funcionalidades:**

- Checkout de suscripción
- Gestión de tarjetas
- Historial de pagos
- Facturas automáticas
- Webhooks de Stripe:
  - `checkout.session.completed`
  - `customer.subscription.updated`
  - `customer.subscription.deleted`
  - `invoice.paid`
  - `invoice.payment_failed`

##### 4. Formularios Clínicos Dinámicos

**Tipos:**

- Historia clínica de primera vez
- Evolución médica
- Signos vitales
- Órdenes médicas
- Consentimiento informado
- Epicrisis

**Características:**

- Constructor de formularios (drag & drop en frontend)
- Validaciones personalizadas
- Campos condicionales
- Guardado automático
- Versionamiento

##### 5. Búsqueda Avanzada

**Implementar:**

- Full-text search en PostgreSQL
- Búsqueda por múltiples criterios
- Sugerencias (autocomplete)
- Filtros inteligentes
- Ordenamiento personalizado

##### 6. Versionamiento de Documentos

**Funcionalidades:**

- Historial de versiones
- Comparación de versiones
- Rollback a versión anterior
- Firma digital por versión

#### Timeline Sprint 2:

**DÍA 8:**

- ✅ Sistema de reportes completo (backend)
- ✅ Generadores PDF/Excel
- ✅ Query builder dinámico

**DÍA 9:**

- ✅ Dashboard analítico (frontend)
- ✅ Gráficos interactivos
- ✅ Stripe integration completa
- ✅ Webhooks handler

**DÍA 10:**

- ✅ Formularios dinámicos
- ✅ Búsqueda avanzada
- ✅ Versionamiento de documentos
- ✅ Testing y bugfixes

---

### 📱 SPRINT 3 (Días 11-12)

**Objetivo:** App móvil con funcionalidades esenciales

#### Tecnología:

- React Native + Expo
- React Navigation
- Zustand (estado)
- React Native Paper (UI)
- Expo Camera (para OCR móvil)

#### Funcionalidades App Móvil:

##### Autenticación:

- Login con email/contraseña
- Biometría (Face ID / Touch ID)
- Mantener sesión

##### Dashboard Móvil:

- Resumen de estadísticas
- Accesos rápidos
- Notificaciones

##### Pacientes:

- Listar pacientes
- Buscar paciente
- Ver detalle de paciente
- Ver historia clínica

##### Documentos:

- Listar documentos del paciente
- Ver documento (PDF/imagen)
- Tomar foto y subir (con OCR)
- Descargar documento

##### Notificaciones:

- Push notifications
- Lista de notificaciones
- Marcar como leídas

##### Perfil:

- Ver/editar perfil
- Cambiar contraseña
- Preferencias
- Cerrar sesión

#### Pantallas Móviles:

```
mobile/src/screens/
├── auth/
│   ├── LoginScreen.tsx
│   └── BiometricScreen.tsx
├── dashboard/
│   └── DashboardScreen.tsx
├── patients/
│   ├── PatientsListScreen.tsx
│   ├── PatientDetailScreen.tsx
│   └── PatientSearchScreen.tsx
├── documents/
│   ├── DocumentsListScreen.tsx
│   ├── DocumentViewerScreen.tsx
│   └── DocumentCameraScreen.tsx     # Tomar foto con OCR
├── notifications/
│   └── NotificationsScreen.tsx
└── profile/
    ├── ProfileScreen.tsx
    └── SettingsScreen.tsx
```

#### Timeline Sprint 3:

**DÍA 11:**

- ✅ Setup proyecto React Native + Expo
- ✅ Navegación (Stack + Tab)
- ✅ Autenticación (login, biometría)
- ✅ Dashboard y listados básicos

**DÍA 12:**

- ✅ Upload de fotos con OCR
- ✅ Visor de documentos
- ✅ Notificaciones push
- ✅ Testing en iOS y Android
- ✅ Build y publish (Expo)

---

### 🤖 SPRINT 4 (Días 13-14)

**Objetivo:** Integración completa de IA y refinamiento final

#### Integraciones de IA:

##### 1. OCR con Google Vision API

**Implementación:**

```python
# apps/ai/services/ocr_service.py
from google.cloud import vision
import os

class OCRService:
    def __init__(self):
        self.client = vision.ImageAnnotatorClient()

    def extract_text_from_image(self, image_path):
        """Extrae texto de imagen usando Google Vision"""
        with open(image_path, 'rb') as image_file:
            content = image_file.read()

        image = vision.Image(content=content)
        response = self.client.text_detection(image=image)
        texts = response.text_annotations

        if texts:
            return {
                'text': texts[0].description,
                'confidence': texts[0].confidence,
                'language': texts[0].locale
            }
        return None
```

**Uso:**

- Automático al subir documento
- Endpoint manual: `POST /api/ai/ocr/`
- Búsqueda en texto extraído

##### 2. Mejora de Imágenes (Real-ESRGAN + CLAHE)

**Implementación:**

```python
# apps/ai/services/image_enhancement.py
import cv2
from realesrgan import RealESRGAN
import numpy as np

class ImageEnhancer:
    def __init__(self):
        self.model = RealESRGAN(scale=4)

    def enhance_image(self, image_path, output_path):
        """Mejora calidad de imagen médica"""
        # Super-resolución con Real-ESRGAN
        img = cv2.imread(image_path)
        enhanced = self.model.predict(img)

        # CLAHE para mejorar contraste
        lab = cv2.cvtColor(enhanced, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)

        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        l = clahe.apply(l)

        enhanced = cv2.merge([l, a, b])
        enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)

        cv2.imwrite(output_path, enhanced)
        return output_path
```

**Uso:**

- Automático en imágenes médicas de baja calidad
- Endpoint: `POST /api/ai/enhance-image/`

##### 3. Predicción de Riesgos (Árbol de Decisión)

**Implementación:**

```python
# apps/ai/services/risk_prediction.py
from sklearn.tree import DecisionTreeClassifier
import pandas as pd
import joblib

class RiskPredictor:
    def __init__(self):
        self.model = DecisionTreeClassifier(max_depth=5)

    def train(self, clinical_data):
        """Entrena modelo con datos históricos"""
        X = clinical_data[['age', 'blood_pressure', 'glucose', ...]]
        y = clinical_data['risk_level']
        self.model.fit(X, y)
        joblib.dump(self.model, 'risk_model.pkl')

    def predict_risk(self, patient_data):
        """Predice nivel de riesgo del paciente"""
        model = joblib.load('risk_model.pkl')
        risk = model.predict([patient_data])
        probability = model.predict_proba([patient_data])

        return {
            'risk_level': risk[0],
            'probability': probability[0].max(),
            'factors': self.get_important_features()
        }
```

**Uso:**

- Análisis de riesgo al crear/actualizar historia
- Endpoint: `POST /api/ai/predict-risk/`
- Dashboard con alertas

##### 4. Detección de Outliers (Isolation Forest)

**Implementación:**

```python
# apps/ai/services/outlier_detection.py
from sklearn.ensemble import IsolationForest
import pandas as pd

class OutlierDetector:
    def __init__(self):
        self.model = IsolationForest(contamination=0.1)

    def detect_outliers(self, vital_signs):
        """Detecta valores anómalos en signos vitales"""
        data = pd.DataFrame(vital_signs)
        predictions = self.model.fit_predict(data)

        outliers = data[predictions == -1]
        return {
            'has_outliers': len(outliers) > 0,
            'outlier_records': outliers.to_dict('records'),
            'anomaly_score': self.model.score_samples(data).tolist()
        }
```

**Uso:**

- Validación automática de signos vitales
- Alertas en valores anómalos
- Endpoint: `POST /api/ai/detect-outliers/`

#### Refinamiento Final:

##### DÍA 13:

- ✅ Integrar todos los servicios de IA
- ✅ Testing de modelos ML
- ✅ Entrenar con datos de prueba
- ✅ Endpoints de IA funcionando

##### DÍA 14:

- ✅ Optimización de performance
- ✅ Corrección de bugs finales
- ✅ Testing E2E completo
- ✅ Documentación final
- ✅ Video demo
- ✅ Preparar presentación final

---

## 7. INTEGRACIONES DE IA

### 🧠 Resumen de IA Implementada

| Tecnología          | Propósito              | Endpoint                   | Sprint          |
| ------------------- | ---------------------- | -------------------------- | --------------- |
| Google Vision API   | OCR de documentos      | `/api/ai/ocr/`             | Sprint Especial |
| Real-ESRGAN + CLAHE | Mejora de imágenes     | `/api/ai/enhance-image/`   | Sprint 4        |
| Decision Tree       | Predicción de riesgos  | `/api/ai/predict-risk/`    | Sprint 4        |
| Isolation Forest    | Detección de anomalías | `/api/ai/detect-outliers/` | Sprint 4        |

### 📊 Dashboards con IA:

**Dashboard de Riesgos:**

- Lista de pacientes de alto riesgo
- Factores de riesgo principales
- Tendencias de riesgo por especialidad

**Dashboard de Calidad:**

- Documentos con baja calidad de imagen
- Sugerencias de mejora automática
- Estadísticas de OCR (confianza promedio)

---

## 8. MULTI-TENANCY

### 🏢 Implementación de Multi-Tenancy

**Estrategia:** Base de datos compartida con `tenant_id` en todas las tablas

#### TenantMiddleware:

```python
# apps/core/middleware.py
import threading
from django.utils.deprecation import MiddlewareMixin
from .models import Tenant

_thread_locals = threading.local()

def get_current_tenant():
    return getattr(_thread_locals, 'tenant', None)

def set_current_tenant(tenant):
    _thread_locals.tenant = tenant

class TenantMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Opción 1: Header X-Tenant-ID
        tenant_id = request.headers.get('X-Tenant-ID')

        # Opción 2: Subdomain
        if not tenant_id:
            host = request.get_host().split(':')[0]
            subdomain = host.split('.')[0]
            try:
                tenant = Tenant.objects.get(subdomain=subdomain)
                tenant_id = str(tenant.id)
            except Tenant.DoesNotExist:
                pass

        # Opción 3: Usuario autenticado
        if not tenant_id and request.user.is_authenticated:
            tenant_id = str(request.user.tenant_id)

        if tenant_id:
            try:
                tenant = Tenant.objects.get(id=tenant_id)
                set_current_tenant(tenant)
                request.tenant = tenant
            except Tenant.DoesNotExist:
                pass
```

#### BaseModel con Tenant:

```python
# apps/core/models.py
from django.db import models
import uuid

class TenantAwareModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='%(class)s_set'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self.tenant_id:
            self.tenant = get_current_tenant()
        super().save(*args, **kwargs)
```

#### TenantManager:

```python
# apps/core/models.py
from django.db import models

class TenantManager(models.Manager):
    def get_queryset(self):
        qs = super().get_queryset()
        tenant = get_current_tenant()
        if tenant:
            return qs.filter(tenant=tenant, deleted_at__isnull=True)
        return qs.filter(deleted_at__isnull=True)
```

---

## 9. SEGURIDAD Y AUDITORÍA

### 🔒 Medidas de Seguridad

1. **Autenticación:**

   - JWT con refresh tokens
   - 2FA opcional (TOTP)
   - Verificación de email
   - Rate limiting en login

2. **Autorización:**

   - RBAC (Role-Based Access Control)
   - Permisos granulares por recurso
   - Row-level permissions por tenant

3. **Datos:**

   - Passwords hasheados con bcrypt
   - Encriptación en tránsito (HTTPS)
   - Encriptación en reposo (AWS S3)
   - Firma digital de documentos

4. **Auditoría:**
   - Logs de TODAS las acciones
   - Hash SHA-256 inviolable
   - IP, User-Agent, timestamps
   - Cambios before/after en JSONB

### 🕵️ Sistema de Auditoría (Caja Negra)

```python
# apps/audit/models.py
import hashlib
import json
from django.db import models

class AuditLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    tenant = models.ForeignKey('core.Tenant', on_delete=models.CASCADE)
    user = models.ForeignKey('accounts.User', null=True, on_delete=models.SET_NULL)

    action_type = models.CharField(max_length=100)
    resource_type = models.CharField(max_length=100)
    resource_id = models.UUIDField(null=True)

    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()

    changes = models.JSONField(default=dict)
    timestamp = models.DateTimeField(auto_now_add=True)

    log_hash = models.CharField(max_length=64, editable=False)

    def save(self, *args, **kwargs):
        if not self.log_hash:
            self.log_hash = self.generate_hash()
        super().save(*args, **kwargs)

    def generate_hash(self):
        data = f"{self.user_id}{self.action_type}{self.resource_type}{self.timestamp}{json.dumps(self.changes)}"
        return hashlib.sha256(data.encode()).hexdigest()
```

---

## 10. APIS Y SWAGGER

### 📚 Documentación Swagger

**Configuración:**

```python
# config/settings/base.py
INSTALLED_APPS = [
    ...
    'drf_spectacular',
]

REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'CliniDocs API',
    'DESCRIPTION': 'Sistema de Gestión Documental de Historias Clínicas',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}
```

**URLs:**

- `/api/schema/` - Schema OpenAPI
- `/api/docs/` - Swagger UI
- `/api/redoc/` - ReDoc UI

### 📡 Estándares de API

**Respuestas:**

```json
// Success
{
  "status": "success",
  "data": { ... },
  "message": "Operación exitosa"
}

// Error
{
  "status": "error",
  "error": "Descripción del error",
  "code": "ERROR_CODE",
  "details": { ... }
}

// Paginación
{
  "status": "success",
  "data": [...],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 150,
    "pages": 8
  }
}
```

---

## 11. DEPLOYMENT

### 🚀 Stack de Producción

**Backend (Railway/Render):**

- Django + Gunicorn
- PostgreSQL (managed)
- Redis (managed)
- AWS S3 (storage)
- Celery workers

**Frontend (Vercel/Netlify):**

- React build estático
- CDN global
- HTTPS automático

**Móvil (Expo):**

- Expo EAS Build
- Over-the-air updates

### 🔧 Variables de Entorno

```bash
# Backend .env
DEBUG=False
SECRET_KEY=<random-key>
DATABASE_URL=postgresql://...
REDIS_URL=redis://...

AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_STORAGE_BUCKET_NAME=...

STRIPE_SECRET_KEY=...
STRIPE_WEBHOOK_SECRET=...

SENDGRID_API_KEY=...

GOOGLE_VISION_CREDENTIALS=...
```

---

## 12. ROLES DEL EQUIPO

### 👥 División de Trabajo

**Persona 1 (Backend Lead):**

- Arquitectura Django
- Modelos y migraciones
- APIs core (auth, multi-tenancy)
- Integraciones (Stripe, IA)
- Deploy

**Persona 2 (Backend Developer):**

- Modelos de documentos y pacientes
- Sistema de reportes
- Audit logs
- Testing backend

**Persona 3 (Full-Stack):**

- Frontend React
- App móvil React Native
- APIs de usuarios
- Testing E2E
- Documentación

---

## ✅ CHECKLIST FINAL

### Sprint Especial (Día 3):

- [ ] 8 puntos funcionando
- [ ] Demo preparada
- [ ] Swagger completo
- [ ] Deploy funcional

### Sprint 1 (Día 7):

- [ ] Todas las APIs funcionando
- [ ] Frontend completo
- [ ] Testing > 80%
- [ ] Seeders con datos

### Sprint 2 (Día 10):

- [ ] Reportes avanzados
- [ ] Dashboard analítico
- [ ] Stripe completo

### Sprint 3 (Día 12):

- [ ] App móvil funcional
- [ ] Push notifications
- [ ] Testing iOS/Android

### Sprint 4 (Día 14):

- [ ] IA integrada
- [ ] Performance optimizado
- [ ] Documentación completa
- [ ] Video demo final

---

## COMANDOS UTILES

# Ver usuarios creados

python manage.py shell

> > > from apps.accounts.models import User
> > > User.objects.all()

# Ver tenants

> > > from apps.core.models import Tenant
> > > Tenant.objects.all()

# Ver pacientes de un tenant específico

> > > from apps.core.models import set_current_tenant
> > > tenant = Tenant.objects.first()
> > > set_current_tenant(tenant)
> > > from apps.patients.models import Patient
> > > Patient.objects.all()

# Crear backup manual de la BD

pg_dump -U clinidocs_user clinidocs_db > backup_dia1.sql
