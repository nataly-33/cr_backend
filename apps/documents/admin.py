from django.contrib import admin
from .models import ClinicalDocument, MedicalImage, DocumentAccessLog


@admin.register(ClinicalDocument)
class ClinicalDocumentAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'document_type',
        'document_date',
        'specialty',
        'doctor_name',
        'is_signed',
        'is_locked',
        'ocr_processed',
        'created_at'
    ]
    list_filter = [
        'document_type',
        'specialty',
        'is_signed',
        'is_locked',
        'ocr_processed',
        'tenant'
    ]
    search_fields = ['title', 'doctor_name', 'ocr_text']
    readonly_fields = [
        'id', 'file_hash', 'ocr_text', 'ocr_confidence',
        'digital_signature', 'created_at', 'updated_at'
    ]

    fieldsets = (
        ('Información Básica', {
            'fields': ('id', 'tenant', 'clinical_record', 'document_type', 'title', 'description')
        }),
        ('Detalles Médicos', {
            'fields': ('document_date', 'specialty', 'doctor_name', 'doctor_license', 'content', 'tags')
        }),
        ('Archivo', {
            'fields': ('file_path', 'file_name', 'file_size_bytes', 'mime_type', 'file_hash')
        }),
        ('OCR', {
            'fields': ('ocr_processed', 'ocr_text', 'ocr_confidence', 'ocr_job_id'),
            'classes': ('collapse',)
        }),
        ('Firma Digital', {
            'fields': ('is_signed', 'signed_at', 'signed_by', 'digital_signature', 'is_locked'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at', 'deleted_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(MedicalImage)
class MedicalImageAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'image_type',
        'study_date',
        'body_part',
        'enhancement_applied',
        'created_at'
    ]
    list_filter = ['image_type', 'enhancement_applied', 'tenant']
    search_fields = ['title', 'body_part']


@admin.register(DocumentAccessLog)
class DocumentAccessLogAdmin(admin.ModelAdmin):
    list_display = [
        'document',
        'user_name',
        'access_type',
        'ip_address',
        'accessed_at'
    ]
    list_filter = ['access_type', 'accessed_at']
    search_fields = ['user_name', 'user_email']
    readonly_fields = ['id', 'accessed_at']