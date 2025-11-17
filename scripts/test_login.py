"""
Test rápido para verificar que el login funciona
"""

import os
import sys
import django
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from apps.core.models import Tenant

User = get_user_model()

print("\n" + "="*80)
print("TEST: Login Backend")
print("="*80)

# 1. Crear tenant
tenant, created = Tenant.objects.get_or_create(
    subdomain='test-clinic',
    defaults={
        'name': 'Test Clinic',
        'email': 'test@clinic.com',
        'phone': '+591 2 123456',
        'address': 'Test Address',
    }
)
print(f"✅ Tenant: {tenant.name}")

# 2. Crear usuario
user, created = User.objects.get_or_create(
    email='testuser@example.com',
    defaults={
        'first_name': 'Test',
        'last_name': 'User',
        'tenant': tenant,
        'is_active': True,
    }
)
if created:
    user.set_password('TestPassword123!')
    user.save()
    print(f"✅ Usuario creado: {user.email}")
else:
    print(f"✅ Usuario existente: {user.email}")

# 3. Hacer login via API
client = APIClient()
response = client.post('/api/login/', {
    'email': 'testuser@example.com',
    'password': 'TestPassword123!'
})

if response.status_code == 200:
    print(f"✅ Login exitoso! Status: {response.status_code}")
    data = response.json()
    print(f"   - Token de acceso: {data.get('access', '')[:50]}...")
    print(f"   - Token de refresco: {data.get('refresh', '')[:50]}...")
else:
    print(f"❌ Error en login: {response.status_code}")
    print(f"   Respuesta: {response.json()}")

print("\n" + "="*80)
print("Test completado")
print("="*80 + "\n")
