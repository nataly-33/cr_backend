#!/usr/bin/env python
"""
Script para activar tenants de prueba y verificar su estado.
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

from apps.core.models import Tenant
from apps.tenants.models import SubscriptionPlan

print("\n" + "="*80)
print("VERIFICAR Y ACTIVAR TENANTS DE PRUEBA")
print("="*80)

# Listar todos los tenants
tenants = Tenant.objects.filter(deleted_at__isnull=True)

print(f"\n📊 Total de tenants: {tenants.count()}")

for tenant in tenants:
    print(f"\n🏥 {tenant.name}")
    print(f"   ID: {tenant.id}")
    print(f"   Status: {tenant.subscription_status}")
    print(f"   Plan: {tenant.subscription_plan}")
    
    # Activar si no está activo
    if tenant.subscription_status != 'active':
        print(f"   ⚠️  Cambiando estado a 'active'...")
        
        # Asignar un plan si no tiene
        if not tenant.subscription_plan:
            plan = SubscriptionPlan.objects.filter(is_active=True).first()
            if plan:
                tenant.subscription_plan = plan
                print(f"   ✅ Plan asignado: {plan.name}")
        
        tenant.subscription_status = 'active'
        tenant.save()
        print(f"   ✅ Tenant activado exitosamente")
    else:
        print(f"   ✅ Tenant ya está activo")

print("\n" + "="*80)
print("✅ Proceso completado")
print("="*80 + "\n")
