#!/usr/bin/env python
"""
Script para probar la creación de un formulario clínico
"""
import os
import django
import json
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.clinical_records.models import ClinicalRecord, ClinicalForm
from apps.patients.models import Patient
from apps.accounts.models import User
from apps.core.models import Tenant, set_current_tenant

# Obtener tenant y usuario
tenant = Tenant.objects.first()
if not tenant:
    print("❌ No hay tenants disponibles")
    exit(1)

set_current_tenant(tenant)

# Obtener un usuario (doctor)
user = User.objects.filter(tenant=tenant).first()
if not user:
    print("❌ No hay usuarios en este tenant")
    exit(1)

# Obtener una historia clínica activa
clinical_record = ClinicalRecord.objects.filter(
    tenant=tenant,
    status='active'
).first()

if not clinical_record:
    print("⚠ No hay historias clínicas activas, creando una...")
    # Obtener un paciente
    patient = Patient.objects.filter(tenant=tenant).first()
    if not patient:
        print("❌ No hay pacientes en este tenant")
        exit(1)
    
    # Crear una historia clínica
    clinical_record = ClinicalRecord.objects.create(
        tenant=tenant,
        patient=patient,
        blood_type='O+',
        status='active',
        created_by=user
    )
    print(f"✓ Historia clínica creada: {clinical_record.record_number}")

print(f"✓ Tenant: {tenant.name}")
print(f"✓ Usuario: {user.get_full_name()}")
print(f"✓ Historia Clínica: {clinical_record.record_number}")

# Datos para el formulario de triaje
form_data = {
    'vital_signs': {
        'temperature': 36.5,
        'blood_pressure_systolic': 120,
        'blood_pressure_diastolic': 80,
        'heart_rate': 80,
        'respiratory_rate': 16,
        'oxygen_saturation': 98,
        'weight': 70,
        'height': 175,
    },
    'chief_complaint': 'Dolor de cabeza',
    'initial_assessment': 'Paciente con migraña',
    'triage_level': {
        'level': 3,
        'name': 'Urgente',
        'color': 'yellow'
    }
}

# Crear formulario
try:
    clinical_form = ClinicalForm.objects.create(
        tenant=tenant,
        clinical_record=clinical_record,
        form_type='triage',
        form_data=form_data,
        filled_by=user,
        form_date=datetime.now(),
        doctor_name=user.get_full_name(),
        doctor_specialty='Medicina General'
    )
    
    print(f"\n✅ Formulario creado exitosamente")
    print(f"   ID: {clinical_form.id}")
    print(f"   Tipo: {clinical_form.form_type}")
    print(f"   Historia: {clinical_form.clinical_record.record_number}")
    
except Exception as e:
    print(f"\n❌ Error al crear formulario:")
    print(f"   {str(e)}")
    import traceback
    traceback.print_exc()
