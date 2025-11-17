"""
Script para crear un documento de prueba y verificar que el OCR se lance automáticamente
"""
import os
import django
import sys
from io import BytesIO
from django.core.files.uploadedfile import SimpleUploadedFile

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')
django.setup()

from apps.documents.models import ClinicalDocument
from apps.clinical_records.models import ClinicalRecord
from apps.core.models import Tenant
from apps.documents.services import DocumentService
from django.contrib.auth import get_user_model

User = get_user_model()


def create_test_document_with_file():
    """Crear un documento de prueba con un archivo PDF simple"""
    print("=" * 60)
    print("TEST: Crear documento de prueba con archivo PDF")
    print("=" * 60)
    
    try:
        # Obtener datos necesarios
        tenant = Tenant.objects.first()
        if not tenant:
            print("✗ No hay tenants en la base de datos")
            return None
            
        user = User.objects.filter(tenant=tenant).first()
        if not user:
            print("✗ No hay usuarios en el tenant")
            return None
            
        clinical_record = ClinicalRecord.objects.filter(tenant=tenant).first()
        if not clinical_record:
            print("✗ No hay historias clínicas")
            return None
        
        print(f"✓ Tenant: {tenant.name}")
        print(f"✓ Usuario: {user.email}")
        print(f"✓ Historia clínica: {clinical_record.id}")
        print()
        
        # Crear PDF simple con texto
        pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/Resources <<
/Font <<
/F1 <<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
>>
>>
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj
4 0 obj
<<
/Length 125
>>
stream
BT
/F1 18 Tf
100 700 Td
(Receta Medica - Documento de Prueba) Tj
0 -30 Td
(Paciente: Juan Perez) Tj
0 -30 Td
(Medicamento: Paracetamol 500mg) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000349 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
523
%%EOF
"""
        
        # Crear archivo simulado
        pdf_file = SimpleUploadedFile(
            "receta_prueba.pdf",
            pdf_content,
            content_type="application/pdf"
        )
        
        print("📄 Creando documento...")
        
        # Crear documento
        document = ClinicalDocument.objects.create(
            tenant=tenant,
            clinical_record=clinical_record,
            document_type='prescription',
            title='Receta de Prueba - OCR Test',
            description='Documento de prueba para verificar OCR automático',
            document_date=django.utils.timezone.now(),
            doctor_name='Dr. Test',
            mime_type='application/pdf',
            created_by=user
        )
        
        print(f"✓ Documento creado: {document.id}")
        print(f"✓ Estado OCR inicial: {document.ocr_status}")
        print()
        
        # Subir archivo usando DocumentService
        print("📤 Subiendo archivo a S3...")
        doc_service = DocumentService()
        
        # Recrear el archivo porque se cierra después de leerlo
        pdf_file = SimpleUploadedFile(
            "receta_prueba.pdf",
            pdf_content,
            content_type="application/pdf"
        )
        
        success = doc_service.upload_document(document, pdf_file)
        
        if not success:
            print("✗ Error al subir el archivo")
            document.delete()
            return None
        
        print(f"✓ Archivo subido a: {document.file_path}")
        print()
        
        # Verificar que se haya lanzado el OCR
        print("🔍 Verificando que el OCR se lance automáticamente...")
        print("   (El OCR debería procesarse en background si Celery está corriendo)")
        print()
        
        # Recargar documento
        document.refresh_from_db()
        print(f"📊 Estado del documento:")
        print(f"   ID: {document.id}")
        print(f"   Archivo: {document.file_path}")
        print(f"   Estado OCR: {document.ocr_status}")
        print(f"   OCR procesado: {document.ocr_processed}")
        
        if document.ocr_text:
            print(f"   Texto extraído: {len(document.ocr_text)} caracteres")
            print(f"   Preview: {document.ocr_text[:200]}...")
        
        return document
        
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def test_manual_ocr_call(document_id):
    """Probar llamada manual a la tarea OCR"""
    print("\n")
    print("=" * 60)
    print("TEST: Llamada manual a tarea OCR")
    print("=" * 60)
    
    from apps.documents.tasks import process_document_ocr
    
    print(f"🔄 Ejecutando OCR para documento {document_id}...")
    
    try:
        # Ejecutar tarea manualmente (síncrona, sin Celery)
        result = process_document_ocr(str(document_id))
        
        print("\n📊 Resultado:")
        if result.get('success'):
            print(f"✓ OCR completado exitosamente")
            print(f"✓ Texto extraído: {result.get('text_length')} caracteres")
            print(f"✓ Confianza: {result.get('confidence')}%")
            
            # Mostrar documento actualizado
            document = ClinicalDocument.objects.get(id=document_id)
            print(f"\n📄 Documento actualizado:")
            print(f"   Estado: {document.ocr_status}")
            print(f"   Texto: {document.ocr_text[:300]}...")
            
        else:
            print(f"✗ OCR falló: {result.get('error')}")
            
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()


def main():
    print("\n")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║       TEST DE PROCESAMIENTO OCR AUTOMÁTICO CON S3         ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print("\n")
    
    # Crear documento de prueba
    document = create_test_document_with_file()
    
    if not document:
        print("\n❌ No se pudo crear el documento de prueba")
        return
    
    print("\n" + "=" * 60)
    print("✅ Documento creado exitosamente")
    print("=" * 60)
    
    # Preguntar si ejecutar OCR manual
    print("\n📌 OPCIONES:")
    print("1. El OCR se procesará automáticamente si Celery está corriendo")
    print("2. Puedes ejecutar el OCR manualmente ahora (sin Celery)")
    print()
    
    respuesta = input("¿Ejecutar OCR manualmente ahora? (s/n): ")
    
    if respuesta.lower() == 's':
        test_manual_ocr_call(document.id)
    else:
        print("\n⏳ El OCR se procesará en background si Celery está corriendo")
        print(f"   Verifica el estado del documento con ID: {document.id}")
        print("\n   Para ver el estado, ejecuta:")
        print(f"   python manage.py shell")
        print(f"   >>> from apps.documents.models import ClinicalDocument")
        print(f"   >>> doc = ClinicalDocument.objects.get(id='{document.id}')")
        print(f"   >>> print(doc.ocr_status, doc.ocr_text)")
    
    print("\n")


if __name__ == '__main__':
    main()
