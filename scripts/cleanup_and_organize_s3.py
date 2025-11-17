"""
Script para limpiar y organizar archivos en S3 por tenants
Estructura deseada:
  - {tenant_id}/documents/{document_id}.{ext}
  - {tenant_id}/images/{image_id}.{ext}
  - {tenant_id}/backups/{backup_name}.zip
"""
import os
import django
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')
django.setup()

import boto3
from django.conf import settings
from apps.documents.models import ClinicalDocument, MedicalImage

def list_all_s3_files():
    """Listar todos los archivos en S3"""
    print("=" * 60)
    print("LISTANDO ARCHIVOS EN S3")
    print("=" * 60)
    
    s3_client = boto3.client(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME
    )
    
    bucket = settings.AWS_STORAGE_BUCKET_NAME
    
    try:
        response = s3_client.list_objects_v2(Bucket=bucket)
        
        if 'Contents' not in response:
            print("✓ Bucket vacío o sin archivos")
            return []
        
        files = response['Contents']
        print(f"\n📊 Total de archivos: {len(files)}")
        
        # Agrupar por carpeta
        folders = {}
        for file in files:
            key = file['Key']
            folder = key.split('/')[0] if '/' in key else 'root'
            
            if folder not in folders:
                folders[folder] = []
            folders[folder].append({
                'key': key,
                'size': file['Size'],
                'last_modified': file['LastModified']
            })
        
        print("\n📁 Estructura actual:")
        for folder, items in sorted(folders.items()):
            total_size = sum(f['size'] for f in items)
            print(f"\n  {folder}/")
            print(f"    Archivos: {len(items)}")
            print(f"    Tamaño total: {total_size / 1024 / 1024:.2f} MB")
            
            # Mostrar primeros 5 archivos
            for item in items[:5]:
                print(f"      - {item['key']} ({item['size'] / 1024:.1f} KB)")
            
            if len(items) > 5:
                print(f"      ... y {len(items) - 5} más")
        
        return files
        
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return []


def check_database_structure():
    """Verificar cómo están organizados los documentos en la DB"""
    print("\n")
    print("=" * 60)
    print("ESTRUCTURA EN BASE DE DATOS")
    print("=" * 60)
    
    # Documentos clínicos
    docs = ClinicalDocument.objects.all()
    print(f"\n📄 Documentos Clínicos: {docs.count()}")
    
    if docs.exists():
        print("\n  Primeros 5 file_paths:")
        for doc in docs[:5]:
            if doc.file_path:
                print(f"    {doc.file_path}")
    
    # Imágenes médicas
    images = MedicalImage.objects.all()
    print(f"\n🖼️  Imágenes Médicas: {images.count()}")
    
    if images.exists():
        print("\n  Primeros 5 file_paths:")
        for img in images[:5]:
            if img.original_file:
                print(f"    {img.original_file}")


def verify_tenant_organization():
    """Verificar si los archivos ya están organizados por tenant"""
    print("\n")
    print("=" * 60)
    print("VERIFICACIÓN DE ORGANIZACIÓN POR TENANT")
    print("=" * 60)
    
    # Verificar documentos
    docs = ClinicalDocument.objects.filter(file_path__isnull=False).exclude(file_path='')
    
    organized = 0
    not_organized = 0
    
    print(f"\n🔍 Analizando {docs.count()} documentos...")
    
    for doc in docs:
        # Verificar si el file_path incluye tenant_id
        if str(doc.tenant_id) in doc.file_path:
            organized += 1
        else:
            not_organized += 1
    
    print(f"\n✓ Organizados por tenant: {organized}")
    print(f"⚠ No organizados: {not_organized}")
    
    if not_organized == 0:
        print("\n✅ ¡Todos los archivos ya están organizados por tenant!")
        return True
    else:
        print(f"\n⚠️  {not_organized} archivos necesitan reorganización")
        return False


def cleanup_test_files():
    """Eliminar archivos de prueba"""
    print("\n")
    print("=" * 60)
    print("LIMPIEZA DE ARCHIVOS DE PRUEBA")
    print("=" * 60)
    
    s3_client = boto3.client(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME
    )
    
    bucket = settings.AWS_STORAGE_BUCKET_NAME
    
    # Buscar archivos de prueba
    test_patterns = ['test_', 'Test', 'prueba', 'Prueba']
    
    try:
        response = s3_client.list_objects_v2(Bucket=bucket)
        
        if 'Contents' not in response:
            print("✓ No hay archivos para limpiar")
            return
        
        files_to_delete = []
        
        for obj in response['Contents']:
            key = obj['Key']
            # Verificar si es archivo de prueba
            if any(pattern in key for pattern in test_patterns):
                files_to_delete.append(key)
        
        if not files_to_delete:
            print("✓ No se encontraron archivos de prueba")
            return
        
        print(f"\n📋 Archivos de prueba encontrados: {len(files_to_delete)}")
        for key in files_to_delete[:10]:
            print(f"  - {key}")
        
        if len(files_to_delete) > 10:
            print(f"  ... y {len(files_to_delete) - 10} más")
        
        respuesta = input(f"\n⚠️  ¿Eliminar {len(files_to_delete)} archivos de prueba? (s/n): ")
        
        if respuesta.lower() == 's':
            print("\n🗑️  Eliminando archivos...")
            
            for key in files_to_delete:
                try:
                    s3_client.delete_object(Bucket=bucket, Key=key)
                    print(f"  ✓ Eliminado: {key}")
                except Exception as e:
                    print(f"  ✗ Error eliminando {key}: {str(e)}")
            
            print(f"\n✅ {len(files_to_delete)} archivos eliminados")
        else:
            print("\n⏭️  Limpieza cancelada")
        
    except Exception as e:
        print(f"✗ Error: {str(e)}")


def main():
    print("\n")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║          LIMPIEZA Y ORGANIZACIÓN DE S3 POR TENANTS        ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print("\n")
    
    # 1. Listar archivos actuales
    files = list_all_s3_files()
    
    # 2. Verificar estructura en DB
    check_database_structure()
    
    # 3. Verificar organización por tenant
    is_organized = verify_tenant_organization()
    
    # 4. Limpieza de archivos de prueba
    if files:
        input("\n⏸️  Presiona ENTER para continuar con la limpieza...")
        cleanup_test_files()
    
    # Resumen
    print("\n")
    print("=" * 60)
    print("RESUMEN")
    print("=" * 60)
    
    if is_organized:
        print("✅ Los archivos YA están organizados por tenant")
        print("✅ La estructura actual es óptima:")
        print("   documents/{tenant_id}/{document_id}.{ext}")
    else:
        print("⚠️  Se recomienda reorganizar los archivos")
        print("   Ejecuta el script de migración si es necesario")
    
    print("\n💡 RECOMENDACIONES:")
    print("  - Los archivos por tenant facilitan el manejo de permisos")
    print("  - Mejora la organización y búsqueda")
    print("  - Permite eliminar todo de un tenant fácilmente")
    print()


if __name__ == '__main__':
    main()
