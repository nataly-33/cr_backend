import uuid
import hashlib
import json
from django.db import models
from django.utils.translation import gettext_lazy as _


class AuditLog(models.Model):
    """
    Log de auditoría inviolable (caja negra)
    """
    ACTION_TYPE_CHOICES = [
        ('CREATE', 'Crear'),
        ('READ', 'Leer'),
        ('UPDATE', 'Actualizar'),
        ('DELETE', 'Eliminar'),
        ('EXPORT', 'Exportar'),
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
        ('PASSWORD_CHANGE', 'Cambio de Contraseña'),
        ('PERMISSION_CHANGE', 'Cambio de Permisos'),
        ('SIGN', 'Firma Digital'),
        ('DOWNLOAD', 'Descarga'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_('Tenant')
    )

    # Usuario que realizó la acción
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('Usuario')
    )
    user_email = models.CharField(
        max_length=255,
        verbose_name=_('Email del usuario')
    )
    user_name = models.CharField(
        max_length=255,
        verbose_name=_('Nombre del usuario')
    )

    # Acción realizada
    action_type = models.CharField(
        max_length=100,
        choices=ACTION_TYPE_CHOICES,
        verbose_name=_('Tipo de acción')
    )

    # Recurso afectado
    resource_type = models.CharField(
        max_length=100,
        verbose_name=_('Tipo de recurso'),
        help_text=_('patient, document, user, etc.')
    )
    resource_id = models.UUIDField(
        null=True,
        blank=True,
        verbose_name=_('ID del recurso')
    )
    resource_name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_('Nombre del recurso')
    )

    # Detalles de la petición
    ip_address = models.GenericIPAddressField(
        verbose_name=_('Dirección IP')
    )
    user_agent = models.TextField(
        blank=True,
        verbose_name=_('User Agent')
    )
    request_method = models.CharField(
        max_length=10,
        blank=True,
        verbose_name=_('Método HTTP')
    )
    request_path = models.CharField(
        max_length=500,
        blank=True,
        verbose_name=_('Ruta de la petición')
    )
    request_body = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Cuerpo de la petición')
    )

    # Cambios realizados (before/after)
    changes = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Cambios realizados'),
        help_text=_('{"before": {...}, "after": {...}}')
    )

    # Respuesta
    response_status = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_('Status code de respuesta')
    )
    error_message = models.TextField(
        blank=True,
        verbose_name=_('Mensaje de error')
    )

    # Contexto adicional
    session_id = models.UUIDField(
        null=True,
        blank=True,
        verbose_name=_('ID de sesión')
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Metadata adicional')
    )

    # Timestamp inmutable
    timestamp = models.DateTimeField(
        auto_now_add=True,
        editable=False,
        verbose_name=_('Fecha y hora')
    )

    # Hash inviolable (SHA-256)
    log_hash = models.CharField(
        max_length=64,
        editable=False,
        verbose_name=_('Hash SHA-256'),
        help_text=_('Hash del log para detectar manipulación')
    )

    class Meta:
        db_table = 'audit_log'
        verbose_name = _('Log de Auditoría')
        verbose_name_plural = _('Logs de Auditoría')
        indexes = [
            models.Index(fields=['tenant', '-timestamp']),
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['resource_type', 'resource_id']),
            models.Index(fields=['action_type']),
            models.Index(fields=['ip_address']),
            models.Index(fields=['-timestamp']),
        ]
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.action_type} - {self.resource_type} - {self.timestamp}"

    def save(self, *args, **kwargs):
        """Genera el hash del log antes de guardar"""
        if not self.log_hash:
            self.log_hash = self.generate_hash()
        super().save(*args, **kwargs)

    def generate_hash(self):
        """
        Genera un hash SHA-256 inviolable del log
        Incluye: id, user_id, action, resource, timestamp, changes
        """
        hash_data = {
            'id': str(self.id),
            'user_id': str(self.user_id) if self.user_id else '',
            'user_email': self.user_email,
            'action_type': self.action_type,
            'resource_type': self.resource_type,
            'resource_id': str(self.resource_id) if self.resource_id else '',
            'timestamp': self.timestamp.isoformat() if self.timestamp else '',
            'changes': json.dumps(self.changes, sort_keys=True),
            'ip_address': str(self.ip_address)
        }

        # Convertir a string JSON ordenado
        hash_string = json.dumps(hash_data, sort_keys=True)

        # Generar hash SHA-256
        return hashlib.sha256(hash_string.encode('utf-8')).hexdigest()

    def verify_integrity(self):
        """
        Verifica la integridad del log comparando el hash almacenado
        con un hash recalculado
        
        Returns:
            bool: True si el log no ha sido manipulado
        """
        current_hash = self.log_hash
        self.log_hash = None
        recalculated_hash = self.generate_hash()
        self.log_hash = current_hash

        return current_hash == recalculated_hash