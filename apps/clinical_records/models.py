import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import TenantAwareModel, TenantManager
from apps.patients.models import Patient


class ClinicalRecord(TenantAwareModel):
    """
    Historia Clínica del paciente
    """
    STATUS_CHOICES = [
        ('active', 'Activa'),
        ('archived', 'Archivada'),
        ('closed', 'Cerrada'),
    ]

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        verbose_name=_('Paciente')
    )

    record_number = models.CharField(
        max_length=100,
        verbose_name=_('Número de expediente'),
        help_text=_('Se genera automáticamente')
    )

    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name=_('Estado')
    )

    # Información clínica básica
    blood_type = models.CharField(
        max_length=10,
        blank=True,
        verbose_name=_('Tipo de sangre')
    )

    allergies = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Alergias'),
        help_text=_('[{"allergen": "...", "severity": "...", "reaction": "..."}]')
    )

    chronic_conditions = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Condiciones crónicas'),
        help_text=_('["Diabetes tipo 2", "Hipertensión"]')
    )

    medications = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Medicamentos actuales'),
        help_text=_('[{"name": "...", "dose": "...", "frequency": "..."}]')
    )

    family_history = models.TextField(
        blank=True,
        verbose_name=_('Antecedentes familiares')
    )

    social_history = models.TextField(
        blank=True,
        verbose_name=_('Antecedentes sociales')
    )

    # Metadata
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='clinical_records_created',
        verbose_name=_('Creado por')
    )

    objects = TenantManager()

    class Meta:
        db_table = 'clinical_record'
        verbose_name = _('Historia Clínica')
        verbose_name_plural = _('Historias Clínicas')
        unique_together = [['tenant', 'record_number']]
        indexes = [
            models.Index(fields=['tenant', 'patient']),
            models.Index(fields=['record_number']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.record_number} - {self.patient.get_full_name()}"

    def save(self, *args, **kwargs):
        """Generar número de expediente automáticamente"""
        if not self.record_number:
            self.record_number = self.generate_record_number()
        super().save(*args, **kwargs)

    def generate_record_number(self):
        """Genera un número único de expediente"""
        from datetime import datetime

        year = datetime.now().year
        count = ClinicalRecord.objects.filter(
            tenant=self.tenant,
            created_at__year=year
        ).count()

        return f"HC-{year}-{str(count + 1).zfill(6)}"


class ClinicalForm(TenantAwareModel):
    """
    Formularios clínicos asociados a una historia clínica.
    Incluye: Triaje, Notas de evolución, Recetas, Órdenes de laboratorio, etc.
    """
    FORM_TYPE_CHOICES = [
        ('triage', 'Triaje'),
        ('consultation', 'Consulta Médica'),
        ('evolution', 'Nota de Evolución'),
        ('prescription', 'Receta Médica'),
        ('lab_order', 'Orden de Laboratorio'),
        ('imaging_order', 'Orden de Imagenología'),
        ('procedure', 'Procedimiento'),
        ('discharge', 'Alta Médica'),
        ('referral', 'Referencia'),
        ('other', 'Otro'),
    ]

    clinical_record = models.ForeignKey(
        ClinicalRecord,
        on_delete=models.CASCADE,
        related_name='forms',
        verbose_name=_('Historia Clínica')
    )

    form_type = models.CharField(
        max_length=100,
        choices=FORM_TYPE_CHOICES,
        verbose_name=_('Tipo de formulario')
    )

    form_template_id = models.UUIDField(
        null=True,
        blank=True,
        verbose_name=_('ID de plantilla'),
        help_text=_('Si se usó una plantilla predefinida')
    )

    form_data = models.JSONField(
        default=dict,
        verbose_name=_('Datos del formulario'),
        help_text=_('Estructura JSON flexible según el tipo de formulario')
    )

    filled_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.PROTECT,
        related_name='filled_forms',
        verbose_name=_('Llenado por')
    )

    doctor_name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_('Nombre del doctor'),
        help_text=_('Opcional, se puede tomar del usuario')
    )

    doctor_specialty = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Especialidad del doctor')
    )

    form_date = models.DateTimeField(
        verbose_name=_('Fecha del formulario'),
        help_text=_('Fecha en que se llenó el formulario')
    )

    objects = TenantManager()

    class Meta:
        db_table = 'clinical_form'
        verbose_name = _('Formulario Clínico')
        verbose_name_plural = _('Formularios Clínicos')
        ordering = ['-form_date']
        indexes = [
            models.Index(fields=['tenant', 'clinical_record']),
            models.Index(fields=['form_type']),
            models.Index(fields=['-form_date']),
        ]

    def __str__(self):
        return f"{self.get_form_type_display()} - {self.clinical_record.record_number} - {self.form_date.strftime('%Y-%m-%d')}"

    def save(self, *args, **kwargs):
        """Auto-llenar doctor_name si está vacío"""
        if not self.doctor_name and self.filled_by:
            self.doctor_name = f"{self.filled_by.first_name} {self.filled_by.last_name}"
            if hasattr(self.filled_by, 'specialty') and self.filled_by.specialty:
                self.doctor_specialty = self.filled_by.specialty
        super().save(*args, **kwargs)