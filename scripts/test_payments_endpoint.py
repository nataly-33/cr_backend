#!/usr/bin/env python
"""
Script para probar el endpoint de pagos.
"""

import os
import sys
import django
from pathlib import Path

# Setup Django
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

print("\n" + "="*80)
print("PROBAR ENDPOINT DE PAGOS")
print("="*80)

# Obtener usuario de prueba
user = User.objects.filter(is_active=True).first()

if not user:
    print("\n❌ No hay usuarios activos en la base de datos")
    sys.exit(1)

print(f"\n👤 Usuario: {user.email}")
print(f"   Tenant: {user.tenant}")
print(f"   Rol: {user.role}")

# Verificar permisos
from apps.accounts.models import Permission
perms = user.get_all_permissions()
print(f"   Permisos: {len(perms)} totales")

has_payment_read = 'payment.read' in perms
print(f"   ✓ payment.read: {'✅' if has_payment_read else '❌'}")

# Crear token JWT
refresh = RefreshToken.for_user(user)
access_token = str(refresh.access_token)

print(f"\n🔐 Token JWT generado")

# Probar endpoint
client = APIClient()

print(f"\n📡 Probando: GET /api/payments/")

response = client.get(
    '/api/payments/',
    HTTP_AUTHORIZATION=f'Bearer {access_token}'
)

print(f"   Status: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    if isinstance(data, dict) and 'results' in data:
        payments = data['results']
        print(f"   ✅ Éxito! {len(payments)} pagos obtenidos")
    else:
        print(f"   ✅ Éxito! Response: {data}")
else:
    print(f"   ❌ Error: {response.json()}")

print("\n" + "="*80 + "\n")
