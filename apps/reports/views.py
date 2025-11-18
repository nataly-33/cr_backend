from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse, FileResponse
from django.db.models import Count, Q
from datetime import datetime, timedelta
import time
import logging
import io

from .models import ReportTemplate, ReportExecution, AIAnalysis
from .serializers import (
    ReportTemplateSerializer,
    ReportExecutionSerializer,
    GenerateReportSerializer,
    QBEExampleSerializer,
    QBEResponseSerializer,
    DynamicReportSerializer,
    AIAnalysisResultSerializer,
    AISummarySerializer,
    AIRecommendationSerializer,
    AIInsightsResponseSerializer,
)
from .services import AIAnalysisService
from .qbe_parser import QBEParser, QBEParseError
from .filters import DynamicFilter
from .dynamic_report import DynamicReportGenerator, DynamicReportError
from .generators.pdf_generator import generate_documents_report
from .generators.excel_generator import generate_documents_excel
from .generators.csv_generator import generate_documents_csv
from apps.documents.models import ClinicalDocument
from apps.patients.models import Patient
from apps.clinical_records.models import ClinicalRecord
from apps.accounts.models import User
from apps.core.models import get_current_tenant
from drf_spectacular.utils import extend_schema

logger = logging.getLogger(__name__)


@extend_schema(tags=['Reports'])
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
        
        # Filtrar por usuario si no es admin o superusuario
        # Los admins (is_staff) y superusuarios pueden ver todos los reportes
        if not (self.request.user.is_staff or self.request.user.is_superuser):
            queryset = queryset.filter(executed_by=self.request.user)
        
        return queryset.select_related('template', 'executed_by')
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Descargar reporte generado"""
        try:
            execution = self.get_object()
            
            # Verificar que el reporte está completado
            if execution.status != 'completed':
                return Response(
                    {'error': 'El reporte no está completado'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Verificar que existe archivo guardado
            if not execution.file_path:
                return Response(
                    {'error': 'No hay archivo disponible para este reporte'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Obtener ruta del archivo
            import os
            from django.conf import settings
            
            # El file_path es relativo (ej: /media/reports/filename.pdf)
            # Necesitamos obtener la ruta absoluta
            if execution.file_path.startswith('/media/'):
                file_path = os.path.join(settings.MEDIA_ROOT, execution.file_path[7:])
            else:
                file_path = os.path.join(settings.MEDIA_ROOT, execution.file_path)
            
            # Verificar que el archivo existe
            if not os.path.exists(file_path):
                return Response(
                    {'error': 'El archivo no existe en el servidor'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Determinar tipo de contenido según extensión
            _, file_ext = os.path.splitext(file_path)
            content_types = {
                '.pdf': 'application/pdf',
                '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                '.csv': 'text/csv'
            }
            content_type = content_types.get(file_ext.lower(), 'application/octet-stream')
            
            # Retornar archivo
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            response = HttpResponse(file_content, content_type=content_type)
            filename = os.path.basename(file_path)
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
            
        except ReportExecution.DoesNotExist:
            return Response(
                {'error': 'Reporte no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.exception("Error downloading report")
            return Response(
                {'error': f'Error al descargar reporte: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    # ==================== AI Analysis Endpoints ====================
    
    @action(detail=True, methods=['post'])
    def analyze(self, request, pk=None):
        """
        Analizar reporte con IA
        POST /api/reports/executions/{id}/analyze/
        """
        try:
            execution = self.get_object()
            
            # Verificar que el reporte está completado
            if execution.status != 'completed':
                return Response(
                    {'detail': 'El reporte no está completado'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Obtener o crear análisis
            analysis, created = AIAnalysis.objects.get_or_create(
                report_execution=execution
            )
            
            # Si no está analizado, ejecutar análisis
            if created or analysis.status == 'pending':
                service = AIAnalysisService()
                analysis = service.analyze_report(execution, analysis)
            
            serializer = AIAnalysisResultSerializer(
                service._serialize_analysis(analysis)
            )
            return Response(serializer.data)
        
        except ReportExecution.DoesNotExist:
            return Response(
                {'detail': 'Reporte no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.exception("Error analyzing report")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def summarize(self, request, pk=None):
        """
        Generar resumen con IA
        POST /api/reports/executions/{id}/summarize/?max_length=500
        """
        try:
            execution = self.get_object()
            max_length = int(request.query_params.get('max_length', 500))
            
            # Verificar que el reporte está completado
            if execution.status != 'completed':
                return Response(
                    {'detail': 'El reporte no está completado'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            service = AIAnalysisService()
            summary = service.generate_summary(execution, max_length)
            
            serializer = AISummarySerializer(summary)
            return Response(serializer.data)
        
        except ReportExecution.DoesNotExist:
            return Response(
                {'detail': 'Reporte no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.exception("Error generating summary")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def recommendations(self, request, pk=None):
        """
        Obtener recomendaciones con IA
        GET /api/reports/executions/{id}/recommendations/
        """
        try:
            execution = self.get_object()
            
            # Verificar que el reporte está completado
            if execution.status != 'completed':
                return Response(
                    {'detail': 'El reporte no está completado'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            service = AIAnalysisService()
            recommendations = service.get_recommendations(execution)
            
            serializer = AIRecommendationSerializer(
                recommendations, 
                many=True
            )
            return Response(serializer.data)
        
        except ReportExecution.DoesNotExist:
            return Response(
                {'detail': 'Reporte no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.exception("Error getting recommendations")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def ai_insights(self, request, pk=None):
        """
        Obtener insights completos de IA
        GET /api/reports/executions/{id}/ai-insights/
        """
        try:
            execution = self.get_object()
            
            # Verificar que el reporte está completado
            if execution.status != 'completed':
                return Response(
                    {'detail': 'El reporte no está completado'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            service = AIAnalysisService()
            insights = service.get_complete_insights(execution)
            
            serializer = AIInsightsResponseSerializer(insights)
            return Response(serializer.data)
        
        except ReportExecution.DoesNotExist:
            return Response(
                {'detail': 'Reporte no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.exception("Error getting AI insights")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


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
            import os
            from django.conf import settings
            from django.core.files.base import ContentFile
            
            # Obtener datos según tipo de reporte
            if report_type == 'documents':
                data = self._get_documents_data(filters, serializer.validated_data)
            elif report_type == 'patients':
                data = self._get_patients_data(filters)
            elif report_type == 'clinical_records':
                data = self._get_clinical_records_data(filters)
            elif report_type == 'audit':
                data = self._get_audit_data(filters)
            elif report_type == 'users':
                data = self._get_users_data(filters)
            else:  # analytics y otros
                data = self._get_analytics_data(filters)
            
            # Generar reporte según formato
            tenant = get_current_tenant()
            user = request.user
            
            if output_format == 'pdf':
                # Usar generador específico según tipo de reporte
                from .generators.pdf_generator import (
                    generate_documents_report,
                    generate_users_report,
                    generate_patients_report,
                    generate_clinical_records_report,
                    generate_audit_report,
                    generate_analytics_report
                )
                
                if report_type == 'documents':
                    file_content = generate_documents_report(data, tenant.name, user.full_name)
                elif report_type == 'users':
                    file_content = generate_users_report(data, tenant.name, user.full_name)
                elif report_type == 'patients':
                    file_content = generate_patients_report(data, tenant.name, user.full_name)
                elif report_type == 'clinical_records':
                    file_content = generate_clinical_records_report(data, tenant.name, user.full_name)
                elif report_type == 'audit':
                    file_content = generate_audit_report(data, tenant.name, user.full_name)
                else:  # analytics
                    file_content = generate_analytics_report(data, tenant.name, user.full_name)
                
                content_type = 'application/pdf'
                file_ext = 'pdf'
            elif output_format == 'excel':
                file_content = generate_documents_excel(data, tenant.name, user.full_name)
                content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                file_ext = 'xlsx'
            else:  # csv
                file_content = generate_documents_csv(data)
                content_type = 'text/csv'
                file_ext = 'csv'
            
            execution_time = int((time.time() - start_time) * 1000)
            
            # Guardar archivo en el sistema de archivos
            reports_dir = os.path.join(settings.MEDIA_ROOT, 'reports')
            os.makedirs(reports_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f'{report_type}_reporte_{timestamp}.{file_ext}'
            filepath = os.path.join(reports_dir, filename)
            
            with open(filepath, 'wb') as f:
                if isinstance(file_content, bytes):
                    f.write(file_content)
                else:
                    f.write(file_content.getvalue() if hasattr(file_content, 'getvalue') else file_content)
            
            # Guardar ejecución con ruta del archivo
            file_url = f'/media/reports/{filename}'
            execution = ReportExecution.objects.create(
                executed_by=user,
                report_type=report_type,
                parameters_used=serializer.validated_data,
                output_format=output_format,
                execution_time_ms=execution_time,
                rows_returned=data.get('total', 0),
                status='completed',
                file_path=file_url
            )
            
            # Retornar respuesta con información del reporte generado
            return Response({
                'id': str(execution.id),
                'status': 'completed',
                'file_url': file_url,
                'filename': filename
            })
            
        except Exception as e:
            logger.exception("Error generating report")
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
    
    @action(detail=False, methods=['get'])
    def available_types(self, request):
        """
        Obtener tipos de reportes disponibles
        GET /api/reports/generator/available-types/
        """
        from .models import ReportExecution
        
        available_types = [
            {'value': choice[0], 'label': choice[1]}
            for choice in ReportExecution.REPORT_TYPE_CHOICES
        ]
        
        output_formats = ['pdf', 'excel', 'csv']
        
        return Response({
            'report_types': available_types,
            'output_formats': [
                {'value': 'pdf', 'label': 'PDF'},
                {'value': 'excel', 'label': 'Excel (XLSX)'},
                {'value': 'csv', 'label': 'CSV'},
            ],
            'description': 'Tipos de reportes disponibles en el sistema'
        })
    
    @action(detail=False, methods=['post'])
    def generate_dynamic(self, request):
        """
        Generar reporte dinámico con múltiples data sources
        
        POST /api/reports/generate-dynamic/
        
        Body:
        {
            'data_sources': ['documents', 'patients'],
            'columns': {
                'documents': ['specialty', 'document_type', 'created_at'],
                'patients': ['full_name', 'date_of_birth']
            },
            'filters': [
                {'field': 'specialty', 'operator': 'eq', 'value': 'Cardiología'}
            ],
            'group_by': ['specialty'],
            'order_by': ['-created_at'],
            'output_format': 'pdf'
        }
        """
        # Validar entrada
        serializer = DynamicReportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        spec = serializer.validated_data
        output_format = spec['output_format']
        start_time = time.time()
        
        try:
            # Obtener tenant (preferir get_current_tenant, fallback a usuarios)
            try:
                tenant = get_current_tenant()
            except:
                # En caso de test, obtener primer tenant del usuario o global
                from apps.core.models import Tenant
                tenant = Tenant.objects.first()
            
            # Crear generador dinámico
            generator = DynamicReportGenerator(spec)
            
            # Obtener buffer con el reporte
            file_buffer = generator.generate()
            
            # Si es string (CSV), convertir a BytesIO
            if isinstance(file_buffer, str):
                file_buffer = io.BytesIO(file_buffer.encode('utf-8'))
            
            execution_time = int((time.time() - start_time) * 1000)
            
            # Determinar tipo de contenido y extensión
            if output_format == 'pdf':
                content_type = 'application/pdf'
                filename = f'reporte_dinamico_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
            elif output_format == 'excel':
                content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                filename = f'reporte_dinamico_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
            else:  # csv
                content_type = 'text/csv'
                filename = f'reporte_dinamico_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            
            # Guardar ejecución
            try:
                ReportExecution.objects.create(
                    tenant=tenant,
                    executed_by=request.user,
                    parameters_used=spec,
                    output_format=output_format,
                    execution_time_ms=execution_time,
                    rows_returned=len(spec.get('data_sources', [])),
                    status='completed'
                )
            except Exception as exec_err:
                logger.warning(f"Could not save report execution: {exec_err}")
            
            # Retornar archivo
            file_buffer.seek(0)
            response = FileResponse(file_buffer, content_type=content_type)
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            response['Cache-Control'] = 'no-cache'
            
            logger.info(
                f"Dynamic report generated: user={request.user.id}, "
                f"sources={spec['data_sources']}, format={output_format}, "
                f"time={execution_time}ms"
            )
            
            return response
        
        except (DynamicReportError, ValueError) as e:
            # Error de validación en spec
            logger.warning(f"Dynamic report validation error: {str(e)}")
            try:
                tenant = get_current_tenant()
            except:
                from apps.core.models import Tenant
                tenant = Tenant.objects.first()
                
            try:
                ReportExecution.objects.create(
                    tenant=tenant,
                    executed_by=request.user,
                    parameters_used=spec,
                    output_format=output_format,
                    status='failed',
                    error_message=str(e)
                )
            except Exception as exec_err:
                logger.warning(f"Could not save report execution: {exec_err}")
                
            return Response(
                {'error': f'Error en especificación de reporte: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        except Exception as e:
            # Error no esperado
            logger.exception(f"Dynamic report generation error: {str(e)}")
            try:
                tenant = get_current_tenant()
            except:
                from apps.core.models import Tenant
                tenant = Tenant.objects.first()
                
            try:
                ReportExecution.objects.create(
                    tenant=tenant,
                    executed_by=request.user,
                    parameters_used=spec,
                    output_format=output_format,
                    status='failed',
                    error_message=str(e)
                )
            except Exception as exec_err:
                logger.warning(f"Could not save report execution: {exec_err}")
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
        recent_documents_qs = queryset.order_by('-created_at')[:50]
        recent_documents = []
        for doc in recent_documents_qs:
            patient_name = '-'
            if doc.clinical_record and doc.clinical_record.patient:
                patient_name = f"{doc.clinical_record.patient.first_name} {doc.clinical_record.patient.last_name}".strip()
            
            recent_documents.append({
                'document_date': doc.document_date,
                'document_type': doc.document_type,
                'title': doc.title,
                'specialty': doc.specialty,
                'doctor_name': doc.doctor_name,
                'patient_name': patient_name
            })
        
        return {
            'total': queryset.count(),
            'by_type': list(by_type),
            'recent_documents': recent_documents
        }
    
    def _get_patients_data(self, filters):
        """Obtener datos de pacientes"""
        queryset = Patient.objects.all()
        
        # Aplicar filtros básicos si se proporcionan
        if filters.get('gender'):
            queryset = queryset.filter(gender=filters['gender'])
        
        if filters.get('date_of_birth_from'):
            queryset = queryset.filter(date_of_birth__gte=filters['date_of_birth_from'])
        
        if filters.get('date_of_birth_to'):
            queryset = queryset.filter(date_of_birth__lte=filters['date_of_birth_to'])
        
        # Estadísticas por género
        by_gender = queryset.values('gender').annotate(count=Count('id')).order_by('gender')
        gender_labels = {
            'M': 'Masculino',
            'F': 'Femenino',
            'O': 'Otro'
        }
        by_gender_display = [
            {
                'gender': gender_labels.get(item['gender'], item['gender']),
                'count': item['count']
            }
            for item in by_gender
        ]
        
        # Rango de edad (calcular edad a partir de fecha de nacimiento)
        age_ranges = {
            '0-18': 0,
            '19-30': 0,
            '31-50': 0,
            '51-65': 0,
            '65+': 0
        }
        
        today = datetime.now().date()
        for patient in queryset:
            age = (today - patient.date_of_birth).days // 365
            if age <= 18:
                age_ranges['0-18'] += 1
            elif age <= 30:
                age_ranges['19-30'] += 1
            elif age <= 50:
                age_ranges['31-50'] += 1
            elif age <= 65:
                age_ranges['51-65'] += 1
            else:
                age_ranges['65+'] += 1
        
        # Pacientes recientes
        recent_patients_qs = queryset.order_by('-created_at')[:10]
        recent_patients = []
        for patient in recent_patients_qs:
            recent_patients.append({
                'id': patient.id,
                'full_name': f"{patient.first_name} {patient.last_name}".strip(),
                'gender': patient.gender,
                'date_of_birth': patient.date_of_birth,
                'email': patient.email if hasattr(patient, 'email') else '',
                'created_at': patient.created_at
            })
        
        return {
            'total': queryset.count(),
            'by_gender': by_gender_display,
            'age_ranges': age_ranges,
            'recent_patients': recent_patients
        }
    
    def _get_analytics_data(self, filters):
        """Obtener datos analíticos del sistema"""
        analytics = {}
        
        # 1. Documentos por mes (últimos 6 meses)
        today = datetime.now()
        six_months_ago = today - timedelta(days=180)
        
        docs_by_month = {}
        for i in range(6):
            date = today - timedelta(days=30*i)
            month_key = date.strftime('%Y-%m')
            docs_by_month[month_key] = 0
        
        docs_qs = ClinicalDocument.objects.filter(
            created_at__gte=six_months_ago
        ).values_list('created_at', flat=True)
        
        for doc_date in docs_qs:
            month_key = doc_date.strftime('%Y-%m')
            if month_key in docs_by_month:
                docs_by_month[month_key] += 1
        
        analytics['documents_by_month'] = [
            {'month': month, 'count': count}
            for month, count in sorted(docs_by_month.items())
        ]
        
        # 2. Documentos por especialidad
        docs_by_specialty = ClinicalDocument.objects.values(
            'specialty'
        ).annotate(count=Count('id')).order_by('-count')[:10]
        
        analytics['documents_by_specialty'] = list(docs_by_specialty)
        
        # 3. Total de documentos por tipo
        docs_by_type = ClinicalDocument.objects.values(
            'document_type'
        ).annotate(count=Count('id')).order_by('-count')
        
        analytics['documents_by_type'] = list(docs_by_type)
        
        # 4. Historias clínicas por estado
        records_by_status = ClinicalRecord.objects.values(
            'status'
        ).annotate(count=Count('id')).order_by('-count')
        
        analytics['records_by_status'] = list(records_by_status)
        
        # 5. Usuarios activos del sistema
        active_users = User.objects.filter(is_active=True).count()
        inactive_users = User.objects.filter(is_active=False).count()
        
        analytics['users_summary'] = {
            'active': active_users,
            'inactive': inactive_users,
            'total': active_users + inactive_users
        }
        
        # 6. Usuarios por grupo/rol
        users_by_staff = {
            'staff': User.objects.filter(is_staff=True).count(),
            'non_staff': User.objects.filter(is_staff=False).count(),
            'superuser': User.objects.filter(is_superuser=True).count()
        }
        
        analytics['users_by_role'] = users_by_staff
        
        # 7. Actividad reciente (últimas 24h)
        last_24h = today - timedelta(hours=24)
        analytics['activity_24h'] = {
            'new_documents': ClinicalDocument.objects.filter(
                created_at__gte=last_24h
            ).count(),
            'new_records': ClinicalRecord.objects.filter(
                created_at__gte=last_24h
            ).count(),
            'new_users': User.objects.filter(
                created_at__gte=last_24h
            ).count()
        }
        
        # 8. Totales generales
        analytics['totals'] = {
            'documents': ClinicalDocument.objects.count(),
            'records': ClinicalRecord.objects.count(),
            'patients': Patient.objects.count(),
            'users': User.objects.count()
        }
        
        return analytics
    
    def _get_clinical_records_data(self, filters):
        """Obtener datos de historias clínicas"""
        from apps.clinical_records.models import ClinicalRecord
        
        queryset = ClinicalRecord.objects.select_related('patient', 'created_by')
        
        # Aplicar filtros
        if filters.get('status'):
            queryset = queryset.filter(status=filters['status'])
        
        # Estadísticas
        by_status = queryset.values('status').annotate(count=Count('id'))
        
        # Registros recientes
        recent_records_qs = queryset.order_by('-created_at')[:50]
        recent_records = []
        for record in recent_records_qs:
            patient_name = '-'
            if record.patient:
                patient_name = f"{record.patient.first_name} {record.patient.last_name}".strip()
            
            recent_records.append({
                'created_at': record.created_at,
                'status': record.status,
                'notes': record.notes,
                'patient_name': patient_name
            })
        
        return {
            'total': queryset.count(),
            'by_status': list(by_status),
            'recent_records': recent_records
        }
    
    def _get_audit_data(self, filters):
        """Obtener datos de auditoría"""
        from apps.audit.models import AuditLog
        
        queryset = AuditLog.objects.select_related('user')
        
        # Aplicar filtros
        if filters.get('action'):
            queryset = queryset.filter(action=filters['action'])
        if filters.get('resource_type'):
            queryset = queryset.filter(resource_type=filters['resource_type'])
        
        # Estadísticas
        by_action = queryset.values('action').annotate(count=Count('id'))
        by_resource = queryset.values('resource_type').annotate(count=Count('id'))
        
        # Logs recientes
        recent_logs = queryset.order_by('-timestamp')[:50].values(
            'timestamp',
            'action',
            'resource_type',
            'description',
            user_name=Q('user__full_name') if hasattr(queryset.model, 'user') else None
        )
        
        return {
            'total': queryset.count(),
            'by_action': list(by_action),
            'by_resource': list(by_resource),
            'recent_logs': list(recent_logs)
        }
    
    def _get_users_data(self, filters):
        """Obtener datos de usuarios"""
        queryset = User.objects.all()
        
        # Aplicar filtros
        if filters.get('is_active') is not None:
            queryset = queryset.filter(is_active=filters['is_active'])
        if filters.get('is_staff') is not None:
            queryset = queryset.filter(is_staff=filters['is_staff'])
        
        # Estadísticas
        active_users = queryset.filter(is_active=True).count()
        inactive_users = queryset.filter(is_active=False).count()
        staff_users = queryset.filter(is_staff=True).count()
        
        # Usuarios recientes
        recent_users_qs = queryset.order_by('-created_at')[:50]
        recent_users = []
        for user in recent_users_qs:
            recent_users.append({
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'is_active': user.is_active,
                'is_staff': user.is_staff,
                'created_at': user.created_at
            })
        
        return {
            'total': queryset.count(),
            'active': active_users,
            'inactive': inactive_users,
            'staff': staff_users,
            'recent_users': recent_users
        }
    
    @action(detail=False, methods=['post'], url_path='ai_generate')
    def ai_generate(self, request):
        """
        Generar reportes con análisis IA.
        
        POST /api/reports/generator/ai_generate/
        
        Body:
        {
            'report_type': 'analytics',  # analytics, patients, system
            'action': 'analyze',  # analyze, summarize, recommend
            'model': 'openai',  # openai, claude, local (optional)
            'context': 'Análisis de documentos clínicos'  # optional
        }
        """
        try:
            from .llm_adapter import LLMManager, OpenAIAdapter, ClaudeAdapter, LocalLLMAdapter
            from django.conf import settings
            
            report_type = request.data.get('report_type', 'analytics')
            action = request.data.get('action', 'analyze')
            model = request.data.get('model', 'local')
            context = request.data.get('context', '')
            
            # Obtener datos del reporte
            if report_type == 'analytics':
                data = self._get_analytics_data({})
            elif report_type == 'patients':
                data = self._get_patients_data({})
            else:
                return Response({
                    'error': f"Tipo de reporte '{report_type}' no soportado",
                    'supported': ['analytics', 'patients', 'system']
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Configurar adaptador LLM
            adapter = None
            
            if model == 'openai':
                api_key = getattr(settings, 'OPENAI_API_KEY', None)
                if api_key:
                    adapter = OpenAIAdapter(api_key)
                else:
                    return Response({
                        'error': 'OpenAI API key no configurada'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            elif model == 'claude':
                api_key = getattr(settings, 'ANTHROPIC_API_KEY', None)
                if api_key:
                    adapter = ClaudeAdapter(api_key)
                else:
                    return Response({
                        'error': 'Anthropic API key no configurada'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            elif model == 'local':
                base_url = getattr(settings, 'LOCAL_LLM_URL', 'http://localhost:11434')
                model_name = getattr(settings, 'LOCAL_LLM_MODEL', 'mistral')
                adapter = LocalLLMAdapter(model_name=model_name, base_url=base_url)
            
            else:
                return Response({
                    'error': f"Modelo LLM '{model}' no soportado",
                    'supported': ['openai', 'claude', 'local']
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if not adapter:
                return Response({
                    'error': 'No se pudo inicializar adaptador LLM'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Ejecutar acción IA
            result = {}
            start_time = time.time()
            
            if action == 'analyze':
                result['analysis'] = adapter.analyze_data(data, context)
            
            elif action == 'summarize':
                text = str(data)
                result['summary'] = adapter.generate_summary(text, max_length=500)
            
            elif action == 'recommend':
                result['recommendations'] = adapter.generate_recommendations(data)
            
            else:
                return Response({
                    'error': f"Acción '{action}' no soportada",
                    'supported': ['analyze', 'summarize', 'recommend']
                }, status=status.HTTP_400_BAD_REQUEST)
            
            elapsed_time = time.time() - start_time
            
            return Response({
                'success': True,
                'report_type': report_type,
                'action': action,
                'model': model,
                'tokens_used': getattr(adapter, 'tokens_used', 0),
                'generation_time_ms': int(elapsed_time * 1000),
                'result': result
            })
            
        except ImportError as e:
            logger.error(f"Error importando módulos IA: {e}")
            return Response({
                'error': 'Módulos IA no disponibles',
                'details': str(e)
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        except Exception as e:
            logger.error(f"Error generando con IA: {e}")
            return Response({
                'error': 'Error en generación IA',
                'details': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class QBEViewSet(viewsets.ViewSet):
    """
    ViewSet para Query By Example (QBE) - Búsqueda por Ejemplo
    
    Proporciona un endpoint que recibe un ejemplo JSON y retorna
    datos que coincidan, permitiendo una búsqueda flexible sin
    que el usuario sepa exactamente qué filtros usar.
    
    Endpoint: POST /api/reports/qbe/query_by_example/
    """
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def query_by_example(self, request):
        """
        POST /api/reports/qbe/query_by_example/
        
        Query By Example - Busca registros que coincidan con un ejemplo
        
        Body:
        {
            'model': 'documents',
            'example': {
                'specialty': 'Cardiología',
                'document_type': 'Historia Clínica',
                'created_at_from': '2025-10-01',
                'created_at_to': '2025-10-31'
            },
            'limit': 100,
            'offset': 0
        }
        
        Response:
        {
            'count': 45,
            'results': [...],
            'filter_spec': {...},
            'fields_used': ['specialty', 'document_type', 'created_at'],
            'next': None,
            'previous': None
        }
        """
        # Validar entrada
        serializer = QBEExampleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        model_name = serializer.validated_data['model']
        example = serializer.validated_data['example']
        limit = serializer.validated_data.get('limit', 100)
        offset = serializer.validated_data.get('offset', 0)
        
        try:
            # Crear parser QBE
            parser = QBEParser(model_name)
            
            # Parsear el ejemplo a Q object
            q_object = parser.parse_example(example)
            
            # Obtener queryset del modelo
            queryset = self._get_base_queryset(model_name)
            
            # Aplicar filtro
            queryset = queryset.filter(q_object)
            
            # Contar total
            total_count = queryset.count()
            
            # Paginar
            results_qs = queryset[offset:offset + limit]
            
            # Convertir a valores serializables
            results = self._serialize_results(model_name, results_qs)
            
            # Obtener spec de filtros (para reusar)
            filter_spec = parser.get_filter_spec(example)
            
            # Determinar URLs de paginación
            next_url = None
            prev_url = None
            
            if offset + limit < total_count:
                next_url = f"/api/reports/qbe/query_by_example/?model={model_name}&limit={limit}&offset={offset + limit}"
            
            if offset > 0:
                prev_offset = max(0, offset - limit)
                prev_url = f"/api/reports/qbe/query_by_example/?model={model_name}&limit={limit}&offset={prev_offset}"
            
            # Guardar la búsqueda en auditoría (opcional)
            logger.info(
                f"QBE Query: user={request.user.id}, model={model_name}, "
                f"filters={len(filter_spec['filters'])}, results={total_count}"
            )
            
            response_data = {
                'count': total_count,
                'results': results,
                'filter_spec': filter_spec,
                'fields_used': list(example.keys()),
                'next': next_url,
                'previous': prev_url,
                'limit': limit,
                'offset': offset,
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
        
        except QBEParseError as e:
            logger.warning(f"QBE Parse Error: {str(e)}")
            return Response(
                {
                    'error': 'Error en búsqueda por ejemplo',
                    'detail': str(e),
                    'supported_fields': parser.get_supported_fields() if 'parser' in locals() else None,
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        except Exception as e:
            logger.exception(f"QBE Query Error: {str(e)}")
            return Response(
                {
                    'error': 'Error procesando búsqueda',
                    'detail': str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def supported_models(self, request):
        """
        GET /api/reports/qbe/supported_models/
        
        Retorna lista de modelos soportados y sus campos
        """
        from .qbe_parser import QBEParser
        
        supported = {}
        
        for model_name in QBEParser.ALLOWED_MODELS.keys():
            try:
                parser = QBEParser(model_name)
                supported[model_name] = {
                    'fields': parser.get_supported_fields(),
                    'description': f"Búsquedas en {model_name}"
                }
            except Exception as e:
                logger.warning(f"Error loading model {model_name}: {e}")
        
        return Response(supported, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'])
    def validate_example(self, request):
        """
        POST /api/reports/qbe/validate_example/
        
        Valida que un ejemplo sea correcto sin ejecutar la búsqueda
        
        Body:
        {
            'model': 'documents',
            'example': {
                'specialty': 'Cardiología',
                'invalid_field': 'valor'
            }
        }
        
        Response:
        {
            'valid': False,
            'errors': ['Campo invalid_field no permitido'],
            'supported_fields': [...]
        }
        """
        try:
            model = request.data.get('model')
            example = request.data.get('example', {})
            
            if not model:
                return Response(
                    {'error': 'Campo model es requerido'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            parser = QBEParser(model)
            valid, errors = parser.validate_example(example)
            
            response = {
                'valid': valid,
                'errors': errors,
                'supported_fields': parser.get_supported_fields(),
            }
            
            return Response(response, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.exception(f"Validation error: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _get_base_queryset(self, model_name: str):
        """Obtiene el queryset base para un modelo"""
        if model_name == 'documents':
            return ClinicalDocument.objects.select_related(
                'clinical_record__patient',
                'created_by'
            )
        elif model_name == 'patients':
            from apps.patients.models import Patient
            return Patient.objects.all()
        elif model_name == 'clinical_records':
            from apps.clinical_records.models import ClinicalRecord
            return ClinicalRecord.objects.select_related('patient')
        elif model_name == 'users':
            from apps.accounts.models import User
            return User.objects.all()
        elif model_name == 'audit_logs':
            from apps.audit.models import AuditLog
            return AuditLog.objects.select_related('user')
        else:
            raise ValueError(f"Modelo {model_name} no soportado")
    
    def _serialize_results(self, model_name: str, queryset):
        """Serializa los resultados según el modelo"""
        results = []
        
        for obj in queryset:
            if model_name == 'documents':
                results.append({
                    'id': obj.id,
                    'title': obj.title,
                    'document_type': obj.document_type,
                    'specialty': obj.specialty,
                    'doctor_name': obj.doctor_name,
                    'created_at': obj.created_at.isoformat() if obj.created_at else None,
                    'document_date': obj.document_date.isoformat() if obj.document_date else None,
                    'status': obj.status if hasattr(obj, 'status') else None,
                })
            elif model_name == 'patients':
                results.append({
                    'id': obj.id,
                    'full_name': f"{obj.first_name} {obj.last_name}",
                    'identity_document': obj.identity_document,
                    'date_of_birth': obj.date_of_birth.isoformat() if obj.date_of_birth else None,
                    'gender': obj.gender,
                    'created_at': obj.created_at.isoformat() if obj.created_at else None,
                })
            elif model_name == 'clinical_records':
                results.append({
                    'id': obj.id,
                    'record_number': obj.record_number,
                    'patient_name': obj.patient.full_name if obj.patient else None,
                    'status': obj.status,
                    'created_at': obj.created_at.isoformat() if obj.created_at else None,
                    'chief_complaint': obj.chief_complaint if hasattr(obj, 'chief_complaint') else None,
                })
            elif model_name == 'users':
                results.append({
                    'id': obj.id,
                    'full_name': obj.full_name,
                    'email': obj.email,
                    'is_active': obj.is_active,
                    'created_at': obj.created_at.isoformat() if obj.created_at else None,
                })
            elif model_name == 'audit_logs':
                results.append({
                    'id': obj.id,
                    'action': obj.action,
                    'model_name': obj.model_name,
                    'user_name': obj.user.full_name if obj.user else None,
                    'created_at': obj.created_at.isoformat() if obj.created_at else None,
                    'ip_address': obj.ip_address if hasattr(obj, 'ip_address') else None,
                })
        
        return results


@extend_schema(tags=['Reports - Dynamic'])
class DynamicReportsViewSet(viewsets.ViewSet):
    """
    ViewSet para reportes dinámicos con Query Builder
    Permite generar reportes personalizados con filtros seguros
    """
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'], url_path='generate')
    def generate_dynamic_report(self, request):
        """
        Generar reporte dinámico con filtros personalizados

        POST /api/reports/dynamic/generate/

        Body:
        {
            "model": "patient",
            "filters": [
                {"field": "age", "operator": "gt", "value": 18},
                {"field": "city", "operator": "equals", "value": "La Paz"}
            ],
            "fields": ["first_name", "last_name", "email", "birth_date"],
            "order_by": "-created_at",
            "limit": 100,
            "export_format": "json"  // "json", "pdf", "excel", "csv"
        }
        """
        from .dynamic_reports_service import DynamicReportBuilder

        try:
            tenant = get_current_tenant()
            if not tenant:
                return Response(
                    {'error': 'Tenant no encontrado'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Obtener parámetros
            model_name = request.data.get('model')
            filters = request.data.get('filters', [])
            fields = request.data.get('fields')
            order_by = request.data.get('order_by')
            limit = request.data.get('limit', 1000)
            export_format = request.data.get('export_format', 'json')

            # Validar parámetros requeridos
            if not model_name:
                return Response(
                    {'error': 'El campo "model" es requerido'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Crear builder
            builder = DynamicReportBuilder(tenant)

            # Generar reporte
            report_data = builder.build_query(
                model_name=model_name,
                filters=filters,
                fields=fields,
                order_by=order_by,
                limit=limit
            )

            # Exportar según formato
            if export_format == 'json':
                return Response(report_data)

            elif export_format in ['pdf', 'excel', 'csv']:
                # Metadatos
                metadata = {
                    'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M'),
                    'user_name': request.user.get_full_name(),
                    'tenant_name': tenant.name if tenant else 'Sistema de Historias Clínicas',
                    'filters_applied': len(filters),
                }

                # Título
                title = f"Reporte de {model_name.replace('_', ' ').title()}"

                # Exportar
                file_content = builder.export_report(
                    report_data=report_data,
                    format_type=export_format,
                    title=title,
                    metadata=metadata
                )

                # Respuesta
                content_types = {
                    'pdf': 'application/pdf',
                    'excel': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    'csv': 'text/csv'
                }

                filenames = {
                    'pdf': f'reporte_{model_name}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf',
                    'excel': f'reporte_{model_name}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx',
                    'csv': f'reporte_{model_name}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
                }

                response = HttpResponse(file_content, content_type=content_types[export_format])
                response['Content-Disposition'] = f'attachment; filename="{filenames[export_format]}"'
                return response

            else:
                return Response(
                    {'error': f'Formato no soportado: {export_format}'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.exception("Error generating dynamic report")
            return Response(
                {'error': f'Error al generar reporte: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'], url_path='aggregate')
    def generate_aggregation_report(self, request):
        """
        Generar reporte con agregaciones (COUNT, SUM, AVG, etc.)

        POST /api/reports/dynamic/aggregate/

        Body:
        {
            "model": "patient",
            "group_by": "gender",
            "aggregations": [
                {"field": "id", "function": "count"}
            ],
            "filters": []
        }
        """
        from .dynamic_reports_service import DynamicReportBuilder

        try:
            tenant = get_current_tenant()
            if not tenant:
                return Response(
                    {'error': 'Tenant no encontrado'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            model_name = request.data.get('model')
            group_by = request.data.get('group_by')
            aggregations = request.data.get('aggregations', [])
            filters = request.data.get('filters', [])

            if not model_name or not group_by:
                return Response(
                    {'error': 'Los campos "model" y "group_by" son requeridos'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            builder = DynamicReportBuilder(tenant)

            report_data = builder.generate_aggregation_report(
                model_name=model_name,
                group_by=group_by,
                aggregations=aggregations,
                filters=filters
            )

            return Response(report_data)

        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.exception("Error generating aggregation report")
            return Response(
                {'error': f'Error al generar reporte: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'], url_path='predefined')
    def get_predefined_reports(self, request):
        """
        Obtener lista de reportes predefinidos

        GET /api/reports/dynamic/predefined/
        """
        from .dynamic_reports_service import DynamicReportBuilder

        try:
            tenant = get_current_tenant()
            builder = DynamicReportBuilder(tenant)
            reports = builder.get_predefined_reports()

            return Response({
                'total': len(reports),
                'reports': reports
            })

        except Exception as e:
            logger.exception("Error getting predefined reports")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )