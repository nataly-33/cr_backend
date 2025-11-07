"""
Serializers para notificaciones: validación y transformación de datos.
"""

from rest_framework import serializers
from django.utils import timezone

from .models import (
    Notification,
    UserNotificationPreferences,
    NotificationAudit,
    NotificationType,
    NotificationChannel,
    NotificationStatus,
)


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer para notificaciones individuales."""
    
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    channel_display = serializers.CharField(source='get_channel_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Notification
        fields = [
            'id', 'user', 'type', 'type_display', 'channel', 'channel_display',
            'title', 'body', 'data', 'extra_metadata', 'status', 'status_display',
            'event_id', 'sent_at', 'read_at', 'created_at', 'updated_at',
            'retry_count', 'last_error'
        ]
        read_only_fields = [
            'id', 'user', 'sent_at', 'read_at', 'created_at', 'updated_at',
            'retry_count', 'last_error', 'type_display', 'channel_display', 'status_display'
        ]


class NotificationListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listados."""
    
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Notification
        fields = [
            'id', 'type', 'type_display', 'title', 'body', 'status', 'status_display',
            'read_at', 'created_at'
        ]
        read_only_fields = fields


class NotificationMarkAsReadSerializer(serializers.Serializer):
    """Serializer para marcar notificación como leída."""
    
    def update(self, instance, validated_data):
        instance.mark_as_read()
        return instance


class UserNotificationPreferencesSerializer(serializers.ModelSerializer):
    """Serializer para preferencias de notificación."""
    
    # Mostrar todas las preferencias con defaults
    all_preferences = serializers.SerializerMethodField()
    
    class Meta:
        model = UserNotificationPreferences
        fields = [
            'id', 'user', 'preferences', 'all_preferences',
            'quiet_hours_enabled', 'quiet_hours_from', 'quiet_hours_to',
            'email_digest_enabled', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'updated_at']
    
    def get_all_preferences(self, obj):
        """Retornar todas las preferencias con defaults."""
        return obj.get_all_preferences()
    
    def validate_quiet_hours_from(self, value):
        """Validar que sea hora válida."""
        if value is not None:
            try:
                # value ya es TimeField
                return value
            except (ValueError, TypeError):
                raise serializers.ValidationError("Hora inválida")
        return value
    
    def validate_quiet_hours_to(self, value):
        """Validar que sea hora válida."""
        if value is not None:
            try:
                return value
            except (ValueError, TypeError):
                raise serializers.ValidationError("Hora inválida")
        return value
    
    def validate(self, data):
        """Validar que las horas de silencio sean coherentes."""
        quiet_hours_enabled = data.get('quiet_hours_enabled', self.instance.quiet_hours_enabled if self.instance else False)
        quiet_hours_from = data.get('quiet_hours_from', self.instance.quiet_hours_from if self.instance else None)
        quiet_hours_to = data.get('quiet_hours_to', self.instance.quiet_hours_to if self.instance else None)
        
        if quiet_hours_enabled and (not quiet_hours_from or not quiet_hours_to):
            raise serializers.ValidationError(
                "Cuando está activado el silencio, debe definir 'quiet_hours_from' y 'quiet_hours_to'."
            )
        
        if quiet_hours_from and quiet_hours_to and quiet_hours_from >= quiet_hours_to:
            raise serializers.ValidationError(
                "'quiet_hours_from' debe ser menor que 'quiet_hours_to'."
            )
        
        return data


class EventPayloadSerializer(serializers.Serializer):
    """
    Serializer para el payload de evento que llega del orquestador.
    
    Ejemplo:
    {
        "event_type": "appointment.created",
        "event_id": "evt_20251104_123",
        "tenant_id": "clinicA",
        "actor_id": 42,
        "resource": { "type": "appointment", "id": 991 },
        "data": {
            "patient_name": "Fer",
            "doctor_name": "Dr. Pérez",
            "scheduled_at": "2025-11-05T09:00:00-04:00"
        },
        "occurred_at": "2025-11-04T12:00:00-04:00"
    }
    """
    
    event_type = serializers.ChoiceField(choices=NotificationType.values)
    event_id = serializers.CharField(max_length=255)
    tenant_id = serializers.UUIDField()
    actor_id = serializers.IntegerField()
    resource = serializers.JSONField()
    data = serializers.JSONField()
    occurred_at = serializers.DateTimeField()
    
    def validate_resource(self, value):
        """Validar que resource tenga type e id."""
        if not isinstance(value, dict) or 'type' not in value or 'id' not in value:
            raise serializers.ValidationError(
                "resource debe ser un objeto con 'type' e 'id'"
            )
        return value


class NotificationAuditSerializer(serializers.ModelSerializer):
    """Serializer para auditoría de notificaciones (read-only)."""
    
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    
    class Meta:
        model = NotificationAudit
        fields = ['id', 'notification', 'action', 'action_display', 'detail', 'created_at']
        read_only_fields = fields


class NotificationStatsSerializer(serializers.Serializer):
    """Serializer para estadísticas de notificaciones."""
    
    total = serializers.IntegerField()
    unread = serializers.IntegerField()
    queued = serializers.IntegerField()
    sent = serializers.IntegerField()
    failed = serializers.IntegerField()
    by_type = serializers.DictField()  # {type: count}
    by_channel = serializers.DictField()  # {channel: count}
