from django.db import models
from apps.core.models import TenantAwareModel
from apps.accounts.models import User


class NotificationType(models.TextChoices):
    DOCUMENT_UPLOADED = 'document_uploaded', 'Documento Cargado'
    RECORD_CREATED = 'record_created', 'Historia Creada'
    RECORD_UPDATED = 'record_updated', 'Historia Actualizada'
    ACCESS_GRANTED = 'access_granted', 'Acceso Otorgado'
    COMMENT_ADDED = 'comment_added', 'Comentario Agregado'


class Notification(TenantAwareModel):
    """Notificación in-app para usuarios"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=50, choices=NotificationType.choices)
    title = models.CharField(max_length=255)
    message = models.TextField()
    
    # Link a recurso relacionado
    related_model = models.CharField(max_length=50, null=True, blank=True)
    related_id = models.CharField(max_length=36, null=True, blank=True)
    
    # Estado
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    icon = models.CharField(max_length=50, default='bell')
    color = models.CharField(max_length=20, default='blue')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['user', '-created_at'])]
        verbose_name = 'Notificación'
        verbose_name_plural = 'Notificaciones'
    
    def __str__(self):
        return f"{self.title} - {self.user}"


class NotificationPreference(TenantAwareModel):
    """Preferencias de notificación por usuario"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_preference')
    
    # Preferencias por tipo de evento
    document_uploaded_email = models.BooleanField(default=True)
    record_created_email = models.BooleanField(default=True)
    record_updated_email = models.BooleanField(default=False)
    access_granted_email = models.BooleanField(default=True)
    comment_added_email = models.BooleanField(default=True)
    
    # Frecuencia máxima
    max_emails_per_day = models.IntegerField(default=10)
    quiet_hours_start = models.TimeField(null=True, blank=True)  # Ej: 21:00
    quiet_hours_end = models.TimeField(null=True, blank=True)    # Ej: 08:00
    
    # Email digest
    send_daily_digest = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Preferencia de Notificación'
        verbose_name_plural = 'Preferencias de Notificación'
    
    def __str__(self):
        return f"Preferencias - {self.user}"


class EmailLog(models.Model):
    """Log de emails enviados (para tracking)"""
    user_email = models.CharField(max_length=255)
    subject = models.CharField(max_length=255)
    notification_type = models.CharField(max_length=50)
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pendiente'),
            ('sent', 'Enviado'),
            ('failed', 'Fallido'),
        ],
        default='pending'
    )
    error_message = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Log de Email'
        verbose_name_plural = 'Logs de Emails'
    
    def __str__(self):
        return f"{self.notification_type} - {self.user_email} - {self.status}"
