import secrets
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from apps.core.models import Tenant
from apps.accounts.models import User, Role
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
        # Generar contraseña temporal
        temp_password = secrets.token_urlsafe(12)
        
        # Link de activación
        activation_url = f"{settings.FRONTEND_URL}/activate/{registration.activation_token}"
        
        # Contexto del email
        context = {
            'tenant_name': registration.tenant_name,
            'admin_name': f"{registration.admin_first_name} {registration.admin_last_name}",
            'subdomain': registration.subdomain,
            'login_url': f"https://{registration.subdomain}.{settings.BASE_DOMAIN}/login",
            'activation_url': activation_url,
            'temp_password': temp_password,
            'plan_name': registration.selected_plan.name,
        }
        
        # Renderizar email
        html_message = render_to_string('emails/tenant_activation.html', context)
        
        # Enviar email
        send_mail(
            subject=f'Bienvenido a MediRecord - Activa tu cuenta',
            message='',  # Texto plano (opcional)
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[registration.admin_email],
            html_message=html_message,
            fail_silently=False,
        )
        
        # Guardar contraseña temporal encriptada para usarla al activar
        from django.contrib.auth.hashers import make_password
        registration.temp_password_hash = make_password(temp_password)
        registration.activation_email_sent_at = timezone.now()
        registration.save()
        
        return True
    
    @staticmethod
    def activate_tenant(activation_token, new_password):
        """
        Paso 4: Activar tenant y crear toda la estructura
        """
        registration = TenantRegistration.objects.get(
            activation_token=activation_token,
            status='payment_completed'
        )
        
        # 1. Crear el Tenant
        tenant = Tenant.objects.create(
            name=registration.tenant_name,
            subdomain=registration.subdomain,
            is_active=True,
            plan=registration.selected_plan.plan_type,
            max_users=registration.selected_plan.max_users,
            max_patients=registration.selected_plan.max_patients,
            storage_limit_gb=registration.selected_plan.storage_gb,
        )
        
        # 2. Crear roles del tenant
        from apps.accounts.services import RoleService
        RoleService.create_default_roles(tenant)
        
        # 3. Crear usuario administrador
        admin_role = Role.objects.get(tenant=tenant, name='Admin TI')
        
        admin_user = User.objects.create(
            tenant=tenant,
            email=f"admin@{registration.subdomain}.{settings.BASE_DOMAIN}",  # Email interno
            personal_email=registration.admin_email,  # Email real
            first_name=registration.admin_first_name,
            last_name=registration.admin_last_name,
            phone=registration.admin_phone,
            is_active=True,
            role=admin_role,
        )
        admin_user.set_password(new_password)  # Password que eligió el usuario
        admin_user.save()
        
        # 4. Actualizar registro
        registration.tenant = tenant
        registration.status = 'activated'
        registration.activated_at = timezone.now()
        registration.save()
        
        return {
            'tenant': tenant,
            'admin_user': admin_user,
            'login_url': f"https://{tenant.subdomain}.{settings.BASE_DOMAIN}/login"
        }