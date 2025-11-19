#!/usr/bin/env python
"""
Script para corregir datos de pacientes:
1. Asignar rol de "Paciente" a todos los pacientes
2. Generar emails únicos según el slug del tenant
   Ej: paciente1@hospital-santa-cruz.com, paciente2@hospital-santa-cruz.com

Ejecutar: python scripts/fix_patients_data.py
"""

import os
import sys
from pathlib import Path

# Setup Django
sys.path.insert(0, str(Path(__file__).parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')

import django
django.setup()

from django.contrib.auth import get_user_model
from apps.patients.models import Patient
from apps.accounts.models import Role
from apps.core.models import Tenant

User = get_user_model()

print("\n" + "="*80)
print("CORRIGIENDO DATOS DE PACIENTES")
print("="*80 + "\n")

# 1. Obtener el rol de Paciente
print("1. BUSCANDO ROL DE PACIENTE")
print("-" * 80)

try:
    patient_role = Role.objects.filter(name__icontains='paciente').first()
    if not patient_role:
        print("   ❌ No existe rol de Paciente")
        sys.exit(1)
    
    print(f"   ✓ Rol encontrado: {patient_role.name} (ID: {patient_role.id})")
    print()
except Exception as e:
    print(f"   ❌ Error: {e}")
    sys.exit(1)

# 2. Obtener todos los pacientes
print("2. OBTENIENDO PACIENTES")
print("-" * 80)

try:
    patients = Patient.objects.select_related('user', 'user__tenant').all()
    total_patients = patients.count()
    print(f"   Total pacientes en BD: {total_patients}")
    print()
except Exception as e:
    print(f"   ❌ Error: {e}")
    sys.exit(1)

if total_patients == 0:
    print("   ⚠️  No hay pacientes para corregir")
    sys.exit(0)

# 3. Agrupar pacientes por tenant
print("3. AGRUPANDO POR TENANT")
print("-" * 80)

patients_by_tenant = {}
for patient in patients:
    tenant = patient.user.tenant if patient.user else None
    if not tenant:
        print(f"   ⚠️  Paciente {patient.user.email} sin tenant asignado - OMITIDO")
        continue
    
    if tenant.id not in patients_by_tenant:
        patients_by_tenant[tenant.id] = []
    patients_by_tenant[tenant.id].append(patient)

print(f"   Tenants encontrados: {len(patients_by_tenant)}")
for tenant_id, patient_list in patients_by_tenant.items():
    tenant = Tenant.objects.get(id=tenant_id)
    print(f"      - {tenant.name} ({tenant.slug}): {len(patient_list)} pacientes")
print()

# 4. Corregir pacientes por tenant
print("4. CORRIGIENDO PACIENTES")
print("-" * 80)

total_corrected = 0
total_errors = 0

for tenant_id, patient_list in patients_by_tenant.items():
    tenant = Tenant.objects.get(id=tenant_id)
    print(f"\n   Tenant: {tenant.name} ({tenant.slug})")
    
    for idx, patient in enumerate(patient_list, 1):
        try:
            user = patient.user
            
            # Generar nuevo email con slug del tenant
            # paciente1@hospital-santa-cruz.com
            new_email = f"paciente{idx}@{tenant.slug}.com"
            
            # Actualizar usuario
            user.email = new_email
            user.username = new_email  # También username
            
            # Asignar rol de paciente
            user.role = patient_role
            
            user.save()
            
            print(f"      ✓ Paciente {idx}: {new_email} | Rol: {patient_role.name}")
            total_corrected += 1
            
        except Exception as e:
            print(f"      ❌ Error corrigiendo paciente {idx}: {str(e)}")
            total_errors += 1

print()
print("="*80)
print("RESULTADO FINAL")
print("="*80)
print(f"✓ Pacientes corregidos: {total_corrected}")
print(f"❌ Errores: {total_errors}")
print()

if total_errors == 0:
    print("✅ TODOS LOS PACIENTES CORREGIDOS CORRECTAMENTE")
else:
    print(f"⚠️  Hubo {total_errors} errores durante la corrección")

print()
