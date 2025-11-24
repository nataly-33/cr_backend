#!/usr/bin/env python
"""Script para verificar el estado del superadmin"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
django.setup()

from apps.accounts.models import User
from django.contrib.auth import authenticate

# Buscar el superadmin
superadmin = User.objects.filter(email='superadmin@clinidocs.com').first()

if superadmin:
    print(f"✓ Usuario: {superadmin.email}")
    print(f"  - is_active: {superadmin.is_active}")
    print(f"  - is_superuser: {superadmin.is_superuser}")
    print(f"  - is_staff: {superadmin.is_staff}")
    print(f"  - tenant: {superadmin.tenant}")
    print(f"  - has_usable_password: {superadmin.has_usable_password()}")
    
    # Intentar autenticar
    print("\nIntentando autenticar...")
    user = authenticate(username='superadmin@clinidocs.com', password='SuperAdmin@123')
    if user:
        print(f"✓ Autenticación exitosa")
    else:
        print(f"✗ Autenticación fallida")
        
        # Intentar con check_password
        print("\nVerificando contraseña directamente...")
        if superadmin.check_password('SuperAdmin@123'):
            print(f"✓ Contraseña correcta")
        else:
            print(f"✗ Contraseña incorrecta")
else:
    print("✗ Superadmin no encontrado")
