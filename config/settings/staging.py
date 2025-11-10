"""
Django settings for STAGING environment.
AWS Configuration with RDS, S3, ElastiCache
"""

from .base import *
import os

# SECURITY
# ==============================================================================
DEBUG = False

ALLOWED_HOSTS = [
    'staging-api.clinidocs.com',  # Tu dominio staging
    'staging.clinidocs.com',
    '*.elasticbeanstalk.com',  # Si usas Elastic Beanstalk
    '*.amazonaws.com',  # Para ALB/ECS
]

# CORS
# ==============================================================================
CORS_ALLOWED_ORIGINS = [
    'https://staging.clinidocs.com',
    'https://staging-web.clinidocs.com',
]

CORS_ALLOW_CREDENTIALS = True

# DATABASE (RDS PostgreSQL)
# ==============================================================================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('RDS_DB_NAME', 'clinidocs_staging'),
        'USER': os.environ.get('RDS_USERNAME', 'postgres'),
        'PASSWORD': os.environ.get('RDS_PASSWORD'),
        'HOST': os.environ.get('RDS_HOSTNAME', 'staging-db.xxxxxx.us-east-1.rds.amazonaws.com'),
        'PORT': os.environ.get('RDS_PORT', '5432'),
        'OPTIONS': {
            'sslmode': 'require',  # Forzar SSL en RDS
        },
        'CONN_MAX_AGE': 600,  # Persistent connections
        'ATOMIC_REQUESTS': True,
    }
}

# CACHES (Redis ElastiCache)
# ==============================================================================
REDIS_ENDPOINT = os.environ.get('REDIS_ENDPOINT', 'staging-redis.xxxxxx.cache.amazonaws.com')
REDIS_PORT = os.environ.get('REDIS_PORT', '6379')
REDIS_DB = os.environ.get('REDIS_DB', '0')

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f'redis://{REDIS_ENDPOINT}:{REDIS_PORT}/{REDIS_DB}',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
            'RETRY_ON_TIMEOUT': True,
            'MAX_CONNECTIONS': 50,
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True
            },
            'PARSER_CLASS': 'redis.connection.HiredisParser',
        },
        'KEY_PREFIX': 'clinidocs_staging',
        'TIMEOUT': 300,
    }
}

# Celery (Redis como broker)
CELERY_BROKER_URL = f'redis://{REDIS_ENDPOINT}:{REDIS_PORT}/1'
CELERY_RESULT_BACKEND = f'redis://{REDIS_ENDPOINT}:{REDIS_PORT}/2'

# STATIC & MEDIA FILES (AWS S3)
# ==============================================================================
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME', 'clinidocs-staging-media')
AWS_S3_REGION_NAME = os.environ.get('AWS_S3_REGION_NAME', 'us-east-1')
AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.{AWS_S3_REGION_NAME}.amazonaws.com'

# S3 configuración
AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=86400',
}
AWS_DEFAULT_ACL = 'private'
AWS_S3_FILE_OVERWRITE = False
AWS_QUERYSTRING_AUTH = True
AWS_QUERYSTRING_EXPIRE = 3600  # URLs firmadas válidas por 1 hora

# Static files via S3
STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/static/'

# Media files via S3
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'

# LOGGING
# ==============================================================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} {name} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/django/staging.log',
            'maxBytes': 1024 * 1024 * 10,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console', 'file'],
            'level': 'ERROR',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# SECURITY SETTINGS
# ==============================================================================
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# HSTS (HTTP Strict Transport Security)
SECURE_HSTS_SECONDS = 31536000  # 1 año
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# RATE LIMITING (más restrictivo en staging)
# ==============================================================================
REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {
    'anon': '100/hour',
    'user': '1000/hour',
    'login': '10/hour',
}

# EMAIL (AWS SES)
# ==============================================================================
EMAIL_BACKEND = 'django_ses.SESBackend'
AWS_SES_REGION_NAME = os.environ.get('AWS_SES_REGION_NAME', 'us-east-1')
AWS_SES_REGION_ENDPOINT = f'email.{AWS_SES_REGION_NAME}.amazonaws.com'
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@clinidocs.com')
SERVER_EMAIL = DEFAULT_FROM_EMAIL

# SENTRY (Error Tracking)
# ==============================================================================
if os.environ.get('SENTRY_DSN'):
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.celery import CeleryIntegration
    
    sentry_sdk.init(
        dsn=os.environ.get('SENTRY_DSN'),
        integrations=[
            DjangoIntegration(),
            CeleryIntegration(),
        ],
        environment='staging',
        traces_sample_rate=0.3,
        send_default_pii=False,
    )

# AUDIT LOGGING - Activado
# ==============================================================================
AUDIT_LOGGING_ENABLED = True
AUDIT_LOG_RETENTION_DAYS = 90

print("✅ Staging settings loaded - AWS RDS + S3 + ElastiCache")
