#!/usr/bin/env python
"""
Script para probar notificación real con Firebase.
Debe tener FIREBASE_SERVICE_ACCOUNT_KEY en .env

Uso:
    python scripts/test_notification_real.py
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

# Cargar variables de entorno desde .env
from dotenv import load_dotenv
load_dotenv()

from apps.accounts.models import User
from apps.notifications.orchestrator import NotificationOrchestrator

def send_test():
    print("=" * 80)
    print("📱 ENVIANDO NOTIFICACIÓN DE PRUEBA")
    print("=" * 80)
    
    # Obtener usuario admin
    user = User.objects.get(email='admin@clinica-lapaz.com')
    print(f"\n✅ Usuario: {user.full_name}")
    print(f"   Token FCM: {user.fcm_token[:50] if user.fcm_token else 'None'}...")
    
    if not user.fcm_token:
        print("\n❌ Usuario no tiene token FCM")
        return
    
    # Crear orquestador
    orchestrator = NotificationOrchestrator(user.tenant)
    
    # Enviar notificación de prueba usando process_event
    print("\n📤 Enviando notificación...")
    
    result = orchestrator.process_event(
        event_type='system.alert',
        event_id=f'test_{__import__("uuid").uuid4()}',
        actor_id=user.id,
        data={
            'message': '¡Las notificaciones push están funcionando correctamente!',
            'title': '🎉 Prueba de Notificación',
            'type': 'test',
        },
        channels=['push', 'in_app']
    )
    
    print(f"\n✅ Resultado: {result}")
    print("\n   Verifica tu celular en los próximos segundos.")
    print("=" * 80)

if __name__ == '__main__':
    send_test()
