"""
Script para probar el procesamiento automático de OCR
Ejecutar: python test_ocr_processing.py
"""
import os
import django
import sys

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')
django.setup()

from apps.documents.tasks import process_document_ocr
from apps.documents.models import ClinicalDocument
from django.contrib.auth import get_user_model

User = get_user_model()


def test_ocr_task_manual():
    """Test 1: Ejecutar tarea OCR manualmente (sin Celery)"""
    print("=" * 60)
    print("TEST 1: Ejecutar tarea OCR manualmente")
    print("=" * 60)
    
    # Buscar documentos con archivo que no tengan OCR procesado
    documents = ClinicalDocument.objects.filter(
        file_path__isnull=False,
        ocr_processed=False
    ).exclude(file_path='')[:5]
    
    if not documents.exists():
        print("⚠ No hay documentos sin procesar")
        print("  Sube un documento PDF o imagen primero")
        return
    
    for doc in documents:
        print(f"\n📄 Documento: {doc.title}")
        print(f"   ID: {doc.id}")
        print(f"   Tipo: {doc.mime_type}")
        print(f"   Archivo: {doc.file_path}")
        print(f"   Estado OCR: {doc.ocr_status}")
        
        # Ejecutar tarea manualmente (sin Celery)
        print("   🔄 Procesando OCR...")
        try:
            result = process_document_ocr(str(doc.id))
            
            # Recargar documento
            doc.refresh_from_db()
            
            if result.get('success'):
                print(f"   ✓ OCR completado")
                print(f"   ✓ Texto extraído: {len(doc.ocr_text)} caracteres")
                print(f"   ✓ Confianza: {doc.ocr_confidence}%")
                print(f"   ✓ Estado: {doc.ocr_status}")
            else:
                print(f"   ✗ OCR falló: {result.get('error')}")
                
        except Exception as e:
            print(f"   ✗ Error: {str(e)}")


def test_celery_task_async():
    """Test 2: Lanzar tarea OCR con Celery (asíncrona)"""
    print("\n")
    print("=" * 60)
    print("TEST 2: Lanzar tarea OCR con Celery (asíncrona)")
    print("=" * 60)
    
    # Buscar documentos pendientes
    documents = ClinicalDocument.objects.filter(
        file_path__isnull=False,
        ocr_status='pending'
    ).exclude(file_path='')[:3]
    
    if not documents.exists():
        print("⚠ No hay documentos pendientes")
        return
    
    print(f"\n📋 Documentos pendientes: {documents.count()}")
    
    for doc in documents:
        print(f"\n📄 Lanzando OCR para: {doc.title}")
        
        try:
            # Lanzar tarea asíncrona
            task = process_document_ocr.delay(str(doc.id))
            
            print(f"   ✓ Tarea lanzada: {task.id}")
            print(f"   ✓ Estado: {task.state}")
            print(f"   ℹ  La tarea se procesará en background")
            print(f"   ℹ  Verifica los logs de Celery worker")
            
        except Exception as e:
            print(f"   ✗ Error: {str(e)}")


def test_ocr_status():
    """Test 3: Verificar estado de documentos con OCR"""
    print("\n")
    print("=" * 60)
    print("TEST 3: Estado de documentos con OCR")
    print("=" * 60)
    
    # Contar por estado
    from django.db.models import Count
    
    status_counts = ClinicalDocument.objects.values('ocr_status').annotate(
        count=Count('id')
    ).order_by('ocr_status')
    
    print("\n📊 Resumen de estados:")
    for status in status_counts:
        print(f"   {status['ocr_status']}: {status['count']} documentos")
    
    # Mostrar últimos procesados
    print("\n📄 Últimos documentos procesados:")
    completed = ClinicalDocument.objects.filter(
        ocr_status='completed'
    ).order_by('-updated_at')[:5]
    
    for doc in completed:
        print(f"\n   ✓ {doc.title}")
        print(f"     Confianza: {doc.ocr_confidence}%")
        print(f"     Texto: {len(doc.ocr_text)} caracteres")
        print(f"     Preview: {doc.ocr_text[:100]}...")


def main():
    """Ejecutar todos los tests"""
    print("\n")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║         VERIFICACIÓN DE PROCESAMIENTO OCR AUTOMÁTICO      ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print("\n")
    
    print("⚠️  IMPORTANTE:")
    print("   - Asegúrate de que Celery worker esté corriendo:")
    print("     celery -A config worker -l info")
    print("   - Asegúrate de que Redis esté corriendo")
    print("   - AWS Textract debe estar configurado en .env")
    print("\n")
    
    # Test 1: Manual
    test_ocr_task_manual()
    
    # Test 2: Asíncrono (requiere Celery)
    input("\n⏸️  Presiona ENTER para probar Celery asíncrono...")
    test_celery_task_async()
    
    # Test 3: Estado
    input("\n⏸️  Presiona ENTER para ver el estado de los documentos...")
    test_ocr_status()
    
    # Resumen
    print("\n")
    print("=" * 60)
    print("RESUMEN")
    print("=" * 60)
    print("✅ Si el Test 1 funcionó: OCR está configurado correctamente")
    print("✅ Si el Test 2 funcionó: Celery está funcionando")
    print("✅ Si ves documentos 'completed': El procesamiento automático está OK")
    print("\n")
    print("🎯 SIGUIENTE PASO:")
    print("   - Sube un documento PDF o imagen desde el frontend")
    print("   - El OCR debería procesarse automáticamente")
    print("   - Verifica en los logs de Celery")
    print("\n")


if __name__ == '__main__':
    main()
