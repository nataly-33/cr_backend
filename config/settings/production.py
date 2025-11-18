"""
Django settings for production environment - CLINIC RECORDS
Deploy en AWS EC2 con todas las funcionalidades:
- PostgreSQL (RDS)
- Redis (Cache + Celery)
- AWS S3 (Media + Backups)
- AWS Textract (OCR)
- SendGrid (Email)
- Stripe (Pagos en modo test)
- Firebase (Push Notifications)

NOTA: Las configuraciones de servicios (S3, Stripe, SendGrid, Firebase) 
están en base.py y se activan mediante variables de entorno.
Este archivo solo contiene overrides específicos de producción.
"""

from .base import *
import os
from pathlib import Path
from decouple import config, Csv

# ============================================================================
# SECURITY SETTINGS
# ============================================================================
DEBUG = False
SECRET_KEY = config('SECRET_KEY')
ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=Csv())

# Security Headers (HTTP - cambiar a True con HTTPS)
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# ============================================================================
# DATABASE - PostgreSQL (RDS o Local)
# ============================================================================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DATABASE_NAME'),
        'USER': config('DATABASE_USER'),
        'PASSWORD': config('DATABASE_PASSWORD'),
        'HOST': config('DATABASE_HOST'),
        'PORT': config('DATABASE_PORT', default='5432'),
        'CONN_MAX_AGE': 600,  # Mantener conexiones abiertas (performance)
        'OPTIONS': {
            'connect_timeout': 10,
        },
    }
}

# ============================================================================
# REDIS - Cache y Celery Broker
# ============================================================================
REDIS_URL = config('REDIS_URL', default='redis://localhost:6379/0')

# Cache Configuration
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            },
        },
        'KEY_PREFIX': 'clinidocs_prod',
        'TIMEOUT': 3600,
    }
}

# Session backend en Redis (mejor performance)
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# ============================================================================
# CELERY - Override para producción
# ============================================================================
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default=REDIS_URL)
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default=REDIS_URL)
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_TASK_ALWAYS_EAGER = False  # Ejecutar tareas en background (no sincrónicamente)
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutos timeout
CELERY_BROKER_TRANSPORT_OPTIONS = {
    'visibility_timeout': 3600,
    'max_connections': 50,
}

# ============================================================================
# STORAGE - Override para S3 en producción
# ============================================================================
# NOTA: USE_S3 se lee desde .env y la configuración base está en base.py
# Aquí solo hacemos el override del MEDIA_URL y DEFAULT_FILE_STORAGE

if USE_S3:
    # Media files en S3
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
else:
    # Fallback a local (no recomendado en producción)
    MEDIA_URL = '/media/'
    MEDIA_ROOT = BASE_DIR / 'media'

# Static files (Nginx los sirve directamente en producción)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# ============================================================================
# CORS - Override para producción
# ============================================================================
CORS_ALLOWED_ORIGINS = config('CORS_ALLOWED_ORIGINS', cast=Csv())
CORS_ALLOW_CREDENTIALS = True

# ============================================================================
# LOGGING - Configuración completa para producción
# ============================================================================

# Crear directorio de logs si no existe
LOGS_DIR = BASE_DIR / 'logs'
LOGS_DIR.mkdir(exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} {name} {module}.{funcName}:{lineno} - {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
        'simple': {
            'format': '[{levelname}] {asctime} - {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
    },
    
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    
    'handlers': {
        # Console output
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        
        # Application logs (INFO y superior)
        'app_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'app.log',
            'maxBytes': 1024 * 1024 * 10,  # 10 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        
        # Error logs (solo errores)
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'errors.log',
            'maxBytes': 1024 * 1024 * 10,  # 10 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        
        # Django request/response logs
        'django_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'django.log',
            'maxBytes': 1024 * 1024 * 10,  # 10 MB
            'backupCount': 3,
            'formatter': 'verbose',
        },
        
        # Celery logs
        'celery_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'celery.log',
            'maxBytes': 1024 * 1024 * 10,  # 10 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    
    'loggers': {
        # Django core
        'django': {
            'handlers': ['console', 'django_file'],
            'level': 'INFO',
            'propagate': False,
        },
        
        # Django requests (4xx, 5xx)
        'django.request': {
            'handlers': ['console', 'error_file'],
            'level': 'ERROR',
            'propagate': False,
        },
        
        # Django server
        'django.server': {
            'handlers': ['console', 'django_file'],
            'level': 'INFO',
            'propagate': False,
        },
        
        # Celery
        'celery': {
            'handlers': ['console', 'celery_file'],
            'level': 'INFO',
            'propagate': False,
        },
        
        # Apps personalizadas
        'apps': {
            'handlers': ['console', 'app_file', 'error_file'],
            'level': 'INFO',
            'propagate': False,
        },
        
        # Boto3 (AWS) - reducir verbosidad
        'boto3': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'botocore': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        's3transfer': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
    
    # Root logger (captura todo lo demás)
    'root': {
        'handlers': ['console', 'app_file'],
        'level': 'INFO',
    },
}

# ============================================================================
# AWS CLOUDWATCH - Audit Logs Monitoring
# ============================================================================
USE_CLOUDWATCH = config('USE_CLOUDWATCH', default=False, cast=bool)
AWS_CLOUDWATCH_LOG_GROUP = config('AWS_CLOUDWATCH_LOG_GROUP', default='/clinidocs-audit')
AWS_REGION = config('AWS_REGION', default='us-east-1')

# ============================================================================
# BACKUP SETTINGS - S3 Backups
# ============================================================================
# Si necesitas cambiar esto, edita apps/backup/services.py
ENABLE_AUTO_BACKUP = config('ENABLE_AUTO_BACKUP', default=True, cast=bool)

# ============================================================================
# REST FRAMEWORK - Rate Limiting para producción
# ============================================================================
REST_FRAMEWORK = {
    **REST_FRAMEWORK,  # Heredar configuración de base.py
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',  # Solo JSON en producción (no browsable API)
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',  # Usuarios anónimos
        'user': '1000/hour',  # Usuarios autenticados
    },
}