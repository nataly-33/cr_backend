"""
Pytest fixtures y configuraciones para tests de reports

Este archivo es autodescubierto por pytest.
"""

import pytest
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.core.models import Tenant, set_current_tenant
from apps.accounts.models import User, Role, Permission
from apps.patients.models import Patient
from apps.clinical_records.models import ClinicalRecord
from apps.documents.models import ClinicalDocument
from datetime import datetime, timedelta
from django.utils import timezone

User = get_user_model()


@pytest.fixture
def tenant():
    """Crea un tenant de prueba"""
    tenant_obj = Tenant.objects.create(
        name='Test Hospital',
        slug='test-hospital',
        subdomain='test'
    )
    set_current_tenant(tenant_obj)
    return tenant_obj


@pytest.fixture
def admin_role(tenant):
    """Crea un rol de administrador"""
    role = Role.objects.create(
        tenant=tenant,
        name='Administrador',
        description='Admin del tenant'
    )
    # Agregar permisos
    perms = Permission.objects.filter(code__in=[
        'patient.create', 'patient.read', 'patient.update', 'patient.delete',
        'clinical_record.create', 'clinical_record.read',
        'document.create', 'document.read', 'document.sign',
        'user.create', 'user.read', 'user.update',
        'role.read', 'report.create', 'report.read'
    ])
    role.permissions.set(perms)
    return role


@pytest.fixture
def doctor_role(tenant):
    """Crea un rol de doctor"""
    role = Role.objects.create(
        tenant=tenant,
        name='Doctor',
        description='Doctor del tenant'
    )
    # Agregar permisos
    perms = Permission.objects.filter(code__in=[
        'patient.read',
        'clinical_record.create', 'clinical_record.read', 'clinical_record.update',
        'document.create', 'document.read', 'document.sign',
        'report.create', 'report.read'
    ])
    role.permissions.set(perms)
    return role


@pytest.fixture
def admin_user(tenant, admin_role):
    """Crea un usuario administrador"""
    user = User.objects.create_user(
        email='admin@test.com',
        password='Admin123!',
        first_name='Admin',
        last_name='User',
        tenant=tenant,
        role=admin_role,
        is_active=True
    )
    return user


@pytest.fixture
def doctor_user(tenant, doctor_role):
    """Crea un usuario doctor"""
    user = User.objects.create_user(
        email='doctor@test.com',
        password='Doctor123!',
        first_name='Doctor',
        last_name='User',
        tenant=tenant,
        role=doctor_role,
        is_active=True
    )
    return user


@pytest.fixture
def patient_data(tenant):
    """Crea datos de paciente de prueba"""
    return {
        'identity_document_type': 'CI',
        'identity_document': '123456789',
        'first_name': 'Juan',
        'last_name': 'Pérez',
        'date_of_birth': '1980-01-15',
        'gender': 'M',
        'phone': '1234567890',
        'email': 'juan@test.com',
        'address': 'Calle Principal 123'
    }


@pytest.fixture
def patient(tenant, patient_data):
    """Crea un paciente de prueba"""
    set_current_tenant(tenant)
    patient_obj = Patient.objects.create(
        tenant=tenant,
        **patient_data
    )
    return patient_obj


@pytest.fixture
def patients(tenant):
    """Crea múltiples pacientes para testing"""
    set_current_tenant(tenant)
    patients = []
    for i in range(10):
        patient = Patient.objects.create(
            tenant=tenant,
            identity_document_type='CI',
            identity_document=f'12345678{i}',
            first_name=f'Patient{i}',
            last_name=f'Test{i}',
            date_of_birth='1980-01-15',
            gender='M' if i % 2 == 0 else 'F',
            phone=f'123456789{i}',
            email=f'patient{i}@test.com'
        )
        patients.append(patient)
    return patients


@pytest.fixture
def clinical_records(tenant, patients, doctor_user):
    """Crea registros clínicos de prueba"""
    set_current_tenant(tenant)
    records = []
    for i, patient in enumerate(patients[:5]):
        record = ClinicalRecord.objects.create(
            tenant=tenant,
            patient=patient,
            record_number=f'REC{i:06d}',
            admission_date=timezone.now() - timedelta(days=i),
            chief_complaint=f'Complaint {i}',
            created_by=doctor_user,
            status='active' if i % 2 == 0 else 'closed'
        )
        records.append(record)
    return records


@pytest.fixture
def documents(tenant, clinical_records):
    """Crea documentos clínicos de prueba"""
    set_current_tenant(tenant)
    documents = []
    specialties = ['Cardiología', 'Neurología', 'Oftalmología', 'Pediatría', 'Oncología']
    doc_types = ['consultation', 'test_result', 'prescription', 'medical_image']
    
    for i, record in enumerate(clinical_records):
        doc = ClinicalDocument.objects.create(
            tenant=tenant,
            clinical_record=record,
            document_type=doc_types[i % len(doc_types)],
            title=f'Document {i}',
            specialty=specialties[i % len(specialties)],
            upload_date=timezone.now() - timedelta(days=i),
            file='test_file.pdf'
        )
        documents.append(doc)
    return documents


@pytest.fixture
def api_client():
    """Crea un cliente API REST"""
    return APIClient()


@pytest.fixture
def authenticated_api_client(api_client, admin_user):
    """Crea un cliente API autenticado"""
    refresh = RefreshToken.for_user(admin_user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return api_client


@pytest.fixture
def django_client():
    """Crea un cliente Django de prueba"""
    return Client()
