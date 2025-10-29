from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Q
from datetime import timedelta
from django.utils import timezone
from drf_spectacular.utils import extend_schema

from .models import AuditLog
from .serializers import AuditLogSerializer, AuditLogListSerializer


@extend_schema(tags=['Audit'])
class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para consultar logs de auditoría (solo lectura)
    Solo admins pueden ver logs
    """
    queryset = AuditLog.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['user_email', 'user_name', 'resource_name', 'ip_address']
    filterset_fields = ['action_type', 'resource_type', 'user', 'response_status']
    ordering = ['-timestamp']

    def get_serializer_class(self):
        if self.action == 'list':
            return AuditLogListSerializer
        return AuditLogSerializer

    def get_queryset(self):
        """
        Solo admins y staff pueden ver logs de auditoría
        Filtrar por tenant actual
        """
        user = self.request.user

        # Solo admins pueden ver logs
        if not user.is_staff and not (user.role and user.role.has_permission('audit.read')):
            return AuditLog.objects.none()

        # Filtrar por tenant
        queryset = AuditLog.objects.filter(tenant=self.request.tenant)

        # Filtrar por rango de fechas si se proporciona
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')

        if date_from:
            queryset = queryset.filter(timestamp__gte=date_from)
        if date_to:
            queryset = queryset.filter(timestamp__lte=date_to)

        return queryset

    @action(detail=True, methods=['get'])
    def verify_integrity(self, request, pk=None):
        """
        Verifica la integridad de un log específico
        """
        log = self.get_object()
        is_valid = log.verify_integrity()

        return Response({
            'log_id': str(log.id),
            'is_valid': is_valid,
            'current_hash': log.log_hash,
            'message': 'Log íntegro' if is_valid else 'ADVERTENCIA: Log ha sido manipulado'
        })

    @action(detail=False, methods=['post'])
    def verify_all(self, request):
        """
        Verifica la integridad de todos los logs del tenant
        """
        logs = self.get_queryset()[:100]  # Limitar a 100 logs por performance

        results = {
            'total_checked': 0,
            'valid': 0,
            'invalid': 0,
            'invalid_logs': []
        }

        for log in logs:
            results['total_checked'] += 1
            if log.verify_integrity():
                results['valid'] += 1
            else:
                results['invalid'] += 1
                results['invalid_logs'].append({
                    'id': str(log.id),
                    'timestamp': log.timestamp,
                    'action': log.action_type,
                    'resource': log.resource_type
                })

        return Response(results)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Estadísticas de auditoría
        """
        queryset = self.get_queryset()

        # Estadísticas por acción
        actions_stats = queryset.values('action_type').annotate(
            count=Count('id')
        ).order_by('-count')

        # Estadísticas por recurso
        resources_stats = queryset.values('resource_type').annotate(
            count=Count('id')
        ).order_by('-count')

        # Actividad por día (últimos 7 días)
        seven_days_ago = timezone.now() - timedelta(days=7)
        daily_activity = queryset.filter(
            timestamp__gte=seven_days_ago
        ).extra(
            select={'day': 'DATE(timestamp)'}
        ).values('day').annotate(
            count=Count('id')
        ).order_by('day')

        # Usuarios más activos
        top_users = queryset.values('user_email', 'user_name').annotate(
            count=Count('id')
        ).order_by('-count')[:10]

        # IPs más frecuentes
        top_ips = queryset.values('ip_address').annotate(
            count=Count('id')
        ).order_by('-count')[:10]

        return Response({
            'total_logs': queryset.count(),
            'actions': list(actions_stats),
            'resources': list(resources_stats),
            'daily_activity': list(daily_activity),
            'top_users': list(top_users),
            'top_ips': list(top_ips),
        })

    @action(detail=False, methods=['get'])
    def recent_suspicious(self, request):
        """
        Actividad sospechosa reciente
        """
        queryset = self.get_queryset()

        # Failed logins
        failed_logins = queryset.filter(
            action_type='LOGIN',
            response_status__gte=400
        ).order_by('-timestamp')[:10]

        # Multiple access from different IPs
        users_multiple_ips = queryset.values('user_email').annotate(
            ip_count=Count('ip_address', distinct=True),
            access_count=Count('id')
        ).filter(ip_count__gt=3).order_by('-access_count')[:10]

        # After-hours activity (example: 10PM - 6AM)
        after_hours = queryset.filter(
            Q(timestamp__hour__gte=22) | Q(timestamp__hour__lt=6)
        ).order_by('-timestamp')[:10]

        return Response({
            'failed_logins': AuditLogListSerializer(failed_logins, many=True).data,
            'users_multiple_ips': list(users_multiple_ips),
            'after_hours_activity': AuditLogListSerializer(after_hours, many=True).data,
        })