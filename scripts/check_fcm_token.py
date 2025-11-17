#!/usr/bin/env python
"""
Script para verificar el token FCM de un usuario en la base de datos.

Uso:
    python scripts/check_fcm_token.py

Ejecutar desde el directorio cr_backend/
"""
import os
import sys
import django

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.accounts.models import User

def check_fcm_token():
    """Verifica el token FCM del usuario admin."""
    email = "admin@clinica-lapaz.com"
    
    try:
        user = User.objects.get(email=email)
        
        print("=" * 80)
        print(f"📱 TOKEN FCM PARA: {user.full_name} ({user.email})")
        print("=" * 80)
        
        if user.fcm_token:
            print(f"\n✅ TOKEN ENCONTRADO:")
            print(f"   Longitud: {len(user.fcm_token)} caracteres")
            print(f"   Primeros 50 chars: {user.fcm_token[:50]}...")
            print(f"   Últimos 20 chars: ...{user.fcm_token[-20:]}")
            print(f"\n📊 DETALLES DEL USUARIO:")
            print(f"   ID: {user.id}")
            print(f"   Role: {user.role_name}")
            print(f"   Active: {user.is_active}")
            print(f"   Last Login: {user.last_login}")
        else:
            print("\n❌ TOKEN NO ENCONTRADO (es None o vacío)")
            print("\n🔍 POSIBLES CAUSAS:")
            print("   1. El usuario no ha hecho login desde la app móvil")
            print("   2. Firebase no está inicializado correctamente")
            print("   3. No se enviaron permisos de notificación")
            print("   4. Error en el envío del token al backend")
        
        print("\n" + "=" * 80)
        
    except User.DoesNotExist:
        print(f"❌ Usuario con email '{email}' no existe")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_fcm_token()
