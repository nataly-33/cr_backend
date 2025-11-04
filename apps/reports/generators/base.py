"""
Clase Base para Generadores de Reportes

Proporciona una interfaz unificada para todos los generadores (PDF, Excel, CSV)
y métodos compartidos para metadatos, filtrado y formateo.
"""

from abc import ABC, abstractmethod
from io import BytesIO, StringIO
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class BaseReportGenerator(ABC):
    """
    Clase base abstracta para generadores de reportes.
    
    Define la interfaz común que deben implementar todos los generadores
    específicos (PDF, Excel, CSV, etc).
    """
    
    # Tipos de formato soportados
    SUPPORTED_FORMATS = ['pdf', 'excel', 'csv']
    
    def __init__(self, title: str = "Reporte", format_type: str = "pdf"):
        """
        Inicializar generador de reportes
        
        Args:
            title: Título del reporte
            format_type: Tipo de formato (pdf, excel, csv)
        """
        self.title = title
        self.format_type = format_type.lower()
        self.data = []
        self.metadata = {}
        self.created_at = datetime.now()
        
        if self.format_type not in self.SUPPORTED_FORMATS:
            raise ValueError(
                f"Formato {self.format_type} no soportado. "
                f"Soportados: {', '.join(self.SUPPORTED_FORMATS)}"
            )
    
    @abstractmethod
    def generate(self) -> bytes:
        """
        Generar el reporte en el formato especificado.
        
        Returns:
            bytes: Contenido del archivo generado
        """
        pass
    
    @abstractmethod
    def add_table(self, data: List[Dict[str, Any]], headers: Optional[List[str]] = None) -> None:
        """
        Agregar una tabla al reporte.
        
        Args:
            data: Lista de diccionarios con los datos
            headers: Lista de encabezados (opcional)
        """
        pass
    
    @abstractmethod
    def add_section(self, title: str, content: str) -> None:
        """
        Agregar una sección con título y contenido.
        
        Args:
            title: Título de la sección
            content: Contenido de la sección
        """
        pass
    
    def set_metadata(self, key: str, value: Any) -> None:
        """
        Establecer metadata del reporte.
        
        Args:
            key: Clave de metadata
            value: Valor de metadata
        """
        self.metadata[key] = value
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Obtener toda la metadata del reporte.
        
        Returns:
            dict: Metadata del reporte
        """
        return {
            'title': self.title,
            'format': self.format_type,
            'created_at': self.created_at.isoformat(),
            'custom': self.metadata
        }
    
    def get_file_extension(self) -> str:
        """
        Obtener extensión de archivo según formato.
        
        Returns:
            str: Extensión de archivo (ej: .pdf, .xlsx, .csv)
        """
        extensions = {
            'pdf': '.pdf',
            'excel': '.xlsx',
            'csv': '.csv'
        }
        return extensions.get(self.format_type, '.bin')
    
    def get_mime_type(self) -> str:
        """
        Obtener MIME type según formato.
        
        Returns:
            str: MIME type (ej: application/pdf)
        """
        mime_types = {
            'pdf': 'application/pdf',
            'excel': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'csv': 'text/csv'
        }
        return mime_types.get(self.format_type, 'application/octet-stream')
    
    def get_filename(self) -> str:
        """
        Obtener nombre de archivo recomendado.
        
        Returns:
            str: Nombre de archivo
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_title = "".join(c for c in self.title if c.isalnum() or c in (' ', '_')).rstrip()
        return f"{safe_title}_{timestamp}{self.get_file_extension()}"
    
    def format_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Formatear datos para el reporte (conversión tipos, limpieza, etc).
        
        Args:
            data: Datos originales
            
        Returns:
            list: Datos formateados
        """
        formatted = []
        for row in data:
            formatted_row = {}
            for key, value in row.items():
                formatted_row[key] = self._format_value(value)
            formatted.append(formatted_row)
        return formatted
    
    def _format_value(self, value: Any) -> str:
        """
        Formatear un valor individual.
        
        Args:
            value: Valor a formatear
            
        Returns:
            str: Valor formateado
        """
        if value is None:
            return '-'
        elif isinstance(value, datetime):
            return value.strftime('%d/%m/%Y %H:%M:%S')
        elif isinstance(value, bool):
            return 'Sí' if value else 'No'
        elif isinstance(value, (int, float)):
            return str(value)
        else:
            return str(value)
    
    def validate_data(self, data: List[Dict[str, Any]]) -> bool:
        """
        Validar que los datos sean válidos.
        
        Args:
            data: Datos a validar
            
        Returns:
            bool: True si es válido
        """
        if not isinstance(data, list):
            logger.error("Datos no son una lista")
            return False
        
        if len(data) == 0:
            logger.warning("Lista de datos vacía")
            return True  # Permitir reporte vacío
        
        if not all(isinstance(row, dict) for row in data):
            logger.error("No todos los elementos son diccionarios")
            return False
        
        return True
    
    def log_generation(self, success: bool = True, message: str = "") -> None:
        """
        Registrar evento de generación de reporte.
        
        Args:
            success: Si fue exitoso
            message: Mensaje adicional
        """
        status = "SUCCESS" if success else "ERROR"
        log_msg = f"[{status}] Reporte '{self.title}' ({self.format_type}) generado"
        if message:
            log_msg += f": {message}"
        
        if success:
            logger.info(log_msg)
        else:
            logger.error(log_msg)


class ReportGeneratorFactory:
    """
    Factory para crear instancias de generadores según tipo.
    """
    
    _generators = {}
    
    @classmethod
    def register(cls, format_type: str, generator_class: type) -> None:
        """
        Registrar un nuevo tipo de generador.
        
        Args:
            format_type: Tipo de formato (pdf, excel, csv)
            generator_class: Clase del generador
        """
        cls._generators[format_type.lower()] = generator_class
    
    @classmethod
    def create(cls, format_type: str, title: str = "Reporte") -> BaseReportGenerator:
        """
        Crear un generador del tipo especificado.
        
        Args:
            format_type: Tipo de formato
            title: Título del reporte
            
        Returns:
            BaseReportGenerator: Instancia del generador
            
        Raises:
            ValueError: Si el tipo de formato no está registrado
        """
        format_type = format_type.lower()
        if format_type not in cls._generators:
            raise ValueError(
                f"Tipo de generador '{format_type}' no registrado. "
                f"Disponibles: {list(cls._generators.keys())}"
            )
        
        return cls._generators[format_type](title=title, format_type=format_type)
    
    @classmethod
    def get_supported_formats(cls) -> List[str]:
        """
        Obtener lista de formatos soportados.
        
        Returns:
            list: Formatos disponibles
        """
        return list(cls._generators.keys())
