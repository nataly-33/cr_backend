#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from rest_framework.test import APIRequestFactory
from rest_framework.test import force_authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from apps.clinical_records.views import ClinicalRecordViewSet
from apps.clinical_records.models import ClinicalRecord
from apps.accounts.models import User
from apps.core.models import Tenant
from apps.patients.models import Patient
import json

# Get test tenant
all_tenants = Tenant.objects.all()
print(f"All tenants: {list(all_tenants.values_list('slug', flat=True))}")
tenant = Tenant.objects.get(slug='hospital-general-santa-cruz')
print(f"Testing with tenant: {tenant}")

# Get a user with doctor role
user = User.objects.filter(tenant=tenant, role__name__icontains='Doctor').first()
if not user:
    # Try admin
    user = User.objects.filter(tenant=tenant, role__name__icontains='Administrador').first()
print(f"Testing with user: {user}")

# Create a new patient for testing if needed
from datetime import date
from faker import Faker

fake = Faker('es_ES')

# Get a patient without active clinical record
all_patients = Patient.objects.filter(tenant=tenant)
patient = None
for p in all_patients:
    has_active = ClinicalRecord.objects.filter(
        tenant=tenant, 
        patient=p, 
        status='active'
    ).exists()
    if not has_active:
        patient = p
        break

# If all have active records, create a new patient
if not patient:
    patient = Patient.objects.create(
        tenant=tenant,
        first_name="Test",
        last_name="Patient",
        identity_document="99999999",
        gender="M",
        date_of_birth=date(1990, 1, 1),
        phone="123456789",
        email="testpatient@example.com"
    )
    print("Created new patient for testing")

print(f"Testing with patient: {patient}")

if tenant and user and patient:
    # Create factory and viewset
    factory = APIRequestFactory()
    
    # Prepare data
    data = {
        'patient': str(patient.id),
        'blood_type': 'O+',
        'allergies': [],
        'chronic_conditions': [],
        'medications': [],
        'family_history': 'Test family history',
        'social_history': 'Test social history',
    }
    
    print("\n" + "="*50)
    print("Creating POST request with data:")
    print(json.dumps(data, indent=2))
    print("="*50 + "\n")
    
    # Create POST request
    request = factory.post('/api/clinical-records/', data, format='json')
    request.tenant = tenant
    force_authenticate(request, user=user)
    
    # Call viewset
    view = ClinicalRecordViewSet.as_view({'post': 'create'})
    response = view(request)
    
    print(f"Response status: {response.status_code}")
    print(f"Response data: {response.data}")
else:
    print("Missing test data!")
