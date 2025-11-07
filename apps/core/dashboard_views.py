"""
Dashboard endpoints para estadísticas globales del sistema.
"""

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
import logging

from apps.patients.models import Patient
from apps.documents.models import ClinicalDocument
from apps.clinical_records.models import ClinicalRecord, ClinicalForm
from apps.accounts.models import User
from apps.audit.models import AuditLog
from apps.core.models import get_current_tenant

logger = logging.getLogger(__name__)


class DashboardViewSet(viewsets.ViewSet):
    """
    ViewSet para estadísticas y datos del dashboard.
    
    Endpoints:
    - GET /api/dashboard/overview/ - Estadísticas generales
    - GET /api/dashboard/activity/ - Actividad reciente
    - GET /api/dashboard/documents-stats/ - Estadísticas de documentos
    - GET /api/dashboard/forms-stats/ - Estadísticas de formularios
    - GET /api/dashboard/users-activity/ - Actividad de usuarios
    """
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def overview(self, request):
        """
        Estadísticas generales del dashboard.
        Retorna: Pacientes, Documentos, Historias, Usuarios, Formularios
        """
        tenant = get_current_tenant()
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)

        # Pacientes
        total_patients = Patient.objects.filter(
            tenant=tenant,
            deleted_at__isnull=True
        ).count()

        patients_this_month = Patient.objects.filter(
            tenant=tenant,
            deleted_at__isnull=True,
            created_at__date__gte=month_ago
        ).count()

        # Documentos
        total_documents = ClinicalDocument.objects.filter(
            tenant=tenant,
            deleted_at__isnull=True
        ).count()

        documents_today = ClinicalDocument.objects.filter(
            tenant=tenant,
            deleted_at__isnull=True,
            created_at__date=today
        ).count()

        documents_this_week = ClinicalDocument.objects.filter(
            tenant=tenant,
            deleted_at__isnull=True,
            created_at__date__gte=week_ago
        ).count()

        # Historias Clínicas
        total_records = ClinicalRecord.objects.filter(
            tenant=tenant
        ).count()

        records_active = ClinicalRecord.objects.filter(
            tenant=tenant,
            status='active'
        ).count()

        # Usuarios
        total_users = User.objects.filter(
            tenant=tenant
        ).count()

        active_users = User.objects.filter(
            tenant=tenant,
            is_active=True
        ).count()

        # Formularios
        total_forms = ClinicalForm.objects.filter(
            tenant=tenant
        ).count()

        forms_today = ClinicalForm.objects.filter(
            tenant=tenant,
            form_date__date=today
        ).count()

        return Response({
            'patients': {
                'total': total_patients,
                'new_this_month': patients_this_month,
            },
            'documents': {
                'total': total_documents,
                'today': documents_today,
                'this_week': documents_this_week,
            },
            'clinical_records': {
                'total': total_records,
                'active': records_active,
            },
            'users': {
                'total': total_users,
                'active': active_users,
            },
            'forms': {
                'total': total_forms,
                'today': forms_today,
            },
            'timestamp': timezone.now().isoformat(),
        })

    @action(detail=False, methods=['get'])
    def activity(self, request):
        """
        Actividad reciente del sistema.
        Retorna: Últimas acciones, cambios, creaciones
        """
        tenant = get_current_tenant()
        limit = int(request.query_params.get('limit', 20))
        days = int(request.query_params.get('days', 7))

        cutoff_date = timezone.now() - timedelta(days=days)

        # Obtener logs de auditoría recientes
        recent_logs = AuditLog.objects.filter(
            tenant=tenant,
            timestamp__gte=cutoff_date
        ).order_by('-timestamp')[:limit]

        activity = []
        for log in recent_logs:
            activity.append({
                'id': str(log.id),
                'action': log.action_type,
                'resource_type': log.resource_type,
                'resource_name': log.resource_name,
                'user': {
                    'id': str(log.user.id) if log.user else None,
                    'name': log.user_name or 'Sistema',
                    'email': log.user_email,
                },
                'timestamp': log.timestamp.isoformat(),
                'details': {
                    'before': log.changes.get('before', {}),
                    'after': log.changes.get('after', {}),
                    'ip_address': log.ip_address,
                    'status_code': log.response_status,
                }
            })

        return Response({
            'activity': activity,
            'total': len(activity),
            'timestamp': timezone.now().isoformat(),
        })

    @action(detail=False, methods=['get'])
    def documents_stats(self, request):
        """
        Estadísticas detalladas de documentos.
        Retorna: Por tipo, especialidad, firma, etc.
        """
        tenant = get_current_tenant()
        today = timezone.now().date()

        # Por tipo
        by_type = ClinicalDocument.objects.filter(
            tenant=tenant,
            deleted_at__isnull=True
        ).values('document_type').annotate(count=Count('id')).order_by('-count')

        # Por especialidad
        by_specialty = ClinicalDocument.objects.filter(
            tenant=tenant,
            deleted_at__isnull=True
        ).values('specialty').annotate(count=Count('id')).order_by('-count')

        # Firmados vs No firmados
        signed_count = ClinicalDocument.objects.filter(
            tenant=tenant,
            deleted_at__isnull=True,
            is_signed=True
        ).count()

        unsigned_count = ClinicalDocument.objects.filter(
            tenant=tenant,
            deleted_at__isnull=True,
            is_signed=False
        ).count()

        # Últimos 7 días
        week_ago = today - timedelta(days=7)
        documents_per_day = []

        for i in range(7):
            day = week_ago + timedelta(days=i)
            count = ClinicalDocument.objects.filter(
                tenant=tenant,
                deleted_at__isnull=True,
                created_at__date=day
            ).count()
            documents_per_day.append({
                'date': day.isoformat(),
                'count': count,
            })

        return Response({
            'by_type': [
                {'type': item['document_type'], 'count': item['count']}
                for item in by_type
            ],
            'by_specialty': [
                {'specialty': item['specialty'] or 'General', 'count': item['count']}
                for item in by_specialty
            ],
            'signatures': {
                'signed': signed_count,
                'unsigned': unsigned_count,
            },
            'per_day': documents_per_day,
            'timestamp': timezone.now().isoformat(),
        })

    @action(detail=False, methods=['get'])
    def forms_stats(self, request):
        """
        Estadísticas de formularios clínicos.
        Retorna: Por tipo, últimos 7 días, tendencia
        """
        tenant = get_current_tenant()
        today = timezone.now().date()

        # Por tipo
        by_type = ClinicalForm.objects.filter(
            tenant=tenant
        ).values('form_type').annotate(count=Count('id')).order_by('-count')

        # Últimos 7 días
        week_ago = today - timedelta(days=7)
        forms_per_day = []

        for i in range(7):
            day = week_ago + timedelta(days=i)
            count = ClinicalForm.objects.filter(
                tenant=tenant,
                form_date__date=day
            ).count()
            forms_per_day.append({
                'date': day.isoformat(),
                'count': count,
            })

        # Top usuarios que crean formularios
        top_users = ClinicalForm.objects.filter(
            tenant=tenant,
            form_date__date__gte=week_ago
        ).values('filled_by__first_name', 'filled_by__last_name').annotate(
            count=Count('id')
        ).order_by('-count')[:5]

        return Response({
            'by_type': [
                {'type': item['form_type'], 'count': item['count']}
                for item in by_type
            ],
            'per_day': forms_per_day,
            'top_users': [
                {
                    'name': f"{item['filled_by__first_name']} {item['filled_by__last_name']}",
                    'forms': item['count']
                }
                for item in top_users
            ],
            'timestamp': timezone.now().isoformat(),
        })

    @action(detail=False, methods=['get'])
    def users_activity(self, request):
        """
        Actividad de usuarios en los últimos 7 días.
        Retorna: Usuarios activos, acciones por usuario, etc.
        """
        tenant = get_current_tenant()
        days = int(request.query_params.get('days', 7))
        cutoff_date = timezone.now() - timedelta(days=days)

        # Usuarios activos
        active_users = set()
        user_actions = {}

        logs = AuditLog.objects.filter(
            tenant=tenant,
            timestamp__gte=cutoff_date
        )

        for log in logs:
            if log.user:
                active_users.add(log.user.id)
                user_key = f"{log.user.first_name} {log.user.last_name}"

                if user_key not in user_actions:
                    user_actions[user_key] = {
                        'user_id': str(log.user.id),
                        'total_actions': 0,
                        'by_action': {}
                    }

                user_actions[user_key]['total_actions'] += 1

                action = log.action
                if action not in user_actions[user_key]['by_action']:
                    user_actions[user_key]['by_action'][action] = 0
                user_actions[user_key]['by_action'][action] += 1

        return Response({
            'active_users': len(active_users),
            'users_activity': list(user_actions.values()),
            'timestamp': timezone.now().isoformat(),
        })
