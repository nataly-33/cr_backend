"""
Servicio de almacenamiento para archivos DICOM.
Soporta almacenamiento local y S3.
"""

import os
import hashlib
import logging
import uuid
from typing import Tuple, Optional, BinaryIO
from datetime import datetime

from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

logger = logging.getLogger(__name__)


class DicomStorageService:
    """
    Servicio para almacenar y recuperar archivos DICOM.

    Estructura de almacenamiento:
        dicom/
            {tenant_id}/
                {study_uid}/
                    {series_uid}/
                        {instance_uid}.dcm

    Uso:
        storage = DicomStorageService(tenant_id)
        file_path, file_hash = storage.save_instance(
            study_uid='1.2.3...',
            series_uid='1.2.3...',
            instance_uid='1.2.3...',
            file_content=binary_content
        )
    """

    BASE_DIR = 'dicom'

    def __init__(self, tenant_id: str):
        """
        Inicializa el servicio de almacenamiento.

        Args:
            tenant_id: ID del tenant (UUID como string)
        """
        self.tenant_id = str(tenant_id)
        self.use_s3 = getattr(settings, 'USE_S3', False)

    def get_study_path(self, study_uid: str) -> str:
        """
        Obtiene la ruta base para un estudio.

        Args:
            study_uid: Study Instance UID

        Returns:
            Ruta relativa al directorio del estudio
        """
        # Sanitizar el UID (remover caracteres problemáticos)
        safe_study_uid = self._sanitize_uid(study_uid)
        return os.path.join(self.BASE_DIR, self.tenant_id, safe_study_uid)

    def get_series_path(self, study_uid: str, series_uid: str) -> str:
        """
        Obtiene la ruta base para una serie.

        Args:
            study_uid: Study Instance UID
            series_uid: Series Instance UID

        Returns:
            Ruta relativa al directorio de la serie
        """
        safe_series_uid = self._sanitize_uid(series_uid)
        return os.path.join(self.get_study_path(study_uid), safe_series_uid)

    def get_instance_path(
        self,
        study_uid: str,
        series_uid: str,
        instance_uid: str
    ) -> str:
        """
        Obtiene la ruta completa para una instancia DICOM.

        Args:
            study_uid: Study Instance UID
            series_uid: Series Instance UID
            instance_uid: SOP Instance UID

        Returns:
            Ruta relativa al archivo .dcm
        """
        safe_instance_uid = self._sanitize_uid(instance_uid)
        return os.path.join(
            self.get_series_path(study_uid, series_uid),
            f"{safe_instance_uid}.dcm"
        )

    def save_instance(
        self,
        study_uid: str,
        series_uid: str,
        instance_uid: str,
        file_content: bytes,
        original_filename: Optional[str] = None
    ) -> Tuple[str, str, int]:
        """
        Guarda un archivo DICOM.

        Args:
            study_uid: Study Instance UID
            series_uid: Series Instance UID
            instance_uid: SOP Instance UID
            file_content: Contenido binario del archivo
            original_filename: Nombre original del archivo (opcional)

        Returns:
            Tuple de (file_path, file_hash, file_size)
        """
        # Calcular hash
        file_hash = hashlib.sha256(file_content).hexdigest()
        file_size = len(file_content)

        # Generar ruta
        file_path = self.get_instance_path(study_uid, series_uid, instance_uid)

        # Guardar archivo
        if self.use_s3:
            self._save_to_s3(file_path, file_content)
        else:
            self._save_to_local(file_path, file_content)

        logger.info(f"DICOM guardado: {file_path} ({file_size} bytes)")

        return file_path, file_hash, file_size

    def save_instance_from_file(
        self,
        study_uid: str,
        series_uid: str,
        instance_uid: str,
        file_obj: BinaryIO
    ) -> Tuple[str, str, int]:
        """
        Guarda un archivo DICOM desde un objeto file-like.

        Args:
            study_uid: Study Instance UID
            series_uid: Series Instance UID
            instance_uid: SOP Instance UID
            file_obj: Objeto file-like

        Returns:
            Tuple de (file_path, file_hash, file_size)
        """
        file_content = file_obj.read()
        return self.save_instance(
            study_uid, series_uid, instance_uid, file_content
        )

    def get_instance(self, file_path: str) -> bytes:
        """
        Recupera el contenido de un archivo DICOM.

        Args:
            file_path: Ruta relativa al archivo

        Returns:
            Contenido binario del archivo
        """
        if self.use_s3:
            return self._read_from_s3(file_path)
        else:
            return self._read_from_local(file_path)

    def get_instance_stream(self, file_path: str) -> BinaryIO:
        """
        Obtiene un stream del archivo DICOM para streaming.

        Args:
            file_path: Ruta relativa al archivo

        Returns:
            Objeto file-like para streaming
        """
        if self.use_s3:
            return self._get_s3_stream(file_path)
        else:
            return self._get_local_stream(file_path)

    def delete_instance(self, file_path: str) -> bool:
        """
        Elimina un archivo DICOM.

        Args:
            file_path: Ruta relativa al archivo

        Returns:
            True si se eliminó correctamente
        """
        try:
            if self.use_s3:
                self._delete_from_s3(file_path)
            else:
                self._delete_from_local(file_path)
            logger.info(f"DICOM eliminado: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error eliminando DICOM {file_path}: {e}")
            return False

    def delete_study(self, study_uid: str) -> bool:
        """
        Elimina todos los archivos de un estudio.

        Args:
            study_uid: Study Instance UID

        Returns:
            True si se eliminó correctamente
        """
        study_path = self.get_study_path(study_uid)
        try:
            if self.use_s3:
                self._delete_directory_s3(study_path)
            else:
                self._delete_directory_local(study_path)
            logger.info(f"Estudio DICOM eliminado: {study_path}")
            return True
        except Exception as e:
            logger.error(f"Error eliminando estudio {study_path}: {e}")
            return False

    def get_file_url(self, file_path: str, expiration: int = 3600) -> str:
        """
        Obtiene una URL para acceder al archivo.

        Args:
            file_path: Ruta relativa al archivo
            expiration: Tiempo de expiración en segundos (solo S3)

        Returns:
            URL del archivo
        """
        if self.use_s3:
            return self._get_s3_url(file_path, expiration)
        else:
            # URL local a través de Django
            return f"{settings.MEDIA_URL}{file_path}"

    def file_exists(self, file_path: str) -> bool:
        """
        Verifica si un archivo existe.

        Args:
            file_path: Ruta relativa al archivo

        Returns:
            True si el archivo existe
        """
        if self.use_s3:
            return self._exists_in_s3(file_path)
        else:
            return self._exists_in_local(file_path)

    # =========================================================================
    # Métodos privados - Local Storage
    # =========================================================================

    def _save_to_local(self, file_path: str, content: bytes) -> None:
        """Guarda archivo en almacenamiento local."""
        full_path = os.path.join(settings.MEDIA_ROOT, file_path)

        # Crear directorio si no existe
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        with open(full_path, 'wb') as f:
            f.write(content)

    def _read_from_local(self, file_path: str) -> bytes:
        """Lee archivo desde almacenamiento local."""
        full_path = os.path.join(settings.MEDIA_ROOT, file_path)

        with open(full_path, 'rb') as f:
            return f.read()

    def _get_local_stream(self, file_path: str) -> BinaryIO:
        """Obtiene stream de archivo local."""
        full_path = os.path.join(settings.MEDIA_ROOT, file_path)
        return open(full_path, 'rb')

    def _delete_from_local(self, file_path: str) -> None:
        """Elimina archivo del almacenamiento local."""
        full_path = os.path.join(settings.MEDIA_ROOT, file_path)
        if os.path.exists(full_path):
            os.remove(full_path)

    def _delete_directory_local(self, dir_path: str) -> None:
        """Elimina directorio recursivamente del almacenamiento local."""
        import shutil
        full_path = os.path.join(settings.MEDIA_ROOT, dir_path)
        if os.path.exists(full_path):
            shutil.rmtree(full_path)

    def _exists_in_local(self, file_path: str) -> bool:
        """Verifica si archivo existe en almacenamiento local."""
        full_path = os.path.join(settings.MEDIA_ROOT, file_path)
        return os.path.exists(full_path)

    # =========================================================================
    # Métodos privados - S3 Storage
    # =========================================================================

    def _get_s3_client(self):
        """Obtiene cliente S3 de boto3."""
        import boto3
        return boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME,
        )

    def _save_to_s3(self, file_path: str, content: bytes) -> None:
        """Guarda archivo en S3."""
        s3 = self._get_s3_client()
        s3.put_object(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            Key=file_path,
            Body=content,
            ContentType='application/dicom',
        )

    def _read_from_s3(self, file_path: str) -> bytes:
        """Lee archivo desde S3."""
        s3 = self._get_s3_client()
        response = s3.get_object(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            Key=file_path,
        )
        return response['Body'].read()

    def _get_s3_stream(self, file_path: str) -> BinaryIO:
        """Obtiene stream de archivo S3."""
        s3 = self._get_s3_client()
        response = s3.get_object(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            Key=file_path,
        )
        return response['Body']

    def _delete_from_s3(self, file_path: str) -> None:
        """Elimina archivo de S3."""
        s3 = self._get_s3_client()
        s3.delete_object(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            Key=file_path,
        )

    def _delete_directory_s3(self, dir_path: str) -> None:
        """Elimina directorio de S3."""
        s3 = self._get_s3_client()

        # Listar todos los objetos con el prefijo
        paginator = s3.get_paginator('list_objects_v2')
        pages = paginator.paginate(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            Prefix=dir_path,
        )

        # Eliminar en lotes
        for page in pages:
            if 'Contents' in page:
                objects = [{'Key': obj['Key']} for obj in page['Contents']]
                s3.delete_objects(
                    Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                    Delete={'Objects': objects},
                )

    def _exists_in_s3(self, file_path: str) -> bool:
        """Verifica si archivo existe en S3."""
        s3 = self._get_s3_client()
        try:
            s3.head_object(
                Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                Key=file_path,
            )
            return True
        except Exception:
            return False

    def _get_s3_url(self, file_path: str, expiration: int = 3600) -> str:
        """Genera URL pre-firmada de S3."""
        s3 = self._get_s3_client()
        return s3.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                'Key': file_path,
            },
            ExpiresIn=expiration,
        )

    # =========================================================================
    # Utilidades
    # =========================================================================

    def _sanitize_uid(self, uid: str) -> str:
        """
        Sanitiza un UID DICOM para usar como nombre de directorio.
        Los UIDs DICOM solo contienen dígitos y puntos.
        """
        # Reemplazar puntos por guiones bajos para compatibilidad
        # con sistemas de archivos
        return uid.replace('.', '_')

    def get_study_size(self, study_uid: str) -> int:
        """
        Calcula el tamaño total de un estudio en bytes.

        Args:
            study_uid: Study Instance UID

        Returns:
            Tamaño total en bytes
        """
        study_path = self.get_study_path(study_uid)
        total_size = 0

        if self.use_s3:
            s3 = self._get_s3_client()
            paginator = s3.get_paginator('list_objects_v2')
            pages = paginator.paginate(
                Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                Prefix=study_path,
            )
            for page in pages:
                if 'Contents' in page:
                    total_size += sum(obj['Size'] for obj in page['Contents'])
        else:
            full_path = os.path.join(settings.MEDIA_ROOT, study_path)
            if os.path.exists(full_path):
                for dirpath, dirnames, filenames in os.walk(full_path):
                    for f in filenames:
                        fp = os.path.join(dirpath, f)
                        total_size += os.path.getsize(fp)

        return total_size
