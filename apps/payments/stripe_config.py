"""
Configuración de Stripe para pagos.
"""

import os
import stripe as stripe_sdk
from django.conf import settings

# Inicializar Stripe con clave privada
stripe_sdk.api_key = getattr(settings, 'STRIPE_SECRET_KEY', os.environ.get('STRIPE_SECRET_KEY'))

# Configuraciones
STRIPE_PUBLIC_KEY = getattr(settings, 'STRIPE_PUBLIC_KEY', os.environ.get('STRIPE_PUBLIC_KEY'))
STRIPE_SECRET_KEY = getattr(settings, 'STRIPE_SECRET_KEY', os.environ.get('STRIPE_SECRET_KEY'))
STRIPE_WEBHOOK_SECRET = getattr(settings, 'STRIPE_WEBHOOK_SECRET', os.environ.get('STRIPE_WEBHOOK_SECRET'))

# URLs para redirects después del checkout
FRONTEND_URL = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173')
CHECKOUT_SUCCESS_URL = f"{FRONTEND_URL}/billing/success"
CHECKOUT_CANCEL_URL = f"{FRONTEND_URL}/billing/cancel"


def create_checkout_session(
    plan,
    tenant,
    success_url=None,
    cancel_url=None,
):
    """
    Crear una sesión de checkout con Stripe.
    
    Args:
        plan: SubscriptionPlan instance
        tenant: Tenant instance
        success_url: URL de éxito
        cancel_url: URL de cancelación
    
    Returns:
        dict: {'session_id': '...', 'url': '...'}
    """
    try:
        session = stripe_sdk.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[
                {
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': plan.name,
                            'description': plan.description or f'Plan {plan.name}',
                            'images': [plan.image_url] if hasattr(plan, 'image_url') and plan.image_url else [],
                        },
                        'unit_amount': int(plan.price_monthly * 100),  # En centavos
                    },
                    'quantity': 1,
                }
            ],
            mode='subscription',
            success_url=success_url or CHECKOUT_SUCCESS_URL + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=cancel_url or CHECKOUT_CANCEL_URL,
            client_reference_id=str(tenant.id),
            metadata={
                'tenant_id': str(tenant.id),
                'plan_id': str(plan.id),
                'plan_name': plan.name,
            },
        )
        
        return {
            'session_id': session.id,
            'url': session.url,
        }
    except stripe_sdk.error.StripeError as e:
        raise Exception(f'Error creando sesión de checkout: {str(e)}')


def verify_webhook_signature(payload, sig_header):
    """
    Verificar que el webhook venga de Stripe.
    
    Args:
        payload: Body del request (raw)
        sig_header: Valor del header 'stripe-signature'
    
    Returns:
        dict: Evento de Stripe desencriptado
    
    Raises:
        Exception: Si la firma no es válida
    """
    try:
        event = stripe_sdk.Webhook.construct_event(
            payload,
            sig_header,
            STRIPE_WEBHOOK_SECRET,
        )
        return event
    except ValueError:
        raise Exception('Payload inválido')
    except stripe_sdk.error.SignatureVerificationError:
        raise Exception('Firma de webhook no válida')


def handle_checkout_session_completed(session):
    """
    Manejar el evento checkout.session.completed de Stripe.
    
    Args:
        session: Datos de la sesión de Stripe
    
    Returns:
        dict: {'success': True/False, 'data': {...}}
    """
    try:
        tenant_id = session.get('metadata', {}).get('tenant_id')
        plan_id = session.get('metadata', {}).get('plan_id')
        
        if not tenant_id or not plan_id:
            raise Exception('Metadata incompleta en sesión')
        
        return {
            'success': True,
            'tenant_id': tenant_id,
            'plan_id': plan_id,
            'amount': session.get('amount_total') / 100,  # Convertir de centavos
            'currency': session.get('currency', 'usd').upper(),
            'stripe_session_id': session.get('id'),
            'stripe_payment_intent_id': session.get('payment_intent'),
            'stripe_customer_id': session.get('customer'),
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
        }
