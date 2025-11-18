#!/usr/bin/env python
"""
Script para probar notificaciones push manualmente
"""
import os
import django
import sys

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
django.setup()

from apps.notifications.models import NotificationToken, Notification
from apps.notifications.tasks import enviar_notificacion_push
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

def test_push_notification():
    """
    Prueba completa de notificaciones push
    """
    print("=" * 80)
    print("PRUEBA DE NOTIFICACIONES PUSH")
    print("=" * 80)
    
    # 1. Verificar tokens FCM registrados
    print("\n1. TOKENS FCM REGISTRADOS:")
    tokens = NotificationToken.objects.all()
    print(f"   Total de tokens: {tokens.count()}")
    for token in tokens[:5]:  # Mostrar primeros 5
        print(f"   - Usuario: {token.user.email}, Token: {token.token[:20]}..., Creado: {token.created_at}")
    
    if not tokens.exists():
        print("   ⚠️  NO HAY TOKENS FCM REGISTRADOS - La app móvil no se registró")
        return False
    
    # 2. Crear una notificación de prueba
    print("\n2. CREANDO NOTIFICACIÓN DE PRUEBA:")
    try:
        notification = Notification.objects.create(
            title="🧪 Test de Notificación",
            body="Esta es una notificación de prueba desde el backend",
            notification_type="test",
            created_by=User.objects.first()  # Primer admin
        )
        print(f"   ✓ Notificación creada: {notification.id}")
    except Exception as e:
        print(f"   ✗ Error al crear notificación: {e}")
        return False
    
    # 3. Enviar a todos los tokens
    print("\n3. ENVIANDO A TODOS LOS USUARIOS:")
    for token in tokens:
        try:
            print(f"\n   Enviando a {token.user.email}...")
            
            # Opción 1: Via tarea Celery (asíncrono)
            print(f"      → Disparando tarea Celery...")
            task = enviar_notificacion_push.delay(
                notification_id=notification.id,
                user_id=token.user.id
            )
            print(f"      ✓ Tarea Celery disparada: {task.id}")
            
            # Opción 2: Ejecutar síncronamente para ver errores inmediatamente
            print(f"      → Ejecutando síncronamente para diagnóstico...")
            try:
                from apps.notifications.services import firebase_service
                result = firebase_service.enviar_push_notification(
                    token_fcm=token.token,
                    titulo=notification.title,
                    body=notification.body,
                    datos={
                        "notification_id": str(notification.id),
                        "user_id": str(token.user.id)
                    }
                )
                if result.get('success'):
                    print(f"      ✓ Push enviado correctamente: {result}")
                else:
                    print(f"      ✗ Error al enviar: {result}")
            except Exception as e:
                print(f"      ✗ Excepción: {e}")
                import traceback
                traceback.print_exc()
                
        except Exception as e:
            print(f"   ✗ Error para {token.user.email}: {e}")
    
    print("\n" + "=" * 80)
    print("PRUEBA COMPLETADA")
    print("=" * 80)
    print("\nQué verificar:")
    print("  1. ¿Aparecen tareas en Celery? Ver: tail -f logs/celery.log")
    print("  2. ¿Hay errores de Firebase? Buscar 'firebase' en los logs")
    print("  3. ¿Llega el push a tu dispositivo? (app cerrada)")
    print("=" * 80)

if __name__ == '__main__':
    test_push_notification()
