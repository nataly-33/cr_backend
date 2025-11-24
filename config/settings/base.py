import os
import json
from pathlib import Path
from datetime import timedelta
from decouple import config, Csv
import dj_database_url

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Firebase configuration - Load from environment or .env
def get_firebase_credentials():
    """Load Firebase credentials from environment variable or .env file"""
    try:
        cred_json = config('FIREBASE_SERVICE_ACCOUNT_KEY', default=None)
        if cred_json:
            # Si es string JSON, parsearlo
            if isinstance(cred_json, str):
                return json.loads(cred_json)
            return cred_json
    except Exception as e:
        print(f"⚠️ Error loading Firebase credentials: {e}")
    return None

# Security
SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=Csv())

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third party apps
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'drf_spectacular',
    'django_celery_beat',
    'django_celery_results',
    'crum', 

    # Local apps
    'apps.core',
    'apps.accounts',
    'apps.tenants',
    'apps.patients',
    'apps.clinical_records',
    'apps.documents',
    'apps.audit',
    'apps.reports',
    'apps.reports_ai',
    'apps.backup',
    'apps.seed',
    'apps.notifications',
    'apps.payments',
    'apps.ai',
    'apps.dicom',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'crum.CurrentRequestUserMiddleware',  
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    # Custom middleware
    'apps.core.middleware.TenantMiddleware',
    'apps.audit.middleware.AuditLogMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database - PostgreSQL 
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DATABASE_NAME', default='clinic_records_db'),
        'USER': config('DATABASE_USER', default='clinic_admin'),
        'PASSWORD': config('DATABASE_PASSWORD'),
        'HOST': config('DATABASE_HOST', default='localhost'),
        'PORT': config('DATABASE_PORT', default='5432'),
    }
}

# Custom User Model
AUTH_USER_MODEL = 'accounts.User'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'es-bo'
TIME_ZONE = 'America/La_Paz'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Media files
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# JWT Settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=config('JWT_ACCESS_TOKEN_LIFETIME', default=60, cast=int)),
    'REFRESH_TOKEN_LIFETIME': timedelta(minutes=config('JWT_REFRESH_TOKEN_LIFETIME', default=1440, cast=int)),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
}

# CORS Settings
CORS_ALLOWED_ORIGINS = config('CORS_ALLOWED_ORIGINS', cast=Csv())
CORS_ALLOW_CREDENTIALS = True

# Spectacular (Swagger) Settings
SPECTACULAR_SETTINGS = {
    'TITLE': 'CliniDocs API',
    'DESCRIPTION': 'Sistema de Gestión Documental de Historias Clínicas - API Documentation',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'SCHEMA_PATH_PREFIX': '/api',
    
    # Autenticación
    'SECURITY': [
        {
            'Bearer': {
                'type': 'http',
                'scheme': 'bearer',
                'bearerFormat': 'JWT',
            }
        }
    ],
    
    'TAGS': [
        {'name': 'Accounts', 'description': 'Autenticación y gestión de usuarios'},
        {'name': 'Audit', 'description': 'Logs de auditoría'},
        {'name': 'Backup', 'description': 'Sistema de backup'},
        {'name': 'Clinical Forms', 'description': 'Formularios clínicos'},
        {'name': 'Clinical Records', 'description': 'Historias clínicas'},
        {'name': 'DICOM', 'description': 'Estudios DICOM - Imagenología médica (CT, MRI, X-Ray)'},
        {'name': 'Documents', 'description': 'Documentos clínicos'},
        {'name': 'Notifications', 'description': 'Sistema de notificaciones'},
        {'name': 'Patients', 'description': 'Gestión de pacientes'},
        {'name': 'Public - Planes', 'description': 'Planes de suscripción (público)'},
        {'name': 'Public - Registro', 'description': 'Registro de nuevos tenants (público)'},
        {'name': 'Reports', 'description': 'Sistema de reportes'},
        {'name': 'Tenants', 'description': 'Gestión de tenants (hospitales/clínicas)'},
    ],
}

# Celery Configuration
REDIS_URL = config('REDIS_URL', default='redis://localhost:6379/0')
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default=REDIS_URL)
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default=REDIS_URL)
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# Configuración de reportes
REPORTS_DIR = BASE_DIR / 'media' / 'reports'
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Configuración de backups
BACKUPS_DIR = BASE_DIR / 'media' / 'backups'
BACKUPS_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================================
# AWS S3 Y TEXTRACT - Storage y OCR
# ============================================================================
USE_S3 = config('USE_S3', default=False, cast=bool)
USE_S3_BACKUP = config('USE_S3_BACKUP', default=False, cast=bool)

# Cargar credenciales AWS si están configuradas
AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID', default=None)
AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY', default=None)
AWS_STORAGE_BUCKET_NAME = config('AWS_STORAGE_BUCKET_NAME', default=None)
AWS_S3_REGION_NAME = config('AWS_S3_REGION_NAME', default='us-east-1')
AWS_TEXTRACT_REGION = config('AWS_TEXTRACT_REGION', default='us-east-1')
ENABLE_OCR = config('ENABLE_OCR', default=False, cast=bool)

# ============================================================================
# OPENAI - Reportes con IA
# ============================================================================
OPENAI_API_KEY = config('OPENAI_API_KEY', default=None)
OPENAI_MODEL = config('OPENAI_MODEL', default='gpt-4-mini')

# Límites de seguridad
REPORTS_AI_MAX_ROWS = config('REPORTS_AI_MAX_ROWS', default=1000, cast=int)
REPORTS_AI_MAX_QUERY_LENGTH = config('REPORTS_AI_MAX_QUERY_LENGTH', default=5000, cast=int)
REPORTS_AI_EXECUTION_TIMEOUT = config('REPORTS_AI_EXECUTION_TIMEOUT', default=30, cast=int)

# Configuración S3 (se aplica si USE_S3=True en cualquier ambiente)
if USE_S3 or USE_S3_BACKUP:
    AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com' if AWS_STORAGE_BUCKET_NAME else None
    AWS_S3_FILE_OVERWRITE = False
    AWS_DEFAULT_ACL = 'private'
    AWS_S3_OBJECT_PARAMETERS = {
        'CacheControl': 'max-age=86400',
    }
    AWS_S3_VERIFY = True
    AWS_QUERYSTRING_AUTH = True
    AWS_QUERYSTRING_EXPIRE = 3600

# ============================================================================
# CLOUDWATCH - Logging en AWS
# ============================================================================
USE_CLOUDWATCH = config('USE_CLOUDWATCH', default=False, cast=bool)
AWS_CLOUDWATCH_LOG_GROUP = config('AWS_CLOUDWATCH_LOG_GROUP', default='/clinidocs-audit')

# ============================================================================
# EMAIL - SendGrid
# ============================================================================
SENDGRID_ENABLED = config('SENDGRID_ENABLED', default=False, cast=bool)

if SENDGRID_ENABLED:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = 'smtp.sendgrid.net'
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True
    EMAIL_HOST_USER = 'apikey' 
    EMAIL_HOST_PASSWORD = config('SENDGRID_API_KEY')
    DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@clinidocs.com')
    SERVER_EMAIL = DEFAULT_FROM_EMAIL
else:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@localhost')

# ============================================================================
# STRIPE - Pagos y Suscripciones
# ============================================================================
STRIPE_ENABLED = config('STRIPE_ENABLED', default=False, cast=bool)
STRIPE_SECRET_KEY = config('STRIPE_SECRET_KEY', default='')
STRIPE_PUBLISHABLE_KEY = config('STRIPE_PUBLISHABLE_KEY', default='')
STRIPE_WEBHOOK_SECRET = config('STRIPE_WEBHOOK_SECRET', default='')

# ============================================================================
# FIREBASE - Notificaciones Push
# ============================================================================
FIREBASE_SERVER_KEY = config('FIREBASE_SERVER_KEY', default='')

# ============================================================================
# FRONTEND Y URLS
# ============================================================================
FRONTEND_URL = config('FRONTEND_URL', default='http://localhost:5173')
BASE_DOMAIN = config('BASE_DOMAIN', default='localhost')

# ============================================================================
# LOGGING
# ============================================================================

from config.settings.logging import LOGGING
