import os
from celery import Celery
from celery.schedules import crontab

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

# Create Celery app
app = Celery('clinidocs')

# Load configuration from Django settings using 'CELERY_' prefix
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from all registered Django apps
app.autodiscover_tasks()

# Configure periodic tasks (beat schedule)
app.conf.beat_schedule = {
    # Backup automático diario a las 2:00 AM
    'backup-diario': {
        'task': 'apps.backup.tasks.crear_backup_automatico',
        'schedule': crontab(hour=2, minute=0),
        'options': {'expires': 3600},  # Expira en 1 hora si no se ejecuta
    },
    # Limpieza de backups antiguos cada domingo a las 3:00 AM
    'limpiar-backups-antiguos': {
        'task': 'apps.backup.tasks.limpiar_backups_vencidos',
        'schedule': crontab(hour=3, minute=0, day_of_week=0),
    },
}

# Task serialization format
app.conf.task_serializer = 'json'
app.conf.result_serializer = 'json'
app.conf.accept_content = ['json']
app.conf.timezone = 'America/Costa_Rica'
app.conf.enable_utc = True

# Task result expiration
app.conf.result_expires = 3600

@app.task(bind=True)
def debug_task(self):
    """Task de prueba para verificar que Celery funciona"""
    print(f'Request: {self.request!r}')
