import uuid
from django.db import models
from apps.core.models import BaseModel


class BackupJob(BaseModel):
    """Job de backup"""
    
    BACKUP_TYPE_CHOICES = [
        ('full', 'Completo'),
        ('incremental', 'Incremental'),
        ('differential', 'Diferencial'),
    ]
    
    SCOPE_CHOICES = [
        ('tenant', 'Por Tenant'),
        ('system', 'Sistema Completo'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('processing', 'Procesando'),
        ('completed', 'Completado'),
        ('failed', 'Fallido'),
    ]
    
    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='backups'
    )
    
    backup_type = models.CharField(max_length=50, choices=BACKUP_TYPE_CHOICES)
    backup_scope = models.CharField(max_length=100, choices=SCOPE_CHOICES)
    
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='pending')
    
    storage_location = models.CharField(max_length=500, blank=True)
    backup_size_bytes = models.BigIntegerField(null=True)
    
    includes_database = models.BooleanField(default=True)
    includes_files = models.BooleanField(default=True)
    includes_audit_logs = models.BooleanField(default=True)
    
    is_encrypted = models.BooleanField(default=True)
    encryption_key_id = models.CharField(max_length=255, blank=True)
    
    scheduled = models.BooleanField(default=False)
    schedule_cron = models.CharField(max_length=100, blank=True)
    
    can_restore = models.BooleanField(default=True)
    retention_until = models.DateField(null=True, blank=True)
    
    started_at = models.DateTimeField(null=True)
    completed_at = models.DateTimeField(null=True)
    
    error_message = models.TextField(blank=True)
    retry_count = models.IntegerField(default=0)
    
    metadata = models.JSONField(default=dict)
    
    class Meta:
        db_table = 'backup_job'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Backup {self.id} - {self.status}"