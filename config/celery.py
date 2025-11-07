"""
Celery configuration for CliniDocs.

Configura:
- Broker: Redis (para encolar tareas)
- Backend: Redis (para almacenar resultados)
- Beat Schedule: Tareas programadas
- Serialization: JSON para compatibilidad
"""

import os
import logging
from celery import Celery
from celery.schedules import crontab
from celery.signals import task_prerun, task_postrun, task_failure

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

# Create Celery app
app = Celery('clinidocs')

# Load configuration from Django settings using 'CELERY_' prefix
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from all registered Django apps
app.autodiscover_tasks()

# ============================================================================
# CONFIGURACIÓN DE TASKS
# ============================================================================

app.conf.task_track_started = True
app.conf.task_acks_late = True
app.conf.worker_prefetch_multiplier = 4
app.conf.worker_max_tasks_per_child = 1000

# ============================================================================
# BEAT SCHEDULE - TAREAS PROGRAMADAS
# ============================================================================

app.conf.beat_schedule = {
    # ========== BACKUP ==========
    'backup-sistema-diario': {
        'task': 'apps.backup.tasks.crear_backup_automatico',
        'schedule': crontab(hour=2, minute=0),  # 2:00 AM diarios
        'options': {
            'expires': 3600,  # Expira en 1 hora si no se ejecuta
            'queue': 'backups',
            'priority': 10,
        },
    },
    'limpiar-backups-vencidos': {
        'task': 'apps.backup.tasks.limpiar_backups_vencidos',
        'schedule': crontab(hour=3, minute=0, day_of_week=0),  # Domingo 3:00 AM
        'options': {
            'expires': 3600,
            'queue': 'backups',
            'priority': 10,
        },
    },
    
    # ========== NOTIFICACIONES ==========
    'reintentar-notificaciones-fallidas': {
        'task': 'apps.notifications.tasks.requeue_failed_notifications',
        'schedule': crontab(hour='*/6'),  # Cada 6 horas
        'options': {
            'expires': 1800,
            'queue': 'notifications',
            'priority': 5,
        },
    },
    'limpiar-notificaciones-antiguas': {
        'task': 'apps.notifications.tasks.cleanup_old_notifications',
        'schedule': crontab(hour=4, minute=0, day_of_week=0),  # Domingo 4:00 AM
        'options': {
            'expires': 3600,
            'queue': 'notifications',
            'priority': 5,
        },
    },
}

# ============================================================================
# COLAS (QUEUES) - Enrutamiento de tareas
# ============================================================================

from kombu import Queue, Exchange

# Define exchanges
default_exchange = Exchange('celery', type='direct')
backups_exchange = Exchange('backups', type='direct')
notifications_exchange = Exchange('notifications', type='direct')

app.conf.task_queues = (
    # Cola por defecto
    Queue(
        'celery',
        exchange=default_exchange,
        routing_key='celery',
        queue_arguments={'x-max-priority': 10}
    ),
    # Cola para backups (prioridad alta)
    Queue(
        'backups',
        exchange=backups_exchange,
        routing_key='backup.*',
        queue_arguments={'x-max-priority': 10}
    ),
    # Cola para notificaciones
    Queue(
        'notifications',
        exchange=notifications_exchange,
        routing_key='notification.*',
        queue_arguments={'x-max-priority': 10}
    ),
)

# Enrutamiento de tareas a colas específicas
app.conf.task_routes = {
    'apps.backup.tasks.*': {'queue': 'backups', 'priority': 10},
    'apps.notifications.tasks.*': {'queue': 'notifications', 'priority': 5},
}

# ============================================================================
# SERIALIZACIÓN
# ============================================================================

app.conf.task_serializer = 'json'
app.conf.result_serializer = 'json'
app.conf.accept_content = ['json']
app.conf.timezone = 'America/La_Paz'
app.conf.enable_utc = True

# Task result expiration
app.conf.result_expires = 3600  # 1 hora

# ============================================================================
# SIGNAL HANDLERS - Logging
# ============================================================================

logger = logging.getLogger(__name__)

@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, **kwargs):
    """Log cuando una tarea empieza"""
    logger.debug(f'✓ Tarea iniciada: {task.name} (ID: {task_id})')

@task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, result=None, **kwargs):
    """Log cuando una tarea termina exitosamente"""
    logger.debug(f'✓ Tarea completada: {task.name} (ID: {task_id})')

@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, **kwargs):
    """Log cuando una tarea falla"""
    logger.error(f'✗ Tarea fallida: {sender.name} (ID: {task_id}) - Error: {exception}')

# ============================================================================
# TEST TASK
# ============================================================================

@app.task(bind=True, name='celery.debug')
def debug_task(self):
    """
    Tarea de prueba para verificar que Celery funciona.
    
    Uso: celery -A config call celery.debug
    """
    print(f'✓ Celery está funcionando! Request: {self.request!r}')
    return {'status': 'ok', 'message': 'Celery funcionando correctamente'}
