import uuid
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class Tenant(models.Model):
    """
    Modelo de Tenant para multi-tenancy.
    Representa un hospital, clínica o institución médica.
    """
    SUBSCRIPTION_CHOICES = [
        ('basic', 'Basic'),
        ('pro', 'Pro'),
        ('enterprise', 'Enterprise'),
    ]

    STATUS_CHOICES = [
        ('active', 'Activo'),
        ('suspended', 'Suspendido'),
        ('trial', 'Prueba'),
        ('cancelled', 'Cancelado'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(
        max_length=200,
        verbose_name=_('Nombre de la institución')
    )
    slug = models.SlugField(
        unique=True,
        max_length=100,
        verbose_name=_('Slug único')
    )
    subdomain = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_('Subdominio')
    )

    # Subscription
    subscription_plan = models.CharField(
        max_length=20,
        choices=SUBSCRIPTION_CHOICES,
        default='basic',
        verbose_name=_('Plan de suscripción')
    )
    subscription_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='trial',
        verbose_name=_('Estado de suscripción')
    )
    subscription_start = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Inicio de suscripción')
    )
    subscription_end = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Fin de suscripción')
    )

    # Contact info
    email = models.EmailField(verbose_name=_('Email de contacto'))
    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('Teléfono')
    )
    address = models.TextField(
        blank=True,
        verbose_name=_('Dirección')
    )

    # Configuration
    settings = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Configuraciones personalizadas')
    )

    # Limits
    max_users = models.IntegerField(
        default=10,
        verbose_name=_('Máximo de usuarios')
    )
    max_storage_gb = models.IntegerField(
        default=5,
        verbose_name=_('Máximo de almacenamiento (GB)')
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'tenants'
        verbose_name = _('Tenant')
        verbose_name_plural = _('Tenants')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['subdomain']),
            models.Index(fields=['subscription_status']),
        ]

    def __str__(self):
        return self.name

    def clean(self):
        """Validaciones personalizadas"""
        if self.subdomain:
            self.subdomain = self.subdomain.lower()
            # Validar que el subdomain sea alfanumérico
            if not self.subdomain.isalnum():
                raise ValidationError({
                    'subdomain': _('El subdominio solo puede contener letras y números')
                })

    def is_active(self):
        """Verifica si el tenant está activo"""
        return self.subscription_status == 'active'

    def is_trial(self):
        """Verifica si está en período de prueba"""
        return self.subscription_status == 'trial'

    def can_add_user(self):
        """Verifica si puede agregar más usuarios"""
        current_users = self.users.filter(is_active=True).count()
        return current_users < self.max_users


# Thread-local storage para el tenant actual
import threading
_thread_locals = threading.local()


def get_current_tenant():
    """Obtiene el tenant actual del contexto"""
    return getattr(_thread_locals, 'tenant', None)


def set_current_tenant(tenant):
    """Establece el tenant actual en el contexto"""
    _thread_locals.tenant = tenant


class TenantAwareModel(models.Model):
    """
    Modelo abstracto base para todos los modelos con multi-tenancy.
    Incluye tenant_id, soft delete y timestamps automáticos.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name='%(class)s_set',
        verbose_name=_('Tenant')
    )

    # Soft delete
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Fecha de eliminación')
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        """Auto-asignar tenant del contexto si no está establecido"""
        if not self.tenant_id:
            current_tenant = get_current_tenant()
            if current_tenant:
                self.tenant = current_tenant
            else:
                raise ValidationError(_('No se puede crear el objeto sin un tenant activo'))
        super().save(*args, **kwargs)

    def delete(self, using=None, keep_parents=False):
        """Soft delete: marca como eliminado en lugar de borrar"""
        from django.utils import timezone
        self.deleted_at = timezone.now()
        self.save(using=using)


class TenantManager(models.Manager):
    """
    Manager personalizado que filtra automáticamente por tenant.
    Excluye registros con soft delete.
    """
    def get_queryset(self):
        qs = super().get_queryset()
        tenant = get_current_tenant()
        if tenant:
            return qs.filter(tenant=tenant, deleted_at__isnull=True)
        return qs.filter(deleted_at__isnull=True)

    def all_with_deleted(self):
        """Incluye registros eliminados"""
        qs = super().get_queryset()
        tenant = get_current_tenant()
        if tenant:
            return qs.filter(tenant=tenant)
        return qs