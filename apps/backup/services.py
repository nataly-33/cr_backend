import subprocess
import os
from datetime import datetime, timedelta
from django.conf import settings
from .models import BackupJob


class BackupService:
    """Servicio de backup"""
    
    def __init__(self):
        self.backup_dir = getattr(settings, 'BACKUP_DIR', '/tmp/backups')
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def create_backup(self, tenant=None, includes_files=True):
        """Crear backup"""
        
        # Crear job
        job = BackupJob.objects.create(
            tenant=tenant,
            backup_type='full',
            backup_scope='tenant' if tenant else 'system',
            includes_database=True,
            includes_files=includes_files,
            status='processing',
            started_at=datetime.now()
        )
        
        try:
            # Generar nombre de archivo
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            tenant_slug = tenant.slug if tenant else 'system'
            filename = f'backup_{tenant_slug}_{timestamp}.sql'
            filepath = os.path.join(self.backup_dir, filename)
            
            # Ejecutar pg_dump
            db_config = settings.DATABASES['default']
            
            command = [
                'pg_dump',
                '-h', db_config.get('HOST', 'localhost'),
                '-p', str(db_config.get('PORT', 5432)),
                '-U', db_config['USER'],
                '-d', db_config['NAME'],
                '-F', 'c',  # Custom format
                '-f', filepath
            ]
            
            # Agregar filtro por tenant si aplica
            if tenant:
                command.extend([
                    '--schema-only',  # TODO: Implementar filtrado por tenant
                ])
            
            # Ejecutar comando
            env = os.environ.copy()
            env['PGPASSWORD'] = db_config['PASSWORD']
            
            result = subprocess.run(
                command,
                env=env,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                raise Exception(f"pg_dump error: {result.stderr}")
            
            # Obtener tamaño
            file_size = os.path.getsize(filepath)
            
            # Actualizar job
            job.status = 'completed'
            job.storage_location = filepath
            job.backup_size_bytes = file_size
            job.completed_at = datetime.now()
            job.retention_until = datetime.now().date() + timedelta(days=30)
            job.save()
            
            return job
            
        except Exception as e:
            job.status = 'failed'
            job.error_message = str(e)
            job.completed_at = datetime.now()
            job.save()
            raise
    
    def restore_backup(self, job_id):
        """Restaurar backup"""
        
        job = BackupJob.objects.get(id=job_id)
        
        if not job.can_restore:
            raise Exception("Este backup no puede ser restaurado")
        
        if not os.path.exists(job.storage_location):
            raise Exception("Archivo de backup no encontrado")
        
        try:
            # Ejecutar pg_restore
            db_config = settings.DATABASES['default']
            
            command = [
                'pg_restore',
                '-h', db_config.get('HOST', 'localhost'),
                '-p', str(db_config.get('PORT', 5432)),
                '-U', db_config['USER'],
                '-d', db_config['NAME'],
                '-c',  # Clean (drop) database objects before recreating
                job.storage_location
            ]
            
            env = os.environ.copy()
            env['PGPASSWORD'] = db_config['PASSWORD']
            
            result = subprocess.run(
                command,
                env=env,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                raise Exception(f"pg_restore error: {result.stderr}")
            
            return True
            
        except Exception as e:
            raise Exception(f"Error al restaurar: {str(e)}")
        
    """       
    def _upload_to_s3(self, local_path, filename):
        Sube backup a S3
        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME
        )
        
        s3_key = f"backups/{self.tenant.subdomain}/{filename}"
        
        s3_client.upload_file(
            local_path,
            settings.AWS_STORAGE_BUCKET_NAME,
            s3_key,
            ExtraArgs={'ServerSideEncryption': 'AES256'}
        )
        
        # Generar URL firmada válida por 30 días
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                'Key': s3_key
            },
            ExpiresIn=2592000  # 30 días
        )
        
        return url

    def _download_from_s3(self, s3_url, local_path):
        Descarga backup desde S3
        # Extraer bucket y key de la URL
        # Implementación simplificada
        pass
    """