#!/usr/bin/env python
"""
Script para probar el endpoint de planes de suscripción.
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
from apps.tenants.models import SubscriptionPlan
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

print("\n" + "="*80)
print("PROBAR ENDPOINT DE PLANES")
print("="*80)

# Obtener usuario de prueba
user = User.objects.filter(is_active=True).first()

if not user:
    print("\n❌ No hay usuarios activos en la base de datos")
    sys.exit(1)

print(f"\n👤 Usuario: {user.email}")
print(f"   Tenant: {user.tenant}")
print(f"   ID: {user.id}")

# Crear token JWT
refresh = RefreshToken.for_user(user)
access_token = str(refresh.access_token)

print(f"\n🔐 Token JWT generado")
print(f"   (primeros 20 chars) {access_token[:20]}...")

# Probar endpoint
client = APIClient()

print(f"\n📡 Probando: GET /api/tenants/subscription-plans/")

response = client.get(
    '/api/tenants/subscription-plans/',
    HTTP_AUTHORIZATION=f'Bearer {access_token}'
)

print(f"   Status: {response.status_code}")

if response.status_code == 200:
    plans = response.json()
    print(f"   ✅ Éxito! {len(plans)} planes obtenidos:")
    for plan in plans:
        print(f"      - {plan['name']} (${plan['monthly_price']}/mes)")
else:
    print(f"   ❌ Error: {response.json()}")

print("\n" + "="*80 + "\n")
