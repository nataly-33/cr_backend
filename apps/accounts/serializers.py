from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import User, Role, Permission, UserPreferences


class PermissionSerializer(serializers.ModelSerializer):
    """Serializer para permisos"""

    class Meta:
        model = Permission
        fields = [
            'id', 'name', 'code', 'description',
            'resource', 'action', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class RoleSerializer(serializers.ModelSerializer):
    """Serializer para roles"""
    permissions = PermissionSerializer(many=True, read_only=True)
    permission_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = Role
        fields = [
            'id', 'name', 'description', 'permissions',
            'permission_ids', 'is_system_role', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'is_system_role']

    def create(self, validated_data):
        permission_ids = validated_data.pop('permission_ids', [])
        role = Role.objects.create(**validated_data)

        if permission_ids:
            permissions = Permission.objects.filter(id__in=permission_ids)
            role.permissions.set(permissions)

        return role

    def update(self, instance, validated_data):
        permission_ids = validated_data.pop('permission_ids', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if permission_ids is not None:
            permissions = Permission.objects.filter(id__in=permission_ids)
            instance.permissions.set(permissions)

        return instance


class UserPreferencesSerializer(serializers.ModelSerializer):
    """Serializer para preferencias de usuario"""

    class Meta:
        model = UserPreferences
        fields = [
            'theme', 'language', 'email_notifications',
            'push_notifications', 'custom_settings'
        ]


class UserSerializer(serializers.ModelSerializer):
    """Serializer completo para usuarios"""
    role_name = serializers.CharField(source='role.name', read_only=True)
    preferences = UserPreferencesSerializer(read_only=True)
    full_name = serializers.CharField(source='get_full_name', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name',
            'full_name', 'phone', 'gender', 'birth_date',
            'avatar', 'bio', 'professional_id', 'specialty',
            'role', 'role_name', 'is_active', 'email_verified',
            'two_factor_enabled', 'preferences', 'last_login',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'email_verified', 'last_login',
            'created_at', 'updated_at'
        ]
        extra_kwargs = {
            'password': {'write_only': True},
        }


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear usuarios"""
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password]
    )
    password_confirm = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = [
            'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'phone',
            'professional_id', 'specialty', 'role'
        ]

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': 'Las contraseñas no coinciden'
            })
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')

        user = User.objects.create_user(
            password=password,
            **validated_data
        )
        return user


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer para cambiar contraseña"""
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(
        required=True,
        validators=[validate_password]
    )
    new_password_confirm = serializers.CharField(required=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                'new_password_confirm': 'Las contraseñas no coinciden'
            })
        return attrs

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Contraseña actual incorrecta')
        return value


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Serializer personalizado para JWT con datos del usuario"""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Agregar claims personalizados
        token['email'] = user.email
        token['full_name'] = user.get_full_name()
        token['tenant_id'] = str(user.tenant_id) if user.tenant else None
        token['role'] = user.role.name if user.role else None

        return token

    def validate(self, attrs):
        data = super().validate(attrs)

        # Agregar información del usuario a la respuesta
        data['user'] = UserSerializer(self.user).data

        return data


class RegisterSerializer(serializers.Serializer):
    """Serializer para registro de nuevo tenant + usuario admin"""
    # Tenant info
    tenant_name = serializers.CharField(max_length=200)
    tenant_subdomain = serializers.SlugField(max_length=100)

    # Admin user info
    email = serializers.EmailField()
    password = serializers.CharField(
        write_only=True,
        validators=[validate_password]
    )
    password_confirm = serializers.CharField(write_only=True)
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    phone = serializers.CharField(max_length=20, required=False)

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': 'Las contraseñas no coinciden'
            })

        # Validar subdomain único
        from apps.core.models import Tenant
        if Tenant.objects.filter(subdomain=attrs['tenant_subdomain']).exists():
            raise serializers.ValidationError({
                'tenant_subdomain': 'Este subdominio ya está en uso'
            })

        # Validar email único
        if User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError({
                'email': 'Este email ya está registrado'
            })

        return attrs