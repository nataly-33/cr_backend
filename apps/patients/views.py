from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema

from .models import Patient
from .serializers import PatientSerializer, PatientListSerializer
from .filters import PatientFilter
from apps.core.permissions import (
    IsTenantMember,
    HasPermission,
    PermissionByActionMixin,
    PermissionCodes
)


@extend_schema(tags=['Patients'])
class PatientViewSet(PermissionByActionMixin, viewsets.ModelViewSet):
    """
    ViewSet para gestión de pacientes.
    
    Permisos requeridos:
    - list/retrieve: patient.read
    - create: patient.create
    - update: patient.update
    - delete: patient.delete
    """
    queryset = Patient.objects.all()
    permission_classes = [IsTenantMember, HasPermission]
    resource_name = 'patient'  # Para HasPermission
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = PatientFilter
    search_fields = ['first_name', 'last_name', 'identity_document', 'email']
    ordering_fields = ['created_at', 'first_name', 'last_name']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return PatientListSerializer
        return PatientSerializer

    def get_queryset(self):
        """Filtrar pacientes del tenant actual"""
        return Patient.objects.filter(tenant=self.request.tenant)

    def perform_create(self, serializer):
        """Asignar tenant y usuario creador"""
        serializer.save(
            tenant=self.request.tenant,
            created_by=self.request.user
        )

    @action(detail=True, methods=['get'])
    def clinical_records(self, request, pk=None):
        """Retorna las historias clínicas del paciente"""
        patient = self.get_object()
        from apps.clinical_records.serializers import ClinicalRecordSerializer

        records = patient.clinicalrecord_set.filter(deleted_at__isnull=True)
        serializer = ClinicalRecordSerializer(records, many=True)

        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Estadísticas de pacientes del tenant"""
        queryset = self.get_queryset()

        stats = {
            'total': queryset.count(),
            'by_gender': {
                'M': queryset.filter(gender='M').count(),
                'F': queryset.filter(gender='F').count(),
                'O': queryset.filter(gender='O').count(),
            },
            'by_age_range': {
                '0-17': queryset.filter(date_of_birth__year__gte=2007).count(),
                '18-30': queryset.filter(
                    date_of_birth__year__gte=1994,
                    date_of_birth__year__lt=2007
                ).count(),
                '31-50': queryset.filter(
                    date_of_birth__year__gte=1974,
                    date_of_birth__year__lt=1994
                ).count(),
                '51+': queryset.filter(date_of_birth__year__lt=1974).count(),
            }
        }

        return Response(stats)