"""
Endpoint para generar seeders (datos de prueba) mediante API

Permite poblar la base de datos con datos de ejemplo mediante llamadas HTTP
para desarrollo, testing y demostraciones.
"""

import logging
from typing import Dict, Any, List
from django.utils.translation import gettext_lazy as _
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated

logger = logging.getLogger(__name__)


class SeederViewSet(viewsets.ViewSet):
    """
    ViewSet para generar seeders y datos de prueba.
    
    Endpoints:
    - POST /api/seeders/run/ - Ejecutar seeder específico
    - GET /api/seeders/available/ - Listar seeders disponibles
    - POST /api/seeders/reset/ - Limpiar datos
    """
    
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def _get_available_seeders(self) -> Dict[str, Dict[str, Any]]:
        """
        Obtener lista de seeders disponibles.
        
        Returns:
            dict: Seeders disponibles con descripción y cantidad
        """
        return {
            'patients': {
                'name': 'Pacientes',
                'description': 'Generar 50 pacientes de ejemplo',
                'count': 50,
                'module': 'scripts.seed_data'
            },
            'clinical_documents': {
                'name': 'Documentos Clínicos',
                'description': 'Generar 100 documentos clínicos',
                'count': 100,
                'module': 'scripts.seed_data'
            },
            'clinical_records': {
                'name': 'Historias Clínicas',
                'description': 'Generar 40 historias clínicas',
                'count': 40,
                'module': 'scripts.seed_clinical_records'
            },
            'clinical_forms': {
                'name': 'Formularios Clínicos',
                'description': 'Generar 30 formularios clínicos',
                'count': 30,
                'module': 'scripts.seed_clinical_forms'
            },
            'reports': {
                'name': 'Reportes',
                'description': 'Generar 20 reportes de ejemplo',
                'count': 20,
                'module': 'scripts.seed_reports'
            },
            'all': {
                'name': 'Todos los datos',
                'description': 'Generar todos los datos de ejemplo',
                'count': 'variable',
                'module': 'scripts.seed_data'
            }
        }
    
    def _import_seeder_function(self, module_path: str, function_name: str = 'run_seeder'):
        """
        Importar dinámicamente función de seeder.
        
        Args:
            module_path: Ruta del módulo (ej: scripts.seed_data)
            function_name: Nombre de la función a importar
            
        Returns:
            callable: Función de seeder o None si falla
        """
        try:
            module = __import__(module_path, fromlist=[function_name])
            return getattr(module, function_name, None)
        except (ImportError, AttributeError) as e:
            logger.error(f"Error importando seeder {module_path}.{function_name}: {e}")
            return None
    
    def _run_seeder(self, seeder_name: str, tenant=None) -> Dict[str, Any]:
        """
        Ejecutar un seeder específico.
        
        Args:
            seeder_name: Nombre del seeder a ejecutar
            tenant: Tenant para los datos (opcional)
            
        Returns:
            dict: Resultado de la ejecución
        """
        availables = self._get_available_seeders()
        
        if seeder_name not in availables:
            return {
                'success': False,
                'error': f"Seeder '{seeder_name}' no encontrado",
                'available': list(availables.keys())
            }
        
        seeder_info = availables[seeder_name]
        
        try:
            # Importar y ejecutar seeder
            seeder_func = self._import_seeder_function(seeder_info['module'])
            
            if not seeder_func:
                return {
                    'success': False,
                    'error': f"No se pudo cargar seeder '{seeder_name}'",
                    'module': seeder_info['module']
                }
            
            # Ejecutar seeder
            logger.info(f"Ejecutando seeder: {seeder_name}")
            result = seeder_func(tenant=tenant, dry_run=False)
            
            return {
                'success': True,
                'seeder': seeder_name,
                'name': seeder_info['name'],
                'description': seeder_info['description'],
                'result': result,
                'created': seeder_info.get('count', 'variable')
            }
            
        except Exception as e:
            logger.error(f"Error ejecutando seeder {seeder_name}: {e}")
            return {
                'success': False,
                'error': str(e),
                'seeder': seeder_name
            }
    
    @action(detail=False, methods=['get'], url_path='available')
    def available_seeders(self, request):
        """
        Listar seeders disponibles.
        
        GET /api/seeders/available/
        """
        seeders = self._get_available_seeders()
        return Response({
            'count': len(seeders),
            'seeders': seeders,
            'help': 'Para ejecutar un seeder: POST /api/seeders/run/ con {"name": "patients"}'
        })
    
    @action(detail=False, methods=['post'], url_path='run')
    def run_seeder(self, request):
        """
        Ejecutar un seeder específico.
        
        POST /api/seeders/run/
        Body: {"name": "patients"}
        """
        seeder_name = request.data.get('name', '').lower()
        
        if not seeder_name:
            return Response({
                'error': 'Debe especificar "name" del seeder',
                'available': list(self._get_available_seeders().keys())
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Ejecutar seeder
        result = self._run_seeder(seeder_name, tenant=request.user.tenant)
        
        status_code = status.HTTP_200_OK if result.get('success') else status.HTTP_400_BAD_REQUEST
        return Response(result, status=status_code)
    
    @action(detail=False, methods=['post'], url_path='run-all')
    def run_all_seeders(self, request):
        """
        Ejecutar todos los seeders.
        
        POST /api/seeders/run-all/
        """
        seeders_to_run = ['patients', 'clinical_records', 'clinical_documents', 'clinical_forms', 'reports']
        results = []
        
        for seeder in seeders_to_run:
            result = self._run_seeder(seeder, tenant=request.user.tenant)
            results.append(result)
            logger.info(f"Seeder '{seeder}' completado: {result.get('success')}")
        
        # Contar éxitos y errores
        successful = sum(1 for r in results if r.get('success'))
        errors = len(results) - successful
        
        return Response({
            'message': 'Ejecución de todos los seeders completada',
            'total': len(results),
            'successful': successful,
            'errors': errors,
            'results': results
        })
    
    @action(detail=False, methods=['post'], url_path='reset')
    def reset_data(self, request):
        """
        Limpiar datos de ejemplo.
        
        POST /api/seeders/reset/
        """
        try:
            from django.core.management import call_command
            from django.db import connection
            
            # Obtener tenant actual
            tenant = request.user.tenant
            
            if not tenant:
                return Response({
                    'error': 'No hay tenant asociado'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Limpiar datos del tenant
            logger.info(f"Limpiando datos del tenant: {tenant.slug}")
            
            from apps.patients.models import Patient
            from apps.documents.models import ClinicalDocument
            from apps.clinical_records.models import ClinicalRecord
            
            # Contar registros antes
            counts_before = {
                'patients': Patient.objects.filter(tenant=tenant).count(),
                'records': ClinicalRecord.objects.filter(tenant=tenant).count(),
                'documents': ClinicalDocument.objects.filter(tenant=tenant).count(),
            }
            
            # Eliminar
            Patient.objects.filter(tenant=tenant).delete()
            ClinicalRecord.objects.filter(tenant=tenant).delete()
            ClinicalDocument.objects.filter(tenant=tenant).delete()
            
            # Contar después
            counts_after = {
                'patients': Patient.objects.filter(tenant=tenant).count(),
                'records': ClinicalRecord.objects.filter(tenant=tenant).count(),
                'documents': ClinicalDocument.objects.filter(tenant=tenant).count(),
            }
            
            deleted = {
                'patients': counts_before['patients'] - counts_after['patients'],
                'records': counts_before['records'] - counts_after['records'],
                'documents': counts_before['documents'] - counts_after['documents'],
            }
            
            logger.info(f"Datos limpiados: {deleted}")
            
            return Response({
                'success': True,
                'message': 'Datos limpiados exitosamente',
                'tenant': tenant.slug,
                'deleted': deleted
            })
            
        except Exception as e:
            logger.error(f"Error limpiando datos: {e}")
            return Response({
                'error': f"Error limpiando datos: {str(e)}"
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], url_path='dry-run')
    def dry_run_seeder(self, request):
        """
        Simular ejecución de seeder sin cambios.
        
        POST /api/seeders/dry-run/
        Body: {"name": "patients"}
        """
        seeder_name = request.data.get('name', '').lower()
        
        if not seeder_name:
            return Response({
                'error': 'Debe especificar "name" del seeder'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Dry run
        availables = self._get_available_seeders()
        
        if seeder_name not in availables:
            return Response({
                'error': f"Seeder '{seeder_name}' no encontrado"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        seeder_info = availables[seeder_name]
        
        return Response({
            'seeder': seeder_name,
            'name': seeder_info['name'],
            'description': seeder_info['description'],
            'will_create': seeder_info.get('count', 'variable'),
            'message': 'Este es un dry-run. No se crearán datos reales.',
            'to_execute': f'POST /api/seeders/run/ con {{"name": "{seeder_name}"}}'
        })
