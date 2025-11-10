#!/usr/bin/env python
"""
Script para probar los endpoints con un usuario real del seeder.
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
print("PROBAR ENDPOINTS DEL FRONTEND")
print("="*80)

# Obtener usuario doctor
user = User.objects.filter(role__name='Doctor').first()

if not user:
    print("\n❌ No hay usuarios con rol 'Doctor'")
    sys.exit(1)

print(f"\n👤 Usuario: {user.email}")
print(f"   Tenant: {user.tenant}")
print(f"   Rol: {user.role.name}")

# Verificar permisos
if user.role:
    perms = list(user.role.permissions.values_list('code', flat=True))
    print(f"   Permisos del rol: {len(perms)} totales")
    print(f"   Primeros 5: {perms[:5]}")
else:
    perms = []
    print(f"   Permisos: Sin rol asignado")

has_payment_read = 'payment.read' in perms
has_invoice_read = 'invoice.read' in perms
print(f"   ✓ payment.read: {'✅' if has_payment_read else '❌'}")
print(f"   ✓ invoice.read: {'✅' if has_invoice_read else '❌'}")

# Crear token JWT
refresh = RefreshToken.for_user(user)
access_token = str(refresh.access_token)

print(f"\n🔐 Token JWT generado")

# Probar endpoints
client = APIClient()

# Usar headers con X-Tenant-ID para ayudar al middleware
headers = {
    'HTTP_AUTHORIZATION': f'Bearer {access_token}',
    'HTTP_X_TENANT_ID': str(user.tenant.id),
}

print("\n" + "-"*80)
print("ENDPOINT 1: Planes de Suscripción")
print("-"*80)

response = client.get(
    '/api/tenants/subscription-plans/',
    HTTP_AUTHORIZATION=f'Bearer {access_token}',
    HTTP_X_TENANT_ID=str(user.tenant.id)
)

print(f"GET /api/tenants/subscription-plans/")
print(f"Status: {response.status_code}")

if response.status_code == 200:
    plans = response.json()
    print(f"✅ {len(plans)} planes obtenidos:")
    for plan in plans:
        print(f"   - {plan['name']} (${plan['monthly_price']}/mes)")
else:
    print(f"❌ Error: {response.json()}")

print("\n" + "-"*80)
print("ENDPOINT 2: Pagos")
print("-"*80)

response = client.get(
    '/api/payments/',
    HTTP_AUTHORIZATION=f'Bearer {access_token}',
    HTTP_X_TENANT_ID=str(user.tenant.id)
)

print(f"GET /api/payments/")
print(f"Status: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    if isinstance(data, dict) and 'results' in data:
        payments = data['results']
        print(f"✅ {len(payments)} pagos obtenidos")
    else:
        print(f"✅ Response: {data}")
else:
    print(f"❌ Error: {response.json()}")

print("\n" + "-"*80)
print("ENDPOINT 3: Facturas")
print("-"*80)

response = client.get(
    '/api/payments/invoices/',
    HTTP_AUTHORIZATION=f'Bearer {access_token}',
    HTTP_X_TENANT_ID=str(user.tenant.id)
)

print(f"GET /api/payments/invoices/")
print(f"Status: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    if isinstance(data, dict) and 'results' in data:
        invoices = data['results']
        print(f"✅ {len(invoices)} facturas obtenidas")
    else:
        print(f"✅ Response: {data}")
else:
    print(f"❌ Error: {response.json()}")

print("\n" + "="*80)
print("✅ Prueba completada")
print("="*80 + "\n")
