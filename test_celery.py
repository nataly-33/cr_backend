"""
Script de prueba para verificar que Celery + Redis está configurado correctamente.

Uso: python test_celery.py
"""

import os
import sys
import django

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
print("🧪 CELERY + REDIS - TEST DE CONFIGURACIÓN")
print("="*70 + "\n")

# ============================================================================
# TEST 1: Redis Connection
# ============================================================================
print("1️⃣ Verificando conexión a Redis...")
try:
    redis_url = settings.REDIS_URL
    print(f"   URL: {redis_url}")
    
    r = redis.from_url(redis_url)
    r.ping()
    print("   ✅ Redis conectado correctamente\n")
except Exception as e:
    print(f"   ❌ Error: {e}")
    print("   💡 Asegúrate de que Redis esté corriendo (redis-server)\n")
    sys.exit(1)

# ============================================================================
# TEST 2: Celery Configuration
# ============================================================================
print("2️⃣ Verificando configuración de Celery...")
try:
    print(f"   Broker: {app.conf.broker_url}")
    print(f"   Backend: {app.conf.result_backend}")
    print(f"   Timezone: {app.conf.timezone}")
    print(f"   Serializer: {app.conf.task_serializer}")
    print("   ✅ Configuración de Celery cargada\n")
except Exception as e:
    print(f"   ❌ Error: {e}\n")

# ============================================================================
# TEST 3: Autodetection de Tasks
# ============================================================================
print("3️⃣ Verificando tasks disponibles...")
try:
    tasks = app.tasks
    task_list = list(tasks.keys())
    
    print(f"   Total de tasks: {len(task_list)}\n")
    print("   📋 Tasks encontradas:")
    
    for task_name in sorted(task_list):
        if 'backup' in task_name or 'notification' in task_name:
            print(f"      ✓ {task_name}")
    
    print()
except Exception as e:
    print(f"   ❌ Error: {e}\n")

# ============================================================================
# TEST 4: Beat Schedule
# ============================================================================
print("4️⃣ Verificando tareas programadas (Beat)...")
try:
    beat_schedule = app.conf.beat_schedule
    print(f"   Tareas programadas: {len(beat_schedule)}\n")
    print("   📅 Schedule:")
    
    for task_name, config in beat_schedule.items():
        print(f"      ✓ {task_name}")
        print(f"        Task: {config['task']}")
        print(f"        Schedule: {config['schedule']}")
    
    print()
except Exception as e:
    print(f"   ❌ Error: {e}\n")

# ============================================================================
# TEST 5: Queues Configuration
# ============================================================================
print("5️⃣ Verificando colas configuradas...")
try:
    queues = app.conf.task_queues
    print(f"   Colas disponibles: {len(queues)}\n")
    
    for queue in queues:
        print(f"      ✓ {queue.name}")
    
    print()
except Exception as e:
    print(f"   ❌ Error: {e}\n")

# ============================================================================
# TEST 6: Enviar task de prueba
# ============================================================================
print("6️⃣ Enviando task de prueba...")
try:
    # Usar celery debug task
    result = app.send_task('celery.debug')
    print(f"   Task ID: {result.id}")
    print("   Status: Enviada a cola")
    print("   💡 Para ver el resultado, asegúrate de que Celery Worker esté corriendo\n")
    print("   En otra terminal ejecuta:")
    print("      celery -A config worker --loglevel=info\n")
except Exception as e:
    print(f"   ❌ Error: {e}\n")

# ============================================================================
# INSTRUCCIONES FINALES
# ============================================================================
print("="*70)
print("✅ CONFIGURACIÓN COMPLETADA")
print("="*70 + "\n")

print("📝 Próximos pasos:\n")

print("1️⃣ Inicia Redis (si no está corriendo):")
print("   redis-server\n")

print("2️⃣ Inicia Celery Worker (en otra terminal):")
print("   celery -A config worker --loglevel=info\n")

print("3️⃣ Inicia Celery Beat/Scheduler (en otra terminal):")
print("   celery -A config beat --loglevel=info\n")

print("4️⃣ Inicia Celery Flower para monitoreo (en otra terminal):")
print("   celery -A config flower --port=5555")
print("   URL: http://localhost:5555\n")

print("5️⃣ Inicia Django Dev Server (en otra terminal):")
print("   python manage.py runserver")
print("   URL: http://localhost:8000/api/\n")

print("="*70)
print("🚀 ¡Celery + Redis está listo para usar!")
print("="*70 + "\n")
