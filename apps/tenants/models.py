from django.db import models
from django.utils.translation import gettext_lazy as _

class SubscriptionPlan(models.Model):
    """Planes de suscripción disponibles públicamente"""
    
    PLAN_TYPES = [
        ('basic', 'Basic'),
        ('professional', 'Professional'),
        ('enterprise', 'Enterprise'),
    ]
    
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPES)
    description = models.TextField()
    
    # Precios
    monthly_price = models.DecimalField(max_digits=10, decimal_places=2)
    annual_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Límites
    max_users = models.IntegerField()
    max_patients = models.IntegerField()
    storage_gb = models.IntegerField()
    
    # Features
    features = models.JSONField(default=list)  # ["Feature 1", "Feature 2"]
    
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['display_order', 'monthly_price']
    
    def __str__(self):
        return f"{self.name} - ${self.monthly_price}/mes"


class TenantRegistration(models.Model):
    """Registro temporal de nuevos tenants antes de activación"""
    
    STATUS_CHOICES = [
        ('pending_payment', 'Pending Payment'),
        ('payment_completed', 'Payment Completed'),
        ('activated', 'Activated'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Datos del tenant
    tenant_name = models.CharField(max_length=200)
    subdomain = models.SlugField(max_length=63, unique=True)
    
    # Datos del administrador
    admin_first_name = models.CharField(max_length=100)
    admin_last_name = models.CharField(max_length=100)
    admin_email = models.EmailField()  # Email REAL personal
    admin_phone = models.CharField(max_length=20, blank=True)
    
    # Plan seleccionado
    selected_plan = models.ForeignKey(
        SubscriptionPlan, 
        on_delete=models.PROTECT,
        related_name='registrations'
    )
    billing_cycle = models.CharField(
        max_length=20,
        choices=[('monthly', 'Monthly'), ('annual', 'Annual')]
    )
    
    # Estado
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending_payment')
    
    # Pago (simulado inicialmente)
    payment_intent_id = models.CharField(max_length=200, blank=True)  # Para Stripe
    payment_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_completed_at = models.DateTimeField(null=True, blank=True)
    
    # Activación
    activation_token = models.CharField(max_length=100, unique=True, blank=True)
    activation_email_sent_at = models.DateTimeField(null=True, blank=True)
    activated_at = models.DateTimeField(null=True, blank=True)
    
    # Tenant creado (una vez activado)
    tenant = models.OneToOneField(
        'core.Tenant',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='registration'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.tenant_name} ({self.subdomain}) - {self.status}"