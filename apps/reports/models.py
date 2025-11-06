import uuid
from django.db import models
from apps.core.models import TenantAwareModel


class ReportTemplate(TenantAwareModel):
    """Plantillas de reportes predefinidos"""
    
    REPORT_TYPES = [
        ('documents_by_type', 'Documentos por Tipo'),
        ('patients_summary', 'Resumen de Pacientes'),
        ('activity_log', 'Registro de Actividad'),
        ('usage_statistics', 'Estadísticas de Uso'),
    ]

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    report_type = models.CharField(max_length=100, choices=REPORT_TYPES)  
    category = models.CharField(max_length=100, blank=True)
    
    query_template = models.TextField(blank=True)
    parameters = models.JSONField(default=dict)

    output_formats = models.JSONField(default=list) #pdf, excel, csv
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
    
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('processing', 'Procesando'),
        ('completed', 'Completado'),
        ('failed', 'Fallido'),
    ]
    
    REPORT_TYPE_CHOICES = [
        ('documents', 'Documentos Clínicos'),
        ('patients', 'Pacientes'),
        ('clinical_records', 'Historias Clínicas'),
        ('analytics', 'Analíticas'),
        ('audit', 'Auditoría'),
        ('users', 'Usuarios'),
    ]

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
    
    report_type = models.CharField(
        max_length=50,
        choices=REPORT_TYPE_CHOICES,
        blank=True,
        default='documents'
    )
    
    parameters_used = models.JSONField(default=dict)
    output_format = models.CharField(max_length=50)
    
    file_path = models.CharField(max_length=500, blank=True)
    file_size_bytes = models.BigIntegerField(null=True)
    
    execution_time_ms = models.IntegerField(null=True)
    rows_returned = models.IntegerField(null=True)
    
    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default='pending'
    )
    error_message = models.TextField(blank=True)
    
    class Meta:
        db_table = 'report_execution'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Report {self.id} - {self.status}"


class AIAnalysis(TenantAwareModel):
    """Análisis generados por IA para reportes"""
    
    PRIORITY_CHOICES = [
        ('critical', 'Crítica'),
        ('high', 'Alta'),
        ('medium', 'Media'),
        ('low', 'Baja'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('completed', 'Completado'),
        ('failed', 'Fallido'),
    ]

    report_execution = models.OneToOneField(
        ReportExecution,
        on_delete=models.CASCADE,
        related_name='ai_analysis'
    )
    
    # Analysis data
    analysis = models.TextField()
    insights = models.JSONField(default=list)  # List of insight strings
    key_findings = models.JSONField(default=list)  # List of key findings
    confidence_score = models.FloatField(default=0.0)
    
    # Summary data
    summary = models.TextField(blank=True, null=True)
    summary_key_points = models.JSONField(default=list, blank=True)
    
    # Recommendations
    recommendations = models.JSONField(default=list, blank=True)
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    error_message = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'ai_analysis'
        verbose_name = 'AI Analysis'
        verbose_name_plural = 'AI Analyses'
        indexes = [
            models.Index(fields=['report_execution', '-created_at']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"AI Analysis for {self.report_execution_id}"