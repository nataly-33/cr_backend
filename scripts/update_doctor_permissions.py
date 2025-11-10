#!/usr/bin/env python
"""
Script para actualizar permisos del rol Doctor (agregar patient.create y patient.delete)
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

from apps.accounts.models import Role, Permission
from apps.core.models import Tenant

print("\n" + "="*80)
print("ACTUALIZAR PERMISOS DEL ROL DOCTOR")
print("="*80)

# Obtener todos los tenants
tenants = Tenant.objects.all()
print(f"\n📋 Tenants: {tenants.count()}")

updated_count = 0

for tenant in tenants:
    print(f"\n🏥 Tenant: {tenant.name}")
    
    try:
        # Buscar rol Doctor en este tenant
        doctor_role = Role.objects.get(tenant=tenant, name='Doctor')
        
        # Buscar permisos de pacientes
        patient_create = Permission.objects.get(tenant=tenant, code='patient.create')
        patient_delete = Permission.objects.get(tenant=tenant, code='patient.delete')
        
        # Obtener permisos actuales
        current_permissions = set(doctor_role.permissions.values_list('code', flat=True))
        
        # Agregar nuevos permisos si no los tiene
        added = []
        
        if 'patient.create' not in current_permissions:
            doctor_role.permissions.add(patient_create)
            added.append('patient.create')
        
        if 'patient.delete' not in current_permissions:
            doctor_role.permissions.add(patient_delete)
            added.append('patient.delete')
        
        if added:
            print(f"   ✅ Permisos agregados: {', '.join(added)}")
            updated_count += 1
        else:
            print(f"   ℹ️  Ya tenía todos los permisos")
            
    except Role.DoesNotExist:
        print(f"   ⚠️  No existe rol 'Doctor'")
    except Permission.DoesNotExist as e:
        print(f"   ❌ Error: {e}")

print("\n" + "="*80)
print(f"✅ Proceso completado - {updated_count} roles actualizados")
print("="*80 + "\n")
