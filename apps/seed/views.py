from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from apps.backup.seeder_service import SeederService
import logging
from django.conf import settings
from pathlib import Path

logger = logging.getLogger(__name__)


@api_view(['POST', 'GET'])
@permission_classes([AllowAny])
def generate_seed(request):
    """
    Ejecutar el seeder de datos
    
    Métodos: GET, POST
    URL: /api/seed/generate/
    
    Query params:
        - script: Nombre del script seeder (default: seed_data.py)
        - output: Tipo de output (full, summary) (default: summary)
    
    Ejemplos:
        GET /api/seed/generate/
        POST /api/seed/generate/
        POST /api/seed/generate/?script=seed_clinical_records.py
        POST /api/seed/generate/?output=full
    
    Nota: En desarrollo (DEBUG=True), está permitido para todos.
    En producción (DEBUG=False), requiere ser administrador.
    """
    
    # En producción, verificar que sea admin
    if not settings.DEBUG:
        if not (request.user and request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser)):
            return Response(
                {
                    'status': 'error',
                    'message': 'Solo administradores pueden ejecutar seeders',
                    'detail': 'Requiere permisos de administrador en producción'
                },
                status=status.HTTP_403_FORBIDDEN
            )
    
    try:
        # Obtener parámetros
        script_name = request.query_params.get('script', 'seed_data.py')
        output_type = request.query_params.get('output', 'summary').lower()
        
        logger.info(f"Iniciando seeder: {script_name}")
        
        # Ejecutar seeder
        result = SeederService.run_seeder(script_name=script_name)
        
        # Procesar resultado
        if result['success']:
            # Preparar output según lo solicitado
            if output_type == 'full':
                response_data = {
                    'status': 'success',
                    'message': result['message'],
                    'script': script_name,
                    'output': result['stdout'],
                    'error': result['stderr'],
                    'return_code': result['return_code']
                }
            else:  # summary
                # Resumir output (primeras y últimas 10 líneas)
                output_lines = result['stdout'].split('\n')
                if len(output_lines) > 20:
                    output = '\n'.join(output_lines[:10]) + '\n...\n' + '\n'.join(output_lines[-10:])
                else:
                    output = result['stdout']
                
                response_data = {
                    'status': 'success',
                    'message': result['message'],
                    'script': script_name,
                    'output': output,
                    'total_lines': len(output_lines)
                }
            
            logger.info(f"Seeder completado exitosamente: {script_name}")
            
            return Response(response_data, status=status.HTTP_200_OK)
        
        else:
            logger.error(f"Error en seeder {script_name}: {result['stderr']}")
            
            response_data = {
                'status': 'error',
                'message': result['message'],
                'script': script_name,
                'error': result['stderr'],
                'return_code': result['return_code']
            }
            
            return Response(response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    except Exception as e:
        logger.error(f"Error inesperado en seeder: {str(e)}")
        
        return Response(
            {
                'status': 'error',
                'message': f'Error inesperado: {str(e)}',
                'error': str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def list_seeders(request):
    """
    Listar scripts seeders disponibles
    
    URL: /api/seed/list/
    
    Nota: En desarrollo (DEBUG=True), está permitido para todos.
    En producción (DEBUG=False), requiere ser administrador.
    """
    
    # En producción, verificar que sea admin
    if not settings.DEBUG:
        if not (request.user and request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser)):
            return Response(
                {
                    'status': 'error',
                    'message': 'Solo administradores pueden listar seeders',
                    'detail': 'Requiere permisos de administrador en producción'
                },
                status=status.HTTP_403_FORBIDDEN
            )
    
    try:
        base_dir = Path(settings.BASE_DIR)
        scripts_dir = base_dir / 'scripts'
        
        # Encontrar todos los scripts seed_*.py
        if scripts_dir.exists():
            seeders = [
                f.name
                for f in scripts_dir.glob('seed_*.py')
                if f.is_file()
            ]
            seeders.sort()
        else:
            seeders = []
        
        return Response(
            {
                'status': 'success',
                'count': len(seeders),
                'seeders': seeders,
                'scripts_path': str(scripts_dir),
                'debug_mode': settings.DEBUG
            },
            status=status.HTTP_200_OK
        )
    
    except Exception as e:
        return Response(
            {
                'status': 'error',
                'message': f'Error listando seeders: {str(e)}',
                'error': str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
