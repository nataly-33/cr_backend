from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.platypus import Image as RLImage
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime


class PDFReportGenerator:
    """Generador de reportes en PDF"""
    
    def __init__(self, title="Reporte"):
        self.title = title
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
    
    def add_paragraph(self, text):
        """Agregar párrafo"""
        self.story.append(Paragraph(text, self.styles['Normal']))
        self.story.append(Spacer(1, 0.1*inch))
    
    def add_table(self, data, col_widths=None):
        """Agregar tabla al reporte"""
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
    
    def generate(self):
        """Generar el PDF y retornar el buffer"""
        self.doc.build(self.story)
        self.buffer.seek(0)
        return self.buffer
    
    def save(self, filename):
        """Guardar el PDF en un archivo"""
        pdf = self.generate()
        with open(filename, 'wb') as f:
            f.write(pdf.read())
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
        pdf.add_table(table_data, col_widths=[4*inch, 2*inch])
    
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
        pdf.add_table(table_data)
    
    return pdf.generate()