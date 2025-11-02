from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema

from .models import ClinicalRecord
from .serializers import ClinicalRecordSerializer, ClinicalRecordCreateSerializer
from apps.core.permissions import (
    IsTenantMember,
    CanManageClinicalRecords,
    PermissionByActionMixin
)


@extend_schema(tags=['Clinic Record'])
class ClinicalRecordViewSet(PermissionByActionMixin, viewsets.ModelViewSet):
    """
    ViewSet para gestión de historias clínicas.
    
    Permisos requeridos:
    - list/retrieve: clinical_record.read
    - create: clinical_record.create
    - update: clinical_record.update
    - delete: clinical_record.delete
    
    Reglas especiales:
    - Pacientes solo pueden ver SU propia historia clínica
    - Doctores pueden gestionar todas las historias de su tenant
    """
    queryset = ClinicalRecord.objects.all()
    permission_classes = [IsTenantMember, CanManageClinicalRecords]
    resource_name = 'clinical_record'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['record_number', 'patient__first_name', 'patient__last_name']
    filterset_fields = ['status', 'patient']
    ordering_fields = ['created_at', 'record_number']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'create':
            return ClinicalRecordCreateSerializer
        return ClinicalRecordSerializer

    def get_queryset(self):
        """Filtrar historias del tenant actual"""
        return ClinicalRecord.objects.filter(tenant=self.request.tenant)

    def perform_create(self, serializer):
        """Asignar tenant y usuario creador"""
        serializer.save(
            tenant=self.request.tenant,
            created_by=self.request.user
        )

    @action(detail=True, methods=['get'])
    def documents(self, request, pk=None):
        """Retorna los documentos de esta historia clínica"""
        record = self.get_object()
        from apps.documents.serializers import ClinicalDocumentListSerializer

        documents = record.clinicaldocument_set.filter(deleted_at__isnull=True)
        serializer = ClinicalDocumentListSerializer(documents, many=True)

        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def timeline(self, request, pk=None):
        """Timeline cronológico de eventos de la historia clínica"""
        record = self.get_object()

        # Obtener documentos
        documents = record.clinicaldocument_set.filter(
            deleted_at__isnull=True
        ).order_by('-document_date')

        timeline = []
        for doc in documents:
            timeline.append({
                'type': 'document',
                'date': doc.document_date,
                'title': doc.title,
                'document_type': doc.document_type,
                'specialty': doc.specialty,
                'doctor_name': doc.doctor_name,
                'id': str(doc.id)
            })

        # Ordenar por fecha descendente
        timeline.sort(key=lambda x: x['date'], reverse=True)

        return Response(timeline)

    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        """Archivar historia clínica"""
        record = self.get_object()
        record.status = 'archived'
        record.save()

        return Response({
            'message': 'Historia clínica archivada exitosamente',
            'status': record.status
        })

    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        """Cerrar historia clínica"""
        record = self.get_object()
        record.status = 'closed'
        record.save()

        return Response({
            'message': 'Historia clínica cerrada exitosamente',
            'status': record.status
        })