"""
Script para asignar permisos de DICOM a todos los usuarios.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from apps.accounts.models import User, UserPermission
from apps.core.models import PermissionResource

def grant_dicom_permissions():
    """Asigna permisos de DICOM a todos los usuarios del sistema."""
    
    # Obtener o crear el recurso DICOM
    dicom_resource, created = PermissionResource.objects.get_or_create(
        name='dicom',
        defaults={
            'description': 'Gestión de estudios DICOM (imágenes médicas)',
            'module': 'dicom'
        }
    )
    
    if created:
        print(f"✓ Recurso DICOM creado: {dicom_resource}")
    else:
        print(f"✓ Recurso DICOM ya existe: {dicom_resource}")
    
    # Obtener todos los usuarios activos
    users = User.objects.filter(is_active=True)
    total_users = users.count()
    
    print(f"\n📋 Se encontraron {total_users} usuarios activos\n")
    
    updated_count = 0
    created_count = 0
    
    for user in users:
        # Determinar permisos según el tipo de usuario
        if user.is_superuser or user.role == 'admin':
            # Superusuarios y administradores: todos los permisos
            permissions_data = {
                'can_view': True,
                'can_create': True,
                'can_edit': True,
                'can_delete': True,
            }
        elif user.role == 'doctor':
            # Doctores: ver, crear y editar (no eliminar)
            permissions_data = {
                'can_view': True,
                'can_create': True,
                'can_edit': True,
                'can_delete': False,
            }
        else:  # paciente u otros
            # Pacientes: solo ver
            permissions_data = {
                'can_view': True,
                'can_create': False,
                'can_edit': False,
                'can_delete': False,
            }
        
        # Crear o actualizar permisos
        permission, is_created = UserPermission.objects.update_or_create(
            user=user,
            resource=dicom_resource,
            defaults=permissions_data
        )
        
        if is_created:
            created_count += 1
            print(f"✓ Creado  - {user.email} ({user.role or 'sin rol'}) - Ver:{permissions_data['can_view']} Crear:{permissions_data['can_create']} Editar:{permissions_data['can_edit']} Eliminar:{permissions_data['can_delete']}")
        else:
            updated_count += 1
            print(f"↻ Actualizado - {user.email} ({user.role or 'sin rol'}) - Ver:{permissions_data['can_view']} Crear:{permissions_data['can_create']} Editar:{permissions_data['can_edit']} Eliminar:{permissions_data['can_delete']}")
    
    print("\n" + "="*70)
    print("=== RESUMEN ===")
    print(f"Total de usuarios procesados: {total_users}")
    print(f"Permisos creados: {created_count}")
    print(f"Permisos actualizados: {updated_count}")
    print("="*70)
    print("\n✓ Proceso completado. Recarga la aplicación web (F5).")

if __name__ == '__main__':
    grant_dicom_permissions()
