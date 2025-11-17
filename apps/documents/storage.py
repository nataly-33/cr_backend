import boto3
from botocore.exceptions import ClientError
from django.conf import settings
from django.core.files.storage import FileSystemStorage
import logging
import os

logger = logging.getLogger(__name__)


class S3Storage:
    """Clase para manejar uploads a S3 o almacenamiento local"""

    def __init__(self):
        # Verificar si AWS está configurado
        self.use_s3 = hasattr(settings, 'AWS_ACCESS_KEY_ID') and settings.AWS_ACCESS_KEY_ID
        
        if self.use_s3:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_S3_REGION_NAME
            )
            self.bucket_name = settings.AWS_STORAGE_BUCKET_NAME
        else:
            # Usar almacenamiento local
            self.local_storage = FileSystemStorage(location=settings.MEDIA_ROOT)

    def upload_file(self, file_obj, file_path):
        """
        Sube un archivo a S3 o almacenamiento local
        
        Args:
            file_obj: Objeto de archivo de Django
            file_path: Ruta donde se guardará
            
        Returns:
            URL del archivo o None si falla
        """
        if self.use_s3:
            try:
                self.s3_client.upload_fileobj(
                    file_obj,
                    self.bucket_name,
                    file_path,
                    ExtraArgs={
                        'ContentType': file_obj.content_type,
                        'ServerSideEncryption': 'AES256'
                    }
                )

                url = f"https://{self.bucket_name}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{file_path}"
                logger.info(f"File uploaded successfully to S3: {url}")
                return url

            except ClientError as e:
                logger.error(f"Error uploading file to S3: {str(e)}")
                return None
        else:
            # Almacenamiento local
            try:
                # Crear directorio si no existe
                full_path = os.path.join(settings.MEDIA_ROOT, file_path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                
                # Guardar archivo
                saved_path = self.local_storage.save(file_path, file_obj)
                
                # Retornar URL completa
                base_url = getattr(settings, 'BACKEND_URL', 'http://localhost:8000')
                url = f"{base_url}{settings.MEDIA_URL}{saved_path}"
                logger.info(f"File uploaded successfully to local storage: {url}")
                return url
                
            except Exception as e:
                logger.error(f"Error uploading file to local storage: {str(e)}")
                return None

    def delete_file(self, file_path):
        """Elimina un archivo de S3 o almacenamiento local"""
        if self.use_s3:
            try:
                self.s3_client.delete_object(
                    Bucket=self.bucket_name,
                    Key=file_path
                )
                logger.info(f"File deleted successfully from S3: {file_path}")
                return True

            except ClientError as e:
                logger.error(f"Error deleting file from S3: {str(e)}")
                return False
        else:
            # Almacenamiento local
            try:
                full_path = os.path.join(settings.MEDIA_ROOT, file_path)
                if os.path.exists(full_path):
                    os.remove(full_path)
                    logger.info(f"File deleted successfully from local storage: {file_path}")
                return True
                
            except Exception as e:
                logger.error(f"Error deleting file from local storage: {str(e)}")
                return False

    def get_presigned_url(self, file_path, expiration=3600, force_download=False, filename=None):
        """
        Genera una URL firmada para acceso temporal al archivo (S3)
        o URL local (almacenamiento local)

        Args:
            file_path: Ruta del archivo
            expiration: Tiempo de expiración en segundos (solo para S3)
            force_download: Si True, fuerza descarga en lugar de visualización
            filename: Nombre del archivo para descarga (solo si force_download=True)

        Returns:
            URL del archivo o None si falla
        """
        if self.use_s3:
            try:
                params = {
                    'Bucket': self.bucket_name,
                    'Key': file_path
                }

                # Si se debe forzar descarga, agregar Content-Disposition
                if force_download and filename:
                    params['ResponseContentDisposition'] = f'attachment; filename="{filename}"'

                url = self.s3_client.generate_presigned_url(
                    'get_object',
                    Params=params,
                    ExpiresIn=expiration
                )
                return url

            except ClientError as e:
                logger.error(f"Error generating presigned URL: {str(e)}")
                return None
        else:
            # Para almacenamiento local, retornar la URL completa del archivo
            # En desarrollo, usar localhost:8000
            base_url = getattr(settings, 'BACKEND_URL', 'http://localhost:8000')
            return f"{base_url}{settings.MEDIA_URL}{file_path}"

    def file_exists(self, file_path):
        """Verifica si un archivo existe en S3 o almacenamiento local"""
        if self.use_s3:
            try:
                self.s3_client.head_object(
                    Bucket=self.bucket_name,
                    Key=file_path
                )
                return True
            except ClientError:
                return False
        else:
            # Almacenamiento local
            full_path = os.path.join(settings.MEDIA_ROOT, file_path)
            return os.path.exists(full_path)