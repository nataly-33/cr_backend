import secrets
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from apps.core.models import Tenant
from apps.accounts.models import User, Role
from apps.accounts.constants import SystemRoles
from .models import TenantRegistration, SubscriptionPlan


class TenantRegistrationService:
    """Servicio para manejar el registro de nuevos tenants"""
    
    @staticmethod
    def create_registration(data):
        """
        Paso 1: Crear registro de tenant pendiente
        """
        plan = SubscriptionPlan.objects.get(id=data['plan_id'])
        
        # Calcular precio según ciclo
        amount = plan.annual_price if data['billing_cycle'] == 'annual' else plan.monthly_price
        
        registration = TenantRegistration.objects.create(
            tenant_name=data['tenant_name'],
            subdomain=data['subdomain'],
            admin_first_name=data['admin_first_name'],
            admin_last_name=data['admin_last_name'],
            admin_email=data['admin_email'],
            admin_phone=data.get('admin_phone', ''),
            selected_plan=plan,
            billing_cycle=data['billing_cycle'],
            payment_amount=amount,
            status='pending_payment'
        )
        
        return registration
    
    @staticmethod
    def simulate_payment(registration_id):
        """
        Paso 2: Simular pago (para desarrollo)
        En producción, aquí iría la integración con Stripe
        """
        registration = TenantRegistration.objects.get(id=registration_id)
        
        # Simular pago exitoso
        registration.payment_intent_id = f"sim_pay_{secrets.token_hex(16)}"
        registration.payment_completed_at = timezone.now()
        registration.status = 'payment_completed'
        registration.save()
        
        # Generar token de activación
        registration.activation_token = secrets.token_urlsafe(32)
        registration.save()
        
        # Enviar email con credenciales
        TenantRegistrationService.send_activation_email(registration)
        
        return registration
    
    @staticmethod
    def send_activation_email(registration):
        """
        Paso 3: Enviar email con link de activación
        """
        try:
            # Link de activación
            activation_url = f"{settings.FRONTEND_URL}/activate/{registration.activation_token}"

            # Contexto del email
            context = {
                'tenant_name': registration.tenant_name,
                'admin_name': f"{registration.admin_first_name} {registration.admin_last_name}",
                'subdomain': registration.subdomain,
                'login_url': f"https://{registration.subdomain}.{settings.BASE_DOMAIN}/login",
                'activation_url': activation_url,
                'plan_name': registration.selected_plan.name,
            }

            # Renderizar email
            html_message = render_to_string('emails/tenant_activation.html', context)

            # Enviar email
            send_mail(
                subject=f'Bienvenido a Clinic Records - Activa tu cuenta',
                message='',  # Texto plano (opcional)
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[registration.admin_email],
                html_message=html_message,
                fail_silently=False,
            )

            # Guardar fecha de envío del email
            registration.activation_email_sent_at = timezone.now()
            registration.save()

            return True
        except Exception as e:
            # Log del error y re-lanzar con más contexto
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error sending activation email: {str(e)}", exc_info=True)
            raise Exception(f"Failed to send activation email: {str(e)}")
    
    @staticmethod
    def activate_tenant(activation_token, new_password):
        """
        Paso 4: Activar tenant y crear toda la estructura
        """
        import logging
        logger = logging.getLogger(__name__)

        logger.info(f"[ACTIVATE] Iniciando activación con token: {activation_token[:20]}...")

        registration = TenantRegistration.objects.get(
            activation_token=activation_token,
            status='payment_completed'
        )

        logger.info(f"[ACTIVATE] Registration encontrado: ID={registration.id}, subdomain={registration.subdomain}")

        # 1. Verificar si el tenant ya existe o crearlo
        plan = registration.selected_plan
        plan_map = {
            'basic': 'basic',
            'professional': 'pro',
            'enterprise': 'enterprise',
        }

        logger.info(f"[ACTIVATE] Intentando crear/buscar tenant para subdomain={registration.subdomain}")

        tenant, tenant_created = Tenant.objects.get_or_create(
            subdomain=registration.subdomain,
            defaults={
                'name': registration.tenant_name,
                'slug': registration.subdomain,
                'subscription_plan': plan_map.get(plan.plan_type, plan.plan_type),
                'subscription_status': 'active',
                'subscription_start': timezone.now(),
                'max_users': plan.max_users,
                'max_storage_gb': plan.storage_gb,
                'email': registration.admin_email,
                'phone': registration.admin_phone or ''
            }
        )

        if tenant_created:
            logger.info(f"[ACTIVATE] ✅ Tenant CREADO: ID={tenant.id}, name={tenant.name}")
        else:
            logger.info(f"[ACTIVATE] ⏭️  Tenant YA EXISTÍA: ID={tenant.id}, name={tenant.name}")

        # 2. Crear o buscar rol de Administrador TI para este tenant
        logger.info(f"[ACTIVATE] Intentando crear/buscar rol {SystemRoles.ADMIN_TI} para tenant_id={tenant.id}")

        admin_role, role_created = Role.objects.get_or_create(
            tenant=tenant,
            name=SystemRoles.ADMIN_TI,
            defaults={
                'description': 'Administrador del tenant con acceso completo',
                'is_system_role': True
            }
        )

        if role_created:
            logger.info(f"[ACTIVATE] ✅ Rol CREADO: ID={admin_role.id}, name={admin_role.name}")
        else:
            logger.info(f"[ACTIVATE] ⏭️  Rol YA EXISTÍA: ID={admin_role.id}, name={admin_role.name}")

        # Si es un nuevo rol y existe el rol global, copiar permisos
        if role_created:
            try:
                global_admin_role = Role.objects.get(name=SystemRoles.ADMIN_TI, tenant__isnull=True)
                admin_role.permissions.set(global_admin_role.permissions.all())
                logger.info(f"[ACTIVATE] ✅ Permisos copiados del rol global ({global_admin_role.permissions.count()} permisos)")
            except Role.DoesNotExist:
                logger.warning(f"[ACTIVATE] ⚠️  No hay rol global {SystemRoles.ADMIN_TI}, el rol quedará sin permisos")

        # 3. Crear o buscar usuario administrador
        admin_email = f"admin@{registration.subdomain}.{settings.BASE_DOMAIN}"
        logger.info(f"[ACTIVATE] Intentando crear/buscar usuario con email={admin_email}, tenant_id={tenant.id}")

        admin_user, user_created = User.objects.get_or_create(
            tenant=tenant,
            email=admin_email,
            defaults={
                'personal_email': registration.admin_email,
                'first_name': registration.admin_first_name,
                'last_name': registration.admin_last_name,
                'phone': registration.admin_phone,
                'is_active': True,
                'role': admin_role,
            }
        )

        if user_created:
            logger.info(f"[ACTIVATE] ✅ Usuario CREADO: ID={admin_user.id}, email={admin_user.email}")
        else:
            logger.info(f"[ACTIVATE] ⏭️  Usuario YA EXISTÍA: ID={admin_user.id}, email={admin_user.email}")

        # Actualizar contraseña (incluso si el usuario ya existía)
        admin_user.set_password(new_password)
        admin_user.save()
        logger.info(f"[ACTIVATE] ✅ Contraseña establecida para usuario ID={admin_user.id}")

        # Verificar que el usuario realmente se guardó
        verification_user = User.objects.filter(tenant=tenant, email=admin_email).first()
        if verification_user:
            logger.info(f"[ACTIVATE] ✅ VERIFICACIÓN: Usuario encontrado en BD - ID={verification_user.id}, email={verification_user.email}, is_active={verification_user.is_active}")
        else:
            logger.error(f"[ACTIVATE] ❌ ERROR CRÍTICO: Usuario NO encontrado en BD después de crear/actualizar!")

        # 4. Actualizar registro
        registration.tenant = tenant
        registration.status = 'activated'
        registration.activated_at = timezone.now()
        registration.save()

        logger.info(f"[ACTIVATE] ✅ Registro actualizado a 'activated'")
        logger.info(f"[ACTIVATE] ✅✅✅ ACTIVACIÓN COMPLETADA EXITOSAMENTE")
        logger.info(f"[ACTIVATE] URL de login: https://{tenant.subdomain}.{settings.BASE_DOMAIN}/login")
        logger.info(f"[ACTIVATE] Email: {admin_email}")

        return {
            'tenant': tenant,
            'admin_user': admin_user,
            'login_url': f"https://{tenant.subdomain}.{settings.BASE_DOMAIN}/login"
        }