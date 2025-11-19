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
from apps.audit.mixins import AuditMixin


@extend_schema(tags=['Patients'])
class PatientViewSet(AuditMixin, PermissionByActionMixin, viewsets.ModelViewSet):
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

    @action(detail=False, methods=['get'])
    def without_active_record(self, request):
        """Retorna pacientes que NO tienen historia clínica activa"""
        from apps.clinical_records.models import ClinicalRecord
        from django.db.models import Q
        
        # Obtener IDs de pacientes con historia activa
        patients_with_active = ClinicalRecord.objects.filter(
            tenant=request.tenant,
            status='active',
            deleted_at__isnull=True
        ).values_list('patient_id', flat=True)
        
        # Filtrar pacientes sin historia activa
        queryset = self.get_queryset().exclude(id__in=patients_with_active)
        
        # Aplicar búsqueda si existe
        search_query = request.query_params.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query) |
                Q(identity_document__icontains=search_query) |
                Q(email__icontains=search_query)
            )
        
        # Paginación
        page_size = int(request.query_params.get('page_size', 10))
        queryset = queryset[:page_size]
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'results': serializer.data,
            'count': len(serializer.data)
        })

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
        """Estadísticas detalladas de pacientes del tenant"""
        from django.db.models import Count, Q
        from django.utils import timezone
        from datetime import timedelta
        
        queryset = self.get_queryset()
        
        # Contar documentos
        from apps.documents.models import ClinicalDocument
        from apps.clinical_records.models import ClinicalForm, ClinicalRecord
        
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        documents_total = ClinicalDocument.objects.filter(
            tenant=self.request.tenant,
            deleted_at__isnull=True
        ).count()
        
        documents_today = ClinicalDocument.objects.filter(
            tenant=self.request.tenant,
            deleted_at__isnull=True,
            created_at__date=today
        ).count()
        
        documents_this_week = ClinicalDocument.objects.filter(
            tenant=self.request.tenant,
            deleted_at__isnull=True,
            created_at__date__gte=week_ago
        ).count()
        
        # Contar formularios
        forms_total = ClinicalForm.objects.filter(
            tenant=self.request.tenant
        ).count()
        
        forms_by_type = ClinicalForm.objects.filter(
            tenant=self.request.tenant
        ).values('form_type').annotate(count=Count('id')).order_by('-count')
        
        # Contar historias clínicas
        records_total = ClinicalRecord.objects.filter(
            tenant=self.request.tenant
        ).count()
        
        records_active = ClinicalRecord.objects.filter(
            tenant=self.request.tenant,
            status='active'
        ).count()
        
        # Calcular edad promedio
        from django.db.models import F, Q
        from datetime import date
        today_year = today.year
        
        ages = []
        for patient in queryset:
            if patient.date_of_birth:
                age = today_year - patient.date_of_birth.year
                ages.append(age)
        
        avg_age = sum(ages) / len(ages) if ages else 0
        
        stats = {
            'patients': {
                'total': queryset.count(),
                'by_gender': {
                    'M': queryset.filter(gender='M').count(),
                    'F': queryset.filter(gender='F').count(),
                    'O': queryset.filter(gender='O').count(),
                },
                'by_age_range': {
                    '0-17': len([a for a in ages if a < 18]),
                    '18-30': len([a for a in ages if 18 <= a < 31]),
                    '31-50': len([a for a in ages if 31 <= a < 51]),
                    '51+': len([a for a in ages if a >= 51]),
                },
                'average_age': round(avg_age, 1),
            },
            'documents': {
                'total': documents_total,
                'today': documents_today,
                'this_week': documents_this_week,
            },
            'clinical_records': {
                'total': records_total,
                'active': records_active,
                'archived': ClinicalRecord.objects.filter(
                    tenant=self.request.tenant,
                    status='archived'
                ).count(),
                'closed': ClinicalRecord.objects.filter(
                    tenant=self.request.tenant,
                    status='closed'
                ).count(),
            },
            'forms': {
                'total': forms_total,
                'by_type': [
                    {'type': item['form_type'], 'count': item['count']}
                    for item in forms_by_type
                ]
            }
        }

        return Response(stats)