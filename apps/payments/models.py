"""
Modelos para gestión de pagos y facturación con Stripe.

Características:
- Integración con Stripe Checkout
- Gestión de suscripciones
- Generación de facturas
- Auditoría de pagos
"""

import uuid
from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.utils import timezone

from apps.core.models import TenantAwareModel, TenantManager
from apps.tenants.models import SubscriptionPlan


class PaymentStatus(models.TextChoices):
    """Estados de pago."""
    PENDING = 'pending', 'Pendiente'
    PROCESSING = 'processing', 'En procesamiento'
    COMPLETED = 'completed', 'Completado'
    FAILED = 'failed', 'Falló'
    REFUNDED = 'refunded', 'Reembolsado'
    CANCELLED = 'cancelled', 'Cancelado'


class InvoiceStatus(models.TextChoices):
    """Estados de factura."""
    DRAFT = 'draft', 'Borrador'
    ISSUED = 'issued', 'Emitida'
    SENT = 'sent', 'Enviada'
    PAID = 'paid', 'Pagada'
    OVERDUE = 'overdue', 'Vencida'
    CANCELLED = 'cancelled', 'Cancelada'


class Payment(TenantAwareModel):
    """
    Registro de pago con Stripe.
    
    Contiene:
    - Monto y moneda
    - Plan de suscripción asociado
    - IDs de Stripe para rastreo
    - Estado del pago
    - Timestamps
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    
    # Plan
    subscription_plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.PROTECT,
        related_name='payments'
    )
    
    # Monto
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text='Monto en la moneda especificada'
    )
    currency = models.CharField(
        max_length=3,
        default='USD',
        help_text='Código ISO 4217 (USD, EUR, MXN, etc.)'
    )
    
    # Estado del pago
    status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        db_index=True
    )
    
    # IDs de Stripe
    stripe_payment_intent_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        unique=True,
        help_text='ID del PaymentIntent de Stripe'
    )
    stripe_session_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text='ID de la sesión de Checkout de Stripe'
    )
    stripe_customer_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text='ID del Customer en Stripe'
    )
    
    # Fechas
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    
    # Metadatos
    metadata = models.JSONField(default=dict, blank=True)
    
    # Manejo de errores
    error_message = models.TextField(blank=True, null=True)
    retry_count = models.PositiveIntegerField(default=0)
    
    objects = TenantManager()
    
    class Meta:
        db_table = 'payment'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant', 'status']),
            models.Index(fields=['tenant', 'created_at']),
            models.Index(fields=['stripe_payment_intent_id']),
            models.Index(fields=['stripe_session_id']),
        ]
    
    def __str__(self):
        return f"Pago {self.id} - {self.amount} {self.currency} ({self.status})"
    
    def mark_as_completed(self):
        """Marcar pago como completado."""
        self.status = PaymentStatus.COMPLETED
        self.paid_at = timezone.now()
        self.save(update_fields=['status', 'paid_at', 'updated_at'])
    
    def mark_as_failed(self, error_message=''):
        """Marcar pago como fallido."""
        self.status = PaymentStatus.FAILED
        self.error_message = error_message
        self.retry_count += 1
        self.save(update_fields=['status', 'error_message', 'retry_count', 'updated_at'])


class Invoice(TenantAwareModel):
    """
    Factura asociada a un pago.
    
    Contiene:
    - Número de factura único
    - Asociación con pago
    - Montos (subtotal, impuestos, total)
    - Detalles de líneas
    - Estado
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    
    # Asociación
    payment = models.OneToOneField(
        Payment,
        on_delete=models.PROTECT,
        related_name='invoice',
        null=True,
        blank=True
    )
    
    subscription_plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.PROTECT,
        related_name='invoices'
    )
    
    # Número
    invoice_number = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text='Número de factura único (INV-2025-0001, etc.)'
    )
    
    # Montos
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text='Subtotal sin impuestos'
    )
    tax_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text='Monto de impuestos'
    )
    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text='Total (subtotal + impuestos)'
    )
    
    # Moneda
    currency = models.CharField(
        max_length=3,
        default='USD'
    )
    
    # Descripción / Líneas
    description = models.TextField(blank=True)
    line_items = models.JSONField(
        default=list,
        blank=True,
        help_text='Array de ítems de factura'
    )
    
    # Estado
    status = models.CharField(
        max_length=20,
        choices=InvoiceStatus.choices,
        default=InvoiceStatus.DRAFT,
        db_index=True
    )
    
    # Fechas
    issue_date = models.DateField(help_text='Fecha de emisión')
    due_date = models.DateField(null=True, blank=True, help_text='Fecha de vencimiento')
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # IDs Stripe
    stripe_invoice_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        unique=True,
        help_text='ID de Invoice en Stripe'
    )
    
    # Archivo PDF
    pdf_url = models.URLField(blank=True, null=True, help_text='URL del PDF generado')
    
    objects = TenantManager()
    
    class Meta:
        db_table = 'invoice'
        ordering = ['-issue_date']
        indexes = [
            models.Index(fields=['tenant', 'status']),
            models.Index(fields=['tenant', 'invoice_number']),
            models.Index(fields=['tenant', 'issue_date']),
        ]
    
    def __str__(self):
        return f"Factura {self.invoice_number} - {self.total} {self.currency}"
    
    def mark_as_issued(self):
        """Marcar factura como emitida."""
        self.status = InvoiceStatus.ISSUED
        self.save(update_fields=['status', 'updated_at'])
    
    def mark_as_paid(self):
        """Marcar factura como pagada."""
        self.status = InvoiceStatus.PAID
        self.paid_at = timezone.now()
        self.save(update_fields=['status', 'paid_at', 'updated_at'])


class PaymentAudit(TenantAwareModel):
    """
    Log de auditoría para pagos.
    
    Registra todos los eventos relacionados con pagos:
    - Creación
    - Cambios de estado
    - Webhooks recibidos
    - Errores
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    
    # Referencia
    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        related_name='audit_logs',
        null=True,
        blank=True
    )
    
    # Acción
    ACTION_CHOICES = [
        ('created', 'Creado'),
        ('pending', 'Pendiente'),
        ('processing', 'Procesando'),
        ('completed', 'Completado'),
        ('failed', 'Falló'),
        ('refunded', 'Reembolsado'),
        ('webhook', 'Webhook recibido'),
        ('error', 'Error'),
    ]
    
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    detail = models.TextField(blank=True)
    
    # Webhooks
    webhook_event_id = models.CharField(
        max_length=255,
        blank=True,
        help_text='ID del evento de Stripe'
    )
    webhook_data = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    objects = TenantManager()
    
    class Meta:
        db_table = 'payment_audit'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant', 'payment', 'action']),
            models.Index(fields=['webhook_event_id']),
        ]
    
    def __str__(self):
        return f"[{self.action}] Pago {self.payment_id} - {self.created_at}"
