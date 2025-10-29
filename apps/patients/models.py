import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import TenantAwareModel, TenantManager


class Patient(TenantAwareModel):
    """
    Modelo de Paciente con multi-tenancy
    """
    GENDER_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Femenino'),
        ('O', 'Otro'),
    ]

    DOCUMENT_TYPE_CHOICES = [
        ('CI', 'Cédula de Identidad'),
        ('Pasaporte', 'Pasaporte'),
        ('DNI', 'DNI'),
        ('RUT', 'RUT'),
    ]

    # Identificación
    identity_document_type = models.CharField(
        max_length=50,
        choices=DOCUMENT_TYPE_CHOICES,
        default='CI',
        verbose_name=_('Tipo de documento')
    )
    identity_document = models.CharField(
        max_length=100,
        verbose_name=_('Número de documento')
    )

    # Información personal
    first_name = models.CharField(
        max_length=100,
        verbose_name=_('Nombres')
    )
    last_name = models.CharField(
        max_length=100,
        verbose_name=_('Apellidos')
    )
    date_of_birth = models.DateField(
        verbose_name=_('Fecha de nacimiento')
    )
    gender = models.CharField(
        max_length=1,
        choices=GENDER_CHOICES,
        verbose_name=_('Género')
    )

    # Contacto
    phone = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Teléfono')
    )
    email = models.EmailField(
        blank=True,
        verbose_name=_('Email')
    )
    address = models.TextField(
        blank=True,
        verbose_name=_('Dirección')
    )
    city = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Ciudad')
    )

    # Contacto de emergencia
    emergency_contact = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Contacto de emergencia'),
        help_text=_('{"name": "...", "relationship": "...", "phone": "..."}')
    )

    # Metadata
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='patients_created',
        verbose_name=_('Creado por')
    )

    objects = TenantManager()

    class Meta:
        db_table = 'patient'
        verbose_name = _('Paciente')
        verbose_name_plural = _('Pacientes')
        unique_together = [['tenant', 'identity_document']]
        indexes = [
            models.Index(fields=['tenant', 'identity_document']),
            models.Index(fields=['first_name', 'last_name']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.identity_document}"

    def get_full_name(self):
        """Retorna el nombre completo del paciente"""
        return f"{self.first_name} {self.last_name}"

    def get_age(self):
        """Calcula la edad del paciente"""
        from datetime import date
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )