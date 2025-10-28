# 🏥 SISTEMA DE GESTIÓN DOCUMENTAL - HISTORIAS CLÍNICAS

**Versión:** 3.0 Final  
**Última actualización:** Octubre 2025  
**Equipo:** 4 personas  
**Stack:** Django + React + Flutter/React Native + PostgreSQL + AWS

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
| Google Vision API                | OCR de documentos médicos               | [Docs](https://cloud.google.com/vision/docs)                                                    |
| Real-ESRGAN + CLAHE              | Mejora de imágenes médicas              | [GitHub](https://github.com/xinntao/Real-ESRGAN)                                                |
| Scikit-learn (Árbol de Decisión) | Predicción de riesgos                   | [Docs](https://scikit-learn.org/stable/modules/tree.html)                                       |
| Scikit-learn (Isolation Forest)  | Detección de outliers en signos vitales | [Docs](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.IsolationForest.html) |

### 🔧 DevOps & Herramientas

- **Control de Versiones:** Git + GitHub
- **CI/CD:** GitHub Actions
- **Hosting Backend:** Railway o Render
- **Hosting Frontend:** Vercel o Netlify
- **Documentación API:** Swagger (drf-spectacular)
- **Testing:** pytest + pytest-django
- **Linting:** Black + Flake8 + isort
- **Gestión de Tareas:** Trello o Jira

---

## 3. ARQUITECTURA DEL SISTEMA

### 🏗️ Arquitectura General

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND LAYER                          │
├──────────────────────┬─────────────────────┬───────────────────┤
│   React Web App      │   React Native App  │   Admin Panel     │
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
│  Stripe → Pagos  │  SendGrid → Email  │  Google Vision → OCR   │
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
