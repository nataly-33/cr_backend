"""
ViewSets y Views para la API DICOM.
"""

import logging
from django.http import FileResponse, HttpResponse
from django.utils import timezone

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter

from apps.core.permissions import (
    IsTenantMember,
    HasPermission,
    PermissionByActionMixin,
)

from .models import DicomStudy, DicomSeries, DicomInstance, DicomAccessLog
from .serializers import (
    DicomStudySerializer,
    DicomStudyListSerializer,
    DicomStudyDetailSerializer,
    DicomSeriesSerializer,
    DicomInstanceSerializer,
    DicomInstanceMinimalSerializer,
    DicomUploadSerializer,
    DicomBulkUploadSerializer,
    DicomAccessLogSerializer,
    DicomSeriesImageIdsSerializer,
    DicomIngestSerializer,
    DicomIngestResponseSerializer,
    SeriesViewerConfigSerializer,
    StudyViewerConfigSerializer,
)
from .services import (
    DicomUploadService,
    DicomRetrieveService,
    ingest_dicom_files,
    PatientMatchingStrategy,
)

logger = logging.getLogger(__name__)


@extend_schema_view(
    list=extend_schema(
        summary="Listar estudios DICOM",
        description="Lista todos los estudios DICOM del tenant actual.",
        tags=['DICOM'],
    ),
    retrieve=extend_schema(
        summary="Obtener estudio DICOM",
        description="Obtiene los detalles de un estudio DICOM específico.",
        tags=['DICOM'],
    ),
    destroy=extend_schema(
        summary="Eliminar estudio DICOM",
        description="Elimina un estudio DICOM y todos sus archivos asociados.",
        tags=['DICOM'],
    ),
)
class DicomStudyViewSet(PermissionByActionMixin, viewsets.ModelViewSet):
    """
    ViewSet para gestión de estudios DICOM.

    Endpoints:
    - GET /api/dicom/studies/ - Listar estudios
    - GET /api/dicom/studies/?patient_id={id} - Estudios de un paciente
    - GET /api/dicom/studies/{id}/ - Detalle de estudio
    - POST /api/dicom/studies/ingest/ - Ingestión de archivos DICOM
    - POST /api/dicom/studies/upload/ - Subir archivos DICOM (legacy)
    - POST /api/dicom/studies/upload-zip/ - Subir ZIP con DICOM
    - DELETE /api/dicom/studies/{id}/ - Eliminar estudio
    - GET /api/dicom/studies/{id}/metadata/ - Metadata para visor
    - GET /api/dicom/studies/{id}/access-log/ - Log de accesos
    """

    queryset = DicomStudy.objects.all()
    permission_classes = [IsTenantMember]  # Solo validar que sea miembro del tenant
    resource_name = 'dicom'
    parser_classes = [MultiPartParser, FormParser]

    def get_serializer_class(self):
        if self.action == 'list':
            return DicomStudyListSerializer
        elif self.action == 'retrieve':
            return DicomStudyDetailSerializer
        elif self.action == 'upload':
            return DicomUploadSerializer
        elif self.action == 'upload_zip':
            return DicomBulkUploadSerializer
        elif self.action == 'ingest':
            return DicomIngestSerializer
        return DicomStudySerializer

    def get_queryset(self):
        # Filtrar por tenant del usuario actual
        queryset = DicomStudy.objects.filter(tenant=self.request.tenant)

        # Filtros adicionales
        patient_id = self.request.query_params.get('patient_id')
        modality = self.request.query_params.get('modality')
        status_filter = self.request.query_params.get('status')
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')

        if patient_id:
            queryset = queryset.filter(patient_id=patient_id)
        if modality:
            queryset = queryset.filter(modality=modality)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if date_from:
            queryset = queryset.filter(study_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(study_date__lte=date_to)

        return queryset.select_related('patient').prefetch_related('series')

    @extend_schema(
        summary="Subir archivos DICOM",
        description="Sube uno o más archivos DICOM y los asocia a un paciente.",
        request=DicomUploadSerializer,
        responses={201: DicomStudyDetailSerializer},
        tags=['DICOM'],
    )
    @action(detail=False, methods=['post'], url_path='upload')
    def upload(self, request):
        """
        Endpoint para subir archivos DICOM.
        """
        serializer = DicomUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            service = DicomUploadService(
                tenant_id=request.tenant.id,
                user=request.user
            )

            study = service.process_files(
                files=serializer.validated_data['files'],
                patient_id=serializer.validated_data['patient_id'],
                clinical_record_id=serializer.validated_data.get('clinical_record_id'),
            )

            response_serializer = DicomStudyDetailSerializer(
                study,
                context={'request': request}
            )
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Error subiendo DICOM: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        summary="Subir ZIP con archivos DICOM",
        description="Sube un archivo ZIP conteniendo archivos DICOM.",
        request=DicomBulkUploadSerializer,
        responses={201: DicomStudyDetailSerializer},
        tags=['DICOM'],
    )
    @action(detail=False, methods=['post'], url_path='upload-zip')
    def upload_zip(self, request):
        """
        Endpoint para subir un ZIP con archivos DICOM.
        """
        serializer = DicomBulkUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            service = DicomUploadService(
                tenant_id=request.tenant.id,
                user=request.user
            )

            study = service.process_zip(
                zip_file=serializer.validated_data['zip_file'],
                patient_id=serializer.validated_data['patient_id'],
                clinical_record_id=serializer.validated_data.get('clinical_record_id'),
            )

            response_serializer = DicomStudyDetailSerializer(
                study,
                context={'request': request}
            )
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Error subiendo ZIP DICOM: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        summary="Ingerir archivos DICOM",
        description="""
        Ingesta uno o más archivos DICOM usando las funciones ingest_dicom_file()/ingest_dicom_files().

        Este endpoint:
        - Parsea los archivos DICOM con pydicom
        - Extrae metadata (StudyInstanceUID, SeriesInstanceUID, etc.)
        - Agrupa automáticamente por Study y Series
        - Asocia al paciente proporcionado
        - Soporta estrategias de matching de paciente
        """,
        request=DicomIngestSerializer,
        responses={201: DicomIngestResponseSerializer},
        tags=['DICOM'],
    )
    @action(detail=False, methods=['post'], url_path='ingest')
    def ingest(self, request):
        """
        Endpoint de ingestión de archivos DICOM.
        Usa ingest_dicom_files() para procesar múltiples archivos.
        """
        logger.info(f"Recibiendo datos de ingestión: {request.data.keys()}")
        serializer = DicomIngestSerializer(data=request.data)
        if not serializer.is_valid():
            logger.error(f"Errores de validación: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        logger.info(f"Datos validados: {serializer.validated_data.keys()}")

        try:
            # Mapear estrategia
            strategy_map = {
                'REQUIRE_EXISTING': PatientMatchingStrategy.REQUIRE_EXISTING,
                'MATCH_OR_FAIL': PatientMatchingStrategy.MATCH_OR_FAIL,
                'MATCH_OR_CREATE': PatientMatchingStrategy.MATCH_OR_CREATE,
                'ALWAYS_USE_PROVIDED': PatientMatchingStrategy.ALWAYS_USE_PROVIDED,
            }
            # Determinar estrategia basada en si se proporciona patient_id
            patient_id = serializer.validated_data.get('patient_id')
            if patient_id:
                # Si se proporciona patient_id, usar siempre el proporcionado
                strategy = PatientMatchingStrategy.ALWAYS_USE_PROVIDED
            else:
                # Si no se proporciona, usar MATCH_OR_CREATE para permitir estudios sin paciente
                matching_strategy = serializer.validated_data.get('matching_strategy', 'MATCH_OR_CREATE')
                strategy = strategy_map.get(matching_strategy, PatientMatchingStrategy.MATCH_OR_CREATE)

            logger.info(f"Usando estrategia: {strategy}, patient_id: {patient_id}")

            # Llamar a ingest_dicom_files()
            result = ingest_dicom_files(
                files=serializer.validated_data['files'],
                tenant=request.tenant,
                user=request.user,
                patient_id=patient_id,
                clinical_record_id=serializer.validated_data.get('clinical_record_id'),
                patient_strategy=strategy,
            )

            # Preparar respuesta
            # result es un IngestionResult (dataclass)
            studies_list = [result.study] if result.study else []
            response_data = {
                'studies': DicomStudyListSerializer(
                    studies_list,
                    many=True,
                    context={'request': request}
                ).data,
                'total_files_processed': result.total_instances,
                'total_studies_created': 1 if result.study else 0,
                'total_series_created': len(result.series_created),
                'total_instances_created': len(result.instances_created),
                'errors': result.errors,
            }

            return Response(response_data, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Error en ingestión DICOM: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        summary="Obtener metadata para visor",
        description="Retorna metadata del estudio optimizada para Cornerstone3D.",
        responses={200: dict},
        tags=['DICOM'],
    )
    @action(detail=True, methods=['get'], url_path='metadata')
    def metadata(self, request, pk=None):
        """
        Obtiene metadata del estudio para el visor.
        """
        service = DicomRetrieveService(request.tenant.id)
        metadata = service.get_study_metadata_for_viewer(pk)

        # Registrar acceso
        self._log_access(request, pk, 'view')

        return Response(metadata)

    @extend_schema(
        summary="Log de accesos al estudio",
        description="Retorna el historial de accesos al estudio.",
        responses={200: DicomAccessLogSerializer(many=True)},
        tags=['DICOM'],
    )
    @action(detail=True, methods=['get'], url_path='access-log')
    def access_log(self, request, pk=None):
        """
        Obtiene el log de accesos al estudio.
        """
        logs = DicomAccessLog.objects.filter(study_id=pk).order_by('-accessed_at')
        serializer = DicomAccessLogSerializer(logs, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Configuración completa del estudio para visor Cornerstone3D",
        description="""
        Retorna toda la información necesaria para inicializar Cornerstone3D
        con el estudio completo, incluyendo todas sus series.

        **Incluye:**
        - Metadata del estudio (paciente, fecha, descripción)
        - Lista de todas las series con sus imageIds
        - Configuración de volumen 3D para cada serie

        **Uso típico:**
        1. Obtener configuración del estudio
        2. Mostrar lista de series al usuario
        3. Cargar la serie seleccionada usando sus imageIds
        """,
        responses={200: StudyViewerConfigSerializer},
        tags=['DICOM'],
    )
    @action(detail=True, methods=['get'], url_path='viewer-config')
    def viewer_config(self, request, pk=None):
        """
        Configuración completa del estudio para Cornerstone3D.
        """
        # Query optimizada: cargar estudio con todas sus series e instancias
        study = DicomStudy.objects.select_related(
            'patient'
        ).prefetch_related(
            'series',
            'series__instances'
        ).get(pk=pk, tenant=request.tenant)

        serializer = StudyViewerConfigSerializer(
            study,
            context={'request': request}
        )

        # Registrar acceso
        self._log_access(request, pk, 'view')

        return Response(serializer.data)

    def perform_destroy(self, instance):
        """
        Elimina el estudio y sus archivos.
        """
        from .utils.dicom_storage import DicomStorageService
        storage = DicomStorageService(str(instance.tenant_id))
        storage.delete_study(instance.study_instance_uid)
        instance.delete()

    def _log_access(self, request, study_id, access_type):
        """Registra un acceso al estudio."""
        try:
            DicomAccessLog.objects.create(
                tenant=request.tenant,
                study_id=study_id,
                user=request.user,
                access_type=access_type,
                user_email=request.user.email,
                user_name=f"{request.user.first_name} {request.user.last_name}",
                ip_address=self._get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
            )
        except Exception as e:
            logger.warning(f"Error registrando acceso DICOM: {e}")

    def _get_client_ip(self, request):
        """Obtiene la IP del cliente."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')


@extend_schema_view(
    list=extend_schema(
        summary="Listar series de un estudio",
        description="Lista todas las series de un estudio DICOM.",
        tags=['DICOM'],
    ),
    retrieve=extend_schema(
        summary="Obtener serie DICOM",
        description="Obtiene los detalles de una serie DICOM.",
        tags=['DICOM'],
    ),
)
class DicomSeriesViewSet(PermissionByActionMixin, viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para series DICOM (solo lectura).

    Endpoints:
    - GET /api/dicom/series/ - Listar series
    - GET /api/dicom/series/{id}/ - Detalle de serie
    - GET /api/dicom/series/{id}/image-ids/ - ImageIds para Cornerstone
    - GET /api/dicom/series/{id}/viewer-config/ - Config completa para visor
    """

    queryset = DicomSeries.objects.all()
    serializer_class = DicomSeriesSerializer
    permission_classes = [IsTenantMember]  # Solo validar que sea miembro del tenant
    resource_name = 'dicom'

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filtrar por estudio si se proporciona
        study_id = self.request.query_params.get('study_id')
        if study_id:
            queryset = queryset.filter(study_id=study_id)

        return queryset.select_related('study').prefetch_related('instances')

    @extend_schema(
        summary="Obtener imageIds para Cornerstone3D",
        description="Retorna los imageIds de la serie en formato compatible con Cornerstone3D.",
        responses={200: DicomSeriesImageIdsSerializer},
        tags=['DICOM'],
    )
    @action(detail=True, methods=['get'], url_path='image-ids')
    def image_ids(self, request, pk=None):
        """
        Genera los imageIds para Cornerstone3D.
        """
        service = DicomRetrieveService(request.tenant.id)
        base_url = request.build_absolute_uri('/').rstrip('/')
        result = service.get_series_image_ids(pk, base_url)
        return Response(result)

    @extend_schema(
        summary="Configuración completa para visor Cornerstone3D",
        description="""
        Retorna toda la información necesaria para inicializar Cornerstone3D con esta serie.

        **Incluye:**
        - Metadata de la serie (modalidad, descripción, contraste, etc.)
        - Lista ordenada de URLs de streaming (`dicomUrls`)
        - ImageIds pre-formateados (`imageIds`) listos para usar
        - Configuración de volumen 3D (`volumeConfig`) para MPR/VR

        **Performance:**
        - Queries optimizadas con select_related y prefetch_related
        - Instancias pre-ordenadas por instance_number y slice_location
        - Respuesta diseñada para series de 100-300+ cortes

        **Ejemplo de uso en React:**
        ```javascript
        const config = await api.get(`/api/dicom/series/${seriesId}/viewer-config/`);

        // Opción 1: Usar imageIds directamente
        await cornerstone.loadAndCacheImages(config.imageIds);

        // Opción 2: Crear volumen 3D
        const volume = await volumeLoader.createAndCacheVolume(
            config.volumeConfig.volumeId,
            { imageIds: config.imageIds }
        );
        ```
        """,
        responses={200: SeriesViewerConfigSerializer},
        tags=['DICOM'],
    )
    @action(detail=True, methods=['get'], url_path='viewer-config')
    def viewer_config(self, request, pk=None):
        """
        Endpoint optimizado para configurar Cornerstone3D.

        Retorna JSON con toda la información necesaria para el visor:
        - seriesId, studyId, seriesInstanceUID
        - modality, bodyPartExamined, hasContrast
        - dicomUrls: lista ordenada de URLs de streaming
        - imageIds: lista de wadouri:{url} para Cornerstone3D
        - volumeConfig: configuración para volumen 3D
        """
        # Query optimizada: un solo hit a la DB
        series = DicomSeries.objects.select_related(
            'study',
            'study__patient'
        ).prefetch_related(
            'instances'
        ).get(pk=pk, tenant=request.tenant)

        # Obtener instancias ordenadas (ya pre-cargadas)
        instances = list(
            series.instances.order_by('instance_number', 'slice_location')
        )

        # Serializar con contexto
        serializer = SeriesViewerConfigSerializer(
            series,
            context={
                'request': request,
                'instances': instances,
            }
        )

        # Registrar acceso
        self._log_series_access(request, series, 'view')

        return Response(serializer.data)

    @extend_schema(
        summary="Hints de precarga para optimizar carga de imágenes",
        description="""
        Retorna sugerencias para optimizar la carga de imágenes en el visor.

        Útil para:
        - Determinar qué imágenes cargar primero (centro de la serie)
        - Estimar tiempo de carga
        - Configurar concurrencia óptima
        """,
        responses={200: dict},
        tags=['DICOM'],
    )
    @action(detail=True, methods=['get'], url_path='preload-hints')
    def preload_hints(self, request, pk=None):
        """
        Genera hints para optimizar la precarga de imágenes.
        """
        series = self.get_object()
        instance_count = series.number_of_instances or 0
        total_size = series.total_size_bytes or 0

        # Calcular frames críticos (inicio, centro, fin)
        critical_frames = []
        if instance_count > 0:
            critical_frames = [
                0,  # Primera imagen
                instance_count // 2,  # Centro
                instance_count - 1,  # Última imagen
            ]
            # Agregar cuartos si hay suficientes imágenes
            if instance_count > 20:
                critical_frames.extend([
                    instance_count // 4,
                    (instance_count * 3) // 4,
                ])
            critical_frames = sorted(set(critical_frames))

        # Estimar tiempo de carga (asumiendo ~2MB por imagen, 10Mbps conexión)
        avg_size_mb = (total_size / instance_count / 1024 / 1024) if instance_count > 0 else 2
        estimated_ms_per_image = avg_size_mb * 800  # ~800ms por MB en 10Mbps
        estimated_total_ms = int(estimated_ms_per_image * instance_count)

        # Recomendar concurrencia basada en tamaño
        if total_size > 500 * 1024 * 1024:  # > 500MB
            recommended_concurrency = 4
        elif total_size > 100 * 1024 * 1024:  # > 100MB
            recommended_concurrency = 6
        else:
            recommended_concurrency = 8

        return Response({
            'seriesId': str(series.id),
            'numberOfFrames': instance_count,
            'totalSizeBytes': total_size,
            'avgFrameSizeBytes': int(total_size / instance_count) if instance_count > 0 else 0,
            'priority': 1 if series.modality in ['MR', 'CT', 'PT'] else 2,
            'estimatedLoadTimeMs': estimated_total_ms,
            'recommendedConcurrency': recommended_concurrency,
            'criticalFrames': critical_frames,
            'loadingStrategy': 'interleaved' if instance_count > 50 else 'sequential',
        })

    def _log_series_access(self, request, series, access_type):
        """Registra acceso a una serie."""
        try:
            DicomAccessLog.objects.create(
                tenant=request.tenant,
                study=series.study,
                user=request.user,
                access_type=access_type,
                user_email=request.user.email,
                user_name=f"{request.user.first_name} {request.user.last_name}",
                ip_address=self._get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
            )
        except Exception as e:
            logger.warning(f"Error registrando acceso DICOM: {e}")

    def _get_client_ip(self, request):
        """Obtiene la IP del cliente."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')


@extend_schema_view(
    list=extend_schema(
        summary="Listar instancias de una serie",
        description="Lista todas las instancias de una serie DICOM.",
        tags=['DICOM'],
    ),
    retrieve=extend_schema(
        summary="Obtener instancia DICOM",
        description="Obtiene los detalles de una instancia DICOM.",
        tags=['DICOM'],
    ),
)
class DicomInstanceViewSet(PermissionByActionMixin, viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para instancias DICOM (solo lectura).

    Endpoints:
    - GET /api/dicom/instances/ - Listar instancias
    - GET /api/dicom/instances/{id}/ - Detalle de instancia
    - GET /api/dicom/instances/{id}/stream/ - Streaming archivo DICOM (Cornerstone3D)
    - GET /api/dicom/instances/{id}/metadata/ - Metadata de la instancia
    """

    queryset = DicomInstance.objects.all()
    permission_classes = [IsTenantMember]  # Solo validar que sea miembro del tenant
    resource_name = 'dicom'

    def get_serializer_class(self):
        if self.action == 'list':
            return DicomInstanceMinimalSerializer
        return DicomInstanceSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filtrar por serie si se proporciona
        series_id = self.request.query_params.get('series_id')
        if series_id:
            queryset = queryset.filter(series_id=series_id)

        return queryset.select_related('series__study')

    @extend_schema(
        summary="Stream archivo DICOM",
        description="""
        Streaming del archivo DICOM para visualización con Cornerstone3D.

        Headers importantes para el visor:
        - Content-Type: application/dicom
        - Accept-Ranges: bytes (para seeks parciales)
        - Access-Control-Allow-Origin: * (CORS para visor)
        """,
        responses={
            200: {
                'content': {'application/dicom': {}},
                'description': 'Archivo DICOM binario en streaming'
            }
        },
        tags=['DICOM'],
    )
    @action(detail=True, methods=['get'], url_path='stream')
    def stream(self, request, pk=None):
        """
        Endpoint de streaming del archivo DICOM.
        Optimizado para Cornerstone3D con imageId wadouri.
        """
        instance = self.get_object()
        service = DicomRetrieveService(request.tenant.id)

        try:
            # Obtener stream del archivo
            file_stream = service.get_instance_stream(instance.id)

            # Registrar acceso
            self._log_instance_access(request, instance, 'stream')

            # Respuesta con headers para CORS y streaming
            response = FileResponse(
                file_stream,
                content_type='application/dicom',
                as_attachment=False,
            )

            # Headers importantes para Cornerstone3D
            response['Content-Disposition'] = f'inline; filename="{instance.file_name}"'
            response['Content-Length'] = instance.file_size_bytes
            response['Accept-Ranges'] = 'bytes'

            # Headers CORS adicionales para el visor
            response['Access-Control-Allow-Origin'] = '*'
            response['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
            response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
            response['Access-Control-Expose-Headers'] = 'Content-Length, Content-Range'

            return response

        except FileNotFoundError:
            return Response(
                {'error': 'Archivo no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error sirviendo archivo DICOM: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        summary="Obtener metadata de instancia",
        description="Retorna metadata completa de la instancia DICOM.",
        responses={200: dict},
        tags=['DICOM'],
    )
    @action(detail=True, methods=['get'], url_path='metadata')
    def metadata(self, request, pk=None):
        """
        Obtiene metadata completa de la instancia.
        """
        instance = self.get_object()
        return Response({
            'instance': instance.dicom_metadata,
            'series': instance.series.dicom_metadata,
            'study': instance.series.study.dicom_metadata,
        })

    def _log_instance_access(self, request, instance, access_type):
        """Registra acceso a una instancia."""
        try:
            DicomAccessLog.objects.create(
                tenant=request.tenant,
                study=instance.series.study,
                user=request.user,
                access_type=access_type,
                user_email=request.user.email,
                user_name=f"{request.user.first_name} {request.user.last_name}",
                ip_address=self._get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
            )
        except Exception as e:
            logger.warning(f"Error registrando acceso DICOM: {e}")

    def _get_client_ip(self, request):
        """Obtiene la IP del cliente."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')
