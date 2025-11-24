"""
URLs para la app DICOM.

Estructura de endpoints:

DICOM Core (prefijo: /api/dicom/):

Studies:
- GET    /api/dicom/studies/                    - Listar estudios
- GET    /api/dicom/studies/?patient_id={id}    - Estudios por paciente
- GET    /api/dicom/studies/{id}/               - Detalle de estudio
- POST   /api/dicom/studies/ingest/             - Ingestión DICOM
- POST   /api/dicom/studies/upload/             - Upload legacy
- POST   /api/dicom/studies/upload-zip/         - Upload ZIP
- DELETE /api/dicom/studies/{id}/               - Eliminar estudio
- GET    /api/dicom/studies/{id}/metadata/      - Metadata para visor
- GET    /api/dicom/studies/{id}/viewer-config/ - Config completa Cornerstone3D
- GET    /api/dicom/studies/{id}/access-log/    - Log de accesos

Series:
- GET    /api/dicom/series/                     - Listar series
- GET    /api/dicom/series/?study_id={id}       - Series por estudio
- GET    /api/dicom/series/{id}/                - Detalle de serie
- GET    /api/dicom/series/{id}/image-ids/      - ImageIds Cornerstone3D
- GET    /api/dicom/series/{id}/viewer-config/  - Config completa Cornerstone3D
- GET    /api/dicom/series/{id}/preload-hints/  - Hints de precarga
- GET    /api/dicom/series/{id}/instances/      - Instancias de la serie

Instances:
- GET    /api/dicom/instances/                  - Listar instancias
- GET    /api/dicom/instances/?series_id={id}   - Instancias por serie
- GET    /api/dicom/instances/{id}/             - Detalle de instancia
- GET    /api/dicom/instances/{id}/stream/      - Streaming archivo DICOM
- GET    /api/dicom/instances/{id}/metadata/    - Metadata de instancia

Rutas alternativas (anidadas en patients):
- GET    /api/patients/{patient_id}/dicom-studies/  - Estudios del paciente
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from apps.core.permissions import IsTenantMember, HasPermission

from .views import DicomStudyViewSet, DicomSeriesViewSet, DicomInstanceViewSet
from .temp_views import upload_and_view_dicom, stream_temp_dicom
from .models import DicomStudy, DicomSeries
from .serializers import (
    DicomStudyListSerializer,
    DicomInstanceMinimalSerializer,
)

router = DefaultRouter()
router.register(r'studies', DicomStudyViewSet, basename='dicom-study')
router.register(r'series', DicomSeriesViewSet, basename='dicom-series')
router.register(r'instances', DicomInstanceViewSet, basename='dicom-instance')


@api_view(['GET'])
@permission_classes([IsTenantMember, HasPermission])
def series_instances(request, pk):
    """
    Lista las instancias de una serie específica.
    GET /api/dicom/series/{id}/instances/
    """
    try:
        series = DicomSeries.objects.get(pk=pk, tenant=request.tenant)
        instances = series.instances.all().order_by('instance_number', 'slice_location')
        serializer = DicomInstanceMinimalSerializer(instances, many=True)
        return Response(serializer.data)
    except DicomSeries.DoesNotExist:
        return Response({'error': 'Serie no encontrada'}, status=404)


urlpatterns = [
    # Router principal
    path('', include(router.urls)),

    # Endpoint anidado para instancias de una serie
    path(
        'series/<uuid:pk>/instances/',
        series_instances,
        name='dicom-series-instances'
    ),
    
    # Endpoints temporales para visualización rápida (sin BD)
    path('temp/upload/', upload_and_view_dicom, name='temp-upload-dicom'),
    path('temp/stream/<str:file_uuid>/', stream_temp_dicom, name='temp-stream-dicom'),
]


# URLs para incluir en apps/patients/urls.py
# Estas rutas proporcionan acceso anidado a estudios DICOM por paciente

def get_patient_dicom_urls():
    """
    Retorna las URLs para montar en el router de pacientes.
    Uso en apps/patients/urls.py:

        from apps.dicom.urls import get_patient_dicom_urls
        urlpatterns += get_patient_dicom_urls()
    """
    from django.urls import path

    @api_view(['GET'])
    @permission_classes([IsTenantMember, HasPermission])
    def patient_dicom_studies(request, patient_id):
        """
        Lista estudios DICOM de un paciente específico.
        GET /api/patients/{patient_id}/dicom-studies/
        """
        studies = DicomStudy.objects.filter(
            tenant=request.tenant,
            patient_id=patient_id
        ).select_related('patient').prefetch_related('series')

        serializer = DicomStudyListSerializer(
            studies,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)

    return [
        path(
            '<uuid:patient_id>/dicom-studies/',
            patient_dicom_studies,
            name='patient-dicom-studies'
        ),
    ]
