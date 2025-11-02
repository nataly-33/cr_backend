import csv
from io import StringIO


def generate_documents_csv(data):
    """Generar reporte de documentos en CSV"""
    output = StringIO()
    
    if data.get('recent_documents'):
        writer = csv.writer(output)
        
        # Headers
        writer.writerow(['Fecha', 'Tipo', 'Paciente', 'Doctor', 'Especialidad', 'Título'])
        
        # Datos
        for doc in data['recent_documents']:
            writer.writerow([
                doc.get('document_date', '')[:10],
                doc.get('document_type', ''),
                doc.get('patient_name', ''),
                doc.get('doctor_name', ''),
                doc.get('specialty', ''),
                doc.get('title', '')
            ])
    
    return output.getvalue()