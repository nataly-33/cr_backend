from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from apps.core.models import Tenant
from .serializers import TenantSerializer
from drf_spectacular.utils import extend_schema


@extend_schema(tags=['Tenants'])
class TenantViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para consultar información del tenant actual (solo lectura)"""
    queryset = Tenant.objects.all()
    serializer_class = TenantSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Solo el tenant actual"""
        if self.request.user.is_superuser:
            return Tenant.objects.all()
        return Tenant.objects.filter(id=self.request.tenant.id)

    @action(detail=False, methods=['get'])
    def current(self, request):
        """Retorna información del tenant actual"""
        if not request.tenant:
            return Response(
                {'error': 'No tenant found in request'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(request.tenant)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Estadísticas del tenant actual"""
        tenant = request.tenant
        
        stats = {
            'users_count': tenant.users.filter(is_active=True).count(),
            'patients_count': tenant.patient_set.filter(deleted_at__isnull=True).count(),
            'storage_used_gb': round(tenant.current_storage_bytes / (1024**3), 2),
            'storage_limit_gb': tenant.max_storage_gb,
            'users_limit': tenant.max_users,
            'can_add_users': tenant.can_add_user(),
            'subscription_status': tenant.subscription_status,
            'subscription_plan': tenant.subscription_plan,
        }
        
        return Response(stats)