from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse
from django.db import models
from drf_spectacular.utils import extend_schema

from .models import ClinicalDocument, MedicalImage, DocumentAccessLog
from .serializers import (
    ClinicalDocumentSerializer,
    ClinicalDocumentListSerializer,
    ClinicalDocumentUploadSerializer,
    MedicalImageSerializer,
    DocumentAccessLogSerializer
)
from .services import DocumentService


@extend_schema(tags=['Documents'])
class ClinicalDocumentViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de documentos clínicos"""
    queryset = ClinicalDocument.objects.all()
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'doctor_name', 'ocr_text']
    filterset_fields = ['document_type', 'specialty', 'is_signed', 'clinical_record']
    ordering_fields = ['document_date', 'created_at']
    ordering = ['-document_date']

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
        serializer.save(
            tenant=self.request.tenant,
            created_by=self.request.user
        )

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

        # Retornar documento creado
        response_serializer = ClinicalDocumentSerializer(document)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """
        Descarga el documento (genera URL firmada)
        """
        document = self.get_object()

        # Registrar acceso
        doc_service = DocumentService()
        doc_service.log_access(document, request.user, 'download', request)

        # Generar URL firmada
        from .storage import S3Storage
        storage = S3Storage()
        url = storage.get_presigned_url(document.file_path, expiration=300)  # 5 minutos

        if not url:
            return Response(
                {'error': 'Error al generar URL de descarga'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response({'download_url': url})

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
    
@extend_schema(tags=['Documents'])
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

@extend_schema(tags=['Documents'])
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