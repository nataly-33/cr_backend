from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = [
        'timestamp',
        'action_type',
        'user_email',
        'resource_type',
        'ip_address',
        'response_status',
        'verify_status'
    ]
    list_filter = [
        'action_type',
        'resource_type',
        'response_status',
        'timestamp'
    ]
    search_fields = ['user_email', 'user_name', 'ip_address', 'resource_name']
    readonly_fields = [
        'id', 'timestamp', 'log_hash',
        'user', 'user_email', 'user_name',
        'action_type', 'resource_type', 'resource_id',
        'ip_address', 'user_agent', 'request_method',
        'request_path', 'request_body', 'changes',
        'response_status', 'error_message'
    ]

    def verify_status(self, obj):
        """Muestra si el log es válido"""
        is_valid = obj.verify_integrity()
        return '✓ Válido' if is_valid else '✗ MANIPULADO'
    verify_status.short_description = 'Integridad'

    def has_add_permission(self, request):
        """No permitir agregar logs manualmente"""
        return False

    def has_change_permission(self, request, obj=None):
        """No permitir editar logs"""
        return False

    def has_delete_permission(self, request, obj=None):
        """No permitir eliminar logs"""
        return False