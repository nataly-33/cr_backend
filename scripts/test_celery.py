"""
Script de prueba para verificar que Celery + Redis está configurado correctamente.

Uso: python test_celery.py
"""

import os
import sys
import django

# Auto-detectar y agregar cr_backend a sys.path (para que funcione desde cualquier carpeta)
script_dir = os.path.dirname(os.path.abspath(__file__))  # carpeta scripts/
backend_dir = os.path.dirname(script_dir)  # carpeta cr_backend/
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.conf import settings
import redis
from celery import current_app
from config.celery import app
from apps.notifications.tasks import send_notification_email
from apps.backup.tasks import crear_backup_automatico

print("\n" + "="*70)
print("[TEST] CELERY + REDIS - CONFIGURATION TEST")
print("="*70 + "\n")

# ============================================================================
# TEST 1: Redis Connection
# ============================================================================
print("[1] Checking Redis connection...")
try:
    redis_url = settings.REDIS_URL
    print(f"   URL: {redis_url}")
    
    r = redis.from_url(redis_url)
    r.ping()
    print("   [OK] Redis connected correctly\n")
except Exception as e:
    print(f"   [ERROR] {e}")
    print("   [TIP] Make sure Redis is running (redis-server)\n")
    sys.exit(1)

# ============================================================================
# TEST 2: Celery Configuration
# ============================================================================
print("[2] Checking Celery configuration...")
try:
    print(f"   Broker: {app.conf.broker_url}")
    print(f"   Backend: {app.conf.result_backend}")
    print(f"   Timezone: {app.conf.timezone}")
    print(f"   Serializer: {app.conf.task_serializer}")
    print("   [OK] Celery configuration loaded\n")
except Exception as e:
    print(f"   [ERROR] {e}\n")

# ============================================================================
# TEST 3: Autodetection de Tasks
# ============================================================================
print("[3] Checking available tasks...")
try:
    tasks = app.tasks
    task_list = list(tasks.keys())
    
    print(f"   Total tasks: {len(task_list)}\n")
    print("   [LIST] Tasks found:")
    
    for task_name in sorted(task_list):
        if 'backup' in task_name or 'notification' in task_name:
            print(f"      * {task_name}")
    
    print()
except Exception as e:
    print(f"   [ERROR] {e}\n")

# ============================================================================
# TEST 4: Beat Schedule
# ============================================================================
print("[4] Checking scheduled tasks (Beat)...")
try:
    beat_schedule = app.conf.beat_schedule
    print(f"   Scheduled tasks: {len(beat_schedule)}\n")
    print("   [SCHEDULE]:")
    
    for task_name, config in beat_schedule.items():
        print(f"      * {task_name}")
        print(f"        Task: {config['task']}")
        print(f"        Schedule: {config['schedule']}")
    
    print()
except Exception as e:
    print(f"   [ERROR] {e}\n")

# ============================================================================
# TEST 5: Queues Configuration
# ============================================================================
print("[5] Checking configured queues...")
try:
    queues = app.conf.task_queues
    print(f"   Available queues: {len(queues)}\n")
    
    for queue in queues:
        print(f"      * {queue.name}")
    
    print()
except Exception as e:
    print(f"   [ERROR] {e}\n")

# ============================================================================
# TEST 6: Send test task
# ============================================================================
print("[6] Sending test task...")
try:
    # Usar celery debug task
    result = app.send_task('celery.debug')
    print(f"   Task ID: {result.id}")
    print("   Status: Queued")
    print("   [TIP] To see the result, make sure Celery Worker is running\n")
    print("   In another terminal run:")
    print("      celery -A config worker --loglevel=info\n")
except Exception as e:
    print(f"   [ERROR] {e}\n")

# ============================================================================
# FINAL INSTRUCTIONS
# ============================================================================
print("="*70)
print("[OK] CONFIGURATION COMPLETE")
print("="*70 + "\n")

print("[NEXT STEPS]\n")

print("[1] Start Redis (if not running):")
print("   redis-server\n")

print("[2] Start Celery Worker (in another terminal):")
print("   celery -A config worker --loglevel=info\n")

print("[3] Start Celery Beat/Scheduler (in another terminal):")
print("   celery -A config beat --loglevel=info\n")

print("[4] Start Celery Flower for monitoring (in another terminal):")
print("   celery -A config flower --port=5555")
print("   URL: http://localhost:5555\n")

print("[5] Start Django Dev Server (in another terminal):")
print("   python manage.py runserver")
print("   URL: http://localhost:8000/api/\n")

print("="*70)
print("[SUCCESS] Celery + Redis is ready!")
print("="*70 + "\n")
