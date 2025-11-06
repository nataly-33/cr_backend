from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.platypus import Image as RLImage
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime
from .base import BaseReportGenerator
from typing import List, Dict, Any, Optional


class PDFReportGenerator(BaseReportGenerator):
    """Generador de reportes en PDF"""
    
    def __init__(self, title="Reporte", format_type="pdf"):
        super().__init__(title, format_type)
        self.buffer = BytesIO()
        self.doc = SimpleDocTemplate(
            self.buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18,
        )
        self.styles = getSampleStyleSheet()
        self.story = []
        
        # Estilos personalizados
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1f2937'),
            spaceAfter=30,
            alignment=TA_CENTER,
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#374151'),
            spaceAfter=12,
        ))
    
    def add_title(self, title=None):
        """Agregar título al reporte"""
        title_text = title or self.title
        self.story.append(Paragraph(title_text, self.styles['CustomTitle']))
        self.story.append(Spacer(1, 0.2*inch))
    
    def add_metadata(self, tenant_name, generated_by, generated_at=None):
        """Agregar metadata del reporte"""
        if not generated_at:
            generated_at = datetime.now()
        
        metadata = f"""
        <b>Organización:</b> {tenant_name}<br/>
        <b>Generado por:</b> {generated_by}<br/>
        <b>Fecha:</b> {generated_at.strftime('%d/%m/%Y %H:%M')}
        """
        self.story.append(Paragraph(metadata, self.styles['Normal']))
        self.story.append(Spacer(1, 0.3*inch))
    
    def add_heading(self, text):
        """Agregar encabezado de sección"""
        self.story.append(Paragraph(text, self.styles['CustomHeading']))
        self.story.append(Spacer(1, 0.1*inch))
    
    def add_section(self, title: str, content: str) -> None:
        """
        Implementar método abstracto: Agregar una sección al reporte.
        
        Args:
            title: Título de la sección
            content: Contenido de la sección
        """
        self.add_heading(title)
        self.add_paragraph(content)
    
    def add_paragraph(self, text):
        """Agregar párrafo"""
        self.story.append(Paragraph(text, self.styles['Normal']))
        self.story.append(Spacer(1, 0.1*inch))
    
    def add_table(self, data: List[Dict[str, Any]], headers: Optional[List[str]] = None) -> None:
        """
        Implementar método abstracto: Agregar una tabla al reporte.
        
        Args:
            data: Lista de diccionarios con los datos
            headers: Lista de encabezados (opcional)
        """
        if not data:
            return
        
        # Usar headers si están provided, si no extraer del primer diccionario
        if headers is None:
            headers = list(data[0].keys()) if data else []
        
        # Convertir datos a tabla (lista de listas)
        table_data = [headers]
        for row in data:
            table_data.append([str(row.get(col, '')) for col in headers])
        
        # Crear y estilar la tabla
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3b82f6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f3f4f6')]),
        ]))
        
        self.story.append(table)
        self.story.append(Spacer(1, 0.3*inch))
    
    def _add_table_old(self, data, col_widths=None):
        """Agregar tabla al reporte (versión antigua, mantener para compatibilidad)"""
        if not data:
            return
        
        table = Table(data, colWidths=col_widths)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3b82f6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f3f4f6')]),
        ]))
        
        self.story.append(table)
        self.story.append(Spacer(1, 0.3*inch))
    
    def add_spacer(self, height=0.2):
        """Agregar espacio vertical"""
        self.story.append(Spacer(1, height*inch))
    
    def add_page_break(self):
        """Agregar salto de página"""
        self.story.append(PageBreak())
    
    def generate(self) -> bytes:
        """
        Implementar método abstracto: Generar el PDF y retornar bytes.
        
        Returns:
            bytes: Contenido del PDF
        """
        self.doc.build(self.story)
        self.buffer.seek(0)
        return self.buffer.getvalue()
    
    def _generate_old(self):
        """Generar el PDF y retornar el buffer (versión antigua)"""
        self.doc.build(self.story)
        self.buffer.seek(0)
        return self.buffer
    
    def save(self, filename):
        """Guardar el PDF en un archivo"""
        pdf_bytes = self.generate()
        with open(filename, 'wb') as f:
            f.write(pdf_bytes)
        return filename


def generate_documents_report(data, tenant_name, user_name):
    """Generar reporte de documentos"""
    pdf = PDFReportGenerator(title="Reporte de Documentos Clínicos")
    
    # Título y metadata
    pdf.add_title()
    pdf.add_metadata(tenant_name, user_name)
    
    # Resumen
    pdf.add_heading("Resumen")
    pdf.add_paragraph(f"Total de documentos: <b>{data.get('total', 0)}</b>")
    pdf.add_spacer(0.2)
    
    # Tabla de documentos por tipo
    if data.get('by_type'):
        pdf.add_heading("Documentos por Tipo")
        table_data = [['Tipo de Documento', 'Cantidad']]
        table_data.extend([[item['document_type'], str(item['count'])] 
                          for item in data['by_type']])
        pdf._add_table_old(table_data, col_widths=[4*inch, 2*inch])
    
    # Tabla de documentos recientes
    if data.get('recent_documents'):
        pdf.add_heading("Documentos Recientes")
        table_data = [['Fecha', 'Tipo', 'Paciente', 'Doctor']]
        for doc in data['recent_documents'][:10]:
            table_data.append([
                doc.get('document_date', '')[:10],
                doc.get('document_type', ''),
                doc.get('patient_name', ''),
                doc.get('doctor_name', '')
            ])
        pdf._add_table_old(table_data)
    
    return pdf.generate()


def generate_users_report(data, tenant_name, user_name):
    """Generar reporte de usuarios"""
    pdf = PDFReportGenerator(title="Reporte de Usuarios")
    
    # Título y metadata
    pdf.add_title()
    pdf.add_metadata(tenant_name, user_name)
    
    # Resumen
    pdf.add_heading("Resumen de Usuarios")
    pdf.add_paragraph(f"Total de usuarios: <b>{data.get('total', 0)}</b>")
    pdf.add_paragraph(f"Activos: <b>{data.get('active', 0)}</b> | Inactivos: <b>{data.get('inactive', 0)}</b> | Staff: <b>{data.get('staff', 0)}</b>")
    pdf.add_spacer(0.2)
    
    # Tabla de usuarios recientes
    if data.get('recent_users'):
        pdf.add_heading("Usuarios Registrados")
        table_data = [['Nombre', 'Email', 'Rol', 'Estado']]
        for user in data['recent_users'][:20]:
            full_name = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()
            role = 'Staff' if user.get('is_staff') else 'Usuario'
            status = 'Activo' if user.get('is_active') else 'Inactivo'
            table_data.append([
                full_name or 'N/A',
                user.get('email', '')[:30],
                role,
                status
            ])
        pdf._add_table_old(table_data)
    
    return pdf.generate()


def generate_patients_report(data, tenant_name, user_name):
    """Generar reporte de pacientes"""
    pdf = PDFReportGenerator(title="Reporte de Pacientes")
    
    # Título y metadata
    pdf.add_title()
    pdf.add_metadata(tenant_name, user_name)
    
    # Resumen
    pdf.add_heading("Resumen de Pacientes")
    pdf.add_paragraph(f"Total de pacientes: <b>{data.get('total', 0)}</b>")
    pdf.add_spacer(0.2)
    
    # Tabla de pacientes recientes
    if data.get('recent_patients'):
        pdf.add_heading("Pacientes Registrados")
        table_data = [['Nombre', 'Género', 'Fecha de Nacimiento', 'Email']]
        for patient in data['recent_patients'][:20]:
            full_name = patient.get('full_name', 'N/A')
            
            # Convertir date_of_birth a string si es necesario
            dob = patient.get('date_of_birth', '')
            dob_str = str(dob)[:10] if dob else '-'
            
            table_data.append([
                full_name,
                patient.get('gender', '')[:1] if patient.get('gender') else '-',
                dob_str,
                patient.get('email', '')[:30] if patient.get('email') else '-'
            ])
        pdf._add_table_old(table_data)
    
    return pdf.generate()


def generate_clinical_records_report(data, tenant_name, user_name):
    """Generar reporte de historias clínicas"""
    pdf = PDFReportGenerator(title="Reporte de Historias Clínicas")
    
    # Título y metadata
    pdf.add_title()
    pdf.add_metadata(tenant_name, user_name)
    
    # Resumen
    pdf.add_heading("Resumen de Historias Clínicas")
    pdf.add_paragraph(f"Total de historias: <b>{data.get('total', 0)}</b>")
    pdf.add_spacer(0.2)
    
    # Tabla de historias recientes
    if data.get('recent_records'):
        pdf.add_heading("Historias Clínicas Recientes")
        table_data = [['Paciente', 'Estado', 'Fecha', 'Notas']]
        for record in data['recent_records'][:20]:
            # Convertir datetime a string si es necesario
            created_at = record.get('created_at', '')
            created_at_str = str(created_at)[:10] if created_at else '-'
            
            table_data.append([
                record.get('patient_name', 'N/A')[:30] if record.get('patient_name') else 'N/A',
                record.get('status', '-')[:15],
                created_at_str,
                str(record.get('notes', ''))[:40] if record.get('notes') else '-'
            ])
        pdf._add_table_old(table_data)
    
    return pdf.generate()


def generate_audit_report(data, tenant_name, user_name):
    """Generar reporte de auditoría"""
    pdf = PDFReportGenerator(title="Reporte de Auditoría")
    
    # Título y metadata
    pdf.add_title()
    pdf.add_metadata(tenant_name, user_name)
    
    # Resumen
    pdf.add_heading("Resumen de Auditoría")
    pdf.add_paragraph(f"Total de registros: <b>{data.get('total', 0)}</b>")
    pdf.add_spacer(0.2)
    
    # Tabla de logs recientes
    if data.get('recent_logs'):
        pdf.add_heading("Logs de Auditoría Recientes")
        table_data = [['Fecha', 'Acción', 'Recurso', 'Descripción']]
        for log in data['recent_logs'][:20]:
            # Convertir datetime a string si es necesario
            timestamp = log.get('timestamp', '')
            timestamp_str = str(timestamp)[:10] if timestamp else '-'
            
            table_data.append([
                timestamp_str,
                log.get('action', '-')[:15],
                log.get('resource_type', '-')[:20],
                str(log.get('description', ''))[:30] if log.get('description') else '-'
            ])
        pdf._add_table_old(table_data)
    
    return pdf.generate()


def generate_analytics_report(data, tenant_name, user_name):
    """Generar reporte de analíticas"""
    pdf = PDFReportGenerator(title="Reporte de Analíticas")
    
    # Título y metadata
    pdf.add_title()
    pdf.add_metadata(tenant_name, user_name)
    
    # Resumen general
    pdf.add_heading("Resumen General")
    if data.get('general_summary'):
        summary = data['general_summary']
        pdf.add_paragraph(f"Documentos: <b>{summary.get('documents', 0)}</b>")
        pdf.add_paragraph(f"Pacientes: <b>{summary.get('patients', 0)}</b>")
        pdf.add_paragraph(f"Historias Clínicas: <b>{summary.get('clinical_records', 0)}</b>")
        pdf.add_paragraph(f"Usuarios: <b>{summary.get('users', 0)}</b>")
    pdf.add_spacer(0.2)
    
    # Resumen de usuarios
    if data.get('users_summary'):
        pdf.add_heading("Resumen de Usuarios")
        users = data['users_summary']
        pdf.add_paragraph(f"Activos: <b>{users.get('active', 0)}</b> | Inactivos: <b>{users.get('inactive', 0)}</b> | Total: <b>{users.get('total', 0)}</b>")
    
    return pdf.generate()
