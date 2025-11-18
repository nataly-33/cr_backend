"""
Script para verificar usuarios en la base de datos de producción
"""
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
django.setup()

from apps.accounts.models import User
from apps.core.models import Tenant
from apps.tenants.models import TenantRegistration

print("\n" + "="*80)
print("DIAGNÓSTICO DE USUARIOS - PRODUCCIÓN")
print("="*80)

# 1. Ver todas las registraciones
print("\n📋 REGISTRACIONES:")
print("-" * 80)
registrations = TenantRegistration.objects.all().order_by('-created_at')[:10]
for reg in registrations:
    print(f"ID: {reg.id}")
    print(f"  Email: {reg.admin_email}")
    print(f"  Tenant: {reg.tenant_name}")
    print(f"  Subdomain: {reg.subdomain}")
    print(f"  Status: {reg.status}")
    print(f"  Pago: {reg.payment_completed_at}")
    print(f"  Activación: {reg.activated_at}")
    print(f"  Token: {reg.activation_token[:20] if reg.activation_token else 'N/A'}...")
    print()

# 2. Ver todos los tenants
print("\n🏢 TENANTS:")
print("-" * 80)
tenants = Tenant.objects.all()
for tenant in tenants:
    print(f"ID: {tenant.id}")
    print(f"  Name: {tenant.name}")
    print(f"  Subdomain: {tenant.subdomain}")
    print(f"  Email: {tenant.email}")
    print(f"  Status: {tenant.subscription_status}")
    print()

# 3. Ver todos los usuarios
print("\n👤 USUARIOS:")
print("-" * 80)
users = User.objects.all()
if users.exists():
    for user in users:
        print(f"ID: {user.id}")
        print(f"  Email: {user.email}")
        print(f"  Personal Email: {user.personal_email}")
        print(f"  Name: {user.first_name} {user.last_name}")
        print(f"  Tenant: {user.tenant.name if user.tenant else 'N/A'}")
        print(f"  Active: {user.is_active}")
        print(f"  Role: {user.role.name if user.role else 'N/A'}")
        print()
else:
    print("⚠️  NO HAY USUARIOS EN LA BASE DE DATOS")
    print()

# 4. Verificar el usuario específico que está intentando hacer login
print("\n🔍 BUSCAR USUARIO ESPECÍFICO:")
print("-" * 80)
test_emails = [
    'admin@clinica-virginia.com',
    'vanessamartinez1@upb.edu',
    'admin@clinica-virginia',
]

for email in test_emails:
    user = User.objects.filter(email__icontains=email.split('@')[0]).first()
    if user:
        print(f"✅ Usuario encontrado con búsqueda de '{email}':")
        print(f"   Email real: {user.email}")
        print(f"   Tenant: {user.tenant.subdomain if user.tenant else 'N/A'}")
        print(f"   Active: {user.is_active}")
    else:
        print(f"❌ No se encontró usuario con '{email}'")
    print()

# 5. Mostrar BASE_DOMAIN configurado
from django.conf import settings
print("\n⚙️  CONFIGURACIÓN:")
print("-" * 80)
print(f"BASE_DOMAIN: {settings.BASE_DOMAIN}")
print(f"FRONTEND_URL: {settings.FRONTEND_URL}")
print()

print("="*80)
print("FIN DEL DIAGNÓSTICO")
print("="*80 + "\n")
