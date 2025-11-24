"""
Parser de archivos DICOM usando pydicom.
Extrae metadata relevante para almacenar en los modelos.
"""

import logging
from datetime import datetime, date, time
from decimal import Decimal
from typing import Dict, Any, Optional, Tuple, BinaryIO
from io import BytesIO

try:
    import pydicom
    from pydicom.errors import InvalidDicomError
    from pydicom.uid import UID
    PYDICOM_AVAILABLE = True
except ImportError:
    PYDICOM_AVAILABLE = False
    pydicom = None

logger = logging.getLogger(__name__)


class DicomParser:
    """
    Parser para extraer metadata de archivos DICOM.

    Uso:
        parser = DicomParser()
        metadata = parser.parse_file(file_content)
        # o
        metadata = parser.parse_file_path('/path/to/file.dcm')
    """

    # Tags DICOM importantes para Study level
    STUDY_TAGS = [
        'StudyInstanceUID',
        'StudyDate',
        'StudyTime',
        'StudyDescription',
        'AccessionNumber',
        'ReferringPhysicianName',
        'InstitutionName',
        'Modality',
        'BodyPartExamined',
        'PatientName',
        'PatientID',
        'PatientBirthDate',
        'PatientSex',
    ]

    # Tags DICOM importantes para Series level
    SERIES_TAGS = [
        'SeriesInstanceUID',
        'SeriesNumber',
        'SeriesDescription',
        'SeriesDate',
        'SeriesTime',
        'Modality',
        'BodyPartExamined',
        'SliceThickness',
        'PixelSpacing',
        'ImageOrientationPatient',
        'ProtocolName',
        # Información de contraste
        'ContrastBolusAgent',
        'ContrastBolusRoute',
        'ContrastBolusVolume',
        'ContrastBolusStartTime',
    ]

    # Tags DICOM importantes para Instance level
    INSTANCE_TAGS = [
        'SOPInstanceUID',
        'SOPClassUID',
        'InstanceNumber',
        'Rows',
        'Columns',
        'BitsAllocated',
        'BitsStored',
        'HighBit',
        'PixelRepresentation',
        'PhotometricInterpretation',
        'ImagePositionPatient',
        'SliceLocation',
        'WindowCenter',
        'WindowWidth',
        'RescaleIntercept',
        'RescaleSlope',
        'TransferSyntaxUID',
    ]

    def __init__(self):
        if not PYDICOM_AVAILABLE:
            raise ImportError(
                "pydicom no está instalado. Ejecute: pip install pydicom"
            )

    def parse_bytes(self, file_content: bytes) -> Dict[str, Any]:
        """
        Parsea contenido binario de un archivo DICOM.

        Args:
            file_content: Contenido binario del archivo .dcm

        Returns:
            Diccionario con metadata extraída
        """
        try:
            ds = pydicom.dcmread(BytesIO(file_content), force=True)
            return self._extract_metadata(ds)
        except InvalidDicomError as e:
            logger.error(f"Archivo DICOM inválido: {e}")
            raise ValueError(f"El archivo no es un DICOM válido: {e}")
        except Exception as e:
            logger.error(f"Error parseando DICOM: {e}")
            raise

    def parse_file(self, file_path: str) -> Dict[str, Any]:
        """
        Parsea un archivo DICOM desde una ruta.

        Args:
            file_path: Ruta al archivo .dcm

        Returns:
            Diccionario con metadata extraída
        """
        try:
            ds = pydicom.dcmread(file_path, force=True)
            return self._extract_metadata(ds)
        except FileNotFoundError:
            logger.error(f"Archivo no encontrado: {file_path}")
            raise
        except InvalidDicomError as e:
            logger.error(f"Archivo DICOM inválido: {file_path} - {e}")
            raise ValueError(f"El archivo no es un DICOM válido: {e}")
        except Exception as e:
            logger.error(f"Error parseando DICOM {file_path}: {e}")
            raise

    def parse_file_object(self, file_obj: BinaryIO) -> Dict[str, Any]:
        """
        Parsea un archivo DICOM desde un objeto file-like.

        Args:
            file_obj: Objeto file-like con el contenido DICOM

        Returns:
            Diccionario con metadata extraída
        """
        try:
            ds = pydicom.dcmread(file_obj, force=True)
            return self._extract_metadata(ds)
        except InvalidDicomError as e:
            logger.error(f"Archivo DICOM inválido: {e}")
            raise ValueError(f"El archivo no es un DICOM válido: {e}")

    def _extract_metadata(self, ds: 'pydicom.Dataset') -> Dict[str, Any]:
        """
        Extrae toda la metadata relevante del dataset DICOM.

        Args:
            ds: Dataset de pydicom

        Returns:
            Diccionario estructurado con toda la metadata
        """
        metadata = {
            'study': self._extract_study_metadata(ds),
            'series': self._extract_series_metadata(ds),
            'instance': self._extract_instance_metadata(ds),
            'raw': self._extract_raw_metadata(ds),
        }

        return metadata

    def _extract_study_metadata(self, ds: 'pydicom.Dataset') -> Dict[str, Any]:
        """Extrae metadata a nivel de estudio."""
        study_data = {}

        # Study Instance UID (obligatorio)
        study_data['study_instance_uid'] = self._get_value(ds, 'StudyInstanceUID', '')

        # Accession Number
        study_data['accession_number'] = self._get_value(ds, 'AccessionNumber', '')

        # Fecha y hora del estudio
        study_date = self._get_value(ds, 'StudyDate', '')
        study_time = self._get_value(ds, 'StudyTime', '')
        study_data['study_date'] = self._parse_dicom_date(study_date)
        study_data['study_time'] = self._parse_dicom_time(study_time)

        # Descripción
        study_data['study_description'] = self._get_value(ds, 'StudyDescription', '')

        # Modalidad
        study_data['modality'] = self._get_value(ds, 'Modality', 'OT')

        # Parte del cuerpo
        study_data['body_part_examined'] = self._get_value(ds, 'BodyPartExamined', '')

        # Médico referente
        referring_physician = self._get_value(ds, 'ReferringPhysicianName', '')
        study_data['referring_physician_name'] = str(referring_physician) if referring_physician else ''

        # Institución
        study_data['institution_name'] = self._get_value(ds, 'InstitutionName', '')

        # Información del paciente (para validación/matching)
        patient_name = self._get_value(ds, 'PatientName', '')
        study_data['patient_name'] = str(patient_name) if patient_name else ''
        study_data['patient_id'] = self._get_value(ds, 'PatientID', '')
        study_data['patient_birth_date'] = self._parse_dicom_date(
            self._get_value(ds, 'PatientBirthDate', '')
        )
        study_data['patient_sex'] = self._get_value(ds, 'PatientSex', '')

        return study_data

    def _extract_series_metadata(self, ds: 'pydicom.Dataset') -> Dict[str, Any]:
        """Extrae metadata a nivel de serie."""
        series_data = {}

        # Series Instance UID (obligatorio)
        series_data['series_instance_uid'] = self._get_value(ds, 'SeriesInstanceUID', '')

        # Número de serie
        series_data['series_number'] = self._get_int_value(ds, 'SeriesNumber')

        # Descripción
        series_data['series_description'] = self._get_value(ds, 'SeriesDescription', '')

        # Modalidad
        series_data['modality'] = self._get_value(ds, 'Modality', '')

        # Parte del cuerpo examinada
        series_data['body_part_examined'] = self._get_value(ds, 'BodyPartExamined', '')

        # Fecha y hora
        series_date = self._get_value(ds, 'SeriesDate', '')
        series_time = self._get_value(ds, 'SeriesTime', '')
        series_data['series_date'] = self._parse_dicom_date(series_date)
        series_data['series_time'] = self._parse_dicom_time(series_time)

        # Información de contraste
        contrast_agent = self._get_value(ds, 'ContrastBolusAgent', '')
        series_data['contrast_agent'] = str(contrast_agent) if contrast_agent else ''
        series_data['has_contrast'] = bool(contrast_agent)

        # Información adicional de contraste (para metadata)
        series_data['contrast_route'] = self._get_value(ds, 'ContrastBolusRoute', '')
        series_data['contrast_volume'] = self._get_value(ds, 'ContrastBolusVolume', '')

        # Parámetros de adquisición
        series_data['slice_thickness'] = self._get_decimal_value(ds, 'SliceThickness')

        # Pixel Spacing
        pixel_spacing = self._get_value(ds, 'PixelSpacing', None)
        if pixel_spacing:
            series_data['pixel_spacing'] = '\\'.join(str(x) for x in pixel_spacing)
        else:
            series_data['pixel_spacing'] = ''

        # Orientación de imagen
        orientation = self._get_value(ds, 'ImageOrientationPatient', None)
        if orientation:
            series_data['image_orientation_patient'] = '\\'.join(str(x) for x in orientation)
        else:
            series_data['image_orientation_patient'] = ''

        return series_data

    def _extract_instance_metadata(self, ds: 'pydicom.Dataset') -> Dict[str, Any]:
        """Extrae metadata a nivel de instancia."""
        instance_data = {}

        # SOP Instance UID (obligatorio)
        instance_data['sop_instance_uid'] = self._get_value(ds, 'SOPInstanceUID', '')

        # SOP Class UID
        instance_data['sop_class_uid'] = self._get_value(ds, 'SOPClassUID', '')

        # Número de instancia
        instance_data['instance_number'] = self._get_int_value(ds, 'InstanceNumber')

        # Dimensiones de imagen
        instance_data['rows'] = self._get_int_value(ds, 'Rows')
        instance_data['columns'] = self._get_int_value(ds, 'Columns')

        # Bits
        instance_data['bits_allocated'] = self._get_int_value(ds, 'BitsAllocated')
        instance_data['bits_stored'] = self._get_int_value(ds, 'BitsStored')

        # Interpretación fotométrica
        instance_data['photometric_interpretation'] = self._get_value(
            ds, 'PhotometricInterpretation', ''
        )

        # Posición espacial
        position = self._get_value(ds, 'ImagePositionPatient', None)
        if position:
            instance_data['image_position_patient'] = '\\'.join(str(x) for x in position)
        else:
            instance_data['image_position_patient'] = ''

        instance_data['slice_location'] = self._get_decimal_value(ds, 'SliceLocation')

        # Window/Level
        instance_data['window_center'] = self._get_decimal_value(ds, 'WindowCenter')
        instance_data['window_width'] = self._get_decimal_value(ds, 'WindowWidth')

        # Transfer Syntax
        if hasattr(ds, 'file_meta') and hasattr(ds.file_meta, 'TransferSyntaxUID'):
            instance_data['transfer_syntax_uid'] = str(ds.file_meta.TransferSyntaxUID)
        else:
            instance_data['transfer_syntax_uid'] = ''

        # Rescale values (para CT principalmente)
        instance_data['rescale_intercept'] = self._get_decimal_value(ds, 'RescaleIntercept')
        instance_data['rescale_slope'] = self._get_decimal_value(ds, 'RescaleSlope')

        return instance_data

    def _extract_raw_metadata(self, ds: 'pydicom.Dataset') -> Dict[str, Any]:
        """
        Extrae metadata raw para almacenar en JSONField.
        Solo incluye elementos con valores serializables.
        """
        raw_metadata = {}

        for elem in ds:
            if elem.VR == 'SQ':  # Skip sequences
                continue
            if elem.keyword == 'PixelData':  # Skip pixel data
                continue

            try:
                value = self._serialize_value(elem.value)
                if value is not None:
                    raw_metadata[elem.keyword] = {
                        'tag': str(elem.tag),
                        'vr': elem.VR,
                        'value': value,
                    }
            except Exception:
                # Skip non-serializable values
                pass

        return raw_metadata

    def _get_value(self, ds: 'pydicom.Dataset', tag: str, default: Any = None) -> Any:
        """Obtiene un valor del dataset de forma segura."""
        try:
            if hasattr(ds, tag):
                value = getattr(ds, tag)
                if value is not None:
                    return value
        except Exception:
            pass
        return default

    def _get_int_value(self, ds: 'pydicom.Dataset', tag: str) -> Optional[int]:
        """Obtiene un valor entero del dataset."""
        value = self._get_value(ds, tag)
        if value is not None:
            try:
                return int(value)
            except (ValueError, TypeError):
                pass
        return None

    def _get_decimal_value(self, ds: 'pydicom.Dataset', tag: str) -> Optional[Decimal]:
        """Obtiene un valor decimal del dataset."""
        value = self._get_value(ds, tag)
        if value is not None:
            try:
                # Window Center/Width pueden ser listas
                if isinstance(value, (list, tuple)):
                    value = value[0]
                return Decimal(str(value))
            except (ValueError, TypeError):
                pass
        return None

    def _parse_dicom_date(self, date_str: str) -> Optional[date]:
        """Parsea una fecha DICOM (YYYYMMDD) a objeto date."""
        if not date_str:
            return None
        try:
            # Formato DICOM: YYYYMMDD
            return datetime.strptime(date_str[:8], '%Y%m%d').date()
        except (ValueError, TypeError):
            return None

    def _parse_dicom_time(self, time_str: str) -> Optional[time]:
        """Parsea una hora DICOM (HHMMSS.FFFFFF) a objeto time."""
        if not time_str:
            return None
        try:
            # Formato DICOM: HHMMSS.FFFFFF (las fracciones son opcionales)
            time_str = time_str.split('.')[0]  # Remover fracciones
            if len(time_str) >= 6:
                return datetime.strptime(time_str[:6], '%H%M%S').time()
            elif len(time_str) >= 4:
                return datetime.strptime(time_str[:4], '%H%M').time()
            elif len(time_str) >= 2:
                return datetime.strptime(time_str[:2], '%H').time()
        except (ValueError, TypeError):
            pass
        return None

    def _serialize_value(self, value: Any) -> Any:
        """Serializa un valor DICOM para JSON."""
        if value is None:
            return None

        # Tipos básicos
        if isinstance(value, (str, int, float, bool)):
            return value

        # Bytes
        if isinstance(value, bytes):
            return value.decode('utf-8', errors='ignore')

        # Listas/Arrays
        if isinstance(value, (list, tuple)):
            return [self._serialize_value(v) for v in value]

        # PersonName
        if hasattr(value, 'family_name'):
            return str(value)

        # UID
        if isinstance(value, UID):
            return str(value)

        # Otros tipos
        try:
            return str(value)
        except Exception:
            return None

    def get_transfer_syntax_info(self, transfer_syntax_uid: str) -> Dict[str, Any]:
        """
        Retorna información sobre el Transfer Syntax.
        Útil para saber si el archivo está comprimido.
        """
        # Transfer Syntaxes comunes
        TRANSFER_SYNTAXES = {
            '1.2.840.10008.1.2': {
                'name': 'Implicit VR Little Endian',
                'compressed': False,
            },
            '1.2.840.10008.1.2.1': {
                'name': 'Explicit VR Little Endian',
                'compressed': False,
            },
            '1.2.840.10008.1.2.2': {
                'name': 'Explicit VR Big Endian',
                'compressed': False,
            },
            '1.2.840.10008.1.2.4.50': {
                'name': 'JPEG Baseline',
                'compressed': True,
            },
            '1.2.840.10008.1.2.4.51': {
                'name': 'JPEG Extended',
                'compressed': True,
            },
            '1.2.840.10008.1.2.4.57': {
                'name': 'JPEG Lossless',
                'compressed': True,
            },
            '1.2.840.10008.1.2.4.70': {
                'name': 'JPEG Lossless First-Order Prediction',
                'compressed': True,
            },
            '1.2.840.10008.1.2.4.80': {
                'name': 'JPEG-LS Lossless',
                'compressed': True,
            },
            '1.2.840.10008.1.2.4.81': {
                'name': 'JPEG-LS Near-Lossless',
                'compressed': True,
            },
            '1.2.840.10008.1.2.4.90': {
                'name': 'JPEG 2000 Lossless',
                'compressed': True,
            },
            '1.2.840.10008.1.2.4.91': {
                'name': 'JPEG 2000',
                'compressed': True,
            },
            '1.2.840.10008.1.2.5': {
                'name': 'RLE Lossless',
                'compressed': True,
            },
        }

        return TRANSFER_SYNTAXES.get(transfer_syntax_uid, {
            'name': 'Unknown',
            'compressed': False,
        })
