from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse
from django.db import models
from django.conf import settings
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
import logging

logger = logging.getLogger(__name__)

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
    permission_classes = [IsTenantMember]  # Solo requiere ser miembro del tenant por defecto
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
        'process_ocr': [IsTenantMember],  # Procesamiento OCR manual
        'enhance': [IsTenantMember],  # Mejora de imagen con CLAHE - solo miembro del tenant
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

        # OCR Manual: El usuario debe ejecutarlo manualmente desde la interfaz
        # Comentado para evitar consumo automático de créditos de AWS
        # if document.mime_type in ['application/pdf', 'image/jpeg', 'image/png', 'image/tiff']:
        #     process_document_ocr.delay(str(document.id))

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

            # OCR desactivado por defecto - se activa manualmente desde el frontend
            # if instance.mime_type in ['application/pdf', 'image/jpeg', 'image/png', 'image/tiff']:
            #     # Resetear estado OCR
            #     instance.ocr_processed = False
            #     instance.ocr_text = ''
            #     instance.ocr_confidence = None
            #     instance.ocr_status = 'pending'
            #     instance.save()
            #     # Lanzar nueva tarea OCR
            #     process_document_ocr.delay(str(instance.id))

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

        # OCR desactivado por defecto - se activa manualmente desde el frontend con el botón
        # if document.mime_type in ['application/pdf', 'image/jpeg', 'image/png', 'image/tiff']:
        #     # Lanzar tarea Celery asíncrona
        #     process_document_ocr.delay(str(document.id))

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

    @action(detail=True, methods=['post'], url_path='process-ocr')
    def process_ocr(self, request, pk=None):
        """
        Procesar OCR manualmente para un documento
        POST /api/documents/{id}/process-ocr/
        """
        document = self.get_object()

        # Verificar que el documento tiene archivo
        if not document.file_path:
            return Response(
                {'error': 'El documento no tiene archivo asociado'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verificar que sea PDF o imagen
        valid_types = ['application/pdf', 'image/jpeg', 'image/png', 'image/tiff']
        if document.mime_type not in valid_types:
            return Response(
                {'error': 'El OCR solo está disponible para PDF e imágenes'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verificar si ya fue procesado
        if document.ocr_processed and document.ocr_status == 'completed':
            return Response(
                {'message': 'Este documento ya fue procesado con OCR'},
                status=status.HTTP_200_OK
            )

        try:
            # Lanzar tarea de Celery
            process_document_ocr.delay(str(document.id))

            # Actualizar estado
            document.ocr_status = 'processing'
            document.save()

            return Response({
                'message': 'Procesamiento OCR iniciado',
                'ocr_status': 'processing',
                'document_id': str(document.id)
            })

        except Exception as e:
            logger.exception("Error al iniciar procesamiento OCR")
            return Response(
                {'error': f'Error al iniciar OCR: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'], url_path='enhance')
    def enhance_image(self, request, pk=None):
        """
        Mejorar calidad de imagen con CLAHE
        POST /api/documents/{id}/enhance/

        Body (opcional):
        {
            "modality": "xray",  // xray, ct_scan, mri, ultrasound, mammography, pet_scan
            "clip_limit": 2.0,
            "tile_grid_size": [8, 8]
        }
        """
        from .image_enhancement_service import ImageEnhancementService
        from .storage import S3Storage
        import os
        import tempfile
        from django.core.files.base import ContentFile

        try:
            document = self.get_object()

            # Verificar que el documento tiene archivo
            if not document.file_path:
                return Response(
                    {'error': 'El documento no tiene archivo asociado'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Verificar que es una imagen
            file_name = document.file_name or ''
            mime_type = getattr(document, 'mime_type', getattr(document, 'file_type', ''))
            is_image = (
                mime_type and mime_type.startswith('image/') or
                file_name.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.dcm', '.dicom'))
            )

            if not is_image:
                return Response(
                    {'error': 'El documento no es una imagen'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Verificar si ya está mejorada
            if document.enhanced_image_path:
                storage = S3Storage()
                enhanced_url = storage.get_presigned_url(document.enhanced_image_path)
                original_url = storage.get_presigned_url(document.file_path) if document.file_path else document.file_url

                return Response({
                    'message': 'La imagen ya está mejorada',
                    'original_url': original_url,
                    'enhanced_url': enhanced_url
                })

            # Obtener parámetros (opcional)
            modality = request.data.get('modality')  # xray, ct_scan, mri, etc.
            clip_limit = request.data.get('clip_limit')
            tile_grid_size = request.data.get('tile_grid_size')

            # Descargar archivo desde S3 a temporal
            storage = S3Storage()
            temp_original_path = None

            try:
                # Crear archivo temporal para la imagen original
                suffix = os.path.splitext(file_name)[1] or '.jpg'
                
                if storage.use_s3:
                    # Usar un método más seguro en Windows - dejar que boto3 maneje el archivo
                    import tempfile
                    temp_dir = tempfile.gettempdir()
                    import uuid
                    temp_filename = f"enhance_{uuid.uuid4().hex}{suffix}"
                    temp_original_path = os.path.join(temp_dir, temp_filename)
                    
                    # Descargar directamente a la ruta
                    storage.s3_client.download_file(
                        storage.bucket_name,
                        document.file_path,
                        temp_original_path
                    )
                else:
                    # Local storage
                    local_path = os.path.join(settings.MEDIA_ROOT, document.file_path)
                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
                    temp_original_path = temp_file.name
                    temp_file.close()
                    
                    with open(local_path, 'rb') as src:
                        with open(temp_original_path, 'wb') as dst:
                            dst.write(src.read())

            except Exception as e:
                # Limpiar si falla la descarga
                if temp_original_path and os.path.exists(temp_original_path):
                    try:
                        os.remove(temp_original_path)
                    except:
                        pass
                raise e

            # Crear servicio de mejora
            enhancement_service = ImageEnhancementService()

            # Mejorar imagen según parámetros
            if modality:
                # Usar preset por modalidad
                enhanced_path = enhancement_service.enhance_with_preset(
                    temp_original_path,
                    modality=modality,
                    preserve_color=True
                )
            elif clip_limit or tile_grid_size:
                # Usar parámetros manuales
                enhanced_path = enhancement_service.enhance_medical_image(
                    temp_original_path,
                    clip_limit=float(clip_limit) if clip_limit else 2.0,
                    tile_grid_size=tuple(tile_grid_size) if tile_grid_size else (8, 8),
                    preserve_color=True
                )
            else:
                # Auto-detectar
                enhanced_path = enhancement_service.auto_enhance(
                    temp_original_path,
                    modality=None
                )

            # Guardar imagen mejorada en S3 en la carpeta images/
            tenant_slug = request.tenant.slug

            # Original: documents/{tenant_slug}/filename.jpg (ya existe)
            # Enhanced: images/{tenant_slug}/filename_enhanced.jpg (nuevo)
            base_name = os.path.splitext(os.path.basename(file_name))[0]
            enhanced_filename = f"{base_name}_enhanced.jpg"
            s3_enhanced_path = f"images/{tenant_slug}/{enhanced_filename}"

            # Subir imagen mejorada a S3
            with open(enhanced_path, 'rb') as enhanced_file:
                from django.core.files.uploadedfile import InMemoryUploadedFile
                import io

                file_content = enhanced_file.read()
                file_obj = ContentFile(file_content)
                file_obj.content_type = 'image/jpeg'

                enhanced_url = storage.upload_file(file_obj, s3_enhanced_path)

            if not enhanced_url:
                raise Exception("Error al subir imagen mejorada a S3")

            # Actualizar documento con ruta de imagen mejorada
            document.enhanced_image_path = s3_enhanced_path
            document.save()

            # Obtener métricas de comparación
            metrics = enhancement_service.compare_images(temp_original_path, enhanced_path)

            # Limpiar archivos temporales INMEDIATAMENTE después de usarlos
            try:
                if os.path.exists(temp_original_path):
                    os.remove(temp_original_path)
            except Exception as cleanup_error:
                logger.warning(f"No se pudo eliminar archivo temporal original: {cleanup_error}")

            try:
                if os.path.exists(enhanced_path):
                    os.remove(enhanced_path)
            except Exception as cleanup_error:
                logger.warning(f"No se pudo eliminar archivo temporal mejorado: {cleanup_error}")

            # URLs para respuesta
            original_url = storage.get_presigned_url(document.file_path) if document.file_path else document.file_url
            enhanced_presigned_url = storage.get_presigned_url(s3_enhanced_path)

            return Response({
                'message': 'Imagen mejorada exitosamente',
                'original_url': original_url,
                'enhanced_url': enhanced_presigned_url,
                'enhanced_path': s3_enhanced_path,
                'metrics': metrics,
                'method': 'CLAHE',
                'modality': modality if modality else 'auto',
            })

        except Exception as e:
            logger.exception("Error enhancing document image")
            return Response(
                {'error': f'Error al mejorar imagen: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

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

    @action(detail=True, methods=['post'], url_path='enhance')
    def enhance_image(self, request, pk=None):
        """
        Mejorar calidad de imagen con CLAHE
        POST /api/medical-images/{id}/enhance/
        """
        from .image_enhancement_service import ImageEnhancementService

        try:
            medical_image = self.get_object()

            # Verificar que la imagen existe
            if not medical_image.image_file:
                return Response(
                    {'error': 'La imagen no tiene archivo asociado'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Verificar que no esté ya mejorada
            if medical_image.enhanced_file:
                return Response({
                    'message': 'La imagen ya está mejorada',
                    'enhanced_url': medical_image.enhanced_file.url if hasattr(medical_image.enhanced_file, 'url') else str(medical_image.enhanced_file)
                })

            # Crear servicio
            enhancement_service = ImageEnhancementService()

            # Mejorar imagen
            original_path = medical_image.image_file.path
            enhanced_path = enhancement_service.auto_enhance(original_path)

            # Guardar ruta mejorada
            medical_image.enhanced_file = enhanced_path
            medical_image.enhancement_applied = True
            medical_image.enhancement_method = 'clahe'
            medical_image.enhancement_params = {
                'clip_limit': 2.0,
                'tile_grid_size': (8, 8),
                'denoise': True,
                'sharpen': True
            }
            medical_image.save()

            # Obtener métricas
            metrics = enhancement_service.compare_images(original_path, enhanced_path)

            return Response({
                'message': 'Imagen mejorada exitosamente',
                'original_url': medical_image.image_file.url if hasattr(medical_image.image_file, 'url') else str(medical_image.image_file),
                'enhanced_url': medical_image.enhanced_file if isinstance(medical_image.enhanced_file, str) else medical_image.enhanced_file.url,
                'metrics': metrics,
                'method': 'CLAHE',
            })

        except Exception as e:
            logger.exception("Error enhancing image")
            return Response(
                {'error': f'Error al mejorar imagen: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
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