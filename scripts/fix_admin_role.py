#!/usr/bin/env python
"""
Script para verificar y corregir el role del usuario admin.

Uso:
    python scripts/fix_admin_role.py

Ejecutar desde el directorio cr_backend/
"""
import os
import sys
import django

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.accounts.models import User, Role


def fix_admin_role():
    """Verifica y muestra información sobre roles y usuario admin."""
    
    print("=" * 80)
    print("🔍 VERIFICACIÓN DE ROLES Y USUARIO ADMIN")
    print("=" * 80)
    
    # 1. Obtener el usuario admin
    try:
        user = User.objects.get(email='admin@clinica-lapaz.com')
        print(f"\n✅ Usuario encontrado: {user.full_name}")
        print(f"   Email: {user.email}")
        print(f"   Role ID: {user.role.id if user.role else 'None'}")
        print(f"   Role Name: {user.role.name if user.role else 'None'}")
        print(f"   Tenant: {user.tenant.name if user.tenant else 'None'}")
    except User.DoesNotExist:
        print("\n❌ Usuario admin@clinica-lapaz.com no encontrado")
        return False
    
    # 2. Listar todos los roles del tenant
    print(f"\n📋 ROLES EN EL TENANT '{user.tenant.name}':")
    print("-" * 80)
    roles = Role.objects.filter(tenant=user.tenant)
    for role in roles:
        user_count = User.objects.filter(role=role).count()
        print(f"   - {role.name:<30} (ID: {role.id}) → {user_count} usuarios")
    
    # 3. Buscar rol de administrador
    print(f"\n🔍 BUSCANDO ROLES DE ADMINISTRADOR:")
    print("-" * 80)
    admin_roles = Role.objects.filter(
        tenant=user.tenant,
        name__in=['Administrador', 'Admin TI', 'Administrador TI']
    )
    
    for role in admin_roles:
        users = User.objects.filter(role=role)
        print(f"   ✅ Encontrado: {role.name}")
        print(f"      Usuarios: {', '.join([u.email for u in users])}")
    
    if not admin_roles.exists():
        print("   ❌ NO se encontraron roles de administrador")
        print("   El código busca: ['Administrador', 'Admin TI']")
        print(f"   Pero el usuario tiene: '{user.role.name}'")
        
        # Sugerir solución
        print(f"\n💡 SOLUCIÓN SUGERIDA:")
        print(f"   Cambiar el nombre del rol '{user.role.name}' a 'Administrador TI'")
        print(f"   O actualizar el código para incluir '{user.role.name}'")
    
    # 4. Verificar token FCM
    print(f"\n📱 TOKEN FCM:")
    print("-" * 80)
    if user.fcm_token:
        print(f"   ✅ Token guardado ({len(user.fcm_token)} caracteres)")
        print(f"   {user.fcm_token[:50]}...")
    else:
        print(f"   ❌ Token NO guardado")
    
    print("\n" + "=" * 80)
    return True


if __name__ == "__main__":
    fix_admin_role()
