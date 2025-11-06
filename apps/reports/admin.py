from django.contrib import admin
from .models import ReportTemplate, ReportExecution, AIAnalysis


@admin.register(ReportTemplate)
class ReportTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'report_type', 'is_public', 'created_by', 'created_at')
    list_filter = ('is_public', 'report_type', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('id', 'tenant', 'created_at', 'updated_at')
    fieldsets = (
        ('Información Básica', {
            'fields': ('name', 'description', 'report_type', 'category')
        }),
        ('Configuración', {
            'fields': ('query_template', 'parameters', 'output_formats', 'chart_config')
        }),
        ('Permisos', {
            'fields': ('is_public', 'allowed_roles', 'created_by')
        }),
        ('Metadata', {
            'fields': ('id', 'tenant', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ReportExecution)
class ReportExecutionAdmin(admin.ModelAdmin):
    list_display = ('id', 'report_type', 'status', 'executed_by', 'created_at', 'execution_time_ms')
    list_filter = ('status', 'output_format', 'created_at')
    search_fields = ('executed_by__full_name', 'template__name')
    readonly_fields = ('id', 'tenant', 'created_at', 'updated_at', 'execution_time_ms')
    fieldsets = (
        ('Ejecución', {
            'fields': ('template', 'executed_by', 'status', 'error_message')
        }),
        ('Parámetros', {
            'fields': ('parameters_used', 'output_format')
        }),
        ('Resultados', {
            'fields': ('file_path', 'file_size_bytes', 'rows_returned', 'execution_time_ms')
        }),
        ('Metadata', {
            'fields': ('id', 'tenant', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def report_type(self, obj):
        return obj.template.report_type if obj.template else '-'
    report_type.short_description = 'Tipo de Reporte'


@admin.register(AIAnalysis)
class AIAnalysisAdmin(admin.ModelAdmin):
    list_display = ('id', 'report_execution', 'status', 'confidence_score', 'created_at')
    list_filter = ('status', 'confidence_score', 'created_at')
    search_fields = ('report_execution__id', 'analysis')
    readonly_fields = ('id', 'tenant', 'created_at', 'updated_at')
    fieldsets = (
        ('Relación', {
            'fields': ('report_execution', 'status')
        }),
        ('Análisis', {
            'fields': ('analysis', 'insights', 'key_findings', 'confidence_score')
        }),
        ('Resumen', {
            'fields': ('summary', 'summary_key_points'),
            'classes': ('collapse',)
        }),
        ('Recomendaciones', {
            'fields': ('recommendations',),
            'classes': ('collapse',)
        }),
        ('Errores', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id', 'tenant', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
