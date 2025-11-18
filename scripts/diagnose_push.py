#!/usr/bin/env python
"""
Script de diagnóstico para notificaciones push en producción
"""
import os
import sys
import django
import json

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
django.setup()

from dotenv import load_dotenv
load_dotenv()

print("=" * 80)
print("🔍 DIAGNÓSTICO DE NOTIFICACIONES PUSH")
print("=" * 80)

# 1. Verificar Firebase configurado
print("\n1️⃣  VERIFICANDO CONFIGURACIÓN DE FIREBASE:")
try:
    firebase_key = os.getenv('FIREBASE_SERVICE_ACCOUNT_KEY')
    if not firebase_key:
        print("   ❌ FIREBASE_SERVICE_ACCOUNT_KEY no está en .env")
    else:
        # Verificar que es JSON válido
        try:
            key_dict = json.loads(firebase_key)
            print(f"   ✅ Firebase Service Account Key configurado")
            print(f"      Project ID: {key_dict.get('project_id')}")
            print(f"      Client Email: {key_dict.get('client_email')}")
        except json.JSONDecodeError:
            print("   ❌ FIREBASE_SERVICE_ACCOUNT_KEY no es JSON válido")
except Exception as e:
    print(f"   ❌ Error: {e}")

# 2. Verificar Firebase inicializado
print("\n2️⃣  INICIALIZANDO FIREBASE:")
try:
    import firebase_admin
    from firebase_admin import credentials, messaging
    
    if not firebase_admin._apps:
        print("   → Inicializando Firebase Admin SDK...")
        cred = credentials.Certificate(json.loads(firebase_key))
        firebase_admin.initialize_app(cred)
        print("   ✅ Firebase Admin SDK inicializado")
    else:
        print("   ✅ Firebase Admin SDK ya estaba inicializado")
except Exception as e:
    print(f"   ❌ Error inicializando Firebase: {e}")
    sys.exit(1)

# 3. Verificar tokens FCM en BD
print("\n3️⃣  BUSCANDO TOKENS FCM EN BD:")
try:
    from apps.accounts.models import User
    users_with_fcm = User.objects.exclude(fcm_token__isnull=True).exclude(fcm_token='')
    print(f"   Total de usuarios con token FCM: {users_with_fcm.count()}")
    
    if users_with_fcm.exists():
        print("   Primeros 5 usuarios:")
        for i, user in enumerate(users_with_fcm[:5], 1):
            print(f"      {i}. Usuario: {user.email}")
            print(f"         Token: {user.fcm_token[:40]}...")
    else:
        print("   ⚠️  NO HAY TOKENS FCM - La app móvil no se registró")
except Exception as e:
    print(f"   ❌ Error consultando tokens: {e}")
    import traceback
    traceback.print_exc()

# 4. Probar envío de notificación
print("\n4️⃣  PROBANDO ENVÍO DE NOTIFICACIÓN PUSH:")
try:
    from apps.accounts.models import User
    
    users_with_fcm = User.objects.exclude(fcm_token__isnull=True).exclude(fcm_token='')
    if not users_with_fcm.exists():
        print("   ⚠️  No hay usuarios con token para probar")
    else:
        user = users_with_fcm.first()
        fcm_token = user.fcm_token
        
        print(f"   Enviando a: {user.email}")
        print(f"   Token: {fcm_token[:40]}...")
        
        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title="🧪 Prueba de Notificación",
                    body="Si ves esto, ¡las notificaciones funcionan!",
                ),
                data={
                    "notification_type": "test",
                    "timestamp": str(__import__('django').utils.timezone.now()),
                },
                token=fcm_token,
            )
            
            response = messaging.send(message)
            print(f"\n   ✅ NOTIFICACIÓN ENVIADA EXITOSAMENTE")
            print(f"      Message ID: {response}")
            print(f"\n   🔔 Revisa tu celular en 5 segundos")
            
        except Exception as firebase_error:
            print(f"   ❌ Error de Firebase: {firebase_error}")
            print(f"\n   Posibles causas:")
            print(f"      - Token FCM expirado o inválido")
            print(f"      - App no registrada en Firebase Console")
            print(f"      - Credenciales de Firebase incorrectas")
            
except Exception as e:
    print(f"   ❌ Error en prueba: {e}")
    import traceback
    traceback.print_exc()

# 5. Verificar Celery
print("\n5️⃣  VERIFICANDO CELERY:")
try:
    from celery import current_app
    print(f"   Broker: {current_app.conf.broker_url}")
    print(f"   Backend: {current_app.conf.result_backend}")
    
    # Intentar conectar a Redis
    import redis
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    r = redis.from_url(redis_url)
    ping = r.ping()
    if ping:
        print(f"   ✅ Redis está disponible")
    else:
        print(f"   ❌ Redis no responde")
        
except Exception as e:
    print(f"   ❌ Error verificando Celery: {e}")

# 6. Resumen
print("\n" + "=" * 80)
print("📋 RESUMEN DE DIAGNÓSTICO")
print("=" * 80)
print("""
Para que las notificaciones push funcionen necesitas:

1. ✅ Firebase Service Account Key en .env (FIREBASE_SERVICE_ACCOUNT_KEY)
2. ✅ Tokens FCM registrados en la BD (desde la app móvil)
3. ✅ Redis corriendo (para Celery)
4. ✅ Celery Worker corriendo
5. ✅ Token FCM válido y no expirado

Si NO ves tokens FCM, significa que la app móvil no se registró.
Debes:
  1. Instalar la app en el dispositivo
  2. Hacer login
  3. Otorgar permisos de notificaciones
  4. Ver que el token se registre en la BD

Si ves tokens pero NO llega la notificación:
  - Revisa que Firebase está inicializado correctamente
  - Verifica que el token no está expirado
  - Revisa los logs de Celery: tail -f logs/celery.log
""")
print("=" * 80)
