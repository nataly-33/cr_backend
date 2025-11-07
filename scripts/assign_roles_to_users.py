#!/usr/bin/env python
"""
Script para asignar rol a usuarios sin rol.
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
from apps.accounts.models import Role
from apps.accounts.constants import SystemRoles

User = get_user_model()

print("\n" + "="*80)
print("ASIGNAR ROLES A USUARIOS SIN ROL")
print("="*80)

# Encontrar usuarios sin rol
users_without_role = User.objects.filter(role__isnull=True, is_active=True)

print(f"\n👥 Usuarios sin rol: {users_without_role.count()}")

for user in users_without_role:
    print(f"\n📝 {user.email}")
    print(f"   Tenant: {user.tenant}")
    
    if not user.tenant:
        print(f"   ⚠️  No tiene tenant asignado, saltando...")
        continue
    
    # Asignar rol de Doctor al tenant
    try:
        doctor_role = Role.objects.get(
            tenant=user.tenant,
            name='Doctor'
        )
        user.role = doctor_role
        user.save()
        print(f"   ✅ Rol asignado: Doctor")
    except Role.DoesNotExist:
        print(f"   ❌ No existe rol 'Doctor' para este tenant")

print("\n" + "="*80)
print("✅ Proceso completado")
print("="*80 + "\n")
