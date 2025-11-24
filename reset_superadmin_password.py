#!/usr/bin/env python
"""Script para actualizar la contraseña del superadmin"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
django.setup()

from apps.accounts.models import User

# Buscar el superadmin
superadmin = User.objects.filter(email='superadmin@clinidocs.com').first()

if superadmin:
    new_password = 'SuperAdmin@123'
    superadmin.set_password(new_password)
    superadmin.save()
    
    print("Contrasena actualizada para: " + superadmin.email)
    print("Nueva contrasena: " + new_password)
    
    # Verificar
    if superadmin.check_password(new_password):
        print("Verificacion exitosa")
    else:
        print("Verificacion fallida")
else:
    print("Superadmin no encontrado")
