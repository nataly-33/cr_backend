import json
from django.utils.deprecation import MiddlewareMixin
from django.utils import timezone
from .models import AuditLog


class AuditLogMiddleware(MiddlewareMixin):
    """
    Middleware que captura automáticamente todas las acciones
    y las registra en el log de auditoría
    """

    # Métodos que se deben auditar
    AUDITABLE_METHODS = ['POST', 'PUT', 'PATCH', 'DELETE']

    # Paths que NO se deben auditar (para evitar ruido)
    EXCLUDE_PATHS = [
        '/api/schema/',
        '/api/docs/',
        '/admin/jsi18n/',
        '/static/',
        '/media/',
    ]

    def process_request(self, request):
        """Captura información del request"""
        request._audit_start_time = timezone.now()

    def process_response(self, request, response):
        """Registra el log de auditoría después de procesar el response"""
        
        # No auditar si no está autenticado (excepto login/register)
        if not request.user.is_authenticated and request.path not in ['/api/auth/login/', '/api/auth/register/']:
            return response

        # No auditar paths excluidos
        if any(request.path.startswith(path) for path in self.EXCLUDE_PATHS):
            return response

        # Solo auditar ciertos métodos
        if request.method not in self.AUDITABLE_METHODS and request.method != 'GET':
            return response

        # Si es GET, solo auditar endpoints específicos (para no saturar)
        if request.method == 'GET':
            if not any(keyword in request.path for keyword in ['/download/', '/export/', '/api/patients/', '/api/documents/']):
                return response

        try:
            # Extraer información del request
            tenant = getattr(request, 'tenant', None)
            user = request.user if request.user.is_authenticated else None

            # Obtener IP
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(',')[0]
            else:
                ip_address = request.META.get('REMOTE_ADDR')

            # Determinar acción y recurso
            action_type = self._determine_action(request)
            resource_type, resource_id = self._extract_resource_info(request)

            # Capturar request body (solo para POST/PUT/PATCH)
            request_body = {}
            if request.method in ['POST', 'PUT', 'PATCH']:
                try:
                    if hasattr(request, 'data'):
                        request_body = dict(request.data)
                        # Ocultar contraseñas
                        if 'password' in request_body:
                            request_body['password'] = '***HIDDEN***'
                        if 'password_confirm' in request_body:
                            request_body['password_confirm'] = '***HIDDEN***'
                except:
                    pass

            # Crear log de auditoría
            AuditLog.objects.create(
                tenant=tenant,
                user=user,
                user_email=user.email if user else 'anonymous',
                user_name=user.get_full_name() if user else 'Anonymous',
                action_type=action_type,
                resource_type=resource_type,
                resource_id=resource_id,
                ip_address=ip_address,
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                request_method=request.method,
                request_path=request.path,
                request_body=request_body,
                response_status=response.status_code,
                session_id=request.session.session_key if hasattr(request, 'session') else None,
            )

        except Exception as e:
            # No fallar el request si hay error en auditoría
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error creating audit log: {str(e)}")

        return response

    def _determine_action(self, request):
        """Determina el tipo de acción basado en el método HTTP y path"""
        method = request.method
        path = request.path.lower()

        if 'login' in path:
            return 'LOGIN'
        elif 'logout' in path:
            return 'LOGOUT'
        elif 'password' in path:
            return 'PASSWORD_CHANGE'
        elif 'sign' in path:
            return 'SIGN'
        elif 'download' in path:
            return 'DOWNLOAD'
        elif 'export' in path:
            return 'EXPORT'
        elif method == 'POST':
            return 'CREATE'
        elif method == 'GET':
            return 'READ'
        elif method in ['PUT', 'PATCH']:
            return 'UPDATE'
        elif method == 'DELETE':
            return 'DELETE'
        
        return 'UNKNOWN'

    def _extract_resource_info(self, request):
        """Extrae información del recurso del path"""
        path = request.path
        
        # Mapeo de paths a tipos de recursos
        resource_map = {
            'patients': 'patient',
            'clinical-records': 'clinical_record',
            'documents': 'document',
            'users': 'user',
            'roles': 'role',
            'tenants': 'tenant',
        }

        resource_type = 'unknown'
        resource_id = None

        for key, value in resource_map.items():
            if key in path:
                resource_type = value
                # Intentar extraer UUID del path
                import re
                uuid_pattern = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
                match = re.search(uuid_pattern, path)
                if match:
                    resource_id = match.group(0)
                break

        return resource_type, resource_id