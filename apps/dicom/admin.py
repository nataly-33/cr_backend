"""
Admin para modelos DICOM.
"""

from django.contrib import admin
from .models import DicomStudy, DicomSeries, DicomInstance, DicomAccessLog


@admin.register(DicomStudy)
class DicomStudyAdmin(admin.ModelAdmin):
    list_display = [
        'study_description',
        'modality',
        'patient',
        'study_date',
        'number_of_series',
        'number_of_instances',
        'status',
        'created_at',
    ]
    list_filter = ['modality', 'status', 'study_date', 'tenant']
    search_fields = [
        'study_instance_uid',
        'study_description',
        'accession_number',
        'patient__first_name',
        'patient__last_name',
    ]
    readonly_fields = [
        'id',
        'study_instance_uid',
        'study_hash',
        'number_of_series',
        'number_of_instances',
        'total_size_bytes',
        'created_at',
        'updated_at',
    ]
    raw_id_fields = ['patient', 'clinical_record', 'uploaded_by']
    date_hierarchy = 'study_date'


@admin.register(DicomSeries)
class DicomSeriesAdmin(admin.ModelAdmin):
    list_display = [
        'series_description',
        'modality',
        'series_number',
        'study',
        'number_of_instances',
        'created_at',
    ]
    list_filter = ['modality', 'tenant']
    search_fields = [
        'series_instance_uid',
        'series_description',
        'study__study_description',
    ]
    readonly_fields = [
        'id',
        'series_instance_uid',
        'number_of_instances',
        'total_size_bytes',
        'created_at',
        'updated_at',
    ]
    raw_id_fields = ['study']


@admin.register(DicomInstance)
class DicomInstanceAdmin(admin.ModelAdmin):
    list_display = [
        'file_name',
        'instance_number',
        'series',
        'rows',
        'columns',
        'file_size_bytes',
        'created_at',
    ]
    list_filter = ['tenant']
    search_fields = [
        'sop_instance_uid',
        'file_name',
        'series__series_description',
    ]
    readonly_fields = [
        'id',
        'sop_instance_uid',
        'file_hash',
        'created_at',
        'updated_at',
    ]
    raw_id_fields = ['series']


@admin.register(DicomAccessLog)
class DicomAccessLogAdmin(admin.ModelAdmin):
    list_display = [
        'study',
        'access_type',
        'user_name',
        'user_email',
        'ip_address',
        'accessed_at',
    ]
    list_filter = ['access_type', 'accessed_at', 'tenant']
    search_fields = ['user_email', 'user_name', 'study__study_description']
    readonly_fields = [
        'id',
        'log_hash',
        'accessed_at',
    ]
    date_hierarchy = 'accessed_at'
