"""
Serializers para los modelos DICOM.
"""

from rest_framework import serializers
from .models import DicomStudy, DicomSeries, DicomInstance, DicomAccessLog


class DicomInstanceSerializer(serializers.ModelSerializer):
    """
    Serializer para instancias DICOM individuales.
    """
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = DicomInstance
        fields = [
            'id',
            'sop_instance_uid',
            'sop_class_uid',
            'instance_number',
            'file_path',
            'file_name',
            'file_size_bytes',
            'file_hash',
            'rows',
            'columns',
            'bits_allocated',
            'bits_stored',
            'photometric_interpretation',
            'image_position_patient',
            'slice_location',
            'window_center',
            'window_width',
            'transfer_syntax_uid',
            'file_url',
            'created_at',
        ]
        read_only_fields = [
            'id',
            'file_hash',
            'file_url',
            'created_at',
        ]

    def get_file_url(self, obj):
        """Genera URL para acceder al archivo DICOM (streaming)."""
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(f'/api/dicom/instances/{obj.id}/stream/')
        return None


class DicomInstanceMinimalSerializer(serializers.ModelSerializer):
    """
    Serializer mínimo para listas de instancias (rendimiento).
    """

    class Meta:
        model = DicomInstance
        fields = [
            'id',
            'sop_instance_uid',
            'instance_number',
            'slice_location',
            'file_size_bytes',
        ]


class DicomSeriesSerializer(serializers.ModelSerializer):
    """
    Serializer para series DICOM.
    """
    instances = DicomInstanceMinimalSerializer(many=True, read_only=True)
    instance_count = serializers.IntegerField(
        source='number_of_instances',
        read_only=True
    )

    class Meta:
        model = DicomSeries
        fields = [
            'id',
            'series_instance_uid',
            'series_number',
            'series_description',
            'modality',
            'series_date',
            'series_time',
            'body_part_examined',
            'has_contrast',
            'contrast_agent',
            'slice_thickness',
            'pixel_spacing',
            'image_orientation_patient',
            'number_of_instances',
            'total_size_bytes',
            'instance_count',
            'instances',
            'created_at',
        ]
        read_only_fields = [
            'id',
            'number_of_instances',
            'total_size_bytes',
            'created_at',
        ]


class DicomSeriesMinimalSerializer(serializers.ModelSerializer):
    """
    Serializer mínimo para listas de series.
    """

    class Meta:
        model = DicomSeries
        fields = [
            'id',
            'series_instance_uid',
            'series_number',
            'series_description',
            'modality',
            'body_part_examined',
            'has_contrast',
            'number_of_instances',
        ]


class DicomStudySerializer(serializers.ModelSerializer):
    """
    Serializer para estudios DICOM.
    """
    series = DicomSeriesMinimalSerializer(many=True, read_only=True)
    patient_name = serializers.CharField(
        source='patient.full_name',
        read_only=True
    )
    patient_id_display = serializers.CharField(
        source='patient.identity_document',
        read_only=True
    )

    class Meta:
        model = DicomStudy
        fields = [
            'id',
            'study_instance_uid',
            'accession_number',
            'study_date',
            'study_time',
            'study_description',
            'modality',
            'body_part_examined',
            'referring_physician_name',
            'institution_name',
            'number_of_series',
            'number_of_instances',
            'total_size_bytes',
            'status',
            'processing_error',
            'patient',
            'patient_name',
            'patient_id_display',
            'clinical_record',
            'series',
            'uploaded_by',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'study_instance_uid',
            'number_of_series',
            'number_of_instances',
            'total_size_bytes',
            'status',
            'processing_error',
            'uploaded_by',
            'created_at',
            'updated_at',
        ]


class DicomStudyListSerializer(serializers.ModelSerializer):
    """
    Serializer para lista de estudios (rendimiento).
    """
    patient_name = serializers.SerializerMethodField()

    class Meta:
        model = DicomStudy
        fields = [
            'id',
            'study_instance_uid',
            'accession_number',
            'study_date',
            'study_description',
            'modality',
            'body_part_examined',
            'number_of_series',
            'number_of_instances',
            'total_size_bytes',
            'status',
            'patient',
            'patient_name',
            'created_at',
        ]

    def get_patient_name(self, obj):
        if obj.patient:
            return f"{obj.patient.first_name} {obj.patient.last_name}"
        return None


class DicomStudyDetailSerializer(DicomStudySerializer):
    """
    Serializer detallado para un estudio con todas sus series e instancias.
    """
    series = DicomSeriesSerializer(many=True, read_only=True)


class DicomUploadSerializer(serializers.Serializer):
    """
    Serializer para subida de archivos DICOM.
    """
    files = serializers.ListField(
        child=serializers.FileField(),
        min_length=1,
        help_text='Lista de archivos DICOM (.dcm)'
    )
    patient_id = serializers.UUIDField(
        help_text='ID del paciente'
    )
    clinical_record_id = serializers.UUIDField(
        required=False,
        allow_null=True,
        help_text='ID de la historia clínica (opcional)'
    )

    def validate_files(self, files):
        """Valida que los archivos sean DICOM."""
        for file in files:
            # Verificar extensión
            if not file.name.lower().endswith('.dcm'):
                # Permitir archivos sin extensión (común en DICOM)
                if '.' in file.name:
                    raise serializers.ValidationError(
                        f"El archivo {file.name} no tiene extensión .dcm"
                    )

            # Verificar tamaño máximo (100MB por archivo)
            max_size = 100 * 1024 * 1024
            if file.size > max_size:
                raise serializers.ValidationError(
                    f"El archivo {file.name} excede el tamaño máximo de 100MB"
                )

        return files


class DicomBulkUploadSerializer(serializers.Serializer):
    """
    Serializer para subida masiva de archivos DICOM (ZIP).
    """
    zip_file = serializers.FileField(
        help_text='Archivo ZIP con los archivos DICOM'
    )
    patient_id = serializers.UUIDField(
        help_text='ID del paciente'
    )
    clinical_record_id = serializers.UUIDField(
        required=False,
        allow_null=True,
        help_text='ID de la historia clínica (opcional)'
    )

    def validate_zip_file(self, file):
        """Valida que el archivo sea un ZIP válido."""
        if not file.name.lower().endswith('.zip'):
            raise serializers.ValidationError(
                "El archivo debe ser un ZIP"
            )

        # Verificar tamaño máximo (1GB)
        max_size = 1024 * 1024 * 1024
        if file.size > max_size:
            raise serializers.ValidationError(
                "El archivo ZIP excede el tamaño máximo de 1GB"
            )

        return file


class DicomAccessLogSerializer(serializers.ModelSerializer):
    """
    Serializer para logs de acceso DICOM.
    """
    study_description = serializers.CharField(
        source='study.study_description',
        read_only=True
    )

    class Meta:
        model = DicomAccessLog
        fields = [
            'id',
            'study',
            'study_description',
            'access_type',
            'user',
            'user_email',
            'user_name',
            'ip_address',
            'user_agent',
            'accessed_at',
        ]
        read_only_fields = fields


class CornerstoneImageIdSerializer(serializers.Serializer):
    """
    Serializer para generar imageIds compatibles con Cornerstone3D.
    """
    instance_id = serializers.UUIDField()
    image_id = serializers.SerializerMethodField()

    def get_image_id(self, obj):
        """
        Genera el imageId en formato wadouri para Cornerstone3D.

        Formato: wadouri:{url_del_archivo}
        """
        request = self.context.get('request')
        if request:
            url = request.build_absolute_uri(
                f'/api/dicom/instances/{obj["instance_id"]}/file/'
            )
            return f"wadouri:{url}"
        return None


class DicomSeriesImageIdsSerializer(serializers.Serializer):
    """
    Serializer para obtener todos los imageIds de una serie.
    Optimizado para Cornerstone3D.
    """
    series_id = serializers.UUIDField()
    image_ids = serializers.ListField(child=serializers.CharField())
    volume_id = serializers.CharField()
    modality = serializers.CharField()
    series_description = serializers.CharField()
    number_of_frames = serializers.IntegerField()


class DicomMetadataSerializer(serializers.Serializer):
    """
    Serializer para metadata DICOM en formato JSON.
    Compatible con Cornerstone3D metadata providers.
    """
    study = serializers.DictField()
    series = serializers.DictField()
    instance = serializers.DictField()


class DicomIngestSerializer(serializers.Serializer):
    """
    Serializer para ingestión de archivos DICOM.
    Usa las funciones ingest_dicom_file() e ingest_dicom_files().
    """
    files = serializers.ListField(
        child=serializers.FileField(),
        min_length=1,
        help_text='Lista de archivos DICOM (.dcm)'
    )
    patient_id = serializers.UUIDField(
        required=False,
        allow_null=True,
        help_text='ID del paciente al que se asociarán los estudios (opcional)'
    )
    clinical_record_id = serializers.UUIDField(
        required=False,
        allow_null=True,
        help_text='ID de la historia clínica (opcional)'
    )
    matching_strategy = serializers.ChoiceField(
        choices=[
            ('REQUIRE_EXISTING', 'Requiere paciente existente'),
            ('MATCH_OR_FAIL', 'Buscar o fallar'),
            ('MATCH_OR_CREATE', 'Buscar o crear'),
            ('ALWAYS_USE_PROVIDED', 'Usar siempre el proporcionado'),
        ],
        default='ALWAYS_USE_PROVIDED',
        required=False,
        help_text='Estrategia de asociación de paciente'
    )

    def validate_files(self, files):
        """Valida que los archivos sean DICOM válidos."""
        for file in files:
            # Verificar extensión (permitir sin extensión, común en DICOM)
            if '.' in file.name and not file.name.lower().endswith('.dcm'):
                raise serializers.ValidationError(
                    f"El archivo {file.name} no parece ser un archivo DICOM"
                )

            # Verificar tamaño máximo (100MB por archivo)
            max_size = 100 * 1024 * 1024
            if file.size > max_size:
                raise serializers.ValidationError(
                    f"El archivo {file.name} excede el tamaño máximo de 100MB"
                )

        return files


class DicomIngestResponseSerializer(serializers.Serializer):
    """
    Serializer para respuesta de ingestión DICOM.
    """
    studies = DicomStudyListSerializer(many=True)
    total_files_processed = serializers.IntegerField()
    total_studies_created = serializers.IntegerField()
    total_series_created = serializers.IntegerField()
    total_instances_created = serializers.IntegerField()
    errors = serializers.ListField(
        child=serializers.DictField(),
        required=False
    )


# =============================================================================
# SERIALIZERS OPTIMIZADOS PARA CORNERSTONE3D
# =============================================================================

class CornerstoneInstanceSerializer(serializers.Serializer):
    """
    Serializer mínimo para instancias, optimizado para Cornerstone3D.
    Solo incluye los campos necesarios para el visor.
    """
    instanceId = serializers.UUIDField(source='id')
    sopInstanceUID = serializers.CharField(source='sop_instance_uid')
    instanceNumber = serializers.IntegerField(source='instance_number')
    sliceLocation = serializers.DecimalField(
        source='slice_location',
        max_digits=10,
        decimal_places=4,
        allow_null=True
    )
    rows = serializers.IntegerField()
    columns = serializers.IntegerField()
    url = serializers.SerializerMethodField()

    def get_url(self, obj):
        """Genera URL de streaming para esta instancia."""
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(f'/api/dicom/instances/{obj.id}/stream/')
        return None


class SeriesViewerConfigSerializer(serializers.Serializer):
    """
    Serializer optimizado para configurar Cornerstone3D con una serie DICOM.

    Respuesta diseñada para:
    - Inicialización rápida del visor
    - Carga progresiva de imágenes
    - Soporte para volumen 3D (MPR/VR)

    Ejemplo de uso en frontend:
        const config = await api.get(`/api/dicom/series/${seriesId}/viewer-config/`);
        const imageIds = config.dicomUrls.map(url => `wadouri:${url}`);
        await cornerstone.loadAndCacheImages(imageIds);
    """
    # Identificadores
    seriesId = serializers.UUIDField(source='id')
    studyId = serializers.UUIDField(source='study_id')
    seriesInstanceUID = serializers.CharField(source='series_instance_uid')
    studyInstanceUID = serializers.CharField(source='study.study_instance_uid')

    # Metadata de la serie
    modality = serializers.CharField()
    seriesNumber = serializers.IntegerField(source='series_number', allow_null=True)
    seriesDescription = serializers.CharField(source='series_description')
    bodyPartExamined = serializers.CharField(source='body_part_examined')

    # Información de contraste
    hasContrast = serializers.BooleanField(source='has_contrast')
    contrastAgent = serializers.CharField(source='contrast_agent')

    # Parámetros de imagen
    sliceThickness = serializers.DecimalField(
        source='slice_thickness',
        max_digits=10,
        decimal_places=4,
        allow_null=True
    )
    pixelSpacing = serializers.CharField(source='pixel_spacing')
    imageOrientationPatient = serializers.CharField(source='image_orientation_patient')

    # Estadísticas
    numberOfFrames = serializers.IntegerField(source='number_of_instances')
    totalSizeBytes = serializers.IntegerField(source='total_size_bytes')

    # URLs para el visor (lista ordenada de URLs de streaming)
    dicomUrls = serializers.SerializerMethodField()

    # Configuración para volumen 3D
    volumeConfig = serializers.SerializerMethodField()

    # ImageIds pre-formateados para Cornerstone3D
    imageIds = serializers.SerializerMethodField()

    def get_dicomUrls(self, obj):
        """
        Genera lista ordenada de URLs de streaming.

        Las instancias se ordenan por:
        1. instance_number (si está disponible)
        2. slice_location (para ordenar espacialmente)

        Esto garantiza el orden correcto para navegación y volumen 3D.
        """
        request = self.context.get('request')
        if not request:
            return []

        # Las instancias ya vienen pre-cargadas y ordenadas
        instances = self.context.get('instances', [])

        urls = []
        for instance in instances:
            url = request.build_absolute_uri(
                f'/api/dicom/instances/{instance.id}/stream/'
            )
            urls.append(url)

        return urls

    def get_imageIds(self, obj):
        """
        Genera imageIds en formato wadouri para Cornerstone3D.

        Formato: wadouri:{url}

        Esto permite al frontend usar directamente:
            const imageIds = config.imageIds;
            await cornerstone.loadAndCacheImages(imageIds);
        """
        urls = self.get_dicomUrls(obj)
        return [f'wadouri:{url}' for url in urls]

    def get_volumeConfig(self, obj):
        """
        Genera configuración para crear un volumen 3D en Cornerstone3D.

        Incluye:
        - volumeId: Identificador único para el volumen
        - dimensions: Dimensiones del volumen
        - spacing: Espaciado de voxels
        - orientation: Orientación del paciente
        """
        instances = self.context.get('instances', [])

        if not instances:
            return None

        first_instance = instances[0]
        num_slices = len(instances)

        # Calcular dimensiones del volumen
        rows = first_instance.rows or 512
        columns = first_instance.columns or 512

        # Parsear pixel spacing
        pixel_spacing = [1.0, 1.0]
        if obj.pixel_spacing:
            try:
                parts = obj.pixel_spacing.split('\\')
                pixel_spacing = [float(parts[0]), float(parts[1])]
            except (ValueError, IndexError):
                pass

        # Slice thickness o calcular de slice locations
        slice_thickness = float(obj.slice_thickness) if obj.slice_thickness else 1.0

        # Si tenemos múltiples slices, calcular spacing real
        if num_slices > 1:
            first_loc = instances[0].slice_location
            last_loc = instances[-1].slice_location
            if first_loc is not None and last_loc is not None:
                calculated_spacing = abs(float(last_loc) - float(first_loc)) / (num_slices - 1)
                if calculated_spacing > 0:
                    slice_thickness = calculated_spacing

        return {
            'volumeId': f'cornerstoneStreamingImageVolume:{obj.id}',
            'dimensions': {
                'rows': rows,
                'columns': columns,
                'numberOfSlices': num_slices,
            },
            'spacing': {
                'x': pixel_spacing[0],
                'y': pixel_spacing[1],
                'z': slice_thickness,
            },
            'orientation': obj.image_orientation_patient or '',
            'modality': obj.modality,
        }


class StudyViewerConfigSerializer(serializers.Serializer):
    """
    Serializer para configurar Cornerstone3D con un estudio completo.
    Incluye todas las series del estudio.
    """
    # Identificadores
    studyId = serializers.UUIDField(source='id')
    studyInstanceUID = serializers.CharField(source='study_instance_uid')

    # Información del paciente
    patientId = serializers.UUIDField(source='patient_id')
    patientName = serializers.SerializerMethodField()

    # Metadata del estudio
    studyDate = serializers.DateField(source='study_date')
    studyDescription = serializers.CharField(source='study_description')
    modality = serializers.CharField()
    bodyPartExamined = serializers.CharField(source='body_part_examined')
    institutionName = serializers.CharField(source='institution_name')

    # Estadísticas
    numberOfSeries = serializers.IntegerField(source='number_of_series')
    numberOfInstances = serializers.IntegerField(source='number_of_instances')
    totalSizeBytes = serializers.IntegerField(source='total_size_bytes')

    # Series con sus configuraciones
    series = serializers.SerializerMethodField()

    def get_patientName(self, obj):
        if obj.patient:
            return f"{obj.patient.first_name} {obj.patient.last_name}"
        return None

    def get_series(self, obj):
        """Serializa todas las series del estudio."""
        request = self.context.get('request')
        series_list = []

        for series in obj.series.all():
            # Obtener instancias ordenadas
            instances = list(
                series.instances.order_by('instance_number', 'slice_location')
            )

            serializer = SeriesViewerConfigSerializer(
                series,
                context={
                    'request': request,
                    'instances': instances,
                }
            )
            series_list.append(serializer.data)

        return series_list


class BatchImageIdsSerializer(serializers.Serializer):
    """
    Serializer para obtener imageIds de múltiples series a la vez.
    Optimizado para cargar un estudio completo.
    """
    studyId = serializers.UUIDField()
    series = serializers.ListField(
        child=serializers.DictField()
    )
    totalImages = serializers.IntegerField()


class PreloadHintsSerializer(serializers.Serializer):
    """
    Serializer para hints de precarga.
    Ayuda al frontend a optimizar la carga de imágenes.
    """
    seriesId = serializers.UUIDField()
    priority = serializers.IntegerField()
    estimatedLoadTimeMs = serializers.IntegerField()
    recommendedConcurrency = serializers.IntegerField()
    criticalFrames = serializers.ListField(
        child=serializers.IntegerField(),
        help_text='Índices de frames críticos para cargar primero (centro, inicio, fin)'
    )
