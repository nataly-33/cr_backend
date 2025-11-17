from .base import *

DEBUG = True

# ALLOWED_HOSTS para desarrollo (incluye dirección del emulador Android)
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '10.0.2.2', '0.0.0.0', '192.168.100.7', '10.217.24.172']

# Disable password validation in development
AUTH_PASSWORD_VALIDATORS = []

# Celery - Always eager in development (synchronous)
CELERY_TASK_ALWAYS_EAGER = config('CELERY_TASK_ALWAYS_EAGER', default=False, cast=bool)
CELERY_TASK_EAGER_PROPAGATES = True

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'celery': {
            'handlers': ['console'],
            'level': 'INFO',
        },
    },
}