"""
Constructor de Reportes Dinámicos

Permite construir reportes complejos con múltiples data_sources,
columnas personalizadas, filtros dinámicos, agrupación y ordenamiento.

Usa QBEParser para filtros seguros y DynamicFilter para aplicación.
"""

from django.db.models import Q, Count, F
from datetime import datetime
from io import BytesIO
import logging

from .qbe_parser import QBEParser, QBEParseError
from .filters import DynamicFilter, DynamicFilterError
from .generators.pdf_generator import PDFReportGenerator
from .generators.excel_generator import ExcelReportGenerator
from .generators.csv_generator import generate_documents_csv

logger = logging.getLogger(__name__)


class DynamicReportError(Exception):
    """Excepción para errores en reportes dinámicos"""
    pass


class InvalidDataSourceError(DynamicReportError):
    """Data source no válida"""
    pass


class InvalidColumnError(DynamicReportError):
    """Columna no válida para la data source"""
    pass


class DynamicReportGenerator:
    """
    Generador de reportes dinámicos completamente configurable
    
    Ejemplo uso:
    >>> spec = {
    ...     'data_sources': ['documents', 'patients'],
    ...     'columns': {
    ...         'documents': ['specialty', 'document_type', 'created_at'],
    ...         'patients': ['full_name', 'date_of_birth']
    ...     },
    ...     'filters': [
    ...         {'field': 'specialty', 'operator': 'eq', 'value': 'Cardiología'}
    ...     ],
    ...     'group_by': ['specialty'],
    ...     'order_by': ['-created_at'],
    ...     'output_format': 'pdf'
    ... }
    >>> generator = DynamicReportGenerator(spec)
    >>> pdf_buffer = generator.generate_pdf(tenant_name, user_name)
    """
    
    # Mapeo de data_sources a modelos y campos disponibles
    DATA_SOURCES_CONFIG = {
        'documents': {
            'model_path': 'apps.documents.ClinicalDocument',
            'available_columns': [
                'id', 'title', 'document_type', 'specialty', 'doctor_name',
                'document_date', 'created_at', 'status', 'is_signed'
            ],
            'display_columns': {
                'id': 'ID',
                'title': 'Título',
                'document_type': 'Tipo de Documento',
                'specialty': 'Especialidad',
                'doctor_name': 'Doctor',
                'document_date': 'Fecha del Documento',
                'created_at': 'Fecha Creación',
                'status': 'Estado',
                'is_signed': 'Firmado'
            }
        },
        'patients': {
            'model_path': 'apps.patients.Patient',
            'available_columns': [
                'id', 'first_name', 'last_name', 'gender', 'date_of_birth',
                'identity_document', 'email', 'phone', 'city'
            ],
            'display_columns': {
                'id': 'ID',
                'first_name': 'Nombre',
                'last_name': 'Apellido',
                'gender': 'Género',
                'date_of_birth': 'Fecha Nacimiento',
                'identity_document': 'Documento',
                'email': 'Email',
                'phone': 'Teléfono',
                'city': 'Ciudad'
            }
        },
        'clinical_records': {
            'model_path': 'apps.clinical_records.ClinicalRecord',
            'available_columns': [
                'id', 'record_number', 'status', 'patient',
                'created_at', 'is_archived'
            ],
            'display_columns': {
                'id': 'ID',
                'record_number': 'Número de Registro',
                'status': 'Estado',
                'patient': 'Paciente',
                'created_at': 'Fecha Creación',
                'is_archived': 'Archivado'
            }
        },
        'users': {
            'model_path': 'apps.accounts.User',
            'available_columns': [
                'id', 'first_name', 'last_name', 'email', 'is_active',
                'created_at'
            ],
            'display_columns': {
                'id': 'ID',
                'first_name': 'Nombre',
                'last_name': 'Apellido',
                'email': 'Email',
                'is_active': 'Activo',
                'created_at': 'Fecha Creación'
            }
        }
    }
    
    def __init__(self, report_spec: dict):
        """
        Inicializa el generador con una especificación de reporte
        
        Args:
            report_spec: {
                'data_sources': ['documents', 'patients'],
                'columns': {
                    'documents': ['specialty', 'document_type', 'created_at'],
                    'patients': ['full_name', 'date_of_birth']
                },
                'filters': [
                    {'field': 'specialty', 'operator': 'eq', 'value': 'Cardiología'},
                    {'field': 'created_at', 'operator': 'gte', 'value': '2025-10-01'}
                ],
                'group_by': ['specialty'],
                'order_by': ['-created_at'],
                'limit': 1000,
                'output_format': 'pdf'
            }
        """
        self.report_spec = report_spec
        self.data_sources = report_spec.get('data_sources', [])
        self.columns = report_spec.get('columns', {})
        self.filters = report_spec.get('filters', [])
        self.group_by = report_spec.get('group_by', [])
        self.order_by = report_spec.get('order_by', [])
        self.limit = report_spec.get('limit', 1000)
        self.output_format = report_spec.get('output_format', 'pdf')
        
        self.data_cache = {}
        self._validate_spec()
    
    def _validate_spec(self):
        """Valida que la especificación del reporte sea correcta"""
        # Validar data_sources
        if not self.data_sources:
            raise DynamicReportError("Debe especificar al menos una data_source")
        
        for source in self.data_sources:
            if source not in self.DATA_SOURCES_CONFIG:
                raise InvalidDataSourceError(
                    f"Data source '{source}' no válida. "
                    f"Válidas: {list(self.DATA_SOURCES_CONFIG.keys())}"
                )
        
        # Validar columnas
        if not self.columns:
            raise DynamicReportError("Debe especificar columnas para cada data_source")
        
        for source in self.data_sources:
            if source not in self.columns:
                raise DynamicReportError(f"Debe especificar columnas para '{source}'")
            
            source_cols = self.columns[source]
            available_cols = self.DATA_SOURCES_CONFIG[source]['available_columns']
            
            for col in source_cols:
                if col not in available_cols:
                    raise InvalidColumnError(
                        f"Columna '{col}' no válida para '{source}'. "
                        f"Válidas: {available_cols}"
                    )
        
        # Validar output_format
        if self.output_format not in ['pdf', 'excel', 'csv']:
            raise DynamicReportError(
                f"Formato '{self.output_format}' no soportado. "
                f"Válidos: pdf, excel, csv"
            )
    
    def fetch_data(self):
        """Obtiene data de todas las data_sources aplicando filtros"""
        from django.apps import apps
        
        for source in self.data_sources:
            config = self.DATA_SOURCES_CONFIG[source]
            model_path = config['model_path']
            
            # Cargar modelo
            parts = model_path.rsplit('.', 1)
            app_label = parts[0].split('.')[-1]
            model_name = parts[1]
            model_class = apps.get_model(app_label, model_name)
            
            # Obtener queryset
            queryset = model_class.objects.all()
            
            # Aplicar filtros si existen
            if self.filters:
                filter_spec = {'filters': self.filters}
                queryset = DynamicFilter.apply(queryset, filter_spec)
            
            # Seleccionar columnas
            selected_cols = self.columns[source]
            queryset = queryset.values(*selected_cols)
            
            # Aplicar ordenamiento
            if self.order_by:
                queryset = queryset.order_by(*self.order_by)
            
            # Aplicar límite
            if self.limit:
                queryset = queryset[:self.limit]
            
            # Cachear data
            self.data_cache[source] = list(queryset)
            
            logger.info(f"Fetched {len(self.data_cache[source])} rows from {source}")
    
    def build_report_data(self) -> dict:
        """
        Construye la estructura de datos del reporte
        
        Returns:
            {
                'title': '...',
                'generated_at': '...',
                'data_sources': ['documents', 'patients'],
                'tables': {
                    'documents': {
                        'title': 'Documentos',
                        'headers': [...],
                        'rows': [...]
                    },
                    'patients': {
                        'title': 'Pacientes',
                        'headers': [...],
                        'rows': [...]
                    }
                },
                'summary': {
                    'documents': 45,
                    'patients': 12
                }
            }
        """
        report_data = {
            'title': 'Reporte Dinámico',
            'generated_at': datetime.now().isoformat(),
            'data_sources': self.data_sources,
            'tables': {},
            'summary': {}
        }
        
        for source in self.data_sources:
            config = self.DATA_SOURCES_CONFIG[source]
            selected_cols = self.columns[source]
            data = self.data_cache.get(source, [])
            
            # Headers
            headers = [config['display_columns'].get(col, col) for col in selected_cols]
            
            # Rows (convertir valores a string para mostrar)
            rows = []
            for row_dict in data:
                row = [str(row_dict.get(col, '')) for col in selected_cols]
                rows.append(row)
            
            report_data['tables'][source] = {
                'title': source.replace('_', ' ').title(),
                'headers': headers,
                'rows': rows
            }
            
            report_data['summary'][source] = len(data)
        
        return report_data
    
    def generate(self) -> BytesIO:
        """
        Genera el reporte en el formato especificado
        
        Returns:
            BytesIO con el contenido del reporte
        """
        # Obtener datos
        self.fetch_data()
        
        # Construir estructura
        report_data = self.build_report_data()
        
        # Generar según formato
        if self.output_format == 'pdf':
            return self._generate_pdf(report_data)
        elif self.output_format == 'excel':
            return self._generate_excel(report_data)
        elif self.output_format == 'csv':
            return self._generate_csv(report_data)
        else:
            raise DynamicReportError(f"Formato no soportado: {self.output_format}")
    
    def _generate_pdf(self, report_data: dict) -> BytesIO:
        """Genera PDF del reporte"""
        pdf = PDFReportGenerator(title=report_data['title'])
        
        # Título
        pdf.add_title(report_data['title'])
        
        # Metadata
        pdf.add_metadata(
            "Sistema de Reportes Dinámicos",
            "Sistema",
            datetime.fromisoformat(report_data['generated_at'])
        )
        
        # Resumen
        pdf.add_heading("Resumen")
        for source, count in report_data['summary'].items():
            pdf.add_paragraph(f"<b>{source.title()}:</b> {count} registros")
        
        pdf.add_spacer(0.3)
        
        # Tablas
        for source, table_info in report_data['tables'].items():
            pdf.add_heading(table_info['title'])
            
            # Construir tabla
            table_data = [table_info['headers']] + table_info['rows']
            
            # Limitar filas en PDF (máximo 20 por tabla para no saturar)
            if len(table_data) > 20:
                table_data = table_data[:20]
                pdf.add_paragraph(
                    f"<i>(Mostrando primeras 20 de {len(table_info['rows'])} filas)</i>"
                )
            
            pdf.add_table(table_data, col_widths=None)
            pdf.add_spacer(0.2)
        
        return pdf.generate()
    
    def _generate_excel(self, report_data: dict) -> BytesIO:
        """Genera Excel del reporte"""
        excel = ExcelReportGenerator(title=report_data['title'])
        
        # Hoja 1: Resumen
        sheet1 = excel.create_sheet("Resumen")
        excel.add_title_row(sheet1, report_data['title'])
        
        sheet1['A2'] = 'Generado:'
        sheet1['B2'] = report_data['generated_at']
        
        sheet1['A4'] = 'Data Source'
        sheet1['B4'] = 'Registros'
        
        row = 5
        for source, count in report_data['summary'].items():
            sheet1[f'A{row}'] = source
            sheet1[f'B{row}'] = count
            row += 1
        
        # Hoja por cada data_source
        for source, table_info in report_data['tables'].items():
            sheet = excel.create_sheet(source.title())
            excel.add_title_row(sheet, table_info['title'])
            
            # Tabla
            table_data = [row[:] for row in table_info['rows']]  # Copy rows
            excel.add_table(
                sheet,
                table_data,
                headers=table_info['headers'],
                start_row=3
            )
        
        return excel.generate()
    
    def _generate_csv(self, report_data: dict) -> str:
        """Genera CSV del reporte"""
        import csv
        from io import StringIO
        
        output = StringIO()
        writer = csv.writer(output)
        
        # Escribir cada tabla como CSV separado
        for source, table_info in report_data['tables'].items():
            # Header de tabla
            writer.writerow([f"# {table_info['title']}"])
            writer.writerow(table_info['headers'])
            
            # Data
            writer.writerows(table_info['rows'])
            
            # Espacios
            writer.writerow([])
        
        return output.getvalue()
    
    def get_content_type(self) -> str:
        """Retorna el content-type MIME según formato"""
        if self.output_format == 'pdf':
            return 'application/pdf'
        elif self.output_format == 'excel':
            return 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        elif self.output_format == 'csv':
            return 'text/csv'
        else:
            return 'application/octet-stream'
    
    def get_filename(self) -> str:
        """Retorna el nombre sugerido del archivo"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        ext = self.output_format
        
        # Mapear formato a extensión
        ext_map = {
            'pdf': 'pdf',
            'excel': 'xlsx',
            'csv': 'csv'
        }
        
        return f"reporte_dinamico_{timestamp}.{ext_map.get(ext, ext)}"
    
    @staticmethod
    def get_available_sources() -> dict:
        """Retorna información de las data_sources disponibles"""
        return DynamicReportGenerator.DATA_SOURCES_CONFIG
