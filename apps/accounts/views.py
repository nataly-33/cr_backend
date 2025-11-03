from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.exceptions import PermissionDenied
from django.contrib.auth import logout
from django.db import transaction
from django.utils.text import slugify
from datetime import timedelta
from django.utils import timezone
from drf_spectacular.utils import extend_schema

from .models import User, Role, Permission, UserPreferences
from .serializers import (
    UserSerializer, UserCreateSerializer, RoleSerializer,
    PermissionSerializer, ChangePasswordSerializer,
    CustomTokenObtainPairSerializer, RegisterSerializer,
    UserPreferencesSerializer
)
from apps.core.models import Tenant, set_current_tenant
from apps.core.permissions import (
    IsTenantMember,
    CanManageUsers,
    CanManageRoles,
    PermissionByActionMixin,
    IsSuperAdmin
)


@extend_schema(tags=['Accounts'])
class CustomTokenObtainPairView(TokenObtainPairView):
    """Vista personalizada para obtener JWT"""
    serializer_class = CustomTokenObtainPairSerializer


@extend_schema(tags=['Accounts'])
class RegisterView(viewsets.GenericViewSet):
    """Vista para registro de nuevos tenants"""
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer

    @transaction.atomic
    @action(detail=False, methods=['post'])
    def register(self, request):
        """Registra un nuevo tenant con usuario admin"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        # Crear tenant
        tenant = Tenant.objects.create(
            name=data['tenant_name'],
            slug=slugify(data['tenant_name']),
            subdomain=data['tenant_subdomain'],
            email=data['email'],
            phone=data.get('phone', ''),
            subscription_plan='trial',
            subscription_status='trial',
            subscription_start=timezone.now(),
            subscription_end=timezone.now() + timedelta(days=30)
        )

        # Establecer tenant en contexto
        set_current_tenant(tenant)

        # Crear rol admin
        admin_role = Role.objects.create(
            tenant=tenant,
            name='Administrador',
            description='Rol con todos los permisos',
            is_system_role=True
        )

        # Crear permisos básicos
        resources = ['patient', 'clinical_record', 'document', 'user', 'role', 'report']
        actions = ['create', 'read', 'update', 'delete']

        permissions_list = []
        for resource in resources:
            for action in actions:
                perm = Permission.objects.create(
                    tenant=tenant,
                    name=f'{action.title()} {resource}',
                    code=f'{resource}.{action}',
                    resource=resource,
                    action=action
                )
                permissions_list.append(perm)

        admin_role.permissions.set(permissions_list)

        # Crear usuario admin
        user = User.objects.create_user(
            tenant=tenant,
            email=data['email'],
            password=data['password'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            phone=data.get('phone', ''),
            role=admin_role,
            is_active=True,
            is_staff=True
        )

        return Response({
            'message': 'Registro exitoso',
            'tenant': {
                'id': str(tenant.id),
                'name': tenant.name,
                'subdomain': tenant.subdomain
            },
            'user': UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)


@extend_schema(tags=['Accounts'])
class UserViewSet(PermissionByActionMixin, viewsets.ModelViewSet):
    """
    ViewSet para gestión de usuarios.
    
    Permisos:
    - list/retrieve: Cualquier usuario autenticado (IsAuthenticated)
    - create/update/delete: Solo Administradores TI (CanManageUsers)
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsTenantMember]
    resource_name = 'user'
    
    def get_permissions(self):
        """Permisos diferentes según la acción"""
        if self.action in ['me', 'get_preferences', 'update_preferences']:
            # Solo requiere estar autenticado como miembro del tenant
            return [IsTenantMember()]
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer

    def get_queryset(self):
        """Filtrar usuarios según el tipo de usuario"""
        if self.request.user.is_superuser:
            # Super Admin solo ve usuarios con rol Administrativo de todos los tenants
            return User.objects.filter(
                role__name='Administrativo',
                tenant__isnull=False
            ).select_related('role', 'tenant')
        
        # Usuarios normales ven todos los usuarios de su tenant
        return User.objects.filter(tenant=self.request.tenant).select_related('role', 'tenant')

    @action(detail=False, methods=['get'])
    def me(self, request):
        """Retorna el usuario actual"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def change_password(self, request, pk=None):
        """Cambiar contraseña del usuario"""
        user = self.get_object()

        # Solo el usuario mismo o admin puede cambiar la contraseña
        if request.user != user and not request.user.is_staff:
            return Response(
                {'error': 'No tienes permiso para cambiar esta contraseña'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)

        user.set_password(serializer.validated_data['new_password'])
        user.save()

        return Response({'message': 'Contraseña actualizada exitosamente'})

    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """Activar/desactivar usuario"""
        user = self.get_object()
        user.is_active = not user.is_active
        user.save()

        return Response({
            'message': f"Usuario {'activado' if user.is_active else 'desactivado'}",
            'is_active': user.is_active
        })

    @action(detail=False, methods=['get', 'put'], permission_classes=[permissions.IsAuthenticated])
    def preferences(self, request):
        """Obtener o actualizar preferencias del usuario"""
        # Obtener o crear preferencias si no existen
        preferences, created = UserPreferences.objects.get_or_create(
            user=request.user
        )

        if request.method == 'GET':
            serializer = UserPreferencesSerializer(preferences)
            return Response(serializer.data)

        # PUT - Actualizar preferencias
        serializer = UserPreferencesSerializer(
            preferences,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def get_preferences(self, request):
        """Obtener preferencias del usuario"""
        preferences = request.user.preferences
        serializer = UserPreferencesSerializer(preferences)
        return Response(serializer.data)


@extend_schema(tags=['Accounts'])
class RoleViewSet(PermissionByActionMixin, viewsets.ModelViewSet):
    """
    ViewSet para gestión de roles.
    
    Roles globales (sin tenant_id) - Solo superadmins pueden verlos/editarlos
    Roles por tenant - Solo usuarios del mismo tenant pueden verlos/editarlos
    
    Permisos requeridos:
    - list/retrieve: role.read
    - create: role.create
    - update: role.update
    - delete: role.delete
    
    Solo Administradores TI pueden gestionar roles.
    """
    serializer_class = RoleSerializer
    permission_classes = [IsTenantMember]
    resource_name = 'role'
    
    def get_permissions(self):
        """Permisos dinámicos según la acción"""
        if self.action in ['list', 'retrieve']:
            # Cualquier usuario autenticado puede listar/ver roles
            return [IsTenantMember(), permissions.IsAuthenticated()]
        else:
            # Solo admins pueden crear/modificar/eliminar
            return [IsTenantMember(), CanManageRoles()]

    def get_queryset(self):
        """
        Filtrar roles:
        - Superusuarios: ven todos (globales + por tenant)
        - Usuarios normales: solo ven roles de su tenant
        """
        if self.request.user.is_superuser:
            return Role.objects.all()
        return Role.objects.filter(tenant=self.request.tenant)

    def perform_create(self, serializer):
        """Asignar automáticamente el tenant al crear"""
        if self.request.user.is_superuser and self.request.data.get('tenant'):
            # Superadmin puede especificar tenant (incluyendo NULL para global)
            serializer.save()
        else:
            # Usuario normal siempre crea en su tenant
            serializer.save(tenant=self.request.tenant)

    def perform_update(self, serializer):
        """
        Solo permitir cambios si:
        - Usuario es superadmin, O
        - El rol pertenece al mismo tenant del usuario
        """
        obj = self.get_object()
        if not self.request.user.is_superuser and obj.tenant_id != self.request.tenant.id:
            raise PermissionDenied("No puedes editar roles globales o de otro tenant")
        serializer.save()

    def destroy(self, request, *args, **kwargs):
        """No permitir eliminar roles del sistema y roles globales sin ser superadmin"""
        instance = self.get_object()
        
        if instance.is_system_role:
            return Response(
                {'error': 'No se pueden eliminar roles del sistema'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if instance.tenant_id is None and not request.user.is_superuser:
            return Response(
                {'error': 'No puedes eliminar roles globales'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().destroy(request, *args, **kwargs)


@extend_schema(tags=['Accounts'])
class PermissionViewSet(PermissionByActionMixin, viewsets.ModelViewSet):
    """
    ViewSet para gestión de permisos.
    
    Permisos globales (sin tenant_id) - Solo superadmins pueden verlos/editarlos
    Permisos por tenant - Solo usuarios del mismo tenant pueden verlos/editarlos
    
    Permisos requeridos:
    - list/retrieve: role.read
    - create: role.create
    - update: role.update
    - delete: role.delete
    
    Solo Administradores TI pueden gestionar permisos.
    """
    serializer_class = PermissionSerializer
    permission_classes = [IsTenantMember, CanManageRoles]
    resource_name = 'role'

    def get_queryset(self):
        """
        Filtrar permisos:
        - Superusuarios: ven todos (globales + por tenant)
        - Usuarios normales: solo ven permisos de su tenant
        """
        if self.request.user.is_superuser:
            return Permission.objects.all()
        return Permission.objects.filter(tenant=self.request.tenant)

    def perform_create(self, serializer):
        """Asignar automáticamente el tenant al crear"""
        if self.request.user.is_superuser and self.request.data.get('tenant'):
            # Superadmin puede especificar tenant (incluyendo NULL para global)
            serializer.save()
        else:
            # Usuario normal siempre crea en su tenant
            serializer.save(tenant=self.request.tenant)

    def perform_update(self, serializer):
        """
        Solo permitir cambios si:
        - Usuario es superadmin, O
        - El permiso pertenece al mismo tenant del usuario
        """
        obj = self.get_object()
        if not self.request.user.is_superuser and obj.tenant_id != self.request.tenant.id:
            raise PermissionDenied("No puedes editar permisos globales o de otro tenant")
        serializer.save()

    def destroy(self, request, *args, **kwargs):
        """No permitir eliminar permisos globales sin ser superadmin"""
        instance = self.get_object()
        
        if instance.roles.exists():
            return Response(
                {'error': f'No se puede eliminar este permiso. Está siendo usado por {instance.roles.count()} rol(es)'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if instance.tenant_id is None and not request.user.is_superuser:
            return Response(
                {'error': 'No puedes eliminar permisos globales'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().destroy(request, *args, **kwargs)