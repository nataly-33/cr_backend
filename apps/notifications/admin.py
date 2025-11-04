from django.contrib import admin
from .models import Notification, NotificationPreference, EmailLog


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'type', 'is_read', 'created_at')
    list_filter = ('type', 'is_read', 'created_at')
    search_fields = ('title', 'user__email')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Información General', {
            'fields': ('user', 'type', 'title', 'message')
        }),
        ('Relacionado', {
            'fields': ('related_model', 'related_id')
        }),
        ('Presentación', {
            'fields': ('icon', 'color')
        }),
        ('Estado', {
            'fields': ('is_read', 'read_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'max_emails_per_day')
    search_fields = ('user__email',)
    
    fieldsets = (
        ('Usuario', {
            'fields': ('user',)
        }),
        ('Notificaciones por Email', {
            'fields': (
                'document_uploaded_email',
                'record_created_email',
                'record_updated_email',
                'access_granted_email',
                'comment_added_email'
            )
        }),
        ('Límites', {
            'fields': ('max_emails_per_day',)
        }),
        ('Quiet Hours', {
            'fields': ('quiet_hours_start', 'quiet_hours_end')
        }),
        ('Digest', {
            'fields': ('send_daily_digest',)
        }),
    )


@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = ('user_email', 'notification_type', 'status', 'sent_at')
    list_filter = ('status', 'notification_type', 'created_at')
    search_fields = ('user_email', 'subject')
    readonly_fields = ('user_email', 'subject', 'notification_type', 'created_at', 'error_message')
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
