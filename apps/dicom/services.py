"""
Servicios de negocio para gestión de estudios DICOM.

Este módulo contiene:
- DicomIngestionService: Servicio principal para ingestión de archivos DICOM
- ingest_dicom_file(): Función para procesar un archivo DICOM individual
- ingest_dicom_files(): Función para procesar múltiples archivos DICOM
- DicomRetrieveService: Servicio para recuperar y streaming de archivos

Dependencias:
    pip install pydicom
"""

import logging
import zipfile
import hashlib
from io import BytesIO
from typing import List, Dict, Any, Optional, Tuple, Union, BinaryIO
from uuid import UUID
from dataclasses import dataclass

from django.db import transaction
from django.utils import timezone
from django.core.files.uploadedfile import InMemoryUploadedFile, TemporaryUploadedFile

from apps.patients.models import Patient
from apps.clinical_records.models import ClinicalRecord
from apps.core.models import Tenant, get_current_tenant, set_current_tenant

from .models import DicomStudy, DicomSeries, DicomInstance, DicomAccessLog
from .utils.dicom_parser import DicomParser
from .utils.dicom_storage import DicomStorageService

logger = logging.getLogger(__name__)


# =============================================================================
# DATACLASSES PARA RESULTADOS
# =============================================================================

@dataclass
class IngestionResult:
    """Resultado de la ingestión de archivos DICOM."""
    study: DicomStudy
    series_created: List[DicomSeries]
    instances_created: List[DicomInstance]
    patient_matched: bool
    patient_created: bool
    errors: List[str]

    @property
    def success(self) -> bool:
        return len(self.errors) == 0

    @property
    def total_instances(self) -> int:
        return len(self.instances_created)


@dataclass
class PatientMatchResult:
    """Resultado del matching de paciente."""
    patient: Optional[Patient]
    matched: bool
    created: bool
    match_method: str  # 'id', 'name_birthdate', 'created', 'provided'


# =============================================================================
# ESTRATEGIAS DE MATCHING DE PACIENTE
# =============================================================================

class PatientMatchingStrategy:
    """
    Estrategias para resolver el paciente cuando el DICOM contiene
    información de paciente que puede o no coincidir con un Patient existente.

    Estrategias disponibles:
    - REQUIRE_EXISTING: Requiere que se proporcione un patient_id válido
    - MATCH_OR_FAIL: Intenta hacer match por PatientID del DICOM, falla si no encuentra
    - MATCH_OR_CREATE: Intenta match, crea placeholder si no encuentra
    - ALWAYS_USE_PROVIDED: Siempre usa el patient_id proporcionado, ignora DICOM
    """
    REQUIRE_EXISTING = 'require_existing'
    MATCH_OR_FAIL = 'match_or_fail'
    MATCH_OR_CREATE = 'match_or_create'
    ALWAYS_USE_PROVIDED = 'always_use_provided'


class PatientMatcher:
    """
    Servicio para hacer match de pacientes basado en metadata DICOM.
    """

    def __init__(self, tenant: Tenant, strategy: str = PatientMatchingStrategy.REQUIRE_EXISTING):
        self.tenant = tenant
        self.strategy = strategy

    def match_patient(
        self,
        dicom_metadata: Dict[str, Any],
        provided_patient_id: Optional[UUID] = None
    ) -> PatientMatchResult:
        """
        Intenta hacer match de un paciente basado en la metadata DICOM.

        Args:
            dicom_metadata: Metadata extraída del DICOM (nivel study)
            provided_patient_id: ID de paciente proporcionado externamente

        Returns:
            PatientMatchResult con el paciente encontrado/creado
        """
        # Si se proporciona un patient_id, usarlo directamente
        if provided_patient_id:
            try:
                patient = Patient.objects.get(
                    id=provided_patient_id,
                    tenant=self.tenant
                )
                return PatientMatchResult(
                    patient=patient,
                    matched=True,
                    created=False,
                    match_method='provided'
                )
            except Patient.DoesNotExist:
                if self.strategy == PatientMatchingStrategy.ALWAYS_USE_PROVIDED:
                    raise ValueError(f"Paciente {provided_patient_id} no encontrado")

        # Estrategia: Siempre usar el proporcionado
        if self.strategy == PatientMatchingStrategy.ALWAYS_USE_PROVIDED:
            if not provided_patient_id:
                raise ValueError("Se requiere patient_id con la estrategia ALWAYS_USE_PROVIDED")

        # Estrategia: Requiere existente
        if self.strategy == PatientMatchingStrategy.REQUIRE_EXISTING:
            if not provided_patient_id:
                raise ValueError(
                    "Se requiere proporcionar un patient_id. "
                    "El sistema no soporta creación automática de pacientes."
                )

        # Extraer información del paciente del DICOM
        dicom_patient_id = dicom_metadata.get('patient_id', '')
        dicom_patient_name = dicom_metadata.get('patient_name', '')
        dicom_birth_date = dicom_metadata.get('patient_birth_date')

        # Intentar match por PatientID del DICOM
        if dicom_patient_id:
            patient = self._match_by_dicom_id(dicom_patient_id)
            if patient:
                return PatientMatchResult(
                    patient=patient,
                    matched=True,
                    created=False,
                    match_method='id'
                )

        # Intentar match por nombre y fecha de nacimiento
        if dicom_patient_name and dicom_birth_date:
            patient = self._match_by_name_and_birthdate(
                dicom_patient_name,
                dicom_birth_date
            )
            if patient:
                return PatientMatchResult(
                    patient=patient,
                    matched=True,
                    created=False,
                    match_method='name_birthdate'
                )

        # Si llegamos aquí, no encontramos match
        if self.strategy == PatientMatchingStrategy.MATCH_OR_FAIL:
            raise ValueError(
                f"No se encontró paciente con PatientID={dicom_patient_id} "
                f"o nombre={dicom_patient_name}"
            )

        # Estrategia: Crear placeholder
        if self.strategy == PatientMatchingStrategy.MATCH_OR_CREATE:
            patient = self._create_placeholder_patient(dicom_metadata)
            return PatientMatchResult(
                patient=patient,
                matched=False,
                created=True,
                match_method='created'
            )

        # Por defecto, fallar
        raise ValueError("No se pudo resolver el paciente para el estudio DICOM")

    def _match_by_dicom_id(self, dicom_patient_id: str) -> Optional[Patient]:
        """Busca paciente por el PatientID del DICOM."""
        # Buscar en identity_document o en dicom_metadata de estudios previos
        patient = Patient.objects.filter(
            tenant=self.tenant,
            identity_document=dicom_patient_id,
            deleted_at__isnull=True
        ).first()

        return patient

    def _match_by_name_and_birthdate(
        self,
        name: str,
        birth_date
    ) -> Optional[Patient]:
        """Busca paciente por nombre y fecha de nacimiento."""
        # Parsear nombre DICOM (formato: Apellido^Nombre)
        name_parts = str(name).replace('^', ' ').split()
        if len(name_parts) < 2:
            return None

        # Intentar match aproximado
        patient = Patient.objects.filter(
            tenant=self.tenant,
            date_of_birth=birth_date,
            deleted_at__isnull=True
        ).filter(
            first_name__icontains=name_parts[-1],
            last_name__icontains=name_parts[0]
        ).first()

        return patient

    def _create_placeholder_patient(self, dicom_metadata: Dict[str, Any]) -> Patient:
        """
        Crea un paciente placeholder basado en la metadata DICOM.
        Este paciente deberá ser completado/verificado posteriormente.
        """
        name = dicom_metadata.get('patient_name', 'DICOM Patient')
        name_parts = str(name).replace('^', ' ').split()

        first_name = name_parts[-1] if len(name_parts) > 1 else 'Desconocido'
        last_name = name_parts[0] if name_parts else 'DICOM'

        patient = Patient.objects.create(
            tenant=self.tenant,
            first_name=first_name,
            last_name=last_name,
            identity_document=dicom_metadata.get('patient_id', f'DICOM-{timezone.now().timestamp()}'),
            identity_document_type='CI',
            date_of_birth=dicom_metadata.get('patient_birth_date') or timezone.now().date(),
            gender=self._parse_gender(dicom_metadata.get('patient_sex', '')),
        )

        logger.warning(
            f"Paciente placeholder creado: {patient.id} - {first_name} {last_name}"
        )

        return patient

    def _parse_gender(self, sex: str) -> str:
        """Convierte el sexo DICOM a gender del modelo (1 carácter)."""
        sex_map = {
            'M': 'M',
            'F': 'F',
            'O': 'O',
        }
        return sex_map.get(sex.upper(), 'O') if sex else 'O'


# =============================================================================
# SERVICIO PRINCIPAL DE INGESTIÓN
# =============================================================================

class DicomIngestionService:
    """
    Servicio principal para ingestión de archivos DICOM.

    Uso básico:
        service = DicomIngestionService(tenant, user)
        result = service.ingest_file(file, patient_id=patient_id)
        # o
        result = service.ingest_files(files, patient_id=patient_id)

    Uso avanzado (auto-matching de paciente):
        service = DicomIngestionService(
            tenant, user,
            patient_strategy=PatientMatchingStrategy.MATCH_OR_CREATE
        )
        result = service.ingest_files(files)  # Sin patient_id
    """

    def __init__(
        self,
        tenant: Tenant,
        user,
        patient_strategy: str = PatientMatchingStrategy.REQUIRE_EXISTING
    ):
        self.tenant = tenant
        self.user = user
        self.parser = DicomParser()
        self.storage = DicomStorageService(str(tenant.id))
        self.patient_matcher = PatientMatcher(tenant, patient_strategy)

    def ingest_file(
        self,
        file: Union[InMemoryUploadedFile, TemporaryUploadedFile, BinaryIO, bytes],
        patient_id: Optional[UUID] = None,
        clinical_record_id: Optional[UUID] = None,
        filename: Optional[str] = None
    ) -> DicomInstance:
        """
        Procesa un único archivo DICOM.

        Args:
            file: Archivo DICOM (puede ser UploadedFile, file object o bytes)
            patient_id: ID del paciente (opcional según estrategia)
            clinical_record_id: ID de historia clínica (opcional)
            filename: Nombre del archivo (opcional, se extrae del file si es posible)

        Returns:
            DicomInstance creado

        Raises:
            ValueError: Si el archivo no es DICOM válido o no se puede resolver el paciente
        """
        # Normalizar el archivo a bytes
        if isinstance(file, bytes):
            file_content = file
            filename = filename or 'unknown.dcm'
        elif hasattr(file, 'read'):
            file_content = file.read()
            filename = filename or getattr(file, 'name', 'unknown.dcm')
            # Resetear el puntero si es posible
            if hasattr(file, 'seek'):
                file.seek(0)
        else:
            raise ValueError(f"Tipo de archivo no soportado: {type(file)}")

        # Parsear metadata
        metadata = self.parser.parse_bytes(file_content)

        # Resolver paciente
        patient_result = self.patient_matcher.match_patient(
            metadata['study'],
            patient_id
        )
        patient = patient_result.patient

        # Resolver historia clínica
        clinical_record = None
        if clinical_record_id:
            clinical_record = ClinicalRecord.objects.get(
                id=clinical_record_id,
                patient=patient,
                tenant=self.tenant
            )

        # Crear/actualizar Study, Series, Instance
        with transaction.atomic():
            study = self._get_or_create_study(metadata, patient, clinical_record)
            series = self._get_or_create_series(metadata, study)
            instance = self._create_instance(metadata, series, file_content, filename)

            # Actualizar estadísticas
            series.update_statistics()
            study.update_statistics()

            # Registrar auditoría
            self._audit_ingestion(study, instance)

        return instance

    def ingest_files(
        self,
        files: List[Union[InMemoryUploadedFile, TemporaryUploadedFile, BinaryIO]],
        patient_id: Optional[UUID] = None,
        clinical_record_id: Optional[UUID] = None
    ) -> IngestionResult:
        """
        Procesa múltiples archivos DICOM.

        Args:
            files: Lista de archivos DICOM
            patient_id: ID del paciente
            clinical_record_id: ID de historia clínica (opcional)

        Returns:
            IngestionResult con el estudio y las instancias creadas
        """
        if not files:
            raise ValueError("No se proporcionaron archivos")

        instances_created = []
        series_created = []
        errors = []
        study = None
        patient_matched = False
        patient_created = False

        # Procesar primer archivo para establecer estudio y paciente
        first_file = files[0]
        first_content = first_file.read() if hasattr(first_file, 'read') else first_file
        if hasattr(first_file, 'seek'):
            first_file.seek(0)

        first_metadata = self.parser.parse_bytes(first_content)

        # Resolver paciente una sola vez
        patient_result = self.patient_matcher.match_patient(
            first_metadata['study'],
            patient_id
        )
        patient = patient_result.patient
        patient_matched = patient_result.matched
        patient_created = patient_result.created

        # Resolver historia clínica
        clinical_record = None
        if clinical_record_id:
            clinical_record = ClinicalRecord.objects.get(
                id=clinical_record_id,
                patient=patient,
                tenant=self.tenant
            )

        # Procesar todos los archivos dentro de una transacción
        with transaction.atomic():
            # Estructuras para agrupar
            studies_cache: Dict[str, DicomStudy] = {}
            series_cache: Dict[str, DicomSeries] = {}

            for idx, file in enumerate(files):
                try:
                    # Leer contenido
                    if hasattr(file, 'read'):
                        file_content = file.read()
                        filename = getattr(file, 'name', f'instance_{idx}.dcm')
                        if hasattr(file, 'seek'):
                            file.seek(0)
                    else:
                        file_content = file
                        filename = f'instance_{idx}.dcm'

                    # Parsear metadata
                    metadata = self.parser.parse_bytes(file_content)

                    study_uid = metadata['study']['study_instance_uid']
                    series_uid = metadata['series']['series_instance_uid']

                    # Obtener o crear Study
                    if study_uid not in studies_cache:
                        study = self._get_or_create_study(
                            metadata, patient, clinical_record
                        )
                        studies_cache[study_uid] = study
                    else:
                        study = studies_cache[study_uid]

                    # Obtener o crear Series
                    if series_uid not in series_cache:
                        series = self._get_or_create_series(metadata, study)
                        series_cache[series_uid] = series
                        series_created.append(series)
                    else:
                        series = series_cache[series_uid]

                    # Crear Instance
                    instance = self._create_instance(
                        metadata, series, file_content, filename
                    )
                    instances_created.append(instance)

                except Exception as e:
                    error_msg = f"Error procesando archivo {idx}: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)

            # Actualizar estadísticas de todas las series
            for series in series_cache.values():
                series.update_statistics()

            # Actualizar estadísticas del estudio
            if study:
                study.update_statistics()
                study.status = 'completed' if not errors else 'failed'
                study.save()

                # Registrar auditoría
                self._audit_bulk_ingestion(study, len(instances_created))

        return IngestionResult(
            study=study,
            series_created=series_created,
            instances_created=instances_created,
            patient_matched=patient_matched,
            patient_created=patient_created,
            errors=errors
        )

    def ingest_zip(
        self,
        zip_file: Union[InMemoryUploadedFile, BinaryIO],
        patient_id: Optional[UUID] = None,
        clinical_record_id: Optional[UUID] = None
    ) -> IngestionResult:
        """
        Procesa un archivo ZIP conteniendo archivos DICOM.

        Args:
            zip_file: Archivo ZIP
            patient_id: ID del paciente
            clinical_record_id: ID de historia clínica (opcional)

        Returns:
            IngestionResult con el estudio y las instancias creadas
        """
        files = []

        zip_content = zip_file.read() if hasattr(zip_file, 'read') else zip_file

        with zipfile.ZipFile(BytesIO(zip_content), 'r') as zf:
            for name in zf.namelist():
                # Ignorar directorios y archivos ocultos
                if name.endswith('/') or name.startswith('__') or name.startswith('.'):
                    continue

                # Detectar archivos DICOM
                lower_name = name.lower()
                is_dicom = (
                    lower_name.endswith(('.dcm', '.dicom')) or
                    '.' not in name.split('/')[-1]  # Sin extensión (común en DICOM)
                )

                if is_dicom:
                    file_content = zf.read(name)
                    # Verificar que sea DICOM válido (magic bytes)
                    if len(file_content) > 132 and file_content[128:132] == b'DICM':
                        # Crear objeto file-like
                        file_obj = BytesIO(file_content)
                        file_obj.name = name.split('/')[-1]
                        files.append(file_obj)

        if not files:
            raise ValueError("No se encontraron archivos DICOM válidos en el ZIP")

        return self.ingest_files(files, patient_id, clinical_record_id)

    def _get_or_create_study(
        self,
        metadata: Dict[str, Any],
        patient: Patient,
        clinical_record: Optional[ClinicalRecord]
    ) -> DicomStudy:
        """Obtiene o crea un DicomStudy."""
        study_meta = metadata['study']
        study_uid = study_meta['study_instance_uid']

        study, created = DicomStudy.objects.update_or_create(
            study_instance_uid=study_uid,
            defaults={
                'tenant': self.tenant,
                'patient': patient,
                'clinical_record': clinical_record,
                'accession_number': study_meta.get('accession_number', ''),
                'study_date': study_meta.get('study_date'),
                'study_time': study_meta.get('study_time'),
                'study_description': study_meta.get('study_description', ''),
                'modality': study_meta.get('modality', 'OT'),
                'body_part_examined': study_meta.get('body_part_examined', ''),
                'referring_physician_name': study_meta.get('referring_physician_name', ''),
                'institution_name': study_meta.get('institution_name', ''),
                'dicom_metadata': metadata.get('raw', {}),
                'uploaded_by': self.user,
                'status': 'processing',
            }
        )

        if created:
            logger.info(f"Estudio DICOM creado: {study_uid}")

        return study

    def _get_or_create_series(
        self,
        metadata: Dict[str, Any],
        study: DicomStudy
    ) -> DicomSeries:
        """Obtiene o crea un DicomSeries."""
        series_meta = metadata['series']
        series_uid = series_meta['series_instance_uid']

        series, created = DicomSeries.objects.update_or_create(
            series_instance_uid=series_uid,
            defaults={
                'tenant': self.tenant,
                'study': study,
                'series_number': series_meta.get('series_number'),
                'series_description': series_meta.get('series_description', ''),
                'modality': series_meta.get('modality', ''),
                'body_part_examined': series_meta.get('body_part_examined', ''),
                'series_date': series_meta.get('series_date'),
                'series_time': series_meta.get('series_time'),
                'has_contrast': series_meta.get('has_contrast', False),
                'contrast_agent': series_meta.get('contrast_agent', ''),
                'slice_thickness': series_meta.get('slice_thickness'),
                'pixel_spacing': series_meta.get('pixel_spacing', ''),
                'image_orientation_patient': series_meta.get('image_orientation_patient', ''),
            }
        )

        if created:
            logger.info(f"Serie DICOM creada: {series_uid}")

        return series

    def _clean_metadata_for_json(self, metadata: Any) -> Any:
        """Limpia metadatos removiendo caracteres Unicode inválidos para PostgreSQL JSON."""
        import json
        if isinstance(metadata, dict):
            return {k: self._clean_metadata_for_json(v) for k, v in metadata.items()}
        elif isinstance(metadata, list):
            return [self._clean_metadata_for_json(item) for item in metadata]
        elif isinstance(metadata, str):
            # Remover caracteres nulos y otros caracteres problemáticos
            return metadata.replace('\x00', '').replace('\u0000', '')
        else:
            return metadata

    def _create_instance(
        self,
        metadata: Dict[str, Any],
        series: DicomSeries,
        file_content: bytes,
        filename: str
    ) -> DicomInstance:
        """Crea un DicomInstance y guarda el archivo."""
        instance_meta = metadata['instance']
        sop_uid = instance_meta['sop_instance_uid']

        # Guardar archivo en storage
        file_path, file_hash, file_size = self.storage.save_instance(
            study_uid=series.study.study_instance_uid,
            series_uid=series.series_instance_uid,
            instance_uid=sop_uid,
            file_content=file_content,
            original_filename=filename
        )

        # Limpiar metadatos para evitar caracteres Unicode inválidos
        cleaned_metadata = self._clean_metadata_for_json(instance_meta)
        
        # Crear o actualizar instancia
        instance, created = DicomInstance.objects.update_or_create(
            sop_instance_uid=sop_uid,
            defaults={
                'tenant': self.tenant,
                'series': series,
                'sop_class_uid': instance_meta.get('sop_class_uid', ''),
                'instance_number': instance_meta.get('instance_number'),
                'file_path': file_path,
                'file_name': filename,
                'file_size_bytes': file_size,
                'file_hash': file_hash,
                'rows': instance_meta.get('rows'),
                'columns': instance_meta.get('columns'),
                'bits_allocated': instance_meta.get('bits_allocated'),
                'bits_stored': instance_meta.get('bits_stored'),
                'photometric_interpretation': instance_meta.get('photometric_interpretation', ''),
                'image_position_patient': instance_meta.get('image_position_patient', ''),
                'slice_location': instance_meta.get('slice_location'),
                'window_center': instance_meta.get('window_center'),
                'window_width': instance_meta.get('window_width'),
                'transfer_syntax_uid': instance_meta.get('transfer_syntax_uid', ''),
                'dicom_metadata': cleaned_metadata,
            }
        )

        return instance

    def _audit_ingestion(self, study: DicomStudy, instance: DicomInstance):
        """Registra auditoría de ingestión de un archivo."""
        try:
            DicomAccessLog.objects.create(
                tenant=self.tenant,
                study=study,
                user=self.user,
                access_type='upload',
                user_email=self.user.email,
                user_name=f"{self.user.first_name} {self.user.last_name}",
            )
        except Exception as e:
            logger.warning(f"Error registrando auditoría: {e}")

    def _audit_bulk_ingestion(self, study: DicomStudy, instance_count: int):
        """Registra auditoría de ingestión masiva."""
        try:
            DicomAccessLog.objects.create(
                tenant=self.tenant,
                study=study,
                user=self.user,
                access_type='upload',
                user_email=self.user.email,
                user_name=f"{self.user.first_name} {self.user.last_name}",
            )
            logger.info(
                f"Ingestión completada: {instance_count} instancias, "
                f"estudio {study.study_instance_uid}"
            )
        except Exception as e:
            logger.warning(f"Error registrando auditoría: {e}")


# =============================================================================
# FUNCIONES DE CONVENIENCIA
# =============================================================================

def ingest_dicom_file(
    file: Union[InMemoryUploadedFile, BinaryIO, bytes],
    tenant: Tenant,
    user,
    patient_id: Optional[UUID] = None,
    clinical_record_id: Optional[UUID] = None,
    patient_strategy: str = PatientMatchingStrategy.REQUIRE_EXISTING
) -> DicomInstance:
    """
    Función de conveniencia para ingerir un único archivo DICOM.

    Args:
        file: Archivo DICOM
        tenant: Tenant actual
        user: Usuario que realiza la subida
        patient_id: ID del paciente (requerido con estrategia por defecto)
        clinical_record_id: ID de historia clínica (opcional)
        patient_strategy: Estrategia de matching de paciente

    Returns:
        DicomInstance creado

    Ejemplo:
        instance = ingest_dicom_file(
            file=request.FILES['dicom'],
            tenant=request.tenant,
            user=request.user,
            patient_id=patient.id
        )
    """
    service = DicomIngestionService(tenant, user, patient_strategy)
    return service.ingest_file(file, patient_id, clinical_record_id)


def ingest_dicom_files(
    files: List[Union[InMemoryUploadedFile, BinaryIO]],
    tenant: Tenant,
    user,
    patient_id: Optional[UUID] = None,
    clinical_record_id: Optional[UUID] = None,
    patient_strategy: str = PatientMatchingStrategy.REQUIRE_EXISTING
) -> IngestionResult:
    """
    Función de conveniencia para ingerir múltiples archivos DICOM.

    Args:
        files: Lista de archivos DICOM
        tenant: Tenant actual
        user: Usuario que realiza la subida
        patient_id: ID del paciente
        clinical_record_id: ID de historia clínica (opcional)
        patient_strategy: Estrategia de matching de paciente

    Returns:
        IngestionResult con estudio, series e instancias creadas

    Ejemplo:
        result = ingest_dicom_files(
            files=request.FILES.getlist('dicoms'),
            tenant=request.tenant,
            user=request.user,
            patient_id=patient.id
        )
        print(f"Creadas {result.total_instances} instancias")
    """
    service = DicomIngestionService(tenant, user, patient_strategy)
    return service.ingest_files(files, patient_id, clinical_record_id)


# =============================================================================
# SERVICIO DE RECUPERACIÓN (para streaming a visores)
# =============================================================================

class DicomRetrieveService:
    """
    Servicio para recuperar y servir archivos DICOM.
    Optimizado para streaming a visores como Cornerstone3D.
    """

    def __init__(self, tenant_id: UUID):
        self.tenant_id = tenant_id
        self.storage = DicomStorageService(str(tenant_id))

    def get_instance_file(self, instance_id: UUID) -> Tuple[bytes, str]:
        """
        Obtiene el contenido de un archivo DICOM.

        Args:
            instance_id: ID de la instancia

        Returns:
            Tuple de (contenido, nombre_archivo)
        """
        instance = DicomInstance.objects.get(id=instance_id)
        content = self.storage.get_instance(instance.file_path)
        return content, instance.file_name

    def get_instance_stream(self, instance_id: UUID):
        """
        Obtiene un stream del archivo DICOM.

        Args:
            instance_id: ID de la instancia

        Returns:
            Objeto file-like para streaming
        """
        instance = DicomInstance.objects.get(id=instance_id)
        return self.storage.get_instance_stream(instance.file_path)

    def get_series_image_ids(self, series_id: UUID, base_url: str) -> Dict[str, Any]:
        """
        Genera los imageIds para una serie completa.
        Optimizado para Cornerstone3D.

        Args:
            series_id: ID de la serie
            base_url: URL base para construir las URLs

        Returns:
            Diccionario con imageIds y metadata
        """
        series = DicomSeries.objects.select_related('study').get(id=series_id)
        instances = series.instances.order_by('instance_number', 'slice_location')

        image_ids = []
        for instance in instances:
            url = f"{base_url}/api/dicom/instances/{instance.id}/stream/"
            image_ids.append(f"wadouri:{url}")

        return {
            'series_id': str(series_id),
            'study_id': str(series.study_id),
            'modality': series.modality,
            'series_description': series.series_description,
            'number_of_frames': instances.count(),
            'image_ids': image_ids,
            'volume_id': f"volume_{series_id}",
        }

    def get_study_metadata_for_viewer(self, study_id: UUID) -> Dict[str, Any]:
        """
        Obtiene metadata del estudio formateada para visores.

        Args:
            study_id: ID del estudio

        Returns:
            Metadata estructurada
        """
        study = DicomStudy.objects.prefetch_related(
            'series__instances'
        ).get(id=study_id)

        series_list = []
        for series in study.series.all():
            instances_list = []
            for instance in series.instances.order_by('instance_number'):
                instances_list.append({
                    'id': str(instance.id),
                    'sop_instance_uid': instance.sop_instance_uid,
                    'instance_number': instance.instance_number,
                    'slice_location': float(instance.slice_location) if instance.slice_location else None,
                    'rows': instance.rows,
                    'columns': instance.columns,
                })

            series_list.append({
                'id': str(series.id),
                'series_instance_uid': series.series_instance_uid,
                'series_number': series.series_number,
                'series_description': series.series_description,
                'modality': series.modality,
                'has_contrast': series.has_contrast,
                'contrast_agent': series.contrast_agent,
                'slice_thickness': float(series.slice_thickness) if series.slice_thickness else None,
                'instances': instances_list,
            })

        return {
            'id': str(study.id),
            'study_instance_uid': study.study_instance_uid,
            'study_date': study.study_date.isoformat() if study.study_date else None,
            'study_description': study.study_description,
            'modality': study.modality,
            'patient_id': str(study.patient_id),
            'series': series_list,
        }


# =============================================================================
# LEGACY COMPATIBILITY (para mantener compatibilidad con código existente)
# =============================================================================

class DicomUploadService(DicomIngestionService):
    """
    Alias para compatibilidad con código existente.
    Usar DicomIngestionService para nuevo código.
    """

    def __init__(self, tenant_id: UUID, user):
        tenant = Tenant.objects.get(id=tenant_id)
        super().__init__(tenant, user)

    def process_files(
        self,
        files: List,
        patient_id: UUID,
        clinical_record_id: Optional[UUID] = None
    ) -> DicomStudy:
        """Wrapper de compatibilidad."""
        result = self.ingest_files(files, patient_id, clinical_record_id)
        return result.study

    def process_zip(
        self,
        zip_file,
        patient_id: UUID,
        clinical_record_id: Optional[UUID] = None
    ) -> DicomStudy:
        """Wrapper de compatibilidad."""
        result = self.ingest_zip(zip_file, patient_id, clinical_record_id)
        return result.study
