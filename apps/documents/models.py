import uuid
import hashlib
from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import TenantAwareModel, TenantManager
from apps.clinical_records.models import ClinicalRecord


class ClinicalDocument(TenantAwareModel):
    """
    Documento clínico (núcleo del sistema)
    """
    DOCUMENT_TYPE_CHOICES = [
        ('consultation', 'Consulta'),
        ('lab_result', 'Resultado de Laboratorio'),
        ('imaging_report', 'Informe de Imagen'),
        ('prescription', 'Receta'),
        ('surgical_note', 'Nota Quirúrgica'),
        ('discharge_summary', 'Resumen de Alta'),
        ('consent_form', 'Consentimiento Informado'),
        ('progress_note', 'Nota de Evolución'),
        ('referral', 'Referencia'),
    ]

    clinical_record = models.ForeignKey(
        ClinicalRecord,
        on_delete=models.CASCADE,
        verbose_name=_('Historia clínica')
    )

    # Tipo y clasificación
    document_type = models.CharField(
        max_length=100,
        choices=DOCUMENT_TYPE_CHOICES,
        verbose_name=_('Tipo de documento')
    )

    title = models.CharField(
        max_length=255,
        verbose_name=_('Título')
    )

    description = models.TextField(
        blank=True,
        verbose_name=_('Descripción')
    )

    # Información del documento
    document_date = models.DateTimeField(
        verbose_name=_('Fecha del documento'),
        help_text=_('Fecha del evento médico')
    )

    specialty = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Especialidad')
    )

    doctor_name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_('Nombre del médico')
    )

    doctor_license = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Matrícula del médico')
    )

    # Contenido estructurado
    content = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Contenido estructurado'),
        help_text=_('JSON con el contenido del documento')
    )

    # Archivo físico
    file_path = models.CharField(
        max_length=500,
        blank=True,
        verbose_name=_('Ruta del archivo en S3')
    )

    file_name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_('Nombre del archivo')
    )

    file_size_bytes = models.BigIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Tamaño del archivo (bytes)')
    )

    mime_type = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Tipo MIME')
    )

    file_hash = models.CharField(
        max_length=64,
        blank=True,
        verbose_name=_('Hash SHA-256 del archivo'),
        help_text=_('Para verificar integridad')
    )

    # OCR (AWS Textract)
    ocr_text = models.TextField(
        blank=True,
        verbose_name=_('Texto extraído por OCR')
    )

    ocr_confidence = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_('Confianza del OCR (0-100)')
    )

    ocr_processed = models.BooleanField(
        default=False,
        verbose_name=_('OCR procesado')
    )

    ocr_job_id = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_('AWS Textract Job ID')
    )

    ocr_status = models.CharField(
        max_length=50,
        choices=[
            ('pending', 'Pendiente'),
            ('processing', 'Procesando'),
            ('async_processing', 'Procesando (Asíncrono)'),
            ('completed', 'Completado'),
            ('failed', 'Fallido'),
        ],
        default='pending',
        verbose_name=_('Estado del OCR')
    )

    # Estado
    is_signed = models.BooleanField(
        default=False,
        verbose_name=_('Firmado digitalmente')
    )

    signed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Fecha de firma')
    )

    signed_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documents_signed',
        verbose_name=_('Firmado por')
    )

    digital_signature = models.TextField(
        blank=True,
        verbose_name=_('Firma digital')
    )

    is_locked = models.BooleanField(
        default=False,
        verbose_name=_('Bloqueado'),
        help_text=_('Los documentos bloqueados no pueden editarse')
    )

    # Metadata
    tags = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Etiquetas'),
        help_text=_('["laboratorio", "urgente"]')
    )

    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='documents_created',
        verbose_name=_('Creado por')
    )

    objects = TenantManager()

    class Meta:
        db_table = 'clinical_document'
        verbose_name = _('Documento Clínico')
        verbose_name_plural = _('Documentos Clínicos')
        indexes = [
            models.Index(fields=['tenant', 'clinical_record']),
            models.Index(fields=['document_type']),
            models.Index(fields=['document_date']),
            models.Index(fields=['specialty']),
            models.Index(fields=['created_at']),
        ]
        ordering = ['-document_date', '-created_at']

    def __str__(self):
        return f"{self.title} - {self.document_date.strftime('%Y-%m-%d')}"

    def calculate_file_hash(self, file_content):
        """Calcula el hash SHA-256 del archivo"""
        return hashlib.sha256(file_content).hexdigest()

    def sign_document(self, user):
        """Firma digitalmente el documento"""
        from django.utils import timezone
        import hashlib
        import json

        if self.is_signed:
            raise ValueError("El documento ya está firmado")

        # Generar firma digital (hash del contenido + usuario + timestamp)
        signature_data = {
            'document_id': str(self.id),
            'user_id': str(user.id),
            'user_email': user.email,
            'timestamp': timezone.now().isoformat(),
            'file_hash': self.file_hash,
            'content_hash': hashlib.sha256(
                json.dumps(self.content, sort_keys=True).encode()
            ).hexdigest()
        }

        self.digital_signature = hashlib.sha256(
            json.dumps(signature_data, sort_keys=True).encode()
        ).hexdigest()

        self.is_signed = True
        self.signed_at = timezone.now()
        self.signed_by = user
        self.is_locked = True  # Bloquear documento al firmarlo

        self.save()


class MedicalImage(TenantAwareModel):
    """
    Imágenes médicas (Rayos X, Tomografías, etc.)
    """
    IMAGE_TYPE_CHOICES = [
        ('xray', 'Rayos X'),
        ('ct_scan', 'Tomografía'),
        ('mri', 'Resonancia Magnética'),
        ('ultrasound', 'Ecografía'),
        ('mammography', 'Mamografía'),
        ('pet_scan', 'PET Scan'),
    ]

    clinical_record = models.ForeignKey(
        ClinicalRecord,
        on_delete=models.CASCADE,
        verbose_name=_('Historia clínica')
    )

    document = models.ForeignKey(
        ClinicalDocument,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('Documento asociado')
    )

    # Información del estudio
    image_type = models.CharField(
        max_length=100,
        choices=IMAGE_TYPE_CHOICES,
        verbose_name=_('Tipo de imagen')
    )

    title = models.CharField(
        max_length=255,
        verbose_name=_('Título')
    )

    study_date = models.DateTimeField(
        verbose_name=_('Fecha del estudio')
    )

    modality = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Modalidad DICOM'),
        help_text=_('CR, CT, MR, US, etc.')
    )

    body_part = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Parte del cuerpo')
    )

    # Archivos
    file_path = models.CharField(
        max_length=500,
        verbose_name=_('Ruta del archivo en S3')
    )

    file_name = models.CharField(
        max_length=255,
        verbose_name=_('Nombre del archivo')
    )

    file_size_bytes = models.BigIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Tamaño del archivo')
    )

    # DICOM metadata
    dicom_metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Metadatos DICOM')
    )

    # AI Enhancement (Real-ESRGAN + CLAHE)
    enhanced_image_path = models.CharField(
        max_length=500,
        blank=True,
        verbose_name=_('Ruta de imagen mejorada')
    )

    enhancement_applied = models.BooleanField(
        default=False,
        verbose_name=_('Mejora aplicada')
    )

    enhancement_params = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Parámetros de mejora')
    )

    # Metadata
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_('Creado por')
    )

    objects = TenantManager()

    class Meta:
        db_table = 'medical_image'
        verbose_name = _('Imagen Médica')
        verbose_name_plural = _('Imágenes Médicas')
        indexes = [
            models.Index(fields=['tenant', 'clinical_record']),
            models.Index(fields=['image_type']),
            models.Index(fields=['study_date']),
        ]
        ordering = ['-study_date']

    def __str__(self):
        return f"{self.title} - {self.study_date.strftime('%Y-%m-%d')}"


class DocumentAccessLog(models.Model):
    """
    Log de acceso a documentos (tracking)
    """
    ACCESS_TYPE_CHOICES = [
        ('view', 'Visualización'),
        ('download', 'Descarga'),
        ('print', 'Impresión'),
        ('share', 'Compartir'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        verbose_name=_('Tenant')
    )

    document = models.ForeignKey(
        ClinicalDocument,
        on_delete=models.CASCADE,
        verbose_name=_('Documento')
    )

    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_('Usuario')
    )

    # Información del acceso
    access_type = models.CharField(
        max_length=50,
        choices=ACCESS_TYPE_CHOICES,
        verbose_name=_('Tipo de acceso')
    )

    user_email = models.CharField(
        max_length=255,
        verbose_name=_('Email del usuario')
    )

    user_name = models.CharField(
        max_length=255,
        verbose_name=_('Nombre del usuario')
    )

    # Detalles técnicos
    ip_address = models.GenericIPAddressField(
        null=True,
        verbose_name=_('Dirección IP')
    )

    user_agent = models.TextField(
        blank=True,
        verbose_name=_('User Agent')
    )

    # Metadata
    access_reason = models.TextField(
        blank=True,
        verbose_name=_('Razón del acceso'),
        help_text=_('Justificación opcional')
    )

    accessed_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Fecha de acceso')
    )

    class Meta:
        db_table = 'document_access_log'
        verbose_name = _('Log de Acceso a Documento')
        verbose_name_plural = _('Logs de Acceso a Documentos')
        indexes = [
            models.Index(fields=['tenant', 'document']),
            models.Index(fields=['user', 'accessed_at']),
            models.Index(fields=['accessed_at']),
        ]
        ordering = ['-accessed_at']

    def __str__(self):
        return f"{self.access_type} - {self.document.title} - {self.accessed_at}"