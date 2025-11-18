#!/usr/bin/env python
"""
Script para ver logs en vivo cuando se elimina un documento
y verifica toda la cadena de notificaciones push
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
django.setup()

from dotenv import load_dotenv
load_dotenv()

import logging
from apps.accounts.models import User
from apps.notifications.models import Notification, NotificationStatus
from apps.documents.models import ClinicalDocument

# Configurar logging para ver TODO en tiempo real
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)

print("=" * 80)
print("🔍 MONITOREO DE ELIMINACIÓN DE DOCUMENTO")
print("=" * 80)

# 1. Buscar un documento para eliminar
print("\n1️⃣  BUSCANDO UN DOCUMENTO...")
try:
    doc = ClinicalDocument.objects.first()
    if not doc:
        print("   ❌ No hay documentos en la BD")
        sys.exit(1)
    
    print(f"   ✅ Documento encontrado:")
    print(f"      ID: {doc.id}")
    print(f"      Título: {doc.title}")
    print(f"      Paciente: {doc.clinical_record.patient.get_full_name()}")
    print(f"      Tenant: {doc.tenant.name}")
    
except Exception as e:
    print(f"   ❌ Error: {e}")
    sys.exit(1)

# 2. Contar notificaciones antes
print("\n2️⃣  CONTANDO NOTIFICACIONES ANTES...")
notifs_before = Notification.objects.count()
print(f"   Total de notificaciones: {notifs_before}")

# 3. Eliminar el documento
print("\n3️⃣  ELIMINANDO DOCUMENTO (esto debe disparar notificaciones)...")
print(f"   Eliminando: {doc.id}")
try:
    doc.delete()
    print(f"   ✅ Documento eliminado")
except Exception as e:
    print(f"   ❌ Error al eliminar: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 4. Contar notificaciones después
print("\n4️⃣  CONTANDO NOTIFICACIONES DESPUÉS...")
notifs_after = Notification.objects.count()
new_notifs = notifs_after - notifs_before
print(f"   Total de notificaciones: {notifs_after}")
print(f"   Nuevas notificaciones: {new_notifs}")

if new_notifs == 0:
    print("   ⚠️  NO SE CREARON NOTIFICACIONES - Problema en el signal")
else:
    print(f"   ✅ Se crearon {new_notifs} notificaciones")
    
    # 5. Mostrar las notificaciones creadas
    print("\n5️⃣  NOTIFICACIONES CREADAS:")
    recent_notifs = Notification.objects.order_by('-created_at')[:new_notifs]
    for i, notif in enumerate(recent_notifs, 1):
        print(f"\n      {i}. Notificación {notif.id}")
        print(f"         Usuario: {notif.user.email}")
        print(f"         Tipo: {notif.type}")
        print(f"         Canal: {notif.channel}")
        print(f"         Título: {notif.title}")
        print(f"         Status: {notif.status}")
        print(f"         FCM Token: {notif.user.fcm_token[:40] if notif.user.fcm_token else 'NO TIENE'}")
        
        if notif.channel == 'push':
            if not notif.user.fcm_token:
                print(f"         ⚠️  NO PUEDE ENVIAR PUSH: Usuario sin token FCM")
            else:
                print(f"         ✅ Puede enviar push")

# 6. Verificar tareas Celery
print("\n6️⃣  VERIFICANDO TAREAS CELERY:")
try:
    from celery import current_app
    
    # Ver tareas pendientes
    inspect = current_app.control.inspect()
    active_tasks = inspect.active()
    
    if active_tasks:
        for worker, tasks in active_tasks.items():
            print(f"   Worker: {worker}")
            for task in tasks[:5]:  # Primeras 5 tareas
                print(f"      - {task['name']}")
    else:
        print("   No hay tareas activas en Celery")
    
    # Ver cola
    reserved = inspect.reserved()
    if reserved:
        print(f"   Tareas reservadas/pendientes: {reserved}")
    
except Exception as e:
    print(f"   Error verificando Celery: {e}")

# 7. Ver logs de Celery si está disponible
print("\n7️⃣  PRÓXIMOS PASOS:")
print(f"""
   En otro terminal, ejecuta para ver logs en vivo:
   
   tail -f /home/ubuntu/clinic_records/cr_backend/logs/celery.log
   
   Deberías ver:
   - "Push notification XXX enqueued for sending"
   - "✅ Push sent to admin@clinica-lapaz.com"
   
   Si NO ves eso:
   - Celery no está procesando tareas
   - Revisa que el worker esté corriendo
   - Ver: systemctl status celery
   
   En tu móvil:
   - Si el Push llega: ✅ Todo funciona
   - Si NO llega: Token FCM inválido o Firebase mal configurado
""")

print("=" * 80)
