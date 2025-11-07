from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from drf_spectacular.utils import extend_schema
from .models import BackupJob
from .serializers import BackupJobSerializer
from .services import BackupService
from .seeder_service import SeederService


@extend_schema(tags=['Backups'])
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
    
    @action(detail=False, methods=['post'], permission_classes=[IsAdminUser])
    def run_seeder(self, request):
        """
        Ejecutar el seeder de datos
        
        Query params:
            - script: Nombre del script seeder (default: seed_data.py)
            
        Ejemplo:
            POST /api/backup/backup-jobs/run_seeder/
            POST /api/backup/backup-jobs/run_seeder/?script=seed_clinical_records.py
        """
        # Verificar que solo admin puede ejecutar
        if not (request.user.is_staff or request.user.is_superuser):
            return Response(
                {'error': 'Solo administradores pueden ejecutar seeders'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            # Obtener nombre del script del query param
            script_name = request.query_params.get('script', 'seed_data.py')
            
            # Ejecutar seeder
            result = SeederService.run_seeder(script_name=script_name)
            
            # Retornar resultado
            if result['success']:
                return Response(
                    {
                        'status': 'success',
                        'message': result['message'],
                        'output': result['stdout'],
                        'script': script_name
                    },
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {
                        'status': 'error',
                        'message': result['message'],
                        'error': result['stderr'],
                        'script': script_name
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
        except Exception as e:
            return Response(
                {
                    'status': 'error',
                    'message': f'Error inesperado: {str(e)}',
                    'error': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )