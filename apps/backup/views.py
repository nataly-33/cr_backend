from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import BackupJob
from .serializers import BackupJobSerializer
from .services import BackupService


class BackupViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para gestión de backups"""
    queryset = BackupJob.objects.all()
    serializer_class = BackupJobSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Solo admin o superusuario puede ver backups del sistema
        if not (self.request.user.is_staff or self.request.user.is_superuser):
            queryset = queryset.filter(tenant=self.request.user.tenant)
        
        return queryset.order_by('-created_at')
    
    @action(detail=False, methods=['post'])
    def create_backup(self, request):
        """Crear nuevo backup"""
        service = BackupService()
        
        try:
            tenant = request.user.tenant if not (request.user.is_staff or request.user.is_superuser) else None
            job = service.create_backup(tenant=tenant)
            
            serializer = self.get_serializer(job)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        """Restaurar backup"""
        if not (request.user.is_staff or request.user.is_superuser):
            return Response(
                {'error': 'Solo administradores pueden restaurar backups'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        service = BackupService()
        
        try:
            service.restore_backup(pk)
            return Response({'message': 'Backup restaurado exitosamente'})
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )