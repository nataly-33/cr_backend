from rest_framework import serializers
from .models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    """Serializer para logs de auditoría"""
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    is_valid_hash = serializers.SerializerMethodField()

    class Meta:
        model = AuditLog
        fields = [
            'id', 'tenant', 'tenant_name',
            'user', 'user_email', 'user_name',
            'action_type', 'resource_type', 'resource_id', 'resource_name',
            'ip_address', 'user_agent', 'request_method', 'request_path',
            'request_body', 'changes', 'response_status', 'error_message',
            'session_id', 'metadata', 'timestamp', 'log_hash', 'is_valid_hash'
        ]
        read_only_fields = ['id', 'timestamp', 'log_hash']

    def get_is_valid_hash(self, obj):
        """Verifica la integridad del log"""
        return obj.verify_integrity()


class AuditLogListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listados"""
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)

    class Meta:
        model = AuditLog
        fields = [
            'id', 'tenant_name', 'user_email', 'user_name',
            'action_type', 'resource_type', 'ip_address',
            'response_status', 'timestamp'
        ]