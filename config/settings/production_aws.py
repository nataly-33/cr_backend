"""
Django settings for production environment with full AWS configuration.
Use this for AWS deployment (EC2, ECS, Elastic Beanstalk, etc).
"""

from .base import *
from decouple import config
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

# =============================================================================
# SECURITY SETTINGS
# =============================================================================
SECRET_KEY = config('SECRET_KEY')
DEBUG = False
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='*').split(',')

# HTTPS & Security Headers (IMPORTANTE para producción)
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000  # 1 año
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'

# =============================================================================
# CORS Configuration
# =============================================================================
CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default='https://clinidocs.com'
).split(',')
CORS_ALLOW_CREDENTIALS = True

# =============================================================================
# DATABASE - AWS RDS PostgreSQL with SSL
# =============================================================================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('RDS_DB_NAME'),
        'USER': config('RDS_USERNAME'),
        'PASSWORD': config('RDS_PASSWORD'),
        'HOST': config('RDS_HOSTNAME'),
        'PORT': config('RDS_PORT', default='5432'),
        'CONN_MAX_AGE': 600,  # Connection pooling
        'OPTIONS': {
            'sslmode': 'require',  # SSL obligatorio para RDS
            'connect_timeout': 10,
        },
    },
}

# =============================================================================
# REDIS - AWS ElastiCache
# =============================================================================
REDIS_ENDPOINT = config('REDIS_ENDPOINT', default='localhost')
REDIS_PORT = config('REDIS_PORT', default='6379')
REDIS_DB = config('REDIS_DB', default='0')
REDIS_URL = f"redis://{REDIS_ENDPOINT}:{REDIS_PORT}/{REDIS_DB}"

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
            'PARSER_CLASS': 'redis.connection.HiredisParser',
        },
        'KEY_PREFIX': 'clinidocs_prod',
        'TIMEOUT': 3600,
    }
}

SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# =============================================================================
# CELERY - Redis Broker
# =============================================================================
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_TASK_ALWAYS_EAGER = False
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60
CELERY_BROKER_TRANSPORT_OPTIONS = {
    'visibility_timeout': 3600,
    'max_connections': 50,
}

# =============================================================================
# AWS S3 Storage - Media & Static Files
# =============================================================================
AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = config('AWS_STORAGE_BUCKET_NAME')
AWS_S3_REGION_NAME = config('AWS_S3_REGION_NAME', default='us-east-1')
AWS_S3_CUSTOM_DOMAIN = config(
    'AWS_CLOUDFRONT_DOMAIN',
    default=f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
)

AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=86400',  # 1 día
}
AWS_DEFAULT_ACL = 'private'
AWS_S3_FILE_OVERWRITE = False
AWS_QUERYSTRING_AUTH = True
AWS_QUERYSTRING_EXPIRE = 3600

# Media files (user uploads)
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'

# Static files (CSS, JS, imágenes)
STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/static/'

# Backup S3 Configuration
USE_S3_BACKUP = True
AWS_BACKUP_BUCKET = config('BACKUP_S3_BUCKET', default=AWS_STORAGE_BUCKET_NAME)
AWS_BACKUP_REGION = config('BACKUP_S3_REGION', default=AWS_S3_REGION_NAME)

# =============================================================================
# AWS SES - Email Configuration
# =============================================================================
EMAIL_BACKEND = 'django_ses.SESBackend'
AWS_SES_REGION_NAME = config('AWS_SES_REGION_NAME', default='us-east-1')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@clinidocs.com')
SERVER_EMAIL = DEFAULT_FROM_EMAIL

# =============================================================================
# AWS TEXTRACT
# =============================================================================
AWS_TEXTRACT_REGION = config('AWS_TEXTRACT_REGION', default='us-east-1')

# =============================================================================
# SENTRY - Error Tracking (CRÍTICO)
# =============================================================================
SENTRY_DSN = config('SENTRY_DSN', default=None)
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration()],
        environment='production',
        traces_sample_rate=0.1,  # 10% de transacciones
        send_default_pii=False,  # No enviar datos personales
        before_send=lambda event, hint: event if not DEBUG else None,
    )

# =============================================================================
# LOGGING - CloudWatch Compatible
# =============================================================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(name)s %(levelname)s %(message)s',
        },
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'json',
        },
        'file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/clinidocs/error.log',
            'maxBytes': 1024 * 1024 * 10,  # 10 MB
            'backupCount': 5,
            'formatter': 'json',
        },
        'sentry': {
            'level': 'ERROR',
            'class': 'sentry_sdk.integrations.logging.EventHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file', 'sentry'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console', 'file', 'sentry'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# =============================================================================
# REST FRAMEWORK - Rate Limiting (Restrictivo)
# =============================================================================
REST_FRAMEWORK.update({
    'DEFAULT_THROTTLE_RATES': {
        'anon': config('THROTTLE_RATE_ANON', default='50/hour'),
        'user': config('THROTTLE_RATE_USER', default='500/hour'),
        'login': config('THROTTLE_RATE_LOGIN', default='5/hour'),
        'sensitive': '10/hour',
    },
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
})

# =============================================================================
# MIDDLEWARE - Compression & Security
# =============================================================================
MIDDLEWARE.insert(0, 'django.middleware.gzip.GZipMiddleware')

# =============================================================================
# AUDIT LOGGING
# =============================================================================
AUDIT_LOGGING_ENABLED = config('AUDIT_LOGGING_ENABLED', default=True, cast=bool)
AUDIT_LOG_RETENTION_DAYS = config('AUDIT_LOG_RETENTION_DAYS', default=365, cast=int)

# =============================================================================
# JWT Configuration
# =============================================================================
SIMPLE_JWT.update({
    'ACCESS_TOKEN_LIFETIME': timedelta(
        hours=config('JWT_ACCESS_TOKEN_LIFETIME_HOURS', default=1, cast=int)
    ),
    'REFRESH_TOKEN_LIFETIME': timedelta(
        days=config('JWT_REFRESH_TOKEN_LIFETIME_DAYS', default=7, cast=int)
    ),
})

# =============================================================================
# DEPLOYMENT INFO (para healthcheck)
# =============================================================================
DEPLOYMENT_VERSION = config('DEPLOYMENT_VERSION', default='unknown')
DEPLOYMENT_DATE = config('DEPLOYMENT_DATE', default='unknown')
