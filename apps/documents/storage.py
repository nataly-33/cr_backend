import boto3
from botocore.exceptions import ClientError
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class S3Storage:
    """Clase para manejar uploads a S3"""

    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME
        )
        self.bucket_name = settings.AWS_STORAGE_BUCKET_NAME

    def upload_file(self, file_obj, file_path):
        """
        Sube un archivo a S3
        
        Args:
            file_obj: Objeto de archivo de Django
            file_path: Ruta donde se guardará en S3
            
        Returns:
            URL del archivo en S3 o None si falla
        """
        try:
            self.s3_client.upload_fileobj(
                file_obj,
                self.bucket_name,
                file_path,
                ExtraArgs={
                    'ContentType': file_obj.content_type,
                    'ServerSideEncryption': 'AES256'  # Encriptación en reposo
                }
            )

            # Generar URL
            url = f"https://{self.bucket_name}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{file_path}"
            logger.info(f"File uploaded successfully to {url}")
            return url

        except ClientError as e:
            logger.error(f"Error uploading file to S3: {str(e)}")
            return None

    def delete_file(self, file_path):
        """Elimina un archivo de S3"""
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=file_path
            )
            logger.info(f"File deleted successfully: {file_path}")
            return True

        except ClientError as e:
            logger.error(f"Error deleting file from S3: {str(e)}")
            return False

    def get_presigned_url(self, file_path, expiration=3600):
        """
        Genera una URL firmada para acceso temporal al archivo
        
        Args:
            file_path: Ruta del archivo en S3
            expiration: Tiempo de expiración en segundos (default: 1 hora)
            
        Returns:
            URL firmada o None si falla
        """
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': file_path
                },
                ExpiresIn=expiration
            )
            return url

        except ClientError as e:
            logger.error(f"Error generating presigned URL: {str(e)}")
            return None

    def file_exists(self, file_path):
        """Verifica si un archivo existe en S3"""
        try:
            self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=file_path
            )
            return True
        except ClientError:
            return False