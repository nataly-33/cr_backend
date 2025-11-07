"""
Serializers para pagos y facturación.
"""

from rest_framework import serializers
from .models import Payment, Invoice, PaymentAudit


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer completo para pagos."""
    
    subscription_plan_name = serializers.CharField(
        source='subscription_plan.name',
        read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    
    class Meta:
        model = Payment
        fields = [
            'id', 'subscription_plan', 'subscription_plan_name',
            'amount', 'currency', 'status', 'status_display',
            'stripe_payment_intent_id', 'stripe_session_id', 'stripe_customer_id',
            'created_at', 'updated_at', 'paid_at',
            'metadata', 'error_message', 'retry_count'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'paid_at',
            'stripe_payment_intent_id', 'stripe_session_id', 'stripe_customer_id',
            'status_display'
        ]


class PaymentCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear pagos (desde Stripe webhook)."""
    
    class Meta:
        model = Payment
        fields = [
            'subscription_plan', 'amount', 'currency', 'status',
            'stripe_payment_intent_id', 'stripe_session_id', 'stripe_customer_id',
            'metadata'
        ]


class InvoiceSerializer(serializers.ModelSerializer):
    """Serializer completo para facturas."""
    
    subscription_plan_name = serializers.CharField(
        source='subscription_plan.name',
        read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    payment_status = serializers.CharField(
        source='payment.status',
        read_only=True
    )
    
    class Meta:
        model = Invoice
        fields = [
            'id', 'payment', 'subscription_plan', 'subscription_plan_name',
            'invoice_number', 'subtotal', 'tax_amount', 'total', 'currency',
            'description', 'line_items', 'status', 'status_display',
            'issue_date', 'due_date', 'paid_at', 'payment_status',
            'stripe_invoice_id', 'pdf_url',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'paid_at',
            'status_display', 'payment_status', 'stripe_invoice_id'
        ]


class InvoiceCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear facturas."""
    
    class Meta:
        model = Invoice
        fields = [
            'payment', 'subscription_plan', 'invoice_number',
            'subtotal', 'tax_amount', 'total', 'currency',
            'description', 'line_items', 'issue_date', 'due_date'
        ]
    
    def validate_total(self, value):
        """Validar que el total sea coherente."""
        data = self.get_initial()
        subtotal = data.get('subtotal', 0)
        tax = data.get('tax_amount', 0)
        
        expected_total = float(subtotal) + float(tax)
        if float(value) != expected_total:
            raise serializers.ValidationError(
                f'Total debe ser subtotal ({subtotal}) + impuestos ({tax}) = {expected_total}'
            )
        return value


class PaymentAuditSerializer(serializers.ModelSerializer):
    """Serializer para auditoría de pagos."""
    
    action_display = serializers.CharField(
        source='get_action_display',
        read_only=True
    )
    
    class Meta:
        model = PaymentAudit
        fields = [
            'id', 'payment', 'action', 'action_display', 'detail',
            'webhook_event_id', 'webhook_data', 'created_at'
        ]
        read_only_fields = fields
