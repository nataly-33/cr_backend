"""
ViewSets para pagos y facturación con Stripe.
"""

import logging
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.utils import timezone
from rest_framework import viewsets, status, permissions, views
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from django.db import transaction

from apps.core.permissions import IsTenantMember, HasPermission, PermissionByActionMixin
from apps.core.models import Tenant
from apps.tenants.models import SubscriptionPlan
from .models import Payment, Invoice, PaymentAudit, PaymentStatus, InvoiceStatus
from .serializers import (
    PaymentSerializer,
    PaymentCreateSerializer,
    InvoiceSerializer,
    InvoiceCreateSerializer,
    PaymentAuditSerializer,
)
from .stripe_config import (
    create_checkout_session,
    verify_webhook_signature,
    handle_checkout_session_completed,
)
from apps.audit.mixins import AuditMixin

logger = logging.getLogger(__name__)


@extend_schema(tags=['Payments'])
class PaymentViewSet(AuditMixin, PermissionByActionMixin, viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para pagos.
    
    Endpoints:
    - GET /payments/ - Listar pagos del tenant
    - GET /payments/{id}/ - Detalle de pago
    """
    
    permission_classes = [IsTenantMember, HasPermission]
    resource_name = 'payment'
    filterset_fields = ['status', 'subscription_plan']
    ordering_fields = ['created_at', 'paid_at']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return PaymentCreateSerializer
        return PaymentSerializer
    
    def get_queryset(self):
        """Filtrar pagos del tenant actual."""
        return Payment.objects.filter(tenant=self.request.tenant)


@extend_schema(tags=['Payments - Checkout'])
class CheckoutSessionViewSet(views.APIView):
    """
    Crear sesión de checkout con Stripe.
    
    Endpoint:
    - POST /payments/checkout/ - Crear sesión
    """
    
    permission_classes = [IsTenantMember]
    
    def post(self, request):
        """
        Crear una sesión de checkout.
        
        Payload:
        {
            "plan_id": "uuid-del-plan"
        }
        
        Response:
        {
            "session_id": "...",
            "url": "https://checkout.stripe.com/..."
        }
        """
        try:
            plan_id = request.data.get('plan_id')
            
            if not plan_id:
                return Response(
                    {'error': 'plan_id es requerido'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Obtener plan
            try:
                plan = SubscriptionPlan.objects.get(id=plan_id)
            except SubscriptionPlan.DoesNotExist:
                return Response(
                    {'error': 'Plan no encontrado'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Crear sesión
            session_data = create_checkout_session(
                plan=plan,
                tenant=request.tenant,
            )
            
            return Response(session_data, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            logger.error(f'Error creando sesión de checkout: {str(e)}')
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


@extend_schema(tags=['Payments - Webhooks'])
@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookViewSet(views.APIView):
    """
    Webhook para recibir eventos de Stripe.
    
    Endpoint:
    - POST /payments/webhook/ - Recibir webhook
    """
    
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """
        Procesar webhook de Stripe.
        
        Requiere header: Stripe-Signature
        """
        try:
            payload = request.body
            sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')
            
            # Verificar firma
            event = verify_webhook_signature(payload, sig_header)
            
            # Manejar evento
            event_type = event['type']
            event_data = event['data']['object']
            event_id = event['id']
            
            logger.info(f'Webhook recibido: {event_type} (event_id: {event_id})')
            
            # Verificar si ya procesamos este evento (deduplicación)
            if PaymentAudit.objects.filter(webhook_event_id=event_id).exists():
                logger.warning(f'Evento duplicado, ignorando: {event_id}')
                return Response({'status': 'duplicate'}, status=status.HTTP_200_OK)
            
            if event_type == 'checkout.session.completed':
                return self._handle_checkout_completed(event_data, event_id)
            
            elif event_type == 'charge.refunded':
                return self._handle_charge_refunded(event_data, event_id)
            
            else:
                logger.warning(f'Evento no manejado: {event_type}')
                return Response({'status': 'ignored'}, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(f'Error procesando webhook: {str(e)}')
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def _handle_checkout_completed(self, session, event_id):
        """
        Manejar checkout.session.completed.
        
        Soporta 2 flujos:
        1. Pago de suscripción existente (tenant_id + plan_id)
        2. Pago de registro público (registration_id) - ACTIVA el tenant
        """
        try:
            from apps.tenants.models import TenantRegistration
            from apps.tenants.services import TenantRegistrationService
            
            result = handle_checkout_session_completed(session)
            
            if not result['success']:
                logger.error(f"Error: {result['error']}")
                return Response({'error': result['error']}, status=status.HTTP_400_BAD_REQUEST)
            
            payment_type = result.get('type', 'subscription')
            
            # CASO 1: Pago de registro público (nuevo tenant)
            if payment_type == 'registration':
                registration_id = result['registration_id']
                logger.info(f"[WEBHOOK] Procesando registro público: registration_id={registration_id}")
                
                try:
                    registration = TenantRegistration.objects.get(id=registration_id)
                except TenantRegistration.DoesNotExist:
                    # Registro no encontrado - probablemente evento antiguo de pruebas
                    # Retornamos 200 OK para que Stripe NO reintente el evento
                    logger.warning(f"[WEBHOOK] ⚠️ Registro no encontrado (evento antiguo ignorado): registration_id={registration_id}, event_id={event_id}")
                    # Marcar como procesado para deduplicación
                    PaymentAudit.objects.get_or_create(
                        webhook_event_id=event_id,
                        defaults={'status': 'ignored_missing_registration'}
                    )
                    return Response({'status': 'ignored_old_event'}, status=status.HTTP_200_OK)
                
                # Para el flujo de registro público NO creamos objetos Tenant-aware (Payment/Invoice)
                # antes de que exista el tenant. Eso generaba errores porque los modelos
                # heredan TenantAwareModel y requieren un tenant activo.
                #
                # En su lugar: marcamos el registro como pagado, guardamos los IDs de
                # Stripe y generamos un token de activación. Enviamos el email de
                # activación fuera de la transacción (on_commit) para evitar enviar
                # un token que luego sea revertido si ocurre un error.
                import secrets

                registration.payment_intent_id = result.get('stripe_payment_intent_id')
                registration.payment_completed_at = timezone.now()
                registration.status = 'payment_completed'
                registration.activation_token = secrets.token_urlsafe(32)
                registration.save()

                # Enviar email después de confirmar commit para que el token exista
                transaction.on_commit(lambda: TenantRegistrationService.send_activation_email(registration))

                logger.info(f"[WEBHOOK] ✅ Registro {registration_id} marcado como pagado. Email programado a {registration.admin_email}")

                return Response(
                    {
                        'success': True,
                        'type': 'registration',
                        'registration_id': registration_id,
                    },
                    status=status.HTTP_200_OK
                )
            
            # CASO 2: Pago de suscripción existente
            else:
                tenant_id = result['tenant_id']
                plan_id = result['plan_id']
                
                # Obtener tenant y plan
                tenant = Tenant.objects.get(id=tenant_id)
                plan = SubscriptionPlan.objects.get(id=plan_id)
                
                with transaction.atomic():
                    # Crear pago
                    payment = Payment.objects.create(
                        tenant=tenant,
                        subscription_plan=plan,
                        amount=result['amount'],
                        currency=result['currency'],
                        status=PaymentStatus.COMPLETED,
                        stripe_payment_intent_id=result['stripe_payment_intent_id'],
                        stripe_session_id=result['stripe_session_id'],
                        stripe_customer_id=result['stripe_customer_id'],
                        paid_at=timezone.now(),
                        metadata={
                            'event_id': event_id,
                            'session_data': session,
                        }
                    )
                    
                    # Crear factura
                    invoice_number = self._generate_invoice_number(tenant)
                    invoice = Invoice.objects.create(
                        tenant=tenant,
                        payment=payment,
                        subscription_plan=plan,
                        invoice_number=invoice_number,
                        subtotal=result['amount'],
                        tax_amount=0,
                        total=result['amount'],
                        currency=result['currency'],
                        description=f'Suscripción a plan {plan.name}',
                        line_items=[{
                            'description': plan.name,
                            'quantity': 1,
                            'amount': float(result['amount']),
                        }],
                        issue_date=timezone.now().date(),
                        status=InvoiceStatus.PAID,
                        paid_at=timezone.now(),
                    )
                    
                    # Actualizar tenant
                    tenant.subscription_plan = plan
                    tenant.subscription_status = 'active'
                    tenant.stripe_customer_id = result['stripe_customer_id']
                    tenant.save(update_fields=['subscription_plan', 'subscription_status', 'stripe_customer_id'])
                    
                    # Crear audit log
                    PaymentAudit.objects.create(
                        tenant=tenant,
                        payment=payment,
                        action='completed',
                        detail=f'Pago completado via Stripe webhook',
                        webhook_event_id=event_id,
                        webhook_data=session,
                    )
                    
                    logger.info(f'Pago {payment.id} y factura {invoice.invoice_number} creados exitosamente')
                    
                    return Response(
                        {
                            'success': True,
                            'payment_id': str(payment.id),
                            'invoice_id': str(invoice.id),
                        },
                        status=status.HTTP_200_OK
                    )
        
        except Exception as e:
            logger.error(f'Error manejando checkout completado: {str(e)}', exc_info=True)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _handle_charge_refunded(self, charge, event_id):
        """Manejar charge.refunded."""
        try:
            # Buscar pago por payment_intent_id
            payment = Payment.objects.get(
                stripe_payment_intent_id=charge.get('payment_intent')
            )
            
            payment.status = PaymentStatus.REFUNDED
            payment.save(update_fields=['status', 'updated_at'])
            
            # Crear audit log
            PaymentAudit.objects.create(
                tenant=payment.tenant,
                payment=payment,
                action='refunded',
                detail=f'Reembolso procesado',
                webhook_event_id=event_id,
                webhook_data=charge,
            )
            
            logger.info(f'Pago {payment.id} marcado como reembolsado')
            
            return Response({'success': True}, status=status.HTTP_200_OK)
        
        except Payment.DoesNotExist:
            logger.warning(f'Pago no encontrado para reembolso')
            return Response({'status': 'ignored'}, status=status.HTTP_200_OK)
    
    def _generate_invoice_number(self, tenant):
        """Generar número de factura único."""
        from django.utils import timezone
        date_str = timezone.now().strftime('%Y%m%d')
        count = Invoice.objects.filter(
            tenant=tenant,
            issue_date=timezone.now().date()
        ).count() + 1
        return f'INV-{date_str}-{count:04d}'


@extend_schema(tags=['Invoices'])
class InvoiceViewSet(PermissionByActionMixin, viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para facturas.
    
    Endpoints:
    - GET /invoices/ - Listar facturas del tenant
    - GET /invoices/{id}/ - Detalle de factura
    """
    
    permission_classes = [IsTenantMember, HasPermission]
    resource_name = 'invoice'
    serializer_class = InvoiceSerializer
    filterset_fields = ['status', 'subscription_plan']
    ordering_fields = ['issue_date', 'created_at']
    ordering = ['-issue_date']
    
    def get_queryset(self):
        """Filtrar facturas del tenant actual."""
        return Invoice.objects.filter(tenant=self.request.tenant)
