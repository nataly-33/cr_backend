"""
Script de verificación de configuración AWS para CliniDocs
Ejecutar: python verify_aws_config.py
"""

import os
import sys
import django

# Configurar Django - Usar el settings module del entorno (producción o desarrollo)
if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    # Si no está definido, intentar detectar automáticamente
    if os.getenv('DEBUG', 'False').lower() == 'false':
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
    else:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from apps.documents.storage import S3Storage
from apps.audit.services import AuditLogService
from apps.backup.services import BackupService
from apps.core.models import Tenant

def print_separator():
    print("\n" + "="*60 + "\n")

def verify_s3_documents():
    print("📦 VERIFICACIÓN S3 - DOCUMENTOS")
    print_separator()
    
    storage = S3Storage()
    print(f"✓ S3 habilitado: {storage.use_s3}")
    print(f"✓ Bucket: {storage.bucket_name}")
    
    if storage.use_s3:
        print("\n📁 TENANTS Y SUS SLUGS (para carpetas en S3):")
        tenants = Tenant.objects.all()
        if tenants.exists():
            for tenant in tenants:
                print(f"  - {tenant.name} → slug: '{tenant.slug}'")
                print(f"    Carpeta en S3: documents/{tenant.slug}/")
        else:
            print("  ⚠️ No hay tenants creados aún")
    else:
        print("\n⚠️ S3 deshabilitado - usando almacenamiento local")

def verify_cloudwatch():
    print_separator()
    print("📊 VERIFICACIÓN CLOUDWATCH - AUDIT LOGS")
    print_separator()
    
    service = AuditLogService()
    print(f"✓ CloudWatch habilitado: {service.cloudwatch_enabled}")
    
    if service.cloudwatch_enabled:
        print(f"✓ Log Group: {service.log_group}")
        print(f"✓ Log Stream: {service.log_stream}")
        print(f"✓ Región AWS: {os.getenv('AWS_REGION', 'us-east-1')}")
    else:
        print("\n⚠️ CloudWatch deshabilitado")
        print("Para habilitar, asegurar en .env:")
        print("  USE_CLOUDWATCH=True")
        print("  AWS_CLOUDWATCH_LOG_GROUP=/clinidocs-audit")
        print("  AWS_REGION=us-east-1")

def verify_backups():
    print_separator()
    print("💾 VERIFICACIÓN BACKUPS")
    print_separator()
    
    service = BackupService()
    print(f"✓ S3 Backup habilitado: {service.use_s3}")
    
    if service.use_s3:
        print(f"✓ Bucket destino: {service.s3_bucket}")
        print(f"✓ Los backups se guardan en: backups/{{tenant-slug}}/")
        print(f"\n📁 TENANTS QUE TENDRÁN BACKUP:")
        tenants = Tenant.objects.filter(subscription_status='active')
        if tenants.exists():
            for tenant in tenants:
                print(f"  - {tenant.name} → backups/{tenant.slug}/")
        else:
            print("  ⚠️ No hay tenants activos")
    else:
        print("\n⚠️ S3 Backup deshabilitado - backups locales")

def verify_celery_schedule():
    print_separator()
    print("⏰ VERIFICACIÓN CELERY BEAT - BACKUP AUTOMÁTICO")
    print_separator()
    
    from django_celery_beat.models import PeriodicTask
    
    try:
        task = PeriodicTask.objects.get(name='backup-sistema-diario')
        print(f"✓ Tarea encontrada: {task.name}")
        print(f"✓ Habilitada: {task.enabled}")
        print(f"✓ Schedule: {task.crontab}")
        print(f"✓ Task: {task.task}")
        print(f"\n📅 Horario: Todos los días a las 2:00 AM (hora Bolivia)")
    except PeriodicTask.DoesNotExist:
        print("⚠️ Tarea 'backup-sistema-diario' no encontrada")
        print("Ejecutar: python manage.py migrate")

def main():
    print("\n" + "="*60)
    print("  VERIFICACIÓN DE CONFIGURACIÓN AWS - CLINIDOCS")
    print("="*60)
    
    try:
        verify_s3_documents()
        verify_cloudwatch()
        verify_backups()
        verify_celery_schedule()
        
        print_separator()
        print("✅ VERIFICACIÓN COMPLETADA")
        print_separator()
        
        # Resumen
        from django.conf import settings
        print("\n📋 RESUMEN DE VARIABLES:")
        print(f"  USE_S3: {getattr(settings, 'USE_S3', False)}")
        print(f"  USE_CLOUDWATCH: {getattr(settings, 'USE_CLOUDWATCH', False)}")
        print(f"  USE_S3_BACKUP: {getattr(settings, 'USE_S3_BACKUP', False)}")
        print(f"  AWS_STORAGE_BUCKET_NAME: {getattr(settings, 'AWS_STORAGE_BUCKET_NAME', 'N/A')}")
        print(f"  AWS_CLOUDWATCH_LOG_GROUP: {getattr(settings, 'AWS_CLOUDWATCH_LOG_GROUP', 'N/A')}")
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
