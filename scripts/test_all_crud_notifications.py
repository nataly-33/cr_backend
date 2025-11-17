#!/usr/bin/env python
"""
Script para verificar que todas las notificaciones CRUD funcionan correctamente.
"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from dotenv import load_dotenv
load_dotenv()

print("=" * 80)
print("✅ VERIFICACIÓN DE NOTIFICACIONES CRUD")
print("=" * 80)

# 1. Verificar templates
from apps.notifications.templates import TEMPLATES

required_events = [
    'document.created',
    'document.updated',
    'document.deleted',
    'clinical_record.created',
    'clinical_record.updated',
    'clinical_record.deleted',
    'clinical_form.created',
    'clinical_form.updated',
    'clinical_form.deleted',
]

print("\n📋 Verificando templates...")
for event in required_events:
    if event in TEMPLATES:
        print(f"  ✅ {event}: {TEMPLATES[event].title_es}")
    else:
        print(f"  ❌ {event}: FALTA TEMPLATE")

# 2. Verificar reglas de recipientes
from apps.notifications.orchestrator import NotificationOrchestrator
from apps.accounts.models import User

admin_user = User.objects.get(email='admin@clinica-lapaz.com')
orchestrator = NotificationOrchestrator(admin_user.tenant)

print("\n📋 Verificando reglas de destinatarios...")
for event in required_events:
    if event in orchestrator.RECIPIENT_RULES:
        print(f"  ✅ {event}: Regla definida")
    else:
        print(f"  ❌ {event}: FALTA REGLA")

# 3. Verificar que admins se resuelven correctamente
admin_ids = orchestrator._get_admin_user_ids()
print(f"\n👥 Admins encontrados: {len(admin_ids)}")
if admin_ids:
    admin = User.objects.get(id=admin_ids[0])
    print(f"  ✅ Admin principal: {admin.email}")
    print(f"  ✅ Token FCM: {'✓ Configurado' if admin.fcm_token else '✗ Sin token'}")
else:
    print("  ❌ No se encontraron admins")

print("\n" + "=" * 80)
print("✅ VERIFICACIÓN COMPLETADA")
print("=" * 80)
