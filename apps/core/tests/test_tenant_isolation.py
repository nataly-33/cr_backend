import pytest
from django.test import TestCase
from apps.core.models import Tenant, set_current_tenant
from apps.accounts.models import User
from apps.patients.models import Patient


@pytest.mark.django_db
class TestTenantIsolation(TestCase):
    """Tests para verificar el aislamiento de datos por tenant"""
    
    def setUp(self):
        """Crear dos tenants con datos"""
        # Tenant 1
        self.tenant1 = Tenant.objects.create(
            name='Hospital 1',
            slug='hospital-1',
            subdomain='hospital1',
            email='admin@hospital1.com'
        )
        
        # Tenant 2
        self.tenant2 = Tenant.objects.create(
            name='Hospital 2',
            slug='hospital-2',
            subdomain='hospital2',
            email='admin@hospital2.com'
        )
        
        # Crear pacientes para tenant 1
        set_current_tenant(self.tenant1)
        self.patient1_t1 = Patient.objects.create(
            tenant=self.tenant1,
            first_name='Juan',
            last_name='Pérez',
            identity_document='12345678',
            date_of_birth='1990-01-01'
        )
        
        # Crear pacientes para tenant 2
        set_current_tenant(self.tenant2)
        self.patient1_t2 = Patient.objects.create(
            tenant=self.tenant2,
            first_name='María',
            last_name='González',
            identity_document='87654321',
            date_of_birth='1985-05-15'
        )
    
    def test_tenant_isolation(self):
        """Verificar que los datos están aislados por tenant"""
        # Establecer tenant 1
        set_current_tenant(self.tenant1)
        patients_t1 = Patient.objects.all()
        
        # Debe haber solo 1 paciente
        self.assertEqual(patients_t1.count(), 1)
        self.assertEqual(patients_t1.first().identity_document, '12345678')
        
        # Establecer tenant 2
        set_current_tenant(self.tenant2)
        patients_t2 = Patient.objects.all()
        
        # Debe haber solo 1 paciente diferente
        self.assertEqual(patients_t2.count(), 1)
        self.assertEqual(patients_t2.first().identity_document, '87654321')
    
    def test_no_cross_tenant_access(self):
        """Verificar que no se puede acceder a datos de otro tenant"""
        set_current_tenant(self.tenant1)
        
        # Intentar buscar por ID del paciente de tenant 2
        with self.assertRaises(Patient.DoesNotExist):
            Patient.objects.get(id=self.patient1_t2.id)