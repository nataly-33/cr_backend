import uuid
from django.db import models
from apps.core.models import TenantAwareModel


class ReportTemplate(TenantAwareModel):
    """Plantilla de reporte"""
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    report_type = models.CharField(max_length=100)  # documents, patients, analytics
    category = models.CharField(max_length=100, blank=True)
    
    query_template = models.TextField(blank=True)
    parameters = models.JSONField(default=dict)
    
    output_formats = models.JSONField(default=list)  # ['pdf', 'excel', 'csv']
    chart_config = models.JSONField(default=dict, blank=True)
    
    is_public = models.BooleanField(default=False)
    allowed_roles = models.JSONField(default=list)
    
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_report_templates'
    )
    
    class Meta:
        db_table = 'report_template'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name


class ReportExecution(TenantAwareModel):
    """Historial de reportes generados"""
    
    template = models.ForeignKey(
        ReportTemplate,
        on_delete=models.SET_NULL,
        null=True,
        related_name='executions'
    )
    
    executed_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='executed_reports'
    )
    
    parameters_used = models.JSONField(default=dict)
    output_format = models.CharField(max_length=50)
    
    file_path = models.CharField(max_length=500, blank=True)
    file_size_bytes = models.BigIntegerField(null=True)
    
    execution_time_ms = models.IntegerField(null=True)
    rows_returned = models.IntegerField(null=True)
    
    status = models.CharField(
        max_length=50,
        default='completed',
        choices=[
            ('pending', 'Pendiente'),
            ('processing', 'Procesando'),
            ('completed', 'Completado'),
            ('failed', 'Fallido'),
        ]
    )
    error_message = models.TextField(blank=True)
    
    class Meta:
        db_table = 'report_execution'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Report {self.id} - {self.status}"