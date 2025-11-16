from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from .models import Tenant, set_current_tenant
from rest_framework_simplejwt.tokens import AccessToken


class TenantMiddleware(MiddlewareMixin):
    """
    Middleware que identifica y establece el tenant actual basado en:
    1. Header X-Tenant-ID
    2. Subdomain
    3. Usuario autenticado
    """

    def process_request(self, request):
        tenant = None

        # Método 1: Header X-Tenant-ID (útil para APIs)
        tenant_id = request.headers.get('X-Tenant-ID')
        if tenant_id:
            try:
                tenant = Tenant.objects.get(id=tenant_id, deleted_at__isnull=True)
            except (Tenant.DoesNotExist, ValueError):
                return JsonResponse(
                    {'error': 'Tenant no encontrado o inválido'},
                    status=400
                )

        # Método 2: Subdomain (ej: hospital1.clinidocs.com)
        if not tenant:
            host = request.get_host().split(':')[0]  # Remover puerto
            parts = host.split('.')
            if len(parts) > 2:  # Tiene subdomain
                subdomain = parts[0]
                try:
                    tenant = Tenant.objects.get(
                        subdomain=subdomain,
                        deleted_at__isnull=True
                    )
                except Tenant.DoesNotExist:
                    pass

        # Método 3: Usuario autenticado (session auth)
        # NOTE: For JWT (DRF) authentication request.user will usually be
        # Anonymous here because DRF authenticators run later. Try to extract
        # tenant_id from the JWT token if present in the Authorization header.
        if not tenant:
            # First attempt: session-based user (if any)
            try:
                if getattr(request, 'user', None) and request.user.is_authenticated:
                    if hasattr(request.user, 'tenant'):
                        tenant = request.user.tenant
            except Exception:
                # defensive: if request.user access fails, continue to token check
                tenant = None

        # Método 4: JWT token in Authorization header (useful for API calls / Swagger)
        if not tenant:
            auth_header = request.headers.get('Authorization') or request.META.get('HTTP_AUTHORIZATION')
            if auth_header and auth_header.startswith('Bearer '):
                token = auth_header.split(' ', 1)[1].strip()
                try:
                    access = AccessToken(token)
                    tenant_id = access.get('tenant_id')
                    is_superuser = access.get('is_superuser', False)
                    
                    if tenant_id:
                        try:
                            tenant = Tenant.objects.get(id=tenant_id, deleted_at__isnull=True)
                        except Tenant.DoesNotExist:
                            tenant = None
                    
                    # Si es superuser y no tiene tenant_id, permitir sin tenant
                    if is_superuser and not tenant_id:
                        set_current_tenant(None)
                        request.tenant = None
                        return None
                except Exception:
                    # invalid token, ignore and continue
                    tenant = None

        # Establecer tenant en el contexto
        if tenant:
            # Verificar que el tenant esté activo
            if tenant.subscription_status not in ['active', 'trial']:
                return JsonResponse(
                    {
                        'error': 'Tenant suspendido o cancelado',
                        'status': tenant.subscription_status
                    },
                    status=403
                )

            set_current_tenant(tenant)
            request.tenant = tenant
        else:
            # Si no hay tenant, establecer None explícitamente
            request.tenant = None

        return None

    def process_response(self, request, response):
        """Limpiar el contexto del tenant después del request"""
        set_current_tenant(None)
        return response