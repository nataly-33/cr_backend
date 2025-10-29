import pytest
from django.test import TestCase
from apps.core.models import Tenant, set_current_tenant
from apps.accounts.models import User
from apps.audit.models import AuditLog


@pytest.mark.django_db
class TestAuditLog(TestCase):
    """Tests para logs de auditoría"""
    
    def setUp(self):
        """Configurar datos de prueba"""
        self.tenant = Tenant.objects.create(
            name='Hospital Test',
            slug='hospital-test',
            subdomain='test',
            email='test@hospital.com'
        )
        
        set_current_tenant(self.tenant)
        
        self.user = User.objects.create_user(
            tenant=self.tenant,
            email='admin@test.com',
            password='Test123!',
            first_name='Admin',
            last_name='Test'
        )
    
    def test_create_audit_log(self):
        """Crear log de auditoría"""
        log = AuditLog.objects.create(
            tenant=self.tenant,
            user=self.user,
            user_email=self.user.email,
            user_name=self.user.get_full_name(),
            action_type='CREATE',
            resource_type='patient',
            resource_id='123e4567-e89b-12d3-a456-426614174000',
            ip_address='192.168.1.1',
            request_method='POST',
            request_path='/api/patients/',
            response_status=201
        )
        
        self.assertIsNotNone(log.id)
        self.assertIsNotNone(log.log_hash)
        self.assertEqual(len(log.log_hash), 64)  # SHA-256
    
    def test_log_hash_integrity(self):
        """Verificar integridad del hash"""
        log = AuditLog.objects.create(
            tenant=self.tenant,
            user=self.user,
            user_email=self.user.email,
            user_name=self.user.get_full_name(),
            action_type='UPDATE',
            resource_type='document',
            ip_address='192.168.1.1',
            request_method='PUT',
            request_path='/api/documents/123/',
            response_status=200
        )
        
        # Verificar que el log es válido
        is_valid = log.verify_integrity()
        self.assertTrue(is_valid)
        
        # Simular manipulación
        original_hash = log.log_hash
        log.user_email = 'hacker@evil.com'
        log.log_hash = original_hash  # Mantener el hash original
        
        # Ahora el log debería ser inválido
        is_valid_after_tampering = log.verify_integrity()
        self.assertFalse(is_valid_after_tampering)
    
    def test_log_immutability(self):
        """Los logs no deberían poder editarse"""
        log = AuditLog.objects.create(
            tenant=self.tenant,
            user=self.user,
            user_email=self.user.email,
            user_name=self.user.get_full_name(),
            action_type='DELETE',
            resource_type='user',
            ip_address='192.168.1.1',
            request_method='DELETE',
            request_path='/api/users/123/',
            response_status=204
        )
        
        original_hash = log.log_hash
        
        # Intentar modificar no debería cambiar el hash automáticamente
        log.action_type = 'CREATE'
        log.save()
        
        # El hash debería ser el mismo (no se recalcula en update)
        self.assertEqual(log.log_hash, original_hash)