from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Tenant


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'subdomain',
        'subscription_plan',
        'subscription_status',
        'created_at',
        'is_active_status'
    ]
    list_filter = ['subscription_plan', 'subscription_status', 'created_at']
    search_fields = ['name', 'subdomain', 'email']
    readonly_fields = ['id', 'created_at', 'updated_at']

    fieldsets = (
        ('Información Básica', {
            'fields': ('id', 'name', 'slug', 'subdomain')
        }),
        ('Suscripción', {
            'fields': (
                'subscription_plan',
                'subscription_status',
                'subscription_start',
                'subscription_end'
            )
        }),
        ('Contacto', {
            'fields': ('email', 'phone', 'address')
        }),
        ('Límites', {
            'fields': ('max_users', 'max_storage_gb')
        }),
        ('Configuración', {
            'fields': ('settings',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'deleted_at'),
            'classes': ('collapse',)
        }),
    )

    def is_active_status(self, obj):
        return obj.is_active()
    is_active_status.boolean = True
    is_active_status.short_description = 'Activo'