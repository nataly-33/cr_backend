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
from apps.clinical_records.models import ClinicalRecord
import json

# Get test tenant
tenant = Tenant.objects.get(slug='hospital-general-santa-cruz')
print(f"Testing with tenant: {tenant}\n")

# Get a doctor user
user = User.objects.filter(tenant=tenant, role__name__icontains='Doctor').first()
print(f"Testing with user: {user}\n")

# Create factory and viewset
factory = APIRequestFactory()

# Test 1: Get all patients (with active records)
print("="*60)
print("TEST 1: GET /patients/")
print("="*60)
request = factory.get('/api/patients/')
request.tenant = tenant
force_authenticate(request, user=user)

view = PatientViewSet.as_view({'get': 'list'})
response = view(request)

print(f"Status: {response.status_code}")
total_patients = response.data['count'] if hasattr(response.data, '__getitem__') else 0
print(f"Total patients: {total_patients}\n")

# Test 2: Get patients WITHOUT active clinical records
print("="*60)
print("TEST 2: GET /patients/without_active_record/?search=")
print("="*60)

request = factory.get('/api/patients/without_active_record/?search=&page_size=10')
request.tenant = tenant
force_authenticate(request, user=user)

view = PatientViewSet.as_view({'get': 'without_active_record'})
response = view(request)

print(f"Status: {response.status_code}")
print(f"Patients without active record: {len(response.data.get('results', []))}")
print(f"\nSample data:")
if response.data.get('results'):
    print(json.dumps({
        'id': str(response.data['results'][0]['id']),
        'full_name': response.data['results'][0]['full_name'],
        'identity_document': response.data['results'][0]['identity_document'],
    }, indent=2, ensure_ascii=False))
else:
    print("No patients found without active record")

# Test 3: Verify by checking which patients have active records
print("\n" + "="*60)
print("DEBUG: Patients with active clinical records")
print("="*60)

active_record_count = ClinicalRecord.objects.filter(
    tenant=tenant,
    status='active',
    deleted_at__isnull=True
).values('patient').distinct().count()

print(f"Total patients with active records: {active_record_count}")
print(f"Total patients without active records: {total_patients - active_record_count}")
