## ESTRUCTURA COMPLETA DEL PROYECTO

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
```
