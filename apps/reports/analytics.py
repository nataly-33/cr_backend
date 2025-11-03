from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
from calendar import monthrange
import logging

from apps.patients.models import Patient
from apps.clinical_records.models import ClinicalRecord
from apps.documents.models import ClinicalDocument
from apps.audit.models import AuditLog

logger = logging.getLogger(__name__)


class AnalyticsViewSet(viewsets.ViewSet):
    """ViewSet para analytics y reportes analíticos"""
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def overview(self, request):
        """
        Obtener resumen analítico completo con:
        - Pacientes por mes (últimos 12 meses)
        - Documentos por tipo (últimas 4 semanas)
        - Actividad por día (últimos 30 días)
        - Top especialidades
        - Top doctores más activos
        
        Query params:
        - months: número de meses a mostrar (default: 12)
        - days: número de días para actividad (default: 30)
        """
        
        try:
            months = int(request.query_params.get('months', 12))
            days = int(request.query_params.get('days', 30))
        except (ValueError, TypeError) as e:
            logger.error(f"Error parsing parameters: {e}")
            return Response(
                {'error': 'Invalid parameters. months and days must be integers'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            data = {
                'patients_by_month': self._get_patients_by_month(months),
                'documents_by_type': self._get_documents_by_type(),
                'activity_by_day': self._get_activity_by_day(days),
                'top_specialties': self._get_top_specialties(),
                'top_doctors': self._get_top_doctors(),
                'summary': self._get_summary(),
            }
            
            return Response(data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error in analytics overview: {str(e)}", exc_info=True)
            return Response(
                {'error': f'Error al obtener analytics: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _get_patients_by_month(self, months=12):
        """Obtener cantidad de pacientes creados por mes"""
        today = timezone.now()
        data = []
        
        for i in range(months - 1, -1, -1):
            # Calcular el mes
            month_date = today - timedelta(days=30*i)
            month_start = month_date.replace(day=1)
            _, last_day = monthrange(month_date.year, month_date.month)
            month_end = month_date.replace(day=last_day)
            
            count = Patient.objects.filter(
                tenant=self.request.tenant,
                created_at__date__gte=month_start.date(),
                created_at__date__lte=month_end.date()
            ).count()
            
            data.append({
                'month': month_date.strftime('%b %Y'),
                'value': count,
                'date': month_date.isoformat()
            })
        
        return data
    
    def _get_documents_by_type(self):
        """Obtener cantidad de documentos por tipo (últimas 4 semanas)"""
        four_weeks_ago = timezone.now() - timedelta(weeks=4)
        
        documents = ClinicalDocument.objects.filter(
            tenant=self.request.tenant,
            created_at__gte=four_weeks_ago
        ).values('document_type').annotate(count=Count('id')).order_by('-count')
        
        # Mapear tipos de documentos a labels
        type_labels = {
            'consultation': 'Consulta',
            'lab_result': 'Resultado de Laboratorio',
            'imaging': 'Imágenes Médicas',
            'prescription': 'Prescripción',
            'surgery': 'Cirugía',
            'discharge': 'Alta Médica',
            'consent': 'Consentimiento',
            'referral': 'Referencia',
            'other': 'Otros'
        }
        
        return [
            {
                'type': doc['document_type'],
                'label': type_labels.get(doc['document_type'], doc['document_type']),
                'count': doc['count']
            }
            for doc in documents
        ]
    
    def _get_activity_by_day(self, days=30):
        """Obtener actividad (auditoría) por día (últimos N días)"""
        days_ago = timezone.now() - timedelta(days=days)
        today = timezone.now()
        
        data = []
        
        for i in range(days - 1, -1, -1):
            day = today - timedelta(days=i)
            day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            # Contar acciones en ese día (AuditLog usa 'timestamp' no 'created_at')
            count = AuditLog.objects.filter(
                tenant=self.request.tenant,
                timestamp__gte=day_start,
                timestamp__lte=day_end
            ).count()
            
            data.append({
                'day': day.strftime('%a %d'),
                'value': count,
                'date': day.isoformat()
            })
        
        return data
    
    def _get_top_specialties(self, limit=5):
        """Obtener especialidades más usadas"""
        specialties = ClinicalDocument.objects.filter(
            tenant=self.request.tenant,
            specialty__isnull=False
        ).exclude(
            specialty=''
        ).values('specialty').annotate(count=Count('id')).order_by('-count')[:limit]
        
        return [
            {
                'specialty': spec['specialty'],
                'count': spec['count']
            }
            for spec in specialties
        ]
    
    def _get_top_doctors(self, limit=5):
        """Obtener doctores más activos"""
        doctors = ClinicalDocument.objects.filter(
            tenant=self.request.tenant,
            doctor_name__isnull=False
        ).exclude(
            doctor_name=''
        ).values('doctor_name').annotate(count=Count('id')).order_by('-count')[:limit]
        
        return [
            {
                'doctor': doc['doctor_name'],
                'documents': doc['count']
            }
            for doc in doctors
        ]
    
    def _get_summary(self):
        """Obtener resumen general"""
        today = timezone.now()
        month_ago = today - timedelta(days=30)
        week_ago = today - timedelta(days=7)
        
        total_patients = Patient.objects.filter(tenant=self.request.tenant).count()
        patients_this_month = Patient.objects.filter(
            tenant=self.request.tenant,
            created_at__gte=month_ago
        ).count()
        
        total_documents = ClinicalDocument.objects.filter(tenant=self.request.tenant).count()
        documents_this_month = ClinicalDocument.objects.filter(
            tenant=self.request.tenant,
            created_at__gte=month_ago
        ).count()
        
        total_records = ClinicalRecord.objects.filter(tenant=self.request.tenant).count()
        records_this_month = ClinicalRecord.objects.filter(
            tenant=self.request.tenant,
            created_at__gte=month_ago
        ).count()
        
        # Actividad hoy (AuditLog usa 'timestamp' no 'created_at')
        today_start = today.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today.replace(hour=23, minute=59, second=59, microsecond=999999)
        activity_today = AuditLog.objects.filter(
            tenant=self.request.tenant,
            timestamp__gte=today_start,
            timestamp__lte=today_end
        ).count()
        
        return {
            'total_patients': total_patients,
            'patients_this_month': patients_this_month,
            'total_documents': total_documents,
            'documents_this_month': documents_this_month,
            'total_records': total_records,
            'records_this_month': records_this_month,
            'activity_today': activity_today,
        }
