from django.contrib import admin
from .models import Patient


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = [
        'identity_document',
        'first_name',
        'last_name',
        'gender',
        'date_of_birth',
        'phone',
        'created_at'
    ]
    list_filter = ['gender', 'created_at', 'tenant']
    search_fields = ['first_name', 'last_name', 'identity_document', 'email']
    readonly_fields = ['id', 'created_at', 'updated_at', 'created_by']

    fieldsets = (
        ('Identificación', {
            'fields': ('id', 'tenant', 'identity_document_type', 'identity_document')
        }),
        ('Información Personal', {
            'fields': ('first_name', 'last_name', 'date_of_birth', 'gender')
        }),
        ('Contacto', {
            'fields': ('phone', 'email', 'address', 'city')
        }),
        ('Emergencia', {
            'fields': ('emergency_contact',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at', 'deleted_at'),
            'classes': ('collapse',)
        }),
    )