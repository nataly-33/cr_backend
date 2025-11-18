import subprocess
import os
import gzip
import shutil
from datetime import datetime, timedelta
from django.conf import settings
from .models import BackupJob


class BackupService:
    """Servicio de backup con soporte para almacenamiento local y S3"""

    def __init__(self):
        self.backup_dir = getattr(settings, 'BACKUPS_DIR', settings.MEDIA_ROOT / 'backups')
        os.makedirs(self.backup_dir, exist_ok=True)

        # Configuración S3 - Usar el MISMO bucket para documentos y backups
        self.use_s3 = getattr(settings, 'USE_S3_BACKUP', False)
        if self.use_s3:
            import boto3
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=getattr(settings, 'AWS_S3_REGION_NAME', 'us-east-1')
            )
            # Los backups irán a la carpeta "backups/" dentro del mismo bucket
            self.s3_bucket = getattr(settings, 'AWS_STORAGE_BUCKET_NAME', None)
    
    def create_backup(self, tenant=None, includes_files=True):
        """Crear backup con compresión y upload a S3 (opcional)"""

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
            filepath_gz = f'{filepath}.gz'

            # Ejecutar pg_dump
            db_config = settings.DATABASES['default']

            # Determinar el motor de base de datos
            engine = db_config.get('ENGINE', '')

            if 'postgresql' in engine:
                # PostgreSQL backup
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
                    # TODO: Implementar filtrado por tenant usando WHERE clauses
                    pass

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

            elif 'sqlite3' in engine:
                # SQLite backup - simple copy
                db_path = db_config['NAME']
                shutil.copy2(db_path, filepath)
            else:
                raise Exception(f"Base de datos no soportada: {engine}")

            # Comprimir el backup con gzip
            print(f"Comprimiendo backup: {filename}")
            with open(filepath, 'rb') as f_in:
                with gzip.open(filepath_gz, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)

            # Eliminar archivo sin comprimir
            os.remove(filepath)

            # Obtener tamaño del archivo comprimido
            file_size = os.path.getsize(filepath_gz)

            # Subir a S3 si está configurado
            storage_location = filepath_gz
            if self.use_s3 and self.s3_bucket:
                print(f"Subiendo backup a S3...")
                s3_url = self._upload_to_s3(filepath_gz, f'{filename}.gz', tenant)
                storage_location = s3_url
                print(f"Backup subido a S3: {s3_url}")

                # Eliminar archivo local después de subir a S3
                os.remove(filepath_gz)

            # Actualizar job
            job.status = 'completed'
            job.storage_location = storage_location
            job.backup_size_bytes = file_size
            job.completed_at = datetime.now()
            job.retention_until = datetime.now().date() + timedelta(days=30)
            job.save()

            print(f"✓ Backup completado: {storage_location} ({file_size / 1024 / 1024:.2f} MB)")

            return job

        except Exception as e:
            job.status = 'failed'
            job.error_message = str(e)
            job.completed_at = datetime.now()
            job.save()
            raise
    
    def restore_backup(self, job_id):
        """Restaurar backup con soporte para S3 y archivos comprimidos"""

        job = BackupJob.objects.get(id=job_id)

        if not job.can_restore:
            raise Exception("Este backup no puede ser restaurado")

        temp_file = None
        decompressed_file = None

        try:
            storage_location = job.storage_location

            # Si el backup está en S3, descargarlo primero
            if storage_location.startswith('s3://'):
                print("Descargando backup desde S3...")
                temp_file = os.path.join(self.backup_dir, f'temp_restore_{job.id}.sql.gz')
                storage_location = self._download_from_s3(storage_location, temp_file)
                print(f"Backup descargado: {temp_file}")

            # Verificar que el archivo existe
            if not os.path.exists(storage_location):
                raise Exception("Archivo de backup no encontrado")

            # Si el archivo está comprimido, descomprimirlo
            if storage_location.endswith('.gz'):
                print("Descomprimiendo backup...")
                decompressed_file = storage_location[:-3]  # Remove .gz extension
                with gzip.open(storage_location, 'rb') as f_in:
                    with open(decompressed_file, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                restore_file = decompressed_file
                print(f"Backup descomprimido: {decompressed_file}")
            else:
                restore_file = storage_location

            # Ejecutar pg_restore o copiar SQLite
            db_config = settings.DATABASES['default']
            engine = db_config.get('ENGINE', '')

            if 'postgresql' in engine:
                print("Restaurando PostgreSQL...")
                command = [
                    'pg_restore',
                    '-h', db_config.get('HOST', 'localhost'),
                    '-p', str(db_config.get('PORT', 5432)),
                    '-U', db_config['USER'],
                    '-d', db_config['NAME'],
                    '-c',  # Clean (drop) database objects before recreating
                    restore_file
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

            elif 'sqlite3' in engine:
                print("Restaurando SQLite...")
                db_path = db_config['NAME']
                # Backup actual database before restore
                backup_current = f"{db_path}.pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                shutil.copy2(db_path, backup_current)
                # Restore
                shutil.copy2(restore_file, db_path)
                print(f"Base de datos anterior respaldada en: {backup_current}")

            print("✓ Backup restaurado exitosamente")
            return True

        except Exception as e:
            raise Exception(f"Error al restaurar: {str(e)}")

        finally:
            # Limpiar archivos temporales
            if temp_file and os.path.exists(temp_file):
                os.remove(temp_file)
            if decompressed_file and os.path.exists(decompressed_file):
                os.remove(decompressed_file)
        
    def _upload_to_s3(self, local_path, filename, tenant=None):
        """Sube backup a S3 con encriptación"""
        tenant_slug = tenant.slug if tenant else 'system'
        s3_key = f"backups/{tenant_slug}/{filename}"

        # Upload con encriptación server-side
        self.s3_client.upload_file(
            local_path,
            self.s3_bucket,
            s3_key,
            ExtraArgs={'ServerSideEncryption': 'AES256'}
        )

        # Retornar la S3 URL completa
        return f"s3://{self.s3_bucket}/{s3_key}"

    def _download_from_s3(self, s3_url, local_path):
        """Descarga backup desde S3"""
        # Extraer bucket y key de la URL (formato: s3://bucket/key)
        if not s3_url.startswith('s3://'):
            raise ValueError("URL inválida. Debe ser formato s3://bucket/key")

        # Parse S3 URL
        s3_url_parts = s3_url.replace('s3://', '').split('/', 1)
        bucket = s3_url_parts[0]
        key = s3_url_parts[1]

        # Descargar archivo
        self.s3_client.download_file(bucket, key, local_path)
        return local_path