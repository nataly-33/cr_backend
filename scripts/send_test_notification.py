#!/usr/bin/env python
"""
Script para enviar una notificación de prueba al usuario admin.

Uso:
    python scripts/send_test_notification.py

Ejecutar desde el directorio cr_backend/
"""
import os
import sys
import django
import json

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.accounts.models import User
import firebase_admin
from firebase_admin import credentials, messaging


def send_test_notification():
    """Envía una notificación de prueba al usuario admin."""
    
    print("=" * 80)
    print("📱 ENVIANDO NOTIFICACIÓN DE PRUEBA")
    print("=" * 80)
    
    # 1. Obtener el usuario
    try:
        user = User.objects.get(email='admin@clinica-lapaz.com')
        print(f"\n✅ Usuario encontrado: {user.full_name}")
    except User.DoesNotExist:
        print("\n❌ Usuario no encontrado")
        return False
    
    # 2. Verificar que tiene token
    if not user.fcm_token:
        print("❌ El usuario no tiene token FCM guardado")
        print("   Solución: Haz login en la app móvil y espera a que se guarde el token")
        return False
    
    print(f"✅ Token FCM encontrado")
    print(f"   {user.fcm_token[:50]}...")
    
    # 3. Inicializar Firebase
    try:
        # Limpiar apps previas si existen
        for app in firebase_admin._apps.values():
            firebase_admin.delete_app(app)
        
        # Obtener credenciales de variables de entorno
        cred_json = os.getenv('FIREBASE_SERVICE_ACCOUNT_KEY')
        
        if not cred_json:
            print("\n❌ FIREBASE_SERVICE_ACCOUNT_KEY no está definida")
            print("   Verifica que está en tu archivo .env")
            return False
        
        cred_dict = json.loads(cred_json)
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
        
        print("✅ Firebase inicializado correctamente")
    except Exception as e:
        print(f"\n❌ Error inicializando Firebase: {e}")
        return False
    
    # 4. Crear y enviar mensaje
    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title='🎉 Prueba de Notificación',
                body='¡Las notificaciones push funcionan correctamente!',
            ),
            data={
                'type': 'test',
                'timestamp': str(__import__('datetime').datetime.now()),
            },
            token=user.fcm_token,
        )
        
        print("\n📤 Enviando notificación...")
        response = messaging.send(message)
        
        print(f"\n✅ NOTIFICACIÓN ENVIADA CON ÉXITO")
        print(f"   Message ID: {response}")
        print(f"\n   Verifica tu celular en los próximos segundos para recibir la notificación.")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error enviando notificación: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        print("\n" + "=" * 80)


if __name__ == "__main__":
    success = send_test_notification()
    sys.exit(0 if success else 1)
