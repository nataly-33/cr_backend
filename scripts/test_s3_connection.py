"""
Script para verificar conexión a S3 y probar upload/download
Ejecutar: python test_s3_connection.py
"""
import os
import django
import sys

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')
django.setup()

from apps.documents.storage import S3Storage
from django.core.files.base import ContentFile
from django.conf import settings


def test_s3_configuration():
    """Test 1: Verificar configuración de S3"""
    print("=" * 60)
    print("TEST 1: Verificar configuración de S3")
    print("=" * 60)
    
    print(f"✓ AWS_ACCESS_KEY_ID configurado: {bool(getattr(settings, 'AWS_ACCESS_KEY_ID', None))}")
    print(f"✓ AWS_SECRET_ACCESS_KEY configurado: {bool(getattr(settings, 'AWS_SECRET_ACCESS_KEY', None))}")
    print(f"✓ AWS_STORAGE_BUCKET_NAME: {getattr(settings, 'AWS_STORAGE_BUCKET_NAME', 'No configurado')}")
    print(f"✓ AWS_S3_REGION_NAME: {getattr(settings, 'AWS_S3_REGION_NAME', 'No configurado')}")
    print()


def test_s3_storage_initialization():
    """Test 2: Inicializar S3Storage"""
    print("=" * 60)
    print("TEST 2: Inicializar S3Storage")
    print("=" * 60)
    
    try:
        storage = S3Storage()
        print(f"✓ S3Storage inicializado correctamente")
        print(f"✓ Usando S3: {storage.use_s3}")
        
        if storage.use_s3:
            print(f"✓ Bucket configurado: {storage.bucket_name}")
            print(f"✓ Cliente S3 creado: {bool(storage.s3_client)}")
        else:
            print("⚠ ADVERTENCIA: No está usando S3, está en modo local")
            print("  Verifica que las credenciales AWS estén en el .env")
        
        print()
        return storage
        
    except Exception as e:
        print(f"✗ ERROR al inicializar S3Storage: {str(e)}")
        print()
        return None


def test_s3_upload():
    """Test 3: Subir archivo de prueba"""
    print("=" * 60)
    print("TEST 3: Subir archivo de prueba a S3")
    print("=" * 60)
    
    try:
        storage = S3Storage()
        
        if not storage.use_s3:
            print("⚠ No se puede probar upload porque S3 no está configurado")
            print("  El archivo se guardará localmente")
            print()
        
        # Crear archivo de prueba
        test_content = b'Este es un archivo de prueba para verificar S3. Timestamp: ' + str(os.times()).encode()
        test_file = ContentFile(test_content)
        test_file.content_type = 'text/plain'
        test_file_name = 'test_s3_verification.txt'
        
        print(f"📄 Subiendo archivo: {test_file_name}")
        print(f"📦 Tamaño: {len(test_content)} bytes")
        
        # Upload
        url = storage.upload_file(test_file, test_file_name)
        
        if url:
            print(f"✓ Archivo subido exitosamente")
            print(f"✓ URL: {url}")
        else:
            print(f"✗ ERROR: No se pudo subir el archivo")
        
        print()
        return url
        
    except Exception as e:
        print(f"✗ ERROR en upload: {str(e)}")
        import traceback
        traceback.print_exc()
        print()
        return None


def test_s3_file_exists(file_path='test_s3_verification.txt'):
    """Test 4: Verificar si el archivo existe"""
    print("=" * 60)
    print("TEST 4: Verificar existencia del archivo")
    print("=" * 60)
    
    try:
        storage = S3Storage()
        exists = storage.file_exists(file_path)
        
        if exists:
            print(f"✓ El archivo '{file_path}' existe")
        else:
            print(f"✗ El archivo '{file_path}' NO existe")
        
        print()
        return exists
        
    except Exception as e:
        print(f"✗ ERROR verificando archivo: {str(e)}")
        print()
        return False


def test_s3_presigned_url(file_path='test_s3_verification.txt'):
    """Test 5: Generar URL firmada"""
    print("=" * 60)
    print("TEST 5: Generar URL firmada (presigned URL)")
    print("=" * 60)
    
    try:
        storage = S3Storage()
        url = storage.get_presigned_url(file_path, expiration=300)  # 5 minutos
        
        if url:
            print(f"✓ URL firmada generada:")
            print(f"  {url}")
            print(f"  Válida por 5 minutos")
        else:
            print(f"✗ No se pudo generar URL firmada")
        
        print()
        return url
        
    except Exception as e:
        print(f"✗ ERROR generando URL: {str(e)}")
        print()
        return None


def test_s3_delete(file_path='test_s3_verification.txt'):
    """Test 6: Eliminar archivo de prueba"""
    print("=" * 60)
    print("TEST 6: Eliminar archivo de prueba")
    print("=" * 60)
    
    try:
        storage = S3Storage()
        deleted = storage.delete_file(file_path)
        
        if deleted:
            print(f"✓ Archivo '{file_path}' eliminado correctamente")
        else:
            print(f"✗ No se pudo eliminar el archivo")
        
        print()
        return deleted
        
    except Exception as e:
        print(f"✗ ERROR eliminando archivo: {str(e)}")
        print()
        return False


def main():
    """Ejecutar todos los tests"""
    print("\n")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║        VERIFICACIÓN DE CONEXIÓN Y FUNCIONALIDAD S3        ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print("\n")
    
    # Test 1: Configuración
    test_s3_configuration()
    
    # Test 2: Inicialización
    storage = test_s3_storage_initialization()
    if not storage:
        print("❌ No se pudo continuar: Error en inicialización")
        return
    
    # Test 3: Upload
    url = test_s3_upload()
    if not url:
        print("❌ No se pudo continuar: Error en upload")
        return
    
    # Test 4: File exists
    exists = test_s3_file_exists()
    
    # Test 5: Presigned URL
    if exists:
        test_s3_presigned_url()
    
    # Test 6: Delete
    test_s3_delete()
    
    # Resumen
    print("=" * 60)
    print("RESUMEN")
    print("=" * 60)
    
    if storage.use_s3 and url:
        print("✅ S3 está configurado y funcionando correctamente")
        print("✅ Puedes usar S3 para almacenar documentos médicos")
    elif url:
        print("✅ Almacenamiento local funcionando")
        print("⚠  S3 no está configurado, usando almacenamiento local")
    else:
        print("❌ Hay problemas con el almacenamiento")
        print("   Revisa la configuración en .env")
    
    print()


if __name__ == '__main__':
    main()
