from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse
from django.db import models
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes

from .models import ClinicalDocument, MedicalImage, DocumentAccessLog
from .serializers import (
    ClinicalDocumentSerializer,
    ClinicalDocumentListSerializer,
    ClinicalDocumentUploadSerializer,
    MedicalImageSerializer,
    DocumentAccessLogSerializer
)
from .services import DocumentService
from .tasks import process_document_ocr  # Importar tarea Celery
from apps.core.permissions import (
    IsTenantMember,
    CanManageDocuments,
    PermissionByActionMixin,
    PermissionCodes
)

@extend_schema_view(
    list=extend_schema(
        summary="Listar documentos clínicos",
        description="Obtiene la lista de documentos clínicos del tenant actual",
        tags=['Documents'],
        parameters=[
            OpenApiParameter(
                name='document_type',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filtrar por tipo de documento',
            ),
            OpenApiParameter(
                name='specialty',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filtrar por especialidad',
            ),
        ],
    ),
    create=extend_schema(
        summary="Crear documento clínico",
        description="Crea un nuevo documento clínico",
        tags=['documents'],
    ),
    retrieve=extend_schema(
        summary="Obtener documento",
        description="Obtiene los detalles de un documento específico",
        tags=['documents'],
    ),
    update=extend_schema(
        summary="Actualizar documento",
        description="Actualiza un documento existente",
        tags=['documents'],
    ),
    destroy=extend_schema(
        summary="Eliminar documento",
        description="Elimina un documento (soft delete)",
        tags=['documents'],
    ),
)
class ClinicalDocumentViewSet(PermissionByActionMixin, viewsets.ModelViewSet):
    """
    ViewSet para gestión de documentos clínicos.

    Permisos requeridos:
    - list/retrieve: document.read
    - create/upload: document.create
    - update: document.update
    - delete: document.delete
    - sign: document.sign
    - download: document.read
    """
    queryset = ClinicalDocument.objects.all()
    permission_classes = [IsTenantMember, CanManageDocuments]
    resource_name = 'document'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'doctor_name', 'ocr_text']
    filterset_fields = ['document_type', 'specialty', 'is_signed', 'clinical_record']
    ordering_fields = ['document_date', 'created_at']
    ordering = ['-document_date']
    
    # Mapeo de permisos por acción
    permission_classes_by_action = {
        'list': [IsTenantMember],
        'retrieve': [IsTenantMember],
        'create': [IsTenantMember],
        'update': [IsTenantMember, CanManageDocuments],
        'partial_update': [IsTenantMember, CanManageDocuments],
        'destroy': [IsTenantMember, CanManageDocuments],
        'upload': [IsTenantMember],
        'download': [IsTenantMember],  # Solo requiere ser miembro del tenant
        'view': [IsTenantMember],  # Visualización de documentos
        'sign': [IsTenantMember, CanManageDocuments],
        'access_log': [IsTenantMember],
    }

    def get_parser_classes(self):
        """
        Usar MultiPartParser solo para upload y update (cuando se reemplace archivo)
        """
        if self.action in ['upload', 'update', 'partial_update']:
            return [MultiPartParser, FormParser]
        return super().get_parser_classes()

    def get_serializer_class(self):
        if self.action == 'list':
            return ClinicalDocumentListSerializer
        elif self.action == 'upload':
            return ClinicalDocumentUploadSerializer
        return ClinicalDocumentSerializer

    def get_queryset(self):
        """Filtrar documentos del tenant actual"""
        return ClinicalDocument.objects.filter(tenant=self.request.tenant)

    def perform_create(self, serializer):
        """Asignar tenant y usuario creador"""
        document = serializer.save(
            tenant=self.request.tenant,
            created_by=self.request.user
        )

        # Si tiene archivo y es PDF o imagen, lanzar OCR
        if document.mime_type in ['application/pdf', 'image/jpeg', 'image/png', 'image/tiff']:
            process_document_ocr.delay(str(document.id))

    def update(self, request, *args, **kwargs):
        """
        Actualizar documento con soporte opcional para reemplazo de archivo
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        # Verificar si el documento está bloqueado
        if instance.is_locked:
            return Response(
                {'error': 'El documento está bloqueado y no puede ser modificado'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verificar si se está enviando un nuevo archivo
        file_obj = request.FILES.get('file')

        if file_obj:
            # Si hay archivo nuevo, eliminar el antiguo de S3 y subir el nuevo
            from .storage import S3Storage
            storage = S3Storage()

            # Eliminar archivo antiguo si existe
            if instance.file_path:
                storage.delete_file(instance.file_path)

            # Subir nuevo archivo
            doc_service = DocumentService()
            success = doc_service.upload_document(instance, file_obj)

            if not success:
                return Response(
                    {'error': 'Error al subir el nuevo archivo'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            # Lanzar OCR para el nuevo archivo
            if instance.mime_type in ['application/pdf', 'image/jpeg', 'image/png', 'image/tiff']:
                # Resetear estado OCR
                instance.ocr_processed = False
                instance.ocr_text = ''
                instance.ocr_confidence = None
                instance.ocr_status = 'pending'
                instance.save()

                # Lanzar nueva tarea OCR
                process_document_ocr.delay(str(instance.id))

        # Actualizar otros campos
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        """PATCH method"""
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def upload(self, request):
        """
        Upload de documento con archivo
        """
        serializer = ClinicalDocumentUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Crear documento
        file_obj = serializer.validated_data.pop('file')
        document = serializer.save(
            tenant=request.tenant,
            created_by=request.user
        )

        # Subir archivo a S3 y procesar OCR
        doc_service = DocumentService()
        success = doc_service.upload_document(document, file_obj)

        if not success:
            document.delete()
            return Response(
                {'error': 'Error al subir el archivo a S3'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # 🎯 NUEVO: Lanzar tarea OCR automática para PDFs e imágenes
        if document.mime_type in ['application/pdf', 'image/jpeg', 'image/png', 'image/tiff']:
            # Lanzar tarea Celery asíncrona
            process_document_ocr.delay(str(document.id))

        # Retornar documento creado
        response_serializer = ClinicalDocumentSerializer(document)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """
        Descarga el documento (genera URL firmada con Content-Disposition para forzar descarga)
        """
        document = self.get_object()

        # Registrar acceso
        doc_service = DocumentService()
        doc_service.log_access(document, request.user, 'download', request)

        # Generar URL firmada con force_download=True para forzar descarga
        from .storage import S3Storage
        storage = S3Storage()
        url = storage.get_presigned_url(
            document.file_path,
            expiration=300,  # 5 minutos
            force_download=True,
            filename=document.file_name or 'documento'
        )

        if not url:
            return Response(
                {'error': 'Error al generar URL de descarga'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response({
            'url': url,
            'file_name': document.file_name or 'documento'
        })

    @action(detail=True, methods=['get'])
    def view(self, request, pk=None):
        """
        Obtiene URL para visualizar el documento (sin forzar descarga)
        Útil para previsualización en navegador
        """
        document = self.get_object()

        # Registrar acceso
        doc_service = DocumentService()
        doc_service.log_access(document, request.user, 'view', request)

        # Generar URL firmada SIN force_download para permitir visualización
        from .storage import S3Storage
        storage = S3Storage()
        url = storage.get_presigned_url(
            document.file_path,
            expiration=3600,  # 1 hora para visualización
            force_download=False
        )

        if not url:
            return Response(
                {'error': 'Error al generar URL de visualización'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response({
            'url': url,
            'file_name': document.file_name or 'documento'
        })

    @action(detail=True, methods=['post'])
    def sign(self, request, pk=None):
        """
        Firma digitalmente el documento
        """
        document = self.get_object()

        if document.is_locked:
            return Response(
                {'error': 'El documento está bloqueado y no puede ser modificado'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            document.sign_document(request.user)

            return Response({
                'message': 'Documento firmado exitosamente',
                'signed_at': document.signed_at,
                'signed_by': document.signed_by.get_full_name(),
                'digital_signature': document.digital_signature
            })

        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True,methods=['get'])
    def access_log(self, request, pk=None):
        """
        Retorna el log de accesos del documento
        """
        document = self.get_object()
        logs = DocumentAccessLog.objects.filter(
            tenant=request.tenant,
            document=document
        ).order_by('-accessed_at')
        
        serializer = DocumentAccessLogSerializer(logs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def search(self, request):
        """
        Búsqueda avanzada en documentos (incluye OCR)
        """
        query = request.query_params.get('q', '')
        
        if not query:
            return Response({'error': 'Parámetro "q" requerido'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Buscar en título, descripción y texto OCR
        documents = self.get_queryset().filter(
            models.Q(title__icontains=query) |
            models.Q(description__icontains=query) |
            models.Q(ocr_text__icontains=query) |
            models.Q(doctor_name__icontains=query)
        )
        
        serializer = ClinicalDocumentListSerializer(documents, many=True)
        return Response(serializer.data)
    
class MedicalImageViewSet(viewsets.ModelViewSet):
    """ViewSet para imágenes médicas"""
    queryset = MedicalImage.objects.all()
    serializer_class = MedicalImageSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['image_type', 'clinical_record']
    ordering_fields = ['study_date', 'created_at']
    ordering = ['-study_date']

    def get_queryset(self):
        """Filtrar imágenes del tenant actual"""
        return MedicalImage.objects.filter(tenant=self.request.tenant)

    def perform_create(self, serializer):
        """Asignar tenant y usuario creador"""
        serializer.save(
            tenant=self.request.tenant,
            created_by=self.request.user
        )

class DocumentAccessLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para consultar logs de acceso (solo lectura)"""
    queryset = DocumentAccessLog.objects.all()
    serializer_class = DocumentAccessLogSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['document', 'user', 'access_type']
    ordering = ['-accessed_at']

    def get_queryset(self):
        """Filtrar logs del tenant actual"""
        return DocumentAccessLog.objects.filter(tenant=self.request.tenant)