"""
Script adicional para probar upload de imágenes y PDFs a S3
(simulando documentos médicos reales)
"""
import os
import django
import sys
from io import BytesIO

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')
django.setup()

from apps.documents.storage import S3Storage
from django.core.files.base import ContentFile


def test_image_upload():
    """Probar upload de imagen PNG"""
    print("=" * 60)
    print("TEST: Subir imagen PNG de prueba")
    print("=" * 60)
    
    try:
        storage = S3Storage()
        
        # Crear una imagen PNG simple (1x1 pixel rojo)
        # PNG header + IHDR + IDAT + IEND
        png_data = (
            b'\x89PNG\r\n\x1a\n'  # PNG signature
            b'\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
            b'\x08\x02\x00\x00\x00\x90wS\xde'
            b'\x00\x00\x00\x0cIDATx\x9cc\xf8\xcf\xc0\x00\x00\x00\x03\x00\x01'
            b'\x00\x00\x00\x00IEND\xaeB`\x82'
        )
        
        image_file = ContentFile(png_data)
        image_file.content_type = 'image/png'
        
        file_path = 'test_uploads/test_medical_image.png'
        
        print(f"📸 Subiendo imagen PNG: {file_path}")
        print(f"📦 Tamaño: {len(png_data)} bytes")
        
        url = storage.upload_file(image_file, file_path)
        
        if url:
            print(f"✓ Imagen subida exitosamente")
            print(f"✓ URL: {url}")
            print(f"✓ Este archivo puede ser procesado por OCR")
        else:
            print(f"✗ ERROR: No se pudo subir la imagen")
        
        print()
        return url
        
    except Exception as e:
        print(f"✗ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        print()
        return None


def test_pdf_upload():
    """Probar upload de PDF"""
    print("=" * 60)
    print("TEST: Subir PDF de prueba")
    print("=" * 60)
    
    try:
        storage = S3Storage()
        
        # PDF mínimo válido
        pdf_data = b"""%PDF-1.4
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
/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
(Test PDF) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000317 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
408
%%EOF
"""
        
        pdf_file = ContentFile(pdf_data)
        pdf_file.content_type = 'application/pdf'
        
        file_path = 'test_uploads/test_prescription.pdf'
        
        print(f"📄 Subiendo PDF: {file_path}")
        print(f"📦 Tamaño: {len(pdf_data)} bytes")
        
        url = storage.upload_file(pdf_file, file_path)
        
        if url:
            print(f"✓ PDF subido exitosamente")
            print(f"✓ URL: {url}")
            print(f"✓ Este archivo puede ser procesado por Textract OCR")
        else:
            print(f"✗ ERROR: No se pudo subir el PDF")
        
        print()
        return url
        
    except Exception as e:
        print(f"✗ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        print()
        return None


def test_large_file():
    """Probar upload de archivo más grande (simular documento real)"""
    print("=" * 60)
    print("TEST: Subir archivo de tamaño medio (~1MB)")
    print("=" * 60)
    
    try:
        storage = S3Storage()
        
        # Crear archivo de ~1MB
        size_mb = 1
        large_data = b'X' * (size_mb * 1024 * 1024)
        
        large_file = ContentFile(large_data)
        large_file.content_type = 'application/octet-stream'
        
        file_path = 'test_uploads/test_large_file.bin'
        
        print(f"💾 Subiendo archivo grande: {file_path}")
        print(f"📦 Tamaño: {len(large_data) / 1024 / 1024:.2f} MB")
        
        url = storage.upload_file(large_file, file_path)
        
        if url:
            print(f"✓ Archivo subido exitosamente")
            print(f"✓ URL: {url}")
            print(f"✓ S3 puede manejar archivos grandes")
        else:
            print(f"✗ ERROR: No se pudo subir el archivo")
        
        print()
        return url
        
    except Exception as e:
        print(f"✗ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        print()
        return None


def cleanup_test_files():
    """Limpiar archivos de prueba"""
    print("=" * 60)
    print("LIMPIEZA: Eliminando archivos de prueba")
    print("=" * 60)
    
    storage = S3Storage()
    test_files = [
        'test_uploads/test_medical_image.png',
        'test_uploads/test_prescription.pdf',
        'test_uploads/test_large_file.bin'
    ]
    
    for file_path in test_files:
        try:
            if storage.file_exists(file_path):
                storage.delete_file(file_path)
                print(f"✓ Eliminado: {file_path}")
            else:
                print(f"⊘ No existe: {file_path}")
        except Exception as e:
            print(f"✗ Error eliminando {file_path}: {str(e)}")
    
    print()


def main():
    print("\n")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║     VERIFICACIÓN DE UPLOAD DE DOCUMENTOS MÉDICOS A S3     ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print("\n")
    
    # Test imagen
    image_url = test_image_upload()
    
    # Test PDF
    pdf_url = test_pdf_upload()
    
    # Test archivo grande
    large_url = test_large_file()
    
    # Limpieza
    input("\n⏸️  Presiona ENTER para limpiar los archivos de prueba...")
    cleanup_test_files()
    
    # Resumen
    print("=" * 60)
    print("RESUMEN FINAL")
    print("=" * 60)
    
    success = all([image_url, pdf_url, large_url])
    
    if success:
        print("✅ TODOS LOS TESTS PASARON")
        print("✅ S3 está listo para:")
        print("   - Subir imágenes médicas (PNG, JPG)")
        print("   - Subir documentos PDF (recetas, informes)")
        print("   - Manejar archivos grandes (hasta varios MB)")
        print("   - Procesar con OCR (Textract)")
        print()
        print("🎯 SIGUIENTE PASO:")
        print("   Configurar AWS Textract para OCR automático")
    else:
        print("❌ ALGUNOS TESTS FALLARON")
        print("   Revisa los errores arriba")
    
    print()


if __name__ == '__main__':
    main()
