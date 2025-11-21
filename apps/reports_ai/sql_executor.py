"""
Servicio para ejecutar consultas SQL de manera segura
"""
import logging
import time
from typing import Dict, List, Any
from django.db import connection
from django.apps import apps

logger = logging.getLogger(__name__)


class SQLExecutorService:
    """
    Ejecuta consultas SQL de manera segura usando Django ORM cuando sea posible
    """
    
    def execute_query(self, sql: str, params: Dict = None, row_limit: int = 100) -> Dict:
        """
        Ejecutar consulta SQL y retornar resultados
        
        Args:
            sql: Consulta SQL
            params: Parámetros de la consulta
            row_limit: Límite de filas
        
        Returns:
            {
                'columns': [...],
                'data': [...],
                'row_count': 100,
                'execution_time_ms': 45,
                'truncated': False
            }
        """
        start_time = time.time()
        params = params or {}
        
        try:
            # Asegurar límite
            if 'LIMIT' not in sql.upper():
                sql = f"{sql.rstrip(';')} LIMIT {row_limit}"
            
            with connection.cursor() as cursor:
                cursor.execute(sql, params)
                
                # Obtener columnas
                columns = [col[0] for col in cursor.description]
                
                # Obtener datos
                rows = cursor.fetchall()
                
                # Convertir a lista de diccionarios
                data = []
                for row in rows:
                    row_dict = {}
                    for i, value in enumerate(row):
                        # Convertir valores a tipos serializables
                        if hasattr(value, 'isoformat'):
                            row_dict[columns[i]] = value.isoformat()
                        elif isinstance(value, bytes):
                            row_dict[columns[i]] = value.decode('utf-8', errors='ignore')
                        else:
                            row_dict[columns[i]] = value
                    data.append(row_dict)
            
            execution_time = int((time.time() - start_time) * 1000)
            
            return {
                'columns': columns,
                'data': data,
                'row_count': len(data),
                'execution_time_ms': execution_time,
                'truncated': len(data) >= row_limit
            }
        
        except Exception as e:
            logger.error(f"SQL execution error: {e}")
            raise ValueError(f"Error ejecutando consulta: {str(e)}")
    
    def execute_with_orm(self, table_name: str, filters: Dict = None, 
                        fields: List[str] = None, order_by: str = '-created_at',
                        limit: int = 100) -> Dict:
        """
        Ejecutar consulta usando Django ORM (más seguro)
        
        Args:
            table_name: Nombre de la tabla (patient, clinical_form, etc.)
            filters: Diccionario de filtros
            fields: Lista de campos a seleccionar
            order_by: Campo de ordenamiento
            limit: Límite de resultados
        
        Returns:
            Mismo formato que execute_query
        """
        start_time = time.time()
        
        try:
            # Mapeo de tablas a modelos
            table_to_model = {
                'patient': ('patients', 'Patient'),
                'clinical_record': ('clinical_records', 'ClinicalRecord'),
                'clinical_form': ('clinical_records', 'ClinicalForm'),
                'document': ('documents', 'ClinicalDocument'),
                'user': ('accounts', 'User'),
            }
            
            if table_name not in table_to_model:
                raise ValueError(f"Tabla '{table_name}' no soportada")
            
            app_label, model_name = table_to_model[table_name]
            model = apps.get_model(app_label, model_name)
            
            # Construir queryset
            queryset = model.objects.all()
            
            # Aplicar filtros
            if filters:
                queryset = queryset.filter(**filters)
            
            # Ordenar
            if order_by:
                queryset = queryset.order_by(order_by)
            
            # Limitar
            queryset = queryset[:limit]
            
            # Seleccionar campos
            if fields:
                queryset = queryset.values(*fields)
            else:
                queryset = queryset.values()
            
            # Ejecutar
            data = list(queryset)
            
            # Convertir valores a tipos serializables
            for row in data:
                for key, value in row.items():
                    if hasattr(value, 'isoformat'):
                        row[key] = value.isoformat()
                    elif isinstance(value, bytes):
                        row[key] = value.decode('utf-8', errors='ignore')
            
            columns = list(data[0].keys()) if data else []
            
            execution_time = int((time.time() - start_time) * 1000)
            
            return {
                'columns': columns,
                'data': data,
                'row_count': len(data),
                'execution_time_ms': execution_time,
                'truncated': len(data) >= limit
            }
        
        except Exception as e:
            logger.error(f"ORM execution error: {e}")
            raise ValueError(f"Error ejecutando consulta: {str(e)}")
    
    def export_to_format(self, result_data: Dict, format: str = 'json') -> Any:
        """
        Exportar resultados a diferentes formatos
        
        Args:
            result_data: Diccionario con data, columns, etc.
            format: 'json', 'csv', 'excel', 'pdf'
        
        Returns:
            Contenido en el formato solicitado
        """
        if format == 'json':
            return result_data
        
        elif format == 'csv':
            return self._export_csv(result_data)
        
        elif format == 'excel':
            return self._export_excel(result_data)
        
        elif format == 'pdf':
            return self._export_pdf(result_data)
        
        else:
            raise ValueError(f"Formato '{format}' no soportado")
    
    def _export_csv(self, result_data: Dict) -> str:
        """Exportar a CSV"""
        import csv
        from io import StringIO
        
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=result_data['columns'])
        
        writer.writeheader()
        writer.writerows(result_data['data'])
        
        return output.getvalue()
    
    def _export_excel(self, result_data: Dict):
        """Exportar a Excel"""
        from io import BytesIO
        from openpyxl import Workbook
        
        wb = Workbook()
        ws = wb.active
        ws.title = "Reporte"
        
        # Headers
        ws.append(result_data['columns'])
        
        # Data
        for row_dict in result_data['data']:
            row_values = [row_dict.get(col, '') for col in result_data['columns']]
            ws.append(row_values)
        
        # Ajustar anchos
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width
        
        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        return buffer.getvalue()
    
    def _export_pdf(self, result_data: Dict):
        """Exportar a PDF"""
        from io import BytesIO
        from reportlab.lib.pagesizes import letter, landscape
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from datetime import datetime
        
        buffer = BytesIO()
        
        # Orientación landscape para más columnas
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(letter),
            rightMargin=30,
            leftMargin=30,
            topMargin=30,
            bottomMargin=18,
        )
        
        elements = []
        styles = getSampleStyleSheet()
        
        # Título
        title = Paragraph("<b>Reporte de Consulta AI</b>", styles['Title'])
        elements.append(title)
        elements.append(Spacer(1, 12))
        
        # Metadata
        metadata_text = f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br/>"
        metadata_text += f"Registros: {result_data['row_count']}<br/>"
        metadata_text += f"Tiempo de ejecución: {result_data['execution_time_ms']}ms"
        
        metadata = Paragraph(metadata_text, styles['Normal'])
        elements.append(metadata)
        elements.append(Spacer(1, 12))
        
        # Tabla de datos
        table_data = [result_data['columns']]
        
        for row_dict in result_data['data']:
            row = [str(row_dict.get(col, ''))[:50] for col in result_data['columns']]
            table_data.append(row)
        
        # Limitar filas en PDF (máximo 50)
        if len(table_data) > 51:
            table_data = table_data[:51]
            elements.append(Paragraph(
                f"<i>Mostrando primeras 50 de {result_data['row_count']} filas</i>",
                styles['Normal']
            ))
            elements.append(Spacer(1, 6))
        
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(table)
        
        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()
