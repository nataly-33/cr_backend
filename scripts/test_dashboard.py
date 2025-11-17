"""
Test simple para validar que el endpoint del dashboard funciona
"""

import os
import sys
import django
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from apps.core.models import Tenant
from apps.core.permissions import PermissionCodes

User = get_user_model()


def test_dashboard_endpoints():
    """Test que valida que el endpoint del dashboard existe y es accesible"""
    
    print("\n" + "="*80)
    print("Probando endpoints del Dashboard...")
    print("="*80)
    
    client = APIClient()
    
    # 1. Crear un tenant de prueba
    tenant, created = Tenant.objects.get_or_create(
        subdomain='test-clinic',
        defaults={
            'name': 'Test Clinic',
            'email': 'test@clinic.com',
            'phone': '+591 2 123456',
            'address': 'Test Address',
        }
    )
    print(f"\n✅ Tenant: {tenant.name}")
    
    # 2. Crear un usuario de prueba
    user, created = User.objects.get_or_create(
        email='test@test.com',
        defaults={
            'first_name': 'Test',
            'last_name': 'User',
            'tenant': tenant,
            'is_active': True,
        }
    )
    if created:
        user.set_password('TestPass123!')
        user.save()
    print(f"✅ Usuario: {user.email}")
    
    # 3. Autenticar cliente
    client.force_authenticate(user=user)
    client.defaults['HTTP_X_TENANT_ID'] = str(tenant.id)
    
    # 4. Probar endpoints
    endpoints = [
        'overview',
        'activity',
        'documents_stats',
        'forms_stats',
        'users_activity',
    ]
    
    for endpoint in endpoints:
        url = f'/api/dashboard/{endpoint}/'
        print(f"\n  Probando GET {url}")
        
        response = client.get(url)
        
        if response.status_code == 200:
            print(f"    ✅ Éxito! Status: {response.status_code}")
            print(f"    Respuesta parcial: {str(response.json())[:100]}...")
        elif response.status_code == 401:
            print(f"    ⚠️  No autenticado (401)")
        elif response.status_code == 403:
            print(f"    ⚠️  Permiso denegado (403)")
            print(f"    Error: {response.json()}")
        else:
            print(f"    ❌ Error: {response.status_code}")
            print(f"    Respuesta: {response.json()}")
    
    print("\n" + "="*80)
    print("Prueba completada!")
    print("="*80)


if __name__ == '__main__':
    test_dashboard_endpoints()
