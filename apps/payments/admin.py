from django.contrib import admin
from .models import Payment, Invoice, PaymentAudit


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'tenant', 'subscription_plan', 'amount', 'status', 'paid_at', 'created_at')
    list_filter = ('status', 'created_at', 'tenant')
    search_fields = ('id', 'stripe_payment_intent_id', 'stripe_session_id')
    readonly_fields = ('id', 'created_at', 'updated_at', 'stripe_payment_intent_id', 'stripe_session_id')


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'tenant', 'subscription_plan', 'total', 'status', 'issue_date', 'created_at')
    list_filter = ('status', 'issue_date', 'tenant')
    search_fields = ('invoice_number', 'id')
    readonly_fields = ('id', 'created_at', 'updated_at')


@admin.register(PaymentAudit)
class PaymentAuditAdmin(admin.ModelAdmin):
    list_display = ('id', 'tenant', 'payment', 'action', 'created_at')
    list_filter = ('action', 'created_at', 'tenant')
    search_fields = ('payment__id', 'webhook_event_id')
    readonly_fields = ('id', 'created_at')
