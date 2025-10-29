import pytest
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from apps.core.models import Tenant, set_current_tenant
from apps.accounts.models import User, Role, Permission
from apps.patients.models import Patient
from apps.clinical_records.models import ClinicalRecord
from apps.documents.models import ClinicalDocument, DocumentAccessLog


@pytest.mark.django_db
class TestDocumentUploadAndOCR(TestCase):
    """Tests para upload de documentos y OCR"""
    
    def setUp(self):
        """Configurar datos de prueba"""
        # Crear tenant
        self.tenant = Tenant.objects.create(
            name='Hospital Test',
            slug='hospital-test',
            subdomain='test',
            email='test@hospital.com'
        )
        
        set_current_tenant(self.tenant)
        
        # Crear usuario
        self.user = User.objects.create_user(
            tenant=self.tenant,
            email='doctor@test.com',
            password='Test123!',
            first_name='Doctor',
            last_name='Test'
        )
        
        # Crear paciente
        self.patient = Patient.objects.create(
            tenant=self.tenant,
            identity_document='12345678',
            first_name='Juan',
            last_name='Pérez',
            date_of_birth='1990-01-01',
            gender='M'
        )
        
        # Crear historia clínica
        self.clinical_record = ClinicalRecord.objects.create(
            tenant=self.tenant,
            patient=self.patient,
            record_number='HC-2024-000001',
            created_by=self.user
        )
    
    def test_create_document_without_file(self):
        """Crear documento sin archivo"""
        from datetime import datetime
        
        document = ClinicalDocument.objects.create(
            tenant=self.tenant,
            clinical_record=self.clinical_record,
            document_type='consultation',
            title='Consulta de prueba',
            document_date=datetime.now(),
            created_by=self.user
        )
        
        self.assertIsNotNone(document.id)
        self.assertEqual(document.title, 'Consulta de prueba')
        self.assertEqual(document.tenant, self.tenant)
    
    def test_calculate_file_hash(self):
        """Verificar cálculo de hash"""
        document = ClinicalDocument.objects.create(
            tenant=self.tenant,
            clinical_record=self.clinical_record,
            document_type='consultation',
            title='Test',
            document_date='2024-01-01',
            created_by=self.user
        )
        
        file_content = b'test file content'
        hash_value = document.calculate_file_hash(file_content)
        
        self.assertEqual(len(hash_value), 64)  # SHA-256 produces 64 hex chars
    
    def test_sign_document(self):
        """Probar firma digital"""
        from datetime import datetime
        
        document = ClinicalDocument.objects.create(
            tenant=self.tenant,
            clinical_record=self.clinical_record,
            document_type='consultation',
            title='Documento a firmar',
            document_date=datetime.now(),
            created_by=self.user
        )
        
        # Firmar documento
        document.sign_document(self.user)
        
        self.assertTrue(document.is_signed)
        self.assertTrue(document.is_locked)
        self.assertIsNotNone(document.signed_at)
        self.assertEqual(document.signed_by, self.user)
        self.assertIsNotNone(document.digital_signature)
        
        # No se puede firmar dos veces
        with self.assertRaises(ValueError):
            document.sign_document(self.user)


@pytest.mark.django_db
class TestDocumentAccessLog(TestCase):
    """Tests para logs de acceso a documentos"""
    
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
            email='doctor@test.com',
            password='Test123!',
            first_name='Doctor',
            last_name='Test'
        )
        
        self.patient = Patient.objects.create(
            tenant=self.tenant,
            identity_document='12345678',
            first_name='Juan',
            last_name='Pérez',
            date_of_birth='1990-01-01',
            gender='M'
        )
        
        self.clinical_record = ClinicalRecord.objects.create(
            tenant=self.tenant,
            patient=self.patient,
            record_number='HC-2024-000001'
        )
        
        self.document = ClinicalDocument.objects.create(
            tenant=self.tenant,
            clinical_record=self.clinical_record,
            document_type='consultation',
            title='Test Document',
            document_date='2024-01-01',
            created_by=self.user
        )
    
    def test_create_access_log(self):
        """Crear log de acceso"""
        log = DocumentAccessLog.objects.create(
            tenant=self.tenant,
            document=self.document,
            user=self.user,
            access_type='view',
            user_email=self.user.email,
            user_name=self.user.get_full_name(),
            ip_address='192.168.1.1'
        )
        
        self.assertIsNotNone(log.id)
        self.assertEqual(log.access_type, 'view')
        self.assertEqual(log.document, self.document)
    
    def test_access_log_tracking(self):
        """Verificar tracking de múltiples accesos"""
        # Crear varios logs
        for i in range(5):
            DocumentAccessLog.objects.create(
                tenant=self.tenant,
                document=self.document,
                user=self.user,
                access_type='view',
                user_email=self.user.email,
                user_name=self.user.get_full_name(),
                ip_address=f'192.168.1.{i}'
            )
        
        # Contar logs del documento
        logs_count = DocumentAccessLog.objects.filter(
            document=self.document
        ).count()
        
        self.assertEqual(logs_count, 5)