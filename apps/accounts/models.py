import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.contrib.auth.base_user import BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator
from apps.core.models import TenantAwareModel, Tenant


class UserManager(BaseUserManager):
    """Manager personalizado para el modelo User"""

    def create_user(self, email, password=None, **extra_fields):
        """Crea y guarda un usuario normal"""
        if not email:
            raise ValueError(_('El email es obligatorio'))

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Crea y guarda un superusuario"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Modelo de Usuario personalizado con multi-tenancy
    """
    GENDER_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Femenino'),
        ('O', 'Otro'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name='users',
        null=True,
        blank=True,
        verbose_name=_('Tenant')
    )

    # Authentication
    email = models.EmailField(
        unique=True,
        verbose_name=_('Email')
    )
    # Email personal (contacto real) separado del email de sistema/login
    personal_email = models.EmailField(
        max_length=254,
        blank=True,
        null=True,
        verbose_name=_('Email personal')
    )
    username = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        verbose_name=_('Username')
    )

    # Personal Information
    first_name = models.CharField(
        max_length=100,
        verbose_name=_('Nombres')
    )
    last_name = models.CharField(
        max_length=100,
        verbose_name=_('Apellidos')
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message=_('Número de teléfono inválido')
            )
        ],
        verbose_name=_('Teléfono')
    )
    gender = models.CharField(
        max_length=1,
        choices=GENDER_CHOICES,
        blank=True,
        verbose_name=_('Género')
    )
    birth_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Fecha de nacimiento')
    )

    # Profile
    avatar = models.ImageField(
        upload_to='avatars/',
        null=True,
        blank=True,
        verbose_name=_('Avatar')
    )
    bio = models.TextField(
        blank=True,
        verbose_name=_('Biografía')
    )

    # Professional info
    professional_id = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Matrícula profesional')
    )
    specialty = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Especialidad')
    )

    # Role
    role = models.ForeignKey(
        'Role',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users',
        verbose_name=_('Rol')
    )

    # Status
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Activo')
    )
    is_staff = models.BooleanField(
        default=False,
        verbose_name=_('Staff')
    )
    email_verified = models.BooleanField(
        default=False,
        verbose_name=_('Email verificado')
    )

    # Security
    two_factor_enabled = models.BooleanField(
        default=False,
        verbose_name=_('2FA habilitado')
    )
    two_factor_secret = models.CharField(
        max_length=32,
        blank=True,
        verbose_name=_('Secret 2FA')
    )

    # Timestamps
    last_login = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Último login')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        db_table = 'users'
        verbose_name = _('Usuario')
        verbose_name_plural = _('Usuarios')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['tenant', 'is_active']),
        ]

    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"

    def get_full_name(self):
        """Retorna el nombre completo"""
        return f"{self.first_name} {self.last_name}".strip()

    def get_short_name(self):
        """Retorna el nombre corto"""
        return self.first_name

    def has_permission(self, permission_code):
        """Verifica si el usuario tiene un permiso específico"""
        if self.is_superuser:
            return True
        if not self.role:
            return False
        return self.role.permissions.filter(code=permission_code).exists()


class Permission(models.Model):
    """
    Permisos granulares - Globales si tenant es NULL, o específicos por tenant
    """
    RESOURCE_CHOICES = [
        ('patient', 'Pacientes'),
        ('clinical_record', 'Historias Clínicas'),
        ('document', 'Documentos'),
        ('user', 'Usuarios'),
        ('role', 'Roles'),
        ('report', 'Reportes'),
        ('audit', 'Auditoría'),
    ]

    ACTION_CHOICES = [
        ('create', 'Crear'),
        ('read', 'Leer'),
        ('update', 'Actualizar'),
        ('delete', 'Eliminar'),
        ('export', 'Exportar'),
        ('sign', 'Firmar'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='permissions',
        null=True,
        blank=True,
        verbose_name=_('Tenant (NULL para permisos globales)')
    )
    name = models.CharField(
        max_length=100,
        verbose_name=_('Nombre')
    )
    code = models.CharField(
        max_length=100,
        verbose_name=_('Código'),
        help_text=_('Ej: patient.create, document.read')
    )
    description = models.TextField(
        blank=True,
        verbose_name=_('Descripción')
    )
    resource = models.CharField(
        max_length=50,
        choices=RESOURCE_CHOICES,
        verbose_name=_('Recurso')
    )
    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
        verbose_name=_('Acción')
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Creado'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Actualizado'))

    class Meta:
        db_table = 'permissions'
        verbose_name = _('Permiso')
        verbose_name_plural = _('Permisos')
        unique_together = [['tenant', 'code']]
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant', 'resource']),
            models.Index(fields=['code']),
        ]

    def __str__(self):
        scope = "Global" if self.tenant is None else f"Tenant: {self.tenant.name}"
        return f"{self.name} ({self.code}) - {scope}"


class Role(models.Model):
    """
    Roles con permisos asignables - Globales si tenant es NULL, específicos si tiene tenant
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        related_name='roles',
        null=True,
        blank=True,
        verbose_name=_('Tenant (NULL para roles globales)')
    )
    name = models.CharField(
        max_length=100,
        verbose_name=_('Nombre')
    )
    description = models.TextField(
        blank=True,
        verbose_name=_('Descripción')
    )
    permissions = models.ManyToManyField(
        Permission,
        related_name='roles',
        verbose_name=_('Permisos')
    )
    is_system_role = models.BooleanField(
        default=False,
        verbose_name=_('Rol del sistema'),
        help_text=_('Los roles del sistema no pueden ser eliminados')
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Creado'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Actualizado'))

    class Meta:
        db_table = 'roles'
        verbose_name = _('Rol')
        verbose_name_plural = _('Roles')
        unique_together = [['tenant', 'name']]
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant']),
            models.Index(fields=['name']),
        ]

    def __str__(self):
        scope = "Global" if self.tenant is None else f"Tenant: {self.tenant.name}"
        return f"{self.name} - {scope}"

    def has_permission(self, permission_code):
        """Verifica si el rol tiene un permiso específico"""
        return self.permissions.filter(code=permission_code).exists()


class UserPreferences(models.Model):
    """
    Preferencias personalizadas del usuario
    """
    THEME_CHOICES = [
        ('light', 'Claro'),
        ('dark', 'Oscuro'),
        ('blue', 'Azul'),
        ('green', 'Verde'),
        ('purple', 'Púrpura'),
    ]

    LANGUAGE_CHOICES = [
        ('es', 'Español'),
        ('en', 'English'),
    ]

    FONT_SIZE_CHOICES = [
        ('small', 'Pequeño'),
        ('medium', 'Mediano'),
        ('large', 'Grande'),
        ('extra-large', 'Extra Grande'),
    ]

    FONT_FAMILY_CHOICES = [
        ('inter', 'Inter'),
        ('roboto', 'Roboto'),
        ('open-sans', 'Open Sans'),
        ('lato', 'Lato'),
        ('montserrat', 'Montserrat'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='preferences',
        verbose_name=_('Usuario')
    )

    # UI Preferences
    theme = models.CharField(
        max_length=20,
        choices=THEME_CHOICES,
        default='light',
        verbose_name=_('Tema')
    )
    language = models.CharField(
        max_length=5,
        choices=LANGUAGE_CHOICES,
        default='es',
        verbose_name=_('Idioma')
    )
    font_size = models.CharField(
        max_length=20,
        choices=FONT_SIZE_CHOICES,
        default='medium',
        verbose_name=_('Tamaño de fuente')
    )
    font_family = models.CharField(
        max_length=30,
        choices=FONT_FAMILY_CHOICES,
        default='inter',
        verbose_name=_('Tipografía')
    )

    # Notification preferences
    email_notifications = models.BooleanField(
        default=True,
        verbose_name=_('Notificaciones por email')
    )
    push_notifications = models.BooleanField(
        default=True,
        verbose_name=_('Notificaciones push')
    )

    # Custom settings
    custom_settings = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Configuraciones personalizadas')
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_preferences'
        verbose_name = _('Preferencias de usuario')
        verbose_name_plural = _('Preferencias de usuarios')

    def __str__(self):
        return f"Preferences for {self.user.email}"