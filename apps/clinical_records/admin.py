from django.contrib import admin
from .models import ClinicalRecord


@admin.register(ClinicalRecord)
class ClinicalRecordAdmin(admin.ModelAdmin):
    list_display = [
        'record_number',
        'patient',
        'status',
        'blood_type',
        'created_at'
    ]
    list_filter = ['status', 'created_at', 'tenant']
    search_fields = ['record_number', 'patient__first_name', 'patient__last_name']
    readonly_fields = ['id', 'record_number', 'created_at', 'updated_at']