from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse
from django.db.models import Count, Q
from datetime import datetime
import time

from .models import ReportTemplate, ReportExecution
from .serializers import (
    ReportTemplateSerializer,
    ReportExecutionSerializer,
    GenerateReportSerializer
)
from .generators.pdf_generator import generate_documents_report
from .generators.excel_generator import generate_documents_excel
from .generators.csv_generator import generate_documents_csv
from apps.documents.models import ClinicalDocument
from apps.core.models import get_current_tenant


class ReportTemplateViewSet(viewsets.ModelViewSet):
    """ViewSet para plantillas de reportes"""
    queryset = ReportTemplate.objects.all()
    serializer_class = ReportTemplateSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class ReportExecutionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para historial de reportes"""
    queryset = ReportExecution.objects.all()
    serializer_class = ReportExecutionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtrar por usuario si no es admin
        if not self.request.user.is_tenant_owner:
            queryset = queryset.filter(executed_by=self.request.user)
        
        return queryset.select_related('template', 'executed_by')
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Descargar reporte generado"""
        execution = self.get_object()
        
        if not execution.file_path:
            return Response(
                {'error': 'No hay archivo disponible para este reporte'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response({'file_url': execution.file_path})


class ReportGeneratorViewSet(viewsets.ViewSet):
    """ViewSet para generar reportes on-demand"""
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def generate(self, request):
        """Generar reporte"""
        serializer = GenerateReportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        report_type = serializer.validated_data['report_type']
        output_format = serializer.validated_data['output_format']
        filters = serializer.validated_data.get('filters', {})
        
        start_time = time.time()
        
        try:
            # Obtener datos según tipo de reporte
            if report_type == 'documents':
                data = self._get_documents_data(filters, serializer.validated_data)
            elif report_type == 'patients':
                data = self._get_patients_data(filters)
            else:
                data = self._get_analytics_data(filters)
            
            # Generar reporte según formato
            tenant = get_current_tenant()
            user = request.user
            
            if output_format == 'pdf':
                file_content = generate_documents_report(data, tenant.name, user.full_name)
                content_type = 'application/pdf'
                filename = f'reporte_documentos_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
            elif output_format == 'excel':
                file_content = generate_documents_excel(data, tenant.name, user.full_name)
                content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                filename = f'reporte_documentos_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
            else:  # csv
                file_content = generate_documents_csv(data)
                content_type = 'text/csv'
                filename = f'reporte_documentos_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            
            execution_time = int((time.time() - start_time) * 1000)
            
            # Guardar ejecución
            ReportExecution.objects.create(
                executed_by=user,
                parameters_used=serializer.validated_data,
                output_format=output_format,
                execution_time_ms=execution_time,
                rows_returned=data.get('total', 0),
                status='completed'
            )
            
            # Retornar archivo
            response = HttpResponse(file_content, content_type=content_type)
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
            
        except Exception as e:
            # Guardar ejecución fallida
            ReportExecution.objects.create(
                executed_by=request.user,
                parameters_used=serializer.validated_data,
                output_format=output_format,
                status='failed',
                error_message=str(e)
            )
            
            return Response(
                {'error': f'Error al generar reporte: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _get_documents_data(self, filters, validated_data):
        """Obtener datos de documentos"""
        queryset = ClinicalDocument.objects.select_related(
            'clinical_record__patient',
            'created_by'
        )
        
        # Aplicar filtros
        if validated_data.get('date_from'):
            queryset = queryset.filter(document_date__gte=validated_data['date_from'])
        
        if validated_data.get('date_to'):
            queryset = queryset.filter(document_date__lte=validated_data['date_to'])
        
        if validated_data.get('document_type'):
            queryset = queryset.filter(document_type=validated_data['document_type'])
        
        if validated_data.get('specialty'):
            queryset = queryset.filter(specialty=validated_data['specialty'])
        
        # Estadísticas
        by_type = queryset.values('document_type').annotate(count=Count('id'))
        
        # Documentos recientes
        recent_documents = queryset.order_by('-created_at')[:50].values(
            'document_date',
            'document_type',
            'title',
            'specialty',
            'doctor_name',
            patient_name=Q('clinical_record__patient__full_name')
        )
        
        return {
            'total': queryset.count(),
            'by_type': list(by_type),
            'recent_documents': list(recent_documents)
        }
    
    def _get_patients_data(self, filters):
        """Obtener datos de pacientes"""
        #Implemenstar

        return {'total': 0}
    
    def _get_analytics_data(self, filters):
        """Obtener datos analíticos"""
        #Implementar
        return {'total': 0}