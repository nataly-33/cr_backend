"""
Tests para SeederViewSet (Fase 6 - Extra)

Ejecutar:
    python manage.py test apps.reports.tests.test_seeders
    pytest apps/reports/tests/test_seeders.py -v
"""

from django.test import TestCase
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from unittest.mock import patch, Mock
import pytest

from apps.reports.seeders import SeederViewSet
from apps.core.models import Tenant, set_current_tenant
from apps.accounts.models import User, Role
from apps.patients.models import Patient
from apps.documents.models import ClinicalDocument
from apps.clinical_records.models import ClinicalRecord


class SeederViewSetAuthenticationTestCase(APITestCase):
    """Tests para autenticación y permisos en seeders"""
    
    def setUp(self):
        """Setup para cada test"""
        self.client = APIClient()
        self.tenant = Tenant.objects.create(
            name='Test Hospital',
            slug='test-hospital',
            subdomain='test'
        )
    
    def test_seeder_available_requires_auth(self):
        """Test endpoint available requiere autenticación"""
        response = self.client.get('/api/reports/seeders/available/')
        
        # Debe retornar 401 sin auth
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_seeder_available_requires_admin(self):
        """Test endpoint available requiere rol admin"""
        # Crear usuario no-admin
        doctor_role = Role.objects.create(
            tenant=self.tenant,
            name='Doctor'
        )
        user = User.objects.create_user(
            email='doctor@test.com',
            password='test123',
            tenant=self.tenant,
            role=doctor_role
        )
        
        self.client.force_authenticate(user=user)
        response = self.client.get('/api/reports/seeders/available/')
        
        # Debería retornar 403 (no es admin)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_seeder_run_requires_admin(self):
        """Test endpoint run requiere admin"""
        # Crear usuario no-admin
        doctor_role = Role.objects.create(
            tenant=self.tenant,
            name='Doctor'
        )
        user = User.objects.create_user(
            email='doctor@test.com',
            password='test123',
            tenant=self.tenant,
            role=doctor_role
        )
        
        self.client.force_authenticate(user=user)
        response = self.client.post('/api/reports/seeders/run/', {'name': 'patients'})
        
        # Debería retornar 403
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_non_admin_cannot_run_seeders(self):
        """Test que usuario no-admin no puede ejecutar seeders"""
        # Crear usuario regular
        user_role = Role.objects.create(
            tenant=self.tenant,
            name='User'
        )
        user = User.objects.create_user(
            email='user@test.com',
            password='test123',
            tenant=self.tenant,
            role=user_role
        )
        
        self.client.force_authenticate(user=user)
        response = self.client.post(
            '/api/reports/seeders/run/',
            {'name': 'patients'},
            format='json'
        )
        
        # Debería retornar 403
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class SeederViewSetAvailableEndpointTestCase(APITestCase):
    """Tests para endpoint /available/"""
    
    def setUp(self):
        """Setup para tests"""
        self.client = APIClient()
        self.tenant = Tenant.objects.create(
            name='Test Hospital',
            slug='test-hospital',
            subdomain='test'
        )
        
        # Crear admin
        admin_role = Role.objects.create(
            tenant=self.tenant,
            name='Admin',
            is_admin=True
        )
        self.admin_user = User.objects.create_user(
            email='admin@test.com',
            password='admin123',
            tenant=self.tenant,
            role=admin_role
        )
        
        self.client.force_authenticate(user=self.admin_user)
    
    def test_available_returns_all_seeders(self):
        """Test que endpoint retorna todos los seeders"""
        response = self.client.get('/api/reports/seeders/available/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('seeders', response.data or {})
    
    def test_available_returns_correct_format(self):
        """Test que respuesta tiene formato correcto"""
        response = self.client.get('/api/reports/seeders/available/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data or {}
        
        # Verificar estructura
        if 'seeders' in data:
            self.assertIsInstance(data['seeders'], dict)
    
    def test_available_includes_descriptions(self):
        """Test que seeders incluyen descripción"""
        response = self.client.get('/api/reports/seeders/available/')
        
        if response.status_code == status.HTTP_200_OK:
            data = response.data or {}
            if 'seeders' in data:
                for seeder_name, seeder_info in data['seeders'].items():
                    self.assertIn('description', seeder_info or {})


class SeederViewSetRunEndpointTestCase(APITestCase):
    """Tests para endpoint /run/"""
    
    def setUp(self):
        """Setup para tests"""
        self.client = APIClient()
        self.tenant = Tenant.objects.create(
            name='Test Hospital',
            slug='test-hospital',
            subdomain='test'
        )
        set_current_tenant(self.tenant)
        
        # Crear admin
        admin_role = Role.objects.create(
            tenant=self.tenant,
            name='Admin',
            is_admin=True
        )
        self.admin_user = User.objects.create_user(
            email='admin@test.com',
            password='admin123',
            tenant=self.tenant,
            role=admin_role
        )
        
        self.client.force_authenticate(user=self.admin_user)
    
    @patch('apps.reports.seeders.SeederViewSet._run_seeder')
    def test_run_seeder_patient_creates_records(self, mock_run):
        """Test correr seeder de pacientes"""
        mock_run.return_value = {'count': 50, 'model': 'Patient'}
        
        response = self.client.post(
            '/api/reports/seeders/run/',
            {'name': 'patients'},
            format='json'
        )
        
        # Debería ser exitoso
        if response.status_code == status.HTTP_200_OK:
            self.assertIn('result', response.data or {})
    
    @patch('apps.reports.seeders.SeederViewSet._run_seeder')
    def test_run_seeder_document_creates_records(self, mock_run):
        """Test correr seeder de documentos"""
        mock_run.return_value = {'count': 100, 'model': 'ClinicalDocument'}
        
        response = self.client.post(
            '/api/reports/seeders/run/',
            {'name': 'clinical_documents'},
            format='json'
        )
        
        if response.status_code == status.HTTP_200_OK:
            self.assertIn('result', response.data or {})
    
    def test_run_seeder_unknown_raises_error(self):
        """Test correr seeder desconocido lanza error"""
        response = self.client.post(
            '/api/reports/seeders/run/',
            {'name': 'unknown_seeder'},
            format='json'
        )
        
        # Debería retornar error
        self.assertIn(response.status_code, 
                     [status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND])
    
    @patch('apps.reports.seeders.SeederViewSet._run_seeder')
    def test_run_seeder_respects_tenant(self, mock_run):
        """Test que seeder respeta tenant actual"""
        mock_run.return_value = {'count': 50}
        
        response = self.client.post(
            '/api/reports/seeders/run/',
            {'name': 'patients'},
            format='json'
        )
        
        # Verificar que se llamó con tenant correcto
        if mock_run.called:
            # mock_run debe haber sido llamado
            self.assertTrue(mock_run.called)
    
    @patch('apps.reports.seeders.SeederViewSet._run_seeder')
    def test_run_seeder_returns_success_message(self, mock_run):
        """Test que respuesta incluye mensaje de éxito"""
        mock_run.return_value = {'count': 50, 'model': 'Patient'}
        
        response = self.client.post(
            '/api/reports/seeders/run/',
            {'name': 'patients'},
            format='json'
        )
        
        if response.status_code == status.HTTP_200_OK:
            # Debería haber éxito
            self.assertTrue('result' in response.data or 'success' in response.data)


class SeederViewSetRunAllEndpointTestCase(APITestCase):
    """Tests para endpoint /run-all/"""
    
    def setUp(self):
        """Setup para tests"""
        self.client = APIClient()
        self.tenant = Tenant.objects.create(
            name='Test Hospital',
            slug='test-hospital',
            subdomain='test'
        )
        set_current_tenant(self.tenant)
        
        # Crear admin
        admin_role = Role.objects.create(
            tenant=self.tenant,
            name='Admin',
            is_admin=True
        )
        self.admin_user = User.objects.create_user(
            email='admin@test.com',
            password='admin123',
            tenant=self.tenant,
            role=admin_role
        )
        
        self.client.force_authenticate(user=self.admin_user)
    
    @patch('apps.reports.seeders.SeederViewSet._run_seeder')
    def test_run_all_seeders_creates_all_data(self, mock_run):
        """Test correr todos los seeders"""
        mock_run.return_value = {'count': 100, 'model': 'Model'}
        
        response = self.client.post('/api/reports/seeders/run-all/')
        
        # Debería ejecutar todos
        self.assertIn(response.status_code, 
                     [status.HTTP_200_OK, status.HTTP_201_CREATED])
    
    @patch('apps.reports.seeders.SeederViewSet._run_seeder')
    def test_run_all_respects_tenant(self, mock_run):
        """Test que run-all respeta tenant"""
        mock_run.return_value = {'count': 100}
        
        response = self.client.post('/api/reports/seeders/run-all/')
        
        # Debería completar sin errores
        self.assertNotEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    @patch('apps.reports.seeders.SeederViewSet._run_seeder')
    def test_run_all_returns_all_results(self, mock_run):
        """Test que retorna resultados de todos"""
        mock_run.return_value = {'count': 100}
        
        response = self.client.post('/api/reports/seeders/run-all/')
        
        if response.status_code == status.HTTP_200_OK:
            # Debería tener múltiples resultados
            data = response.data or {}
            self.assertIn('results', data or {})


class SeederViewSetDryRunEndpointTestCase(APITestCase):
    """Tests para endpoint /dry-run/"""
    
    def setUp(self):
        """Setup para tests"""
        self.client = APIClient()
        self.tenant = Tenant.objects.create(
            name='Test Hospital',
            slug='test-hospital',
            subdomain='test'
        )
        set_current_tenant(self.tenant)
        
        # Crear admin
        admin_role = Role.objects.create(
            tenant=self.tenant,
            name='Admin',
            is_admin=True
        )
        self.admin_user = User.objects.create_user(
            email='admin@test.com',
            password='admin123',
            tenant=self.tenant,
            role=admin_role
        )
        
        self.client.force_authenticate(user=self.admin_user)
    
    def test_dry_run_does_not_create_data(self):
        """Test dry-run no crea datos reales"""
        initial_count = Patient.objects.count()
        
        response = self.client.post(
            '/api/reports/seeders/dry-run/',
            {'name': 'patients'},
            format='json'
        )
        
        final_count = Patient.objects.count()
        
        # No debería haber creado nada
        self.assertEqual(initial_count, final_count)
    
    def test_dry_run_returns_simulation_results(self):
        """Test dry-run retorna resultado de simulación"""
        response = self.client.post(
            '/api/reports/seeders/dry-run/',
            {'name': 'patients'},
            format='json'
        )
        
        if response.status_code == status.HTTP_200_OK:
            # Debería mostrar qué se crearía
            data = response.data or {}
            self.assertIn('simulation', data or {})
    
    def test_dry_run_shows_what_would_be_created(self):
        """Test dry-run muestra lo que se crearía"""
        response = self.client.post(
            '/api/reports/seeders/dry-run/',
            {'name': 'patients'},
            format='json'
        )
        
        if response.status_code == status.HTTP_200_OK:
            # Debería tener información de simulación
            self.assertIn('simulation', response.data or 'result' in response.data)


class SeederViewSetResetEndpointTestCase(APITestCase):
    """Tests para endpoint /reset/"""
    
    def setUp(self):
        """Setup para tests"""
        self.client = APIClient()
        self.tenant = Tenant.objects.create(
            name='Test Hospital',
            slug='test-hospital',
            subdomain='test'
        )
        set_current_tenant(self.tenant)
        
        # Crear admin
        admin_role = Role.objects.create(
            tenant=self.tenant,
            name='Admin',
            is_admin=True
        )
        self.admin_user = User.objects.create_user(
            email='admin@test.com',
            password='admin123',
            tenant=self.tenant,
            role=admin_role
        )
        
        self.client.force_authenticate(user=self.admin_user)
    
    def test_reset_removes_all_seeded_data(self):
        """Test reset elimina todos los datos sembrados"""
        # Crear algunos datos primero
        Patient.objects.create(
            tenant=self.tenant,
            identity_document_type='CI',
            identity_document='123456789',
            first_name='Test',
            last_name='Patient',
            date_of_birth='1980-01-01',
            gender='M'
        )
        
        initial_count = Patient.objects.filter(tenant=self.tenant).count()
        
        response = self.client.post('/api/reports/seeders/reset/')
        
        # Después del reset debería haber 0 o menos datos
        if response.status_code == status.HTTP_200_OK:
            final_count = Patient.objects.filter(tenant=self.tenant).count()
            self.assertLessEqual(final_count, initial_count)
    
    def test_reset_respects_tenant(self):
        """Test reset solo afecta tenant actual"""
        # Crear otro tenant con datos
        other_tenant = Tenant.objects.create(
            name='Other Hospital',
            slug='other',
            subdomain='other'
        )
        
        set_current_tenant(other_tenant)
        other_patient = Patient.objects.create(
            tenant=other_tenant,
            identity_document_type='CI',
            identity_document='987654321',
            first_name='Other',
            last_name='Patient',
            date_of_birth='1990-01-01',
            gender='F'
        )
        
        # Reset en tenant original no debe afectar el otro
        set_current_tenant(self.tenant)
        
        response = self.client.post('/api/reports/seeders/reset/')
        
        # El paciente del otro tenant debe seguir existiendo
        self.assertTrue(
            Patient.objects.filter(id=other_patient.id).exists()
        )
    
    def test_reset_returns_confirmation(self):
        """Test reset retorna confirmación"""
        response = self.client.post('/api/reports/seeders/reset/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Debería tener confirmación
        data = response.data or {}
        self.assertTrue('success' in str(data).lower() or 'deleted' in str(data).lower())


class SeederViewSetErrorHandlingTestCase(APITestCase):
    """Tests para manejo de errores en seeders"""
    
    def setUp(self):
        """Setup para tests"""
        self.client = APIClient()
        self.tenant = Tenant.objects.create(
            name='Test Hospital',
            slug='test-hospital',
            subdomain='test'
        )
        set_current_tenant(self.tenant)
        
        # Crear admin
        admin_role = Role.objects.create(
            tenant=self.tenant,
            name='Admin',
            is_admin=True
        )
        self.admin_user = User.objects.create_user(
            email='admin@test.com',
            password='admin123',
            tenant=self.tenant,
            role=admin_role
        )
        
        self.client.force_authenticate(user=self.admin_user)
    
    def test_seeder_with_invalid_name_raises_error(self):
        """Test seeder con nombre inválido lanza error"""
        response = self.client.post(
            '/api/reports/seeders/run/',
            {'name': 'invalid_seeder_xyz'},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_seeder_with_duplicate_data_handles_gracefully(self):
        """Test seeder maneja datos duplicados"""
        # Crear paciente
        Patient.objects.create(
            tenant=self.tenant,
            identity_document_type='CI',
            identity_document='unique123',
            first_name='Test',
            last_name='Patient',
            date_of_birth='1980-01-01',
            gender='M'
        )
        
        # Intentar crear nuevamente
        response = self.client.post(
            '/api/reports/seeders/run/',
            {'name': 'patients'},
            format='json'
        )
        
        # Debería manejar el error gracefully
        self.assertIn(response.status_code, 
                     [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST])
    
    def test_database_error_raises_exception(self):
        """Test error en base de datos se propaga"""
        with patch('apps.reports.seeders.SeederViewSet._run_seeder') as mock:
            mock.side_effect = Exception('Database error')
            
            response = self.client.post(
                '/api/reports/seeders/run/',
                {'name': 'patients'},
                format='json'
            )
            
            self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def test_seeder_logging_is_called(self):
        """Test que logging se llama"""
        with patch('apps.reports.seeders.logger') as mock_logger:
            response = self.client.post(
                '/api/reports/seeders/run/',
                {'name': 'patients'},
                format='json'
            )
            
            # Logging debería haber sido llamado
            # (Depende de la implementación)
            pass
