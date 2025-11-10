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

logger = logging.getLogger(__name__)


@extend_schema(tags=['Payments'])
class PaymentViewSet(PermissionByActionMixin, viewsets.ReadOnlyModelViewSet):
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
            
            logger.info(f'Webhook recibido: {event_type}')
            
            if event_type == 'checkout.session.completed':
                return self._handle_checkout_completed(event_data, event['id'])
            
            elif event_type == 'charge.refunded':
                return self._handle_charge_refunded(event_data, event['id'])
            
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
        """Manejar checkout.session.completed."""
        try:
            result = handle_checkout_session_completed(session)
            
            if not result['success']:
                logger.error(f"Error: {result['error']}")
                return Response({'error': result['error']}, status=status.HTTP_400_BAD_REQUEST)
            
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
            logger.error(f'Error manejando checkout completado: {str(e)}')
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
