"""
Script para verificar que Celery y Redis estan funcionando correctamente
"""
import os
import django
import sys

# Auto-detectar y agregar cr_backend a sys.path (para que funcione desde cualquier carpeta)
script_dir = os.path.dirname(os.path.abspath(__file__))  # carpeta scripts/
backend_dir = os.path.dirname(script_dir)  # carpeta cr_backend/
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')
django.setup()

from celery import current_app
from django.conf import settings


def check_redis_connection():
    """Verificar conexion a Redis"""
    print("=" * 60)
    print("[1] CHECKING REDIS CONNECTION")
    print("=" * 60)
    
    try:
        import redis
        
        # Parsear URL de Redis
        redis_url = getattr(settings, 'CELERY_BROKER_URL', settings.REDIS_URL)
        print(f"\n[URL] Redis URL: {redis_url}")
        
        # Conectar a Redis
        r = redis.from_url(redis_url)
        
        # Probar conexion
        r.ping()
        print("[OK] Redis connection successful")
        
        # Informacion del servidor
        info = r.info()
        print(f"[INFO] Redis version: {info['redis_version']}")
        print(f"[INFO] Connected clients: {info['connected_clients']}")
        print(f"[INFO] Memory used: {info['used_memory_human']}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Redis connection failed: {str(e)}")
        print("\n[SOLUTION]:")
        print("   1. Install Redis:")
        print("      - Windows: https://github.com/microsoftarchive/redis/releases")
        print("      - Or use Docker: docker run -d -p 6379:6379 redis")
        print("   2. Start Redis:")
        print("      redis-server")
        return False


def check_celery_config():
    """Verificar configuracion de Celery"""
    print("\n")
    print("=" * 60)
    print("[2] CHECKING CELERY CONFIGURATION")
    print("=" * 60)
    
    print(f"\n[CONFIG] Broker URL: {current_app.conf.broker_url}")
    print(f"[CONFIG] Result backend: {current_app.conf.result_backend}")
    print(f"[CONFIG] Task serializer: {current_app.conf.task_serializer}")
    print(f"[CONFIG] Timezone: {current_app.conf.timezone}")
    
    # Listar tareas registradas
    print(f"\n[LIST] Total registered tasks: {len(current_app.tasks)}")
    
    # Buscar tareas de documents
    doc_tasks = [name for name in current_app.tasks.keys() if 'documents' in name]
    if doc_tasks:
        print("\n[TASKS] Document tasks found:")
        for task in doc_tasks:
            print(f"  * {task}")
    else:
        print("\n[WARNING] No document tasks found")


def test_celery_task():
    """Probar ejecucion de tarea Celery"""
    print("\n")
    print("=" * 60)
    print("[3] TESTING CELERY TASK EXECUTION")
    print("=" * 60)
    
    try:
        from config.celery import debug_task
        
        print("\n[ACTION] Launching test task...")
        
        # Intentar lanzar tarea
        result = debug_task.delay()
        
        print(f"[OK] Task launched: {result.id}")
        print(f"[STATUS] State: {result.state}")
        
        if result.state == 'PENDING':
            print("\n[WARNING] Task is in PENDING state")
            print("   This means:")
            print("   1. Celery worker is NOT running, or")
            print("   2. Task has not been processed yet")
            print("\n[SOLUTION]:")
            print("   Open another terminal and run:")
            print("   celery -A config worker -l info")
        else:
            print(f"\n[OK] Celery worker is working")
        
        return result.state != 'PENDING'
        
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        return False


def check_ocr_task_available():
    """Verificar que la tarea de OCR este disponible"""
    print("\n")
    print("=" * 60)
    print("[4] CHECKING OCR TASK")
    print("=" * 60)
    
    try:
        from apps.documents.tasks import process_document_ocr
        
        print("\n[OK] OCR task found")
        print(f"   Name: {process_document_ocr.name}")
        print(f"   Max retries: {process_document_ocr.max_retries}")
        
        return True
        
    except ImportError as e:
        print(f"[ERROR] Failed to import OCR task: {str(e)}")
        return False


def main():
    print("\n")
    print("=" * 60)
    print("[DIAGNOSTIC] CELERY AND OCR PROCESSING DIAGNOSTIC")
    print("=" * 60)
    print("\n")
    
    # 1. Redis
    redis_ok = check_redis_connection()
    
    # 2. Configuracion Celery
    check_celery_config()
    
    # 3. Tarea OCR
    ocr_task_ok = check_ocr_task_available()
    
    # 4. Test de ejecucion
    if redis_ok:
        celery_ok = test_celery_task()
    else:
        celery_ok = False
    
    # Resumen
    print("\n")
    print("=" * 60)
    print("[SUMMARY] DIAGNOSTIC RESULTS")
    print("=" * 60)
    
    print(f"\n{'[OK]' if redis_ok else '[ERROR]'} Redis: {'Running' if redis_ok else 'Not available'}")
    print(f"{'[OK]' if ocr_task_ok else '[ERROR]'} OCR Task: {'Configured' if ocr_task_ok else 'Not found'}")
    print(f"{'[OK]' if celery_ok else '[ERROR]'} Celery Worker: {'Running' if celery_ok else 'Not running'}")
    
    if redis_ok and ocr_task_ok and celery_ok:
        print("\n[SUCCESS] ALL SYSTEMS OK! Automatic OCR should work")
    elif redis_ok and ocr_task_ok:
        print("\n[WARNING] Celery worker is NOT running")
        print("\n[INSTRUCTIONS] TO START CELERY:")
        print("   Open a new terminal and run:")
        print("   cd d:\\1NATALY\\Proyectos\\clinic_records\\cr_backend")
        print("   .\\venv\\Scripts\\Activate.ps1")
        print("   celery -A config worker -l info --pool=solo")
        print("\n   (Use --pool=solo on Windows)")
    else:
        print("\n[ERROR] There are configuration problems")
        print("   See error messages above")
    
    print()


if __name__ == '__main__':
    main()
