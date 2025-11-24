"""
Modelos DICOM para gestión de estudios de imagenología médica.
Soporta la jerarquía estándar DICOM: Study → Series → Instance
"""

import uuid
import hashlib
from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import TenantAwareModel, TenantManager
from apps.patients.models import Patient
from apps.clinical_records.models import ClinicalRecord
from apps.documents.models import MedicalImage


class DicomStudy(TenantAwareModel):
    """
    Estudio DICOM completo.
    Un estudio puede contener múltiples series (ej: diferentes secuencias de MRI).
    """

    STATUS_CHOICES = [
        ('uploading', 'Subiendo'),
        ('processing', 'Procesando'),
        ('completed', 'Completado'),
        ('failed', 'Fallido'),
    ]

    MODALITY_CHOICES = [
        ('CR', 'Computed Radiography'),
        ('CT', 'Computed Tomography'),
        ('MR', 'Magnetic Resonance'),
        ('US', 'Ultrasound'),
        ('XA', 'X-Ray Angiography'),
        ('MG', 'Mammography'),
        ('PT', 'PET Scan'),
        ('NM', 'Nuclear Medicine'),
        ('DX', 'Digital Radiography'),
        ('OT', 'Other'),
    ]

    # Relaciones
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='dicom_studies',
        verbose_name=_('Paciente')
    )

    clinical_record = models.ForeignKey(
        ClinicalRecord,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='dicom_studies',
        verbose_name=_('Historia Clínica')
    )

    # Enlace opcional con MedicalImage existente
    medical_image = models.ForeignKey(
        MedicalImage,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='dicom_studies',
        verbose_name=_('Imagen Médica Asociada'),
        help_text=_('Enlace opcional al registro de MedicalImage para compatibilidad')
    )

    # Identificadores DICOM (estándar)
    study_instance_uid = models.CharField(
        max_length=128,
        unique=True,
        verbose_name=_('Study Instance UID'),
        help_text=_('Identificador único DICOM del estudio')
    )

    accession_number = models.CharField(
        max_length=64,
        blank=True,
        verbose_name=_('Accession Number'),
        help_text=_('Número de acceso del estudio')
    )

    # Información del estudio
    study_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Fecha del Estudio')
    )

    study_time = models.TimeField(
        null=True,
        blank=True,
        verbose_name=_('Hora del Estudio')
    )

    study_description = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_('Descripción del Estudio')
    )

    modality = models.CharField(
        max_length=16,
        choices=MODALITY_CHOICES,
        default='OT',
        verbose_name=_('Modalidad Principal'),
        help_text=_('Modalidad principal del estudio')
    )

    body_part_examined = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Parte del Cuerpo')
    )

    # Información del médico/institución
    referring_physician_name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_('Médico Referente')
    )

    institution_name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_('Institución')
    )

    # Estadísticas del estudio
    number_of_series = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Número de Series')
    )

    number_of_instances = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Número de Instancias')
    )

    total_size_bytes = models.BigIntegerField(
        default=0,
        verbose_name=_('Tamaño Total (bytes)')
    )

    # Estado y procesamiento
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='uploading',
        verbose_name=_('Estado')
    )

    processing_error = models.TextField(
        blank=True,
        verbose_name=_('Error de Procesamiento')
    )

    # Metadata completa extraída
    dicom_metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Metadatos DICOM'),
        help_text=_('Metadata completa del estudio en formato JSON')
    )

    # Integridad (hash de verificación)
    study_hash = models.CharField(
        max_length=64,
        blank=True,
        verbose_name=_('Hash SHA-256'),
        help_text=_('Hash para verificar integridad del estudio')
    )

    # Usuario que subió el estudio
    uploaded_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='dicom_studies_uploaded',
        verbose_name=_('Subido por')
    )

    objects = TenantManager()

    class Meta:
        db_table = 'dicom_study'
        verbose_name = _('Estudio DICOM')
        verbose_name_plural = _('Estudios DICOM')
        indexes = [
            models.Index(fields=['tenant', 'patient']),
            models.Index(fields=['study_instance_uid']),
            models.Index(fields=['study_date']),
            models.Index(fields=['modality']),
            models.Index(fields=['status']),
            models.Index(fields=['accession_number']),
        ]
        ordering = ['-study_date', '-created_at']

    def __str__(self):
        date_str = self.study_date.strftime('%Y-%m-%d') if self.study_date else 'Sin fecha'
        return f"{self.modality} - {self.study_description or 'Sin descripción'} ({date_str})"

    def calculate_study_hash(self):
        """
        Calcula el hash SHA-256 del estudio basado en los hashes de todas las instancias.
        """
        instance_hashes = list(
            self.series.values_list('instances__file_hash', flat=True)
        )
        combined = ''.join(sorted(filter(None, instance_hashes)))
        self.study_hash = hashlib.sha256(combined.encode()).hexdigest()
        return self.study_hash

    def update_statistics(self):
        """
        Actualiza las estadísticas del estudio (número de series, instancias, tamaño).
        """
        self.number_of_series = self.series.count()
        self.number_of_instances = DicomInstance.objects.filter(
            series__study=self
        ).count()
        self.total_size_bytes = DicomInstance.objects.filter(
            series__study=self
        ).aggregate(total=models.Sum('file_size_bytes'))['total'] or 0
        self.save(update_fields=['number_of_series', 'number_of_instances', 'total_size_bytes'])


class DicomSeries(TenantAwareModel):
    """
    Serie DICOM dentro de un estudio.
    Una serie contiene múltiples instancias (archivos .dcm individuales).
    """

    # Relación con estudio
    study = models.ForeignKey(
        DicomStudy,
        on_delete=models.CASCADE,
        related_name='series',
        verbose_name=_('Estudio')
    )

    # Identificadores DICOM
    series_instance_uid = models.CharField(
        max_length=128,
        unique=True,
        verbose_name=_('Series Instance UID'),
        help_text=_('Identificador único DICOM de la serie')
    )

    series_number = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Número de Serie')
    )

    # Información de la serie
    series_description = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_('Descripción de la Serie')
    )

    modality = models.CharField(
        max_length=16,
        blank=True,
        verbose_name=_('Modalidad'),
        help_text=_('Modalidad específica de esta serie')
    )

    body_part_examined = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Parte del Cuerpo Examinada')
    )

    series_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Fecha de la Serie')
    )

    series_time = models.TimeField(
        null=True,
        blank=True,
        verbose_name=_('Hora de la Serie')
    )

    # Información de contraste
    has_contrast = models.BooleanField(
        default=False,
        verbose_name=_('Con Contraste'),
        help_text=_('Indica si la serie fue adquirida con medio de contraste')
    )

    contrast_agent = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_('Agente de Contraste'),
        help_text=_('Nombre del medio de contraste utilizado')
    )

    # Parámetros de adquisición (específicos para CT/MR)
    slice_thickness = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        null=True,
        blank=True,
        verbose_name=_('Espesor del Corte (mm)')
    )

    pixel_spacing = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Espaciado de Píxeles'),
        help_text=_('Formato: "row_spacing\\column_spacing" en mm')
    )

    image_orientation_patient = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Orientación de Imagen'),
        help_text=_('Cosenos directores de fila y columna')
    )

    # Estadísticas
    number_of_instances = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Número de Instancias')
    )

    total_size_bytes = models.BigIntegerField(
        default=0,
        verbose_name=_('Tamaño Total (bytes)')
    )

    # Metadata
    dicom_metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Metadatos DICOM de la Serie')
    )

    objects = TenantManager()

    class Meta:
        db_table = 'dicom_series'
        verbose_name = _('Serie DICOM')
        verbose_name_plural = _('Series DICOM')
        indexes = [
            models.Index(fields=['tenant', 'study']),
            models.Index(fields=['series_instance_uid']),
            models.Index(fields=['series_number']),
            models.Index(fields=['modality']),
        ]
        ordering = ['series_number', 'created_at']

    def __str__(self):
        return f"Serie {self.series_number}: {self.series_description or self.modality}"

    def update_statistics(self):
        """
        Actualiza las estadísticas de la serie.
        """
        self.number_of_instances = self.instances.count()
        self.total_size_bytes = self.instances.aggregate(
            total=models.Sum('file_size_bytes')
        )['total'] or 0
        self.save(update_fields=['number_of_instances', 'total_size_bytes'])


class DicomInstance(TenantAwareModel):
    """
    Instancia DICOM individual (un archivo .dcm).
    Representa un frame/slice individual del estudio.
    """

    # Relación con serie
    series = models.ForeignKey(
        DicomSeries,
        on_delete=models.CASCADE,
        related_name='instances',
        verbose_name=_('Serie')
    )

    # Identificadores DICOM
    sop_instance_uid = models.CharField(
        max_length=128,
        unique=True,
        verbose_name=_('SOP Instance UID'),
        help_text=_('Identificador único DICOM de la instancia')
    )

    sop_class_uid = models.CharField(
        max_length=128,
        blank=True,
        verbose_name=_('SOP Class UID'),
        help_text=_('Tipo de objeto DICOM')
    )

    instance_number = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Número de Instancia'),
        help_text=_('Posición del frame en la serie')
    )

    # Archivo físico
    file_path = models.CharField(
        max_length=500,
        verbose_name=_('Ruta del Archivo'),
        help_text=_('Ruta relativa al MEDIA_ROOT o URL de S3')
    )

    file_name = models.CharField(
        max_length=255,
        verbose_name=_('Nombre del Archivo')
    )

    file_size_bytes = models.BigIntegerField(
        default=0,
        verbose_name=_('Tamaño del Archivo (bytes)')
    )

    file_hash = models.CharField(
        max_length=64,
        blank=True,
        verbose_name=_('Hash SHA-256'),
        help_text=_('Hash para verificar integridad del archivo')
    )

    # Información de imagen
    rows = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Filas (altura)')
    )

    columns = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Columnas (ancho)')
    )

    bits_allocated = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Bits Allocados')
    )

    bits_stored = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Bits Almacenados')
    )

    photometric_interpretation = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Interpretación Fotométrica'),
        help_text=_('MONOCHROME1, MONOCHROME2, RGB, etc.')
    )

    # Posición espacial (para reconstrucción 3D)
    image_position_patient = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Posición de Imagen'),
        help_text=_('Coordenadas x, y, z del primer píxel')
    )

    slice_location = models.DecimalField(
        max_digits=15,
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name=_('Ubicación del Corte'),
        help_text=_('Posición relativa del corte en mm')
    )

    # Window/Level para visualización
    window_center = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_('Window Center')
    )

    window_width = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_('Window Width')
    )

    # Transfer Syntax (compresión)
    transfer_syntax_uid = models.CharField(
        max_length=128,
        blank=True,
        verbose_name=_('Transfer Syntax UID'),
        help_text=_('Codificación del archivo DICOM')
    )

    # Metadata completa
    dicom_metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Metadatos DICOM de la Instancia')
    )

    objects = TenantManager()

    class Meta:
        db_table = 'dicom_instance'
        verbose_name = _('Instancia DICOM')
        verbose_name_plural = _('Instancias DICOM')
        indexes = [
            models.Index(fields=['tenant', 'series']),
            models.Index(fields=['sop_instance_uid']),
            models.Index(fields=['instance_number']),
            models.Index(fields=['slice_location']),
        ]
        ordering = ['instance_number', 'slice_location']

    def __str__(self):
        return f"Instance {self.instance_number}: {self.file_name}"

    def calculate_file_hash(self, file_content: bytes) -> str:
        """
        Calcula el hash SHA-256 del archivo.
        """
        self.file_hash = hashlib.sha256(file_content).hexdigest()
        return self.file_hash

    def get_absolute_file_path(self):
        """
        Retorna la ruta absoluta del archivo.
        """
        from django.conf import settings
        import os
        return os.path.join(settings.MEDIA_ROOT, self.file_path)


class DicomAccessLog(models.Model):
    """
    Log de acceso a estudios DICOM para auditoría.
    """

    ACCESS_TYPE_CHOICES = [
        ('view', 'Visualización'),
        ('download', 'Descarga'),
        ('stream', 'Streaming'),
        ('export', 'Exportación'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        verbose_name=_('Tenant')
    )

    study = models.ForeignKey(
        DicomStudy,
        on_delete=models.CASCADE,
        related_name='access_logs',
        verbose_name=_('Estudio')
    )

    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_('Usuario')
    )

    access_type = models.CharField(
        max_length=20,
        choices=ACCESS_TYPE_CHOICES,
        verbose_name=_('Tipo de Acceso')
    )

    user_email = models.CharField(
        max_length=255,
        verbose_name=_('Email del Usuario')
    )

    user_name = models.CharField(
        max_length=255,
        verbose_name=_('Nombre del Usuario')
    )

    ip_address = models.GenericIPAddressField(
        null=True,
        verbose_name=_('Dirección IP')
    )

    user_agent = models.TextField(
        blank=True,
        verbose_name=_('User Agent')
    )

    accessed_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Fecha de Acceso')
    )

    # Hash para integridad del log
    log_hash = models.CharField(
        max_length=64,
        blank=True,
        verbose_name=_('Hash del Log')
    )

    class Meta:
        db_table = 'dicom_access_log'
        verbose_name = _('Log de Acceso DICOM')
        verbose_name_plural = _('Logs de Acceso DICOM')
        indexes = [
            models.Index(fields=['tenant', 'study']),
            models.Index(fields=['user', 'accessed_at']),
            models.Index(fields=['accessed_at']),
        ]
        ordering = ['-accessed_at']

    def __str__(self):
        return f"{self.access_type} - {self.study} - {self.accessed_at}"

    def save(self, *args, **kwargs):
        """
        Genera el hash de integridad antes de guardar.
        """
        import json
        if not self.log_hash:
            data = {
                'study_id': str(self.study_id),
                'user_id': str(self.user_id) if self.user_id else None,
                'access_type': self.access_type,
                'user_email': self.user_email,
                'ip_address': self.ip_address,
            }
            self.log_hash = hashlib.sha256(
                json.dumps(data, sort_keys=True).encode()
            ).hexdigest()
        super().save(*args, **kwargs)
