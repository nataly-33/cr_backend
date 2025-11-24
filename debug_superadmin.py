#!/usr/bin/env python
"""Script para revisar el estado exacto del superadmin en BD"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
django.setup()

from apps.accounts.models import User

# Buscar el superadmin
superadmin = User.objects.filter(email='superadmin@clinidocs.com').first()

if superadmin:
    print(f"Email: {superadmin.email}")
    print(f"is_active (bool): {superadmin.is_active} (type: {type(superadmin.is_active).__name__})")
    print(f"is_active == True: {superadmin.is_active == True}")
    print(f"is_active is True: {superadmin.is_active is True}")
    print(f"bool(is_active): {bool(superadmin.is_active)}")
    print(f"is_superuser: {superadmin.is_superuser}")
    print(f"is_staff: {superadmin.is_staff}")
    print(f"password hash: {superadmin.password[:20]}...")
    
    # Prueba de contraseña
    test_pass = 'SuperAdmin@123'
    print(f"\nTesting password '{test_pass}':")
    print(f"check_password result: {superadmin.check_password(test_pass)}")
else:
    print("Superadmin not found!")
