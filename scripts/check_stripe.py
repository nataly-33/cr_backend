#!/usr/bin/env python
"""
Script para verificar la configuración de Stripe en el servidor
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
django.setup()

from django.conf import settings
import stripe

print("=" * 80)
print("🔍 DIAGNÓSTICO DE STRIPE")
print("=" * 80)

# 1. Verificar variables de entorno
print("\n1️⃣ VARIABLES DE ENTORNO:")
print("-" * 80)

stripe_enabled = getattr(settings, 'STRIPE_ENABLED', False)
print(f"STRIPE_ENABLED: {stripe_enabled}")

if hasattr(settings, 'STRIPE_SECRET_KEY'):
    key = settings.STRIPE_SECRET_KEY
    if key:
        masked = key[:7] + "..." + key[-4:] if len(key) > 15 else "***"
        print(f"STRIPE_SECRET_KEY: {masked}")
    else:
        print("STRIPE_SECRET_KEY: ❌ NO CONFIGURADA")
else:
    print("STRIPE_SECRET_KEY: ❌ NO EXISTE EN SETTINGS")

if hasattr(settings, 'STRIPE_PUBLISHABLE_KEY'):
    pub_key = settings.STRIPE_PUBLISHABLE_KEY
    if pub_key:
        masked_pub = pub_key[:7] + "..." + pub_key[-4:] if len(pub_key) > 15 else "***"
        print(f"STRIPE_PUBLISHABLE_KEY: {masked_pub}")
    else:
        print("STRIPE_PUBLISHABLE_KEY: ❌ NO CONFIGURADA")
else:
    print("STRIPE_PUBLISHABLE_KEY: ❌ NO EXISTE EN SETTINGS")

if hasattr(settings, 'FRONTEND_URL'):
    print(f"FRONTEND_URL: {settings.FRONTEND_URL}")
else:
    print("FRONTEND_URL: ❌ NO CONFIGURADA")

# 2. Probar conexión con Stripe
print("\n2️⃣ PRUEBA DE CONEXIÓN CON STRIPE:")
print("-" * 80)

if stripe_enabled and hasattr(settings, 'STRIPE_SECRET_KEY') and settings.STRIPE_SECRET_KEY:
    try:
        stripe.api_key = settings.STRIPE_SECRET_KEY
        
        # Intentar listar los últimos productos (sin crear nada)
        products = stripe.Product.list(limit=1)
        print("✅ Conexión con Stripe API exitosa")
        print(f"   Modo: {'TEST' if 'test' in settings.STRIPE_SECRET_KEY else 'LIVE'}")
        
        # Intentar obtener información de la cuenta
        try:
            account = stripe.Account.retrieve()
            print(f"   Cuenta: {account.get('email', 'N/A')}")
        except:
            print("   (No se pudo obtener info de cuenta)")
            
    except stripe.error.AuthenticationError as e:
        print(f"❌ Error de autenticación: {str(e)}")
        print("   La API key de Stripe parece ser inválida")
    except Exception as e:
        print(f"❌ Error al conectar con Stripe: {str(e)}")
else:
    print("❌ Stripe no está habilitado o faltan credenciales")

# 3. Verificar endpoints de tenants
print("\n3️⃣ ENDPOINTS DE TENANTS:")
print("-" * 80)

try:
    from django.urls import resolve, reverse
    from apps.tenants.models import SubscriptionPlan
    
    # Verificar que existan planes
    plans_count = SubscriptionPlan.objects.filter(is_active=True).count()
    print(f"Planes activos: {plans_count}")
    
    if plans_count > 0:
        plan = SubscriptionPlan.objects.filter(is_active=True).first()
        print(f"  - {plan.name}: ${plan.monthly_price}/mes")
    
    # Verificar rutas
    try:
        from django.urls import get_resolver
        resolver = get_resolver()
        
        # Buscar rutas de checkout
        for pattern in resolver.url_patterns:
            pattern_str = str(pattern.pattern)
            if 'checkout' in pattern_str.lower():
                print(f"✅ Ruta encontrada: {pattern_str}")
    except:
        pass
        
except Exception as e:
    print(f"❌ Error: {str(e)}")

# 4. Simular creación de sesión (sin ejecutar)
print("\n4️⃣ SIMULACIÓN DE CHECKOUT:")
print("-" * 80)

if stripe_enabled and hasattr(settings, 'STRIPE_SECRET_KEY') and settings.STRIPE_SECRET_KEY:
    print("Configuración para sesión de checkout:")
    print(f"  success_url: {settings.FRONTEND_URL}/billing/success?session_id={{CHECKOUT_SESSION_ID}}")
    print(f"  cancel_url: {settings.FRONTEND_URL}/billing/cancel")
    print(f"  payment_method_types: ['card']")
    print(f"  mode: 'payment'")
    print("\n✅ La configuración parece correcta")
else:
    print("❌ No se puede crear sesión de checkout - Stripe no configurado")

print("\n" + "=" * 80)
print("FIN DEL DIAGNÓSTICO")
print("=" * 80)
