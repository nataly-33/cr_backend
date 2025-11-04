"""
Servicio para ejecutar el seeder de datos
"""
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any
from django.conf import settings
import os
import logging

logger = logging.getLogger(__name__)


class SeederService:
    """
    Servicio para ejecutar seeders de datos
    """
    
    @staticmethod
    def get_seeder_path(script_name: str = 'seed_data.py') -> Path:
        """
        Obtiene la ruta del script seeder
        
        Args:
            script_name: Nombre del script seeder (default: seed_data.py)
            
        Returns:
            Path al script seeder
        """
        base_dir = Path(settings.BASE_DIR)
        return base_dir / 'scripts' / script_name
    
    @staticmethod
    def run_seeder(script_name: str = 'seed_data.py', environment: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Ejecuta un script seeder en un proceso separado
        
        Args:
            script_name: Nombre del script seeder (default: seed_data.py)
            environment: Variables de entorno adicionales (opcional)
            
        Returns:
            Dict con resultado de ejecución {
                'success': bool,
                'stdout': str,
                'stderr': str,
                'return_code': int,
                'message': str
            }
        """
        try:
            seeder_path = SeederService.get_seeder_path(script_name)
            
            # Verificar que el archivo existe
            if not seeder_path.exists():
                return {
                    'success': False,
                    'stdout': '',
                    'stderr': f'Seeder script no encontrado: {seeder_path}',
                    'return_code': -1,
                    'message': 'Error: Script seeder no encontrado'
                }
            
            # Preparar entorno
            env = os.environ.copy()
            if environment:
                env.update(environment)
            
            # Obtener el ejecutable de Python del entorno actual
            python_executable = sys.executable
            
            # Ejecutar el seeder
            logger.info(f"Ejecutando seeder: {seeder_path}")
            
            process = subprocess.run(
                [python_executable, str(seeder_path)],
                capture_output=True,
                text=True,
                timeout=300,  # 5 minutos máximo
                env=env
            )
            
            return {
                'success': process.returncode == 0,
                'stdout': process.stdout,
                'stderr': process.stderr,
                'return_code': process.returncode,
                'message': 'Seeder ejecutado exitosamente' if process.returncode == 0 else f'Error en seeder (código: {process.returncode})'
            }
            
        except subprocess.TimeoutExpired:
            logger.error("Timeout ejecutando seeder")
            return {
                'success': False,
                'stdout': '',
                'stderr': 'Timeout: Seeder tardó demasiado en ejecutarse',
                'return_code': -1,
                'message': 'Error: Timeout en ejecución del seeder'
            }
        except Exception as e:
            logger.error(f"Error ejecutando seeder: {str(e)}")
            return {
                'success': False,
                'stdout': '',
                'stderr': str(e),
                'return_code': -1,
                'message': f'Error: {str(e)}'
            }
    
    @staticmethod
    def run_seeder_direct():
        """
        Ejecuta el seeder directamente en el proceso actual (menos recomendado)
        Útil para debugging, pero puede afectar el proceso
        
        Returns:
            Dict con resultado
        """
        try:
            seeder_path = SeederService.get_seeder_path()
            
            if not seeder_path.exists():
                return {
                    'success': False,
                    'message': 'Script seeder no encontrado',
                    'rows_created': {}
                }
            
            logger.info(f"Ejecutando seeder directo: {seeder_path}")
            
            # Ejecutar el script
            exec(open(seeder_path, encoding='utf-8').read())
            
            return {
                'success': True,
                'message': 'Seeder ejecutado exitosamente',
                'rows_created': {}
            }
            
        except Exception as e:
            logger.error(f"Error ejecutando seeder directo: {str(e)}")
            return {
                'success': False,
                'message': f'Error: {str(e)}',
                'rows_created': {}
            }
