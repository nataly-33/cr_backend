"""
Notificaciones: modelos para notificaciones en-app, email y push.

Características:
- Aislamiento por tenant
- Preferencias de usuario (opt-in/out por tipo y canal)
- Auditoría completa
- Idempotencia (event_id único)
- Reintentos automáticos
"""

import uuid
from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.utils import timezone

from apps.core.models import TenantAwareModel, TenantManager
from apps.accounts.models import User


class NotificationType(models.TextChoices):
    """Tipos de eventos que generan notificaciones."""
    APPOINTMENT_CREATED = 'appointment.created', 'Cita creada'
    APPOINTMENT_CANCELED = 'appointment.canceled', 'Cita cancelada'
    APPOINTMENT_REMINDER = 'appointment.reminder', 'Recordatorio de cita'
    CLINICAL_RESULT = 'clinical_record.result', 'Resultado clínico'
    LOW_STOCK = 'inventory.low_stock', 'Stock bajo'
    DOCUMENT_UPLOADED = 'document.uploaded', 'Documento cargado'
    USER_ADDED = 'user.added', 'Usuario agregado'
    SYSTEM_ALERT = 'system.alert', 'Alerta del sistema'


class NotificationChannel(models.TextChoices):
    """Canales de entrega de notificaciones."""
    IN_APP = 'in_app', 'En aplicación'
    EMAIL = 'email', 'Correo electrónico'
    PUSH = 'push', 'Notificación push (móvil)'


class NotificationStatus(models.TextChoices):
    """Estados de una notificación."""
    QUEUED = 'queued', 'Encolada'
    SENT = 'sent', 'Enviada'
    DELIVERED = 'delivered', 'Entregada'
    FAILED = 'failed', 'Falló'
    READ = 'read', 'Leída'


class Notification(TenantAwareModel):
    """
    Notificación individual para un usuario.
    
    Campos:
    - type: tipo de evento que generó la notificación
    - channel: canal de entrega (in_app, email, push)
    - user: destinatario
    - title: asunto/título (≤70 chars)
    - body: cuerpo del mensaje (≤300 chars)
    - data: datos JSON adicionales (variables, IDs de recursos, etc.)
    - status: estado de envío
    - event_id: ID único del evento (para idempotencia)
    - sent_at: cuándo se envió
    - read_at: cuándo se marcó como leída
    - extra_metadata: campos flexibles (link, icon, color, etc.)
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    
    type = models.CharField(
        max_length=50,
        choices=NotificationType.choices,
        db_index=True
    )
    channel = models.CharField(
        max_length=20,
        choices=NotificationChannel.choices,
        default=NotificationChannel.IN_APP
    )
    
    # Contenido
    title = models.CharField(max_length=70)
    body = models.CharField(max_length=300)
    data = models.JSONField(default=dict, blank=True)  # {patient_name, doctor_name, etc.}
    extra_metadata = models.JSONField(default=dict, blank=True)  # {link, icon, color, etc.}
    
    # Estado y tracking
    status = models.CharField(
        max_length=20,
        choices=NotificationStatus.choices,
        default=NotificationStatus.QUEUED,
        db_index=True
    )
    
    # Idempotencia
    event_id = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        help_text='ID único del evento para evitar duplicados'
    )
    
    # Timestamps
    sent_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Manejo de reintentos
    retry_count = models.PositiveIntegerField(default=0)
    last_error = models.TextField(blank=True, null=True)
    
    objects = TenantManager()
    
    class Meta:
        db_table = 'notification'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant', 'user', 'status']),
            models.Index(fields=['tenant', 'user', 'read_at']),
            models.Index(fields=['tenant', 'type']),
        ]
    
    def __str__(self):
        return f"[{self.type}] {self.title} → {self.user.email}"
    
    def mark_as_read(self):
        """Marcar notificación como leída."""
        self.status = NotificationStatus.READ
        self.read_at = timezone.now()
        self.save(update_fields=['status', 'read_at', 'updated_at'])
    
    def mark_as_sent(self, sent_at=None):
        """Marcar notificación como enviada."""
        self.status = NotificationStatus.SENT
        self.sent_at = sent_at or timezone.now()
        self.save(update_fields=['status', 'sent_at', 'updated_at'])
    
    def mark_as_failed(self, error_message: str):
        """Marcar como fallida y guardar el error."""
        self.status = NotificationStatus.FAILED
        self.last_error = error_message
        self.save(update_fields=['status', 'last_error', 'updated_at'])


class UserNotificationPreferences(TenantAwareModel):
    """
    Preferencias de notificación del usuario.
    
    Permite opt-in/out por tipo de evento y canal.
    Incluye horarios de silencio opcionales.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='notification_preferences'
    )
    
    # Matriz de preferencias: {type: {channel: bool}}
    # Ej: {"appointment.created": {"in_app": true, "email": true}, ...}
    preferences = models.JSONField(
        default=dict,
        blank=True,
        help_text='Matriz de tipos × canales con opt-in/out'
    )
    
    # Horarios de silencio
    quiet_hours_enabled = models.BooleanField(default=False)
    quiet_hours_from = models.TimeField(
        null=True,
        blank=True,
        help_text='Hora de inicio del silencio (HH:MM)'
    )
    quiet_hours_to = models.TimeField(
        null=True,
        blank=True,
        help_text='Hora de fin del silencio (HH:MM)'
    )
    
    # Otros
    email_digest_enabled = models.BooleanField(
        default=False,
        help_text='Agrupar notificaciones en resumen diario'
    )
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = TenantManager()
    
    class Meta:
        db_table = 'user_notification_preferences'
    
    def __str__(self):
        return f"Preferencias de {self.user.email}"
    
    def is_enabled(self, notification_type: str, channel: str) -> bool:
        """
        Verificar si un tipo×canal está habilitado.
        Por defecto, todo está habilitado.
        """
        if not self.preferences:
            return True
        
        type_prefs = self.preferences.get(notification_type, {})
        return type_prefs.get(channel, True)
    
    def get_all_preferences(self) -> dict:
        """
        Obtener todas las preferencias con defaults.
        """
        defaults = {
            notif_type: {
                channel: True
                for channel in NotificationChannel.values
            }
            for notif_type in NotificationType.values
        }
        
        # Merge con preferencias guardadas
        if self.preferences:
            for notif_type, channels in self.preferences.items():
                if notif_type in defaults:
                    defaults[notif_type].update(channels)
        
        return defaults


class NotificationAudit(TenantAwareModel):
    """
    Auditoría de notificaciones (quién/qué/cuándo).
    
    Permite rastrear:
    - Cuándo se creó/envió/falló una notificación
    - Razones de fallos o descartes
    - Integridad y conformidad
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    notification = models.ForeignKey(
        Notification,
        on_delete=models.CASCADE,
        related_name='audit_logs',
        null=True,
        blank=True
    )
    
    ACTION_CHOICES = [
        ('created', 'Creada'),
        ('sent', 'Enviada'),
        ('delivered', 'Entregada'),
        ('failed', 'Falló'),
        ('duplicate_ignored', 'Duplicado ignorado'),
        ('tenant_mismatch', 'Aislamiento tenant'),
        ('preference_skipped', 'Omitida por preferencia'),
        ('quiet_hours', 'Omitida por horario'),
        ('read', 'Leída'),
    ]
    
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    detail = models.TextField(blank=True)  # Razón del evento
    created_at = models.DateTimeField(auto_now_add=True)
    
    objects = TenantManager()
    
    class Meta:
        db_table = 'notification_audit'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant', 'notification', 'action']),
            models.Index(fields=['tenant', 'created_at']),
        ]
    
    def __str__(self):
        return f"[{self.action}] {self.notification} at {self.created_at}"
