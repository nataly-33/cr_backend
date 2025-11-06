from django.contrib import admin
from .models import Notification, UserNotificationPreferences, NotificationAudit


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'type', 'channel', 'status', 'created_at']
    list_filter = ['type', 'channel', 'status', 'created_at']
    search_fields = ['user__email', 'title', 'body']
    readonly_fields = ['id', 'event_id', 'created_at', 'updated_at', 'sent_at', 'read_at']
    
    fieldsets = (
        ('Información', {
            'fields': ('id', 'tenant', 'user', 'type', 'channel', 'event_id')
        }),
        ('Contenido', {
            'fields': ('title', 'body', 'data', 'extra_metadata')
        }),
        ('Estado', {
            'fields': ('status', 'retry_count', 'last_error')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'sent_at', 'read_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(UserNotificationPreferences)
class UserNotificationPreferencesAdmin(admin.ModelAdmin):
    list_display = ['user', 'tenant', 'quiet_hours_enabled', 'email_digest_enabled', 'updated_at']
    list_filter = ['quiet_hours_enabled', 'email_digest_enabled', 'updated_at']
    search_fields = ['user__email']
    readonly_fields = ['id', 'updated_at']
    
    fieldsets = (
        ('Usuario', {
            'fields': ('id', 'tenant', 'user')
        }),
        ('Preferencias', {
            'fields': ('preferences', 'email_digest_enabled')
        }),
        ('Horarios de Silencio', {
            'fields': ('quiet_hours_enabled', 'quiet_hours_from', 'quiet_hours_to')
        }),
        ('Metadata', {
            'fields': ('updated_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(NotificationAudit)
class NotificationAuditAdmin(admin.ModelAdmin):
    list_display = ['id', 'notification', 'action', 'created_at']
    list_filter = ['action', 'created_at']
    search_fields = ['notification__user__email', 'detail']
    readonly_fields = ['id', 'created_at']
    
    fieldsets = (
        ('Auditoría', {
            'fields': ('id', 'tenant', 'notification', 'action', 'detail', 'created_at')
        }),
    )
