from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from apps.core.models import Tenant
from .models import SubscriptionPlan, TenantRegistration


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    """Serializer para planes de suscripción (público)"""
    
    class Meta:
        model = SubscriptionPlan
        fields = [
            'id',
            'name',
            'slug',
            'plan_type',
            'description',
            'monthly_price',
            'annual_price',
            'max_users',
            'max_patients',
            'storage_gb',
            'features',
            'is_active',
            'display_order',
        ]
        read_only_fields = ['id', 'slug']


class TenantSerializer(serializers.ModelSerializer):
    """Serializer para tenant (protegido, solo para admin)"""
    
    plan_name = serializers.SerializerMethodField()
    current_users = serializers.SerializerMethodField()
    current_patients = serializers.SerializerMethodField()
    storage_used_gb = serializers.SerializerMethodField()
    
    class Meta:
        model = Tenant
        fields = [
            'id',
            'name',
            'subdomain',
            'plan',
            'plan_name',
            'is_active',
            'max_users',
            'max_patients',
            'storage_limit_gb',
            'current_users',
            'current_patients',
            'storage_used_gb',
            'settings',
            'created_at',
            'trial_ends_at',
        ]
        read_only_fields = [
            'id',
            'subdomain',
            'created_at',
            'current_users',
            'current_patients',
            'storage_used_gb',
        ]
    
    def get_plan_name(self, obj):
        """Nombre legible del plan"""
        plan_names = {
            'basic': 'Básico',
            'professional': 'Profesional',
            'enterprise': 'Empresarial',
        }
        return plan_names.get(obj.plan, obj.plan)
    
    def get_current_users(self, obj):
        """Cantidad actual de usuarios"""
        from apps.accounts.models import User
        return User.objects.filter(tenant=obj, is_active=True).count()
    
    def get_current_patients(self, obj):
        """Cantidad actual de pacientes"""
        from apps.patients.models import Patient
        return Patient.objects.filter(tenant=obj).count()
    
    def get_storage_used_gb(self, obj):
        """Almacenamiento usado en GB"""
        from apps.documents.models import ClinicalDocument
        from django.db.models import Sum
        
        total_bytes = ClinicalDocument.objects.filter(
            tenant=obj
        ).aggregate(
            total=Sum('file_size')
        )['total'] or 0
        
        # Convertir bytes a GB
        return round(total_bytes / (1024 ** 3), 2)


class TenantRegistrationSerializer(serializers.Serializer):
    """Serializer para registro público de nuevo tenant"""
    
    tenant_name = serializers.CharField(
        max_length=200,
        help_text="Nombre de la clínica u hospital"
    )
    subdomain = serializers.SlugField(
        max_length=63,
        help_text="Subdominio único (ej: clinicalapaz)"
    )
    admin_first_name = serializers.CharField(
        max_length=100,
        help_text="Nombre del administrador"
    )
    admin_last_name = serializers.CharField(
        max_length=100,
        help_text="Apellido del administrador"
    )
    admin_email = serializers.EmailField(
        help_text="Email personal del administrador (recibirá las credenciales)"
    )
    admin_phone = serializers.CharField(
        max_length=20,
        required=False,
        allow_blank=True,
        help_text="Teléfono del administrador (opcional)"
    )
    plan_id = serializers.IntegerField(
        help_text="ID del plan de suscripción seleccionado"
    )
    billing_cycle = serializers.ChoiceField(
        choices=['monthly', 'annual'],
        default='monthly',
        help_text="Ciclo de facturación"
    )
    
    def validate_subdomain(self, value):
        """Validar que el subdominio sea único y válido"""
        # Subdominios reservados
        reserved = [
            'www', 'api', 'admin', 'app', 'mail', 'ftp', 
            'smtp', 'pop', 'imap', 'blog', 'dev', 'test',
            'staging', 'production', 'demo'
        ]
        
        if value.lower() in reserved:
            raise serializers.ValidationError(
                f"El subdominio '{value}' está reservado. Elige otro."
            )
        
        # Verificar longitud mínima
        if len(value) < 3:
            raise serializers.ValidationError(
                "El subdominio debe tener al menos 3 caracteres."
            )
        
        # Verificar que no exista
        if Tenant.objects.filter(subdomain=value).exists():
            raise serializers.ValidationError(
                f"El subdominio '{value}' ya está en uso."
            )
        
        # Verificar que no haya registro pendiente
        if TenantRegistration.objects.filter(
            subdomain=value,
            status__in=['pending_payment', 'payment_completed']
        ).exists():
            raise serializers.ValidationError(
                f"El subdominio '{value}' ya tiene un registro en proceso."
            )
        
        return value.lower()
    
    def validate_admin_email(self, value):
        """Validar que el email no esté en uso"""
        from apps.accounts.models import User
        
        # Verificar que no exista un usuario con este personal_email
        if User.objects.filter(personal_email=value).exists():
            raise serializers.ValidationError(
                "Este email ya está registrado en el sistema."
            )
        
        return value.lower()
    
    def validate_plan_id(self, value):
        """Validar que el plan exista y esté activo"""
        try:
            plan = SubscriptionPlan.objects.get(id=value, is_active=True)
            return value
        except SubscriptionPlan.DoesNotExist:
            raise serializers.ValidationError(
                "El plan seleccionado no existe o no está disponible."
            )


class TenantRegistrationDetailSerializer(serializers.ModelSerializer):
    """Serializer detallado para registro de tenant (solo admin)"""
    
    selected_plan_name = serializers.CharField(
        source='selected_plan.name',
        read_only=True
    )
    
    class Meta:
        model = TenantRegistration
        fields = [
            'id',
            'tenant_name',
            'subdomain',
            'admin_first_name',
            'admin_last_name',
            'admin_email',
            'admin_phone',
            'selected_plan',
            'selected_plan_name',
            'billing_cycle',
            'status',
            'payment_amount',
            'payment_completed_at',
            'activation_email_sent_at',
            'activated_at',
            'tenant',
            'created_at',
        ]
        read_only_fields = [
            'id',
            'status',
            'payment_completed_at',
            'activation_email_sent_at',
            'activated_at',
            'tenant',
            'created_at',
        ]


class TenantActivationSerializer(serializers.Serializer):
    """Serializer para activar tenant con nueva contraseña"""
    
    activation_token = serializers.CharField(
        max_length=100,
        help_text="Token de activación recibido por email"
    )
    new_password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        help_text="Nueva contraseña del administrador"
    )
    
    def validate_activation_token(self, value):
        """Validar que el token exista y esté válido"""
        try:
            registration = TenantRegistration.objects.get(
                activation_token=value,
                status='payment_completed'
            )
            # Guardar el registro en el contexto para usarlo después
            self.context['registration'] = registration
            return value
        except TenantRegistration.DoesNotExist:
            raise serializers.ValidationError(
                "Token de activación inválido o expirado."
            )
    
    def validate_new_password(self, value):
        """Validar que la contraseña cumpla con los requisitos"""
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        
        return value


class CheckSubdomainSerializer(serializers.Serializer):
    """Serializer para verificar disponibilidad de subdominio"""
    
    subdomain = serializers.SlugField(
        max_length=63,
        help_text="Subdominio a verificar"
    )
    
    def validate_subdomain(self, value):
        """Normalizar a minúsculas"""
        return value.lower()


class CheckSubdomainResponseSerializer(serializers.Serializer):
    """Serializer para respuesta de verificación de subdominio"""
    
    subdomain = serializers.CharField()
    available = serializers.BooleanField()
    message = serializers.CharField(required=False)


class TenantStatsSerializer(serializers.Serializer):
    """Serializer para estadísticas del tenant"""
    
    users_count = serializers.IntegerField()
    users_limit = serializers.IntegerField()
    users_percentage = serializers.FloatField()
    
    patients_count = serializers.IntegerField()
    patients_limit = serializers.IntegerField()
    patients_percentage = serializers.FloatField()
    
    storage_used_gb = serializers.FloatField()
    storage_limit_gb = serializers.IntegerField()
    storage_percentage = serializers.FloatField()
    
    documents_count = serializers.IntegerField()
    clinical_records_count = serializers.IntegerField()