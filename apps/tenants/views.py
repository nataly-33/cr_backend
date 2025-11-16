from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from django.db.models import Count, Sum

from apps.core.models import Tenant
from apps.core.permissions import IsSuperAdmin
from apps.accounts.constants import SystemRoles
from .models import SubscriptionPlan, TenantRegistration
from .serializers import (
    TenantSerializer,
    SubscriptionPlanSerializer,
    TenantRegistrationSerializer,
    TenantRegistrationDetailSerializer,
    TenantActivationSerializer,
    CheckSubdomainSerializer,
    CheckSubdomainResponseSerializer,
    TenantStatsSerializer,
)
from .services import TenantRegistrationService


@extend_schema(tags=['Tenants'])
class TenantViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para gestión de tenants (solo lectura, solo admin)
    """
    serializer_class = TenantSerializer
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    queryset = Tenant.objects.none()  # Para drf-spectacular schema

    def get_queryset(self):
        # Prevenir error en generación de schema
        if getattr(self, 'swagger_fake_view', False):
            return Tenant.objects.none()

        # Solo ASU (superadmin) puede ver todos los tenants
        if self.request.user.is_superuser:
            return Tenant.objects.all()
        # Los demás solo ven su propio tenant
        return Tenant.objects.filter(id=self.request.user.tenant_id)
    
    @extend_schema(
        summary="Obtener estadísticas del tenant actual",
        responses={200: TenantStatsSerializer}
    )
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Obtener estadísticas de uso del tenant actual"""
        tenant = request.user.tenant

        # Super admin sin tenant: retornar error
        if request.user.is_superuser and tenant is None:
            return Response(
                {'error': 'Super admin no tiene tenant. Use /api/tenants/ para ver todos los tenants.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Contar usuarios activos
        from apps.accounts.models import User
        users_count = User.objects.filter(tenant=tenant, is_active=True).count()
        
        # Contar pacientes
        from apps.patients.models import Patient
        patients_count = Patient.objects.filter(tenant=tenant).count()
        
        # Contar documentos y registros
        from apps.documents.models import ClinicalDocument
        from apps.clinical_records.models import ClinicalRecord
        
        documents_count = ClinicalDocument.objects.filter(tenant=tenant).count()
        records_count = ClinicalRecord.objects.filter(tenant=tenant).count()
        
        # Calcular almacenamiento usado
        total_bytes = ClinicalDocument.objects.filter(
            tenant=tenant
        ).aggregate(
            total=Sum('file_size_bytes')
        )['total'] or 0
        storage_used_gb = round(total_bytes / (1024 ** 3), 2)

        # Límites del tenant (usar valores por defecto si no existen)
        max_patients = 1000  # Valor por defecto
        max_storage_gb = tenant.max_storage_gb if hasattr(tenant, 'max_storage_gb') else 10

        # Calcular porcentajes
        users_percentage = (users_count / tenant.max_users * 100) if tenant.max_users > 0 else 0
        patients_percentage = (patients_count / max_patients * 100) if max_patients > 0 else 0
        storage_percentage = (storage_used_gb / max_storage_gb * 100) if max_storage_gb > 0 else 0

        stats = {
            'users_count': users_count,
            'users_limit': tenant.max_users,
            'users_percentage': round(users_percentage, 2),
            'patients_count': patients_count,
            'patients_limit': max_patients,
            'patients_percentage': round(patients_percentage, 2),
            'storage_used_gb': storage_used_gb,
            'storage_limit_gb': max_storage_gb,
            'storage_percentage': round(storage_percentage, 2),
            'documents_count': documents_count,
            'clinical_records_count': records_count,
        }
        
        serializer = TenantStatsSerializer(stats)
        return Response(serializer.data)


@extend_schema(tags=['Planes - Protegido'])
class SubscriptionPlanViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet protegido para ver planes de suscripción disponibles.
    Requiere autenticación de usuario válido.
    Los planes son iguales para todos los tenants.
    """
    queryset = SubscriptionPlan.objects.filter(is_active=True)
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [IsAuthenticated]  # Solo requiere estar autenticado
    pagination_class = None  # Desactivar paginación para devolver array directo


@extend_schema(tags=['Public - Planes'])
class PublicSubscriptionPlanViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API PÚBLICA para ver planes de suscripción
    No requiere autenticación
    """
    queryset = SubscriptionPlan.objects.filter(is_active=True)
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [AllowAny]
    pagination_class = None  # Desactivar paginación para devolver array directo


@extend_schema(
    request=TenantRegistrationSerializer,
    responses={
        201: OpenApiResponse(
            description="Registro creado exitosamente",
            response={
                'type': 'object',
                'properties': {
                    'registration_id': {'type': 'integer'},
                    'status': {'type': 'string'},
                    'payment_amount': {'type': 'number'},
                    'message': {'type': 'string'},
                }
            }
        ),
        400: OpenApiResponse(description="Datos inválidos"),
    },
    summary="Registrar nuevo tenant",
    description="Endpoint público para registrar un nuevo tenant (clínica/hospital)",
    tags=['Public - Registro']
)
@api_view(['POST'])
@permission_classes([AllowAny])
def public_register_tenant(request):
    """
    API PÚBLICA para registrar un nuevo tenant
    
    Crea un registro de tenant pendiente de pago.
    """
    serializer = TenantRegistrationSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Crear registro
        registration = TenantRegistrationService.create_registration(
            serializer.validated_data
        )
        
        return Response({
            'registration_id': registration.id,
            'status': registration.status,
            'payment_amount': float(registration.payment_amount),
            'message': 'Registro creado exitosamente. Proceda al pago.'
        }, status=status.HTTP_201_CREATED)
    
    except Exception as e:
        return Response({
            'error': 'Error al crear el registro',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    request=None,
    responses={
        200: OpenApiResponse(
            description="Pago simulado exitosamente",
            response={
                'type': 'object',
                'properties': {
                    'status': {'type': 'string'},
                    'message': {'type': 'string'},
                }
            }
        ),
        404: OpenApiResponse(description="Registro no encontrado"),
    },
    summary="Simular pago (desarrollo)",
    description="Endpoint para simular pago en desarrollo. En producción usaría Stripe.",
    tags=['Public - Registro']
)
@api_view(['POST'])
@permission_classes([AllowAny])
def public_simulate_payment(request, registration_id):
    """
    API para simular pago (desarrollo)
    
    En producción, este endpoint sería reemplazado por webhooks de Stripe.
    """
    try:
        registration = TenantRegistrationService.simulate_payment(registration_id)
        
        return Response({
            'status': 'payment_completed',
            'message': f'Email de activación enviado a {registration.admin_email}'
        })
    except TenantRegistration.DoesNotExist:
        return Response(
            {'error': 'Registro no encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': 'Error al procesar el pago', 'detail': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema(
    request=TenantActivationSerializer,
    responses={
        200: OpenApiResponse(
            description="Tenant activado exitosamente",
            response={
                'type': 'object',
                'properties': {
                    'status': {'type': 'string'},
                    'tenant_name': {'type': 'string'},
                    'login_url': {'type': 'string'},
                    'message': {'type': 'string'},
                }
            }
        ),
        400: OpenApiResponse(description="Token inválido o datos incorrectos"),
    },
    summary="Activar tenant con nueva contraseña",
    description="Activa el tenant y crea toda la estructura (roles, admin user, etc.)",
    tags=['Public - Registro']
)
@api_view(['POST'])
@permission_classes([AllowAny])
def public_activate_tenant(request):
    """
    API para activar tenant con token
    
    Una vez activado, el usuario puede iniciar sesión.
    """
    serializer = TenantActivationSerializer(
        data=request.data,
        context={'request': request}
    )
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        result = TenantRegistrationService.activate_tenant(
            activation_token=serializer.validated_data['activation_token'],
            new_password=serializer.validated_data['new_password']
        )
        
        return Response({
            'status': 'activated',
            'tenant_name': result['tenant'].name,
            'login_url': result['login_url'],
            'message': 'Tenant activado exitosamente. Ya puedes iniciar sesión.'
        })
    except TenantRegistration.DoesNotExist:
        return Response(
            {'error': 'Token de activación inválido o expirado'},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        import logging
        import traceback
        logger = logging.getLogger(__name__)
        logger.error(f"Error activating tenant: {str(e)}")
        logger.error(traceback.format_exc())
        return Response(
            {'error': 'Error al activar el tenant', 'detail': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema(
    parameters=[
        OpenApiParameter(
            name='subdomain',
            type=str,
            location=OpenApiParameter.QUERY,
            description='Subdominio a verificar',
            required=True
        )
    ],
    responses={
        200: CheckSubdomainResponseSerializer,
        400: OpenApiResponse(description="Falta parámetro subdomain"),
    },
    summary="Verificar disponibilidad de subdominio",
    description="Verifica si un subdominio está disponible para registro",
    tags=['Public - Registro']
)
@api_view(['GET'])
@permission_classes([AllowAny])
def check_subdomain_availability(request):
    """
    API para verificar disponibilidad de subdominio
    """
    subdomain = request.query_params.get('subdomain', '').lower()
    
    if not subdomain:
        return Response(
            {'error': 'El parámetro subdomain es requerido'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Subdominios reservados
    reserved = [
        'www', 'api', 'admin', 'app', 'mail', 'ftp',
        'smtp', 'pop', 'imap', 'blog', 'dev', 'test',
        'staging', 'production', 'demo'
    ]
    
    # Verificar si está reservado
    if subdomain in reserved:
        return Response({
            'subdomain': subdomain,
            'available': False,
            'message': 'Este subdominio está reservado'
        })
    
    # Verificar si existe
    if Tenant.objects.filter(subdomain=subdomain).exists():
        return Response({
            'subdomain': subdomain,
            'available': False,
            'message': 'Este subdominio ya está en uso'
        })
    
    # Verificar si hay registro pendiente
    if TenantRegistration.objects.filter(
        subdomain=subdomain,
        status__in=['pending_payment', 'payment_completed']
    ).exists():
        return Response({
            'subdomain': subdomain,
            'available': False,
            'message': 'Este subdominio tiene un registro en proceso'
        })
    
    return Response({
        'subdomain': subdomain,
        'available': True,
        'message': 'Subdominio disponible'
    })