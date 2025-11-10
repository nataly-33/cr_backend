#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from rest_framework.test import APIRequestFactory
from rest_framework.test import force_authenticate
from apps.patients.views import PatientViewSet
from apps.accounts.models import User
from apps.core.models import Tenant
from apps.patients.models import Patient
from datetime import date
import json
import random

# Get test tenant
tenant = Tenant.objects.get(slug='hospital-general-santa-cruz')
print(f"Testing with tenant: {tenant}\n")

# Get a doctor user
user = User.objects.filter(tenant=tenant, role__name__icontains='Doctor').first()
print(f"Testing with user: {user}\n")

# Create 3 new patients without clinical records
print("="*60)
print("Creating new patients without clinical records...")
print("="*60)

for i in range(1, 4):
    doc_id = f"{random.randint(10000000, 99999999)}"
    patient = Patient.objects.create(
        tenant=tenant,
        first_name=f"Nuevo{i}",
        last_name=f"Paciente{i}",
        identity_document=doc_id,
        gender="M",
        date_of_birth=date(1990, 1, 1),
        phone="123456789",
        email=f"new{i}@example.com"
    )
    print(f"✓ Creado: {patient.get_full_name()} (ID: {patient.identity_document})")

print(f"\n")

# Now test the endpoint
factory = APIRequestFactory()

print("="*60)
print("TEST: GET /patients/without_active_record/?search=Nuevo")
print("="*60)

request = factory.get('/api/patients/without_active_record/?search=Nuevo&page_size=10')
request.tenant = tenant
force_authenticate(request, user=user)

view = PatientViewSet.as_view({'get': 'without_active_record'})
response = view(request)

print(f"Status: {response.status_code}")
print(f"Patients found: {len(response.data.get('results', []))}\n")

if response.data.get('results'):
    print("Results:")
    for patient in response.data.get('results', []):
        print(f"  - {patient['full_name']} ({patient['identity_document']})")
else:
    print("No patients found")
