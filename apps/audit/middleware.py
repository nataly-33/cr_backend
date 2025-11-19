"""
Middleware de Auditoría - Captura TODAS las acciones automáticamente
Similar a NestJS LoggerService - NO DEPENDE DEL VIEWSET
"""

import json
import logging
from django.utils.deprecation import MiddlewareMixin
from django.utils import timezone
from django.http import HttpRequest, HttpResponse

from .services import AuditLogService
from apps.core.models import Tenant

logger = logging.getLogger(__name__)


class AuditLogMiddleware(MiddlewareMixin):
    """
    Middleware que captura TODAS las acciones automáticamente
    - Similar a tu LoggerService de NestJS
    - Funciona para CUALQUIER ViewSet/endpoint
    - NO requiere importar nada en el código del view
    """

    # Métodos que auditar (modifican datos)
    AUDITABLE_METHODS = ['POST', 'PUT', 'PATCH', 'DELETE']

    # Rutas que NO auditar (evitar ruido)
    EXCLUDE_PATHS = [
        '/api/schema/',
        '/api/docs/',
        '/admin/',
        '/static/',
        '/media/',
        '/health',
        '/metrics',
        '/openapi.json',
    ]

    def process_request(self, request: HttpRequest):
        """Captura información del request ANTES de procesarlo"""
        request._audit_start_time = timezone.now()
        
        # Guardar body para acceso posterior
        try:
            if request.method in self.AUDITABLE_METHODS:
                request._audit_body = request.body.decode('utf-8') if request.body else '{}'
                try:
                    request._audit_body_json = json.loads(request._audit_body)
                except:
                    request._audit_body_json = {}
        except Exception as e:
            logger.debug(f"Could not capture request body: {e}")

    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        """Registra auditoría DESPUÉS de procesar el response"""
        
        # Solo si es petición auditada
        if not hasattr(request, '_audit_start_time'):
            return response
        
        # Solo auditar métodos modificadores en API
        if request.method not in self.AUDITABLE_METHODS:
            return response
        
        # No auditar si no es API
        if not request.path.startswith('/api/'):
            return response

        # No auditar paths excluidos
        if any(request.path.startswith(path) for path in self.EXCLUDE_PATHS):
            return response

        # Solo si está autenticado
        if not request.user or not request.user.is_authenticated:
            return response

        try:
            # Obtener tenant
            tenant = self._get_tenant(request)
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
            audit_service = AuditLogService(tenant=tenant)
            
            audit_service.log_action(
                user=request.user,
                action_type=self._determine_action(request),
                resource_type=self._get_resource_type(request.path),
                ip_address=self._get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', 'Unknown'),
                request_method=request.method,
                request_path=request.path,
                request_body=getattr(request, '_audit_body_json', {}),
                response_status=response.status_code,
                error_message='' if response.status_code < 400 else self._extract_error(response),
            )
            
            logger.debug(f"✓ Audit: {request.user.email} {request.method} {request.path} → {response.status_code}")

        except Exception as e:
            logger.error(f"Error in AuditMiddleware: {type(e).__name__}: {e}", exc_info=True)

        return response

    @staticmethod
    def _get_tenant(request: HttpRequest):
        """Obtener tenant del request"""
        try:
            if hasattr(request.user, 'tenant') and request.user.tenant:
                return request.user.tenant
            return None
        except:
            return None

    @staticmethod
    def _get_client_ip(request: HttpRequest) -> str:
        """Extraer IP del cliente"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip or '127.0.0.1'

    @staticmethod
    def _determine_action(request: HttpRequest) -> str:
        """Determina el tipo de acción basado en el método HTTP"""
        method = request.method
        path = request.path.lower()

        if 'login' in path:
            return 'LOGIN'
        elif 'logout' in path:
            return 'LOGOUT'
        elif 'password' in path:
            return 'PASSWORD_CHANGE'
        elif method == 'POST':
            return 'CREATE'
        elif method in ['PUT', 'PATCH']:
            return 'UPDATE'
        elif method == 'DELETE':
            return 'DELETE'
        
        return 'CREATE' if method == 'POST' else 'OTHER'

    @staticmethod
    def _get_resource_type(path: str) -> str:
        """Extraer tipo de recurso de la ruta"""
        # /api/patients/ → patient
        # /api/documents/ → document
        
        parts = path.strip('/').split('/')
        if len(parts) >= 2:
            resource = parts[1]
            if resource.endswith('s'):
                resource = resource[:-1]
            return resource.replace('-', '_')
        
        return 'unknown'

    @staticmethod
    def _extract_error(response: HttpResponse) -> str:
        """Extraer mensaje de error de la respuesta"""
        try:
            if response.get('content-type', '').startswith('application/json'):
                data = json.loads(response.content)
                if isinstance(data, dict):
                    return str(data.get('detail', data.get('error', '')))
        except:
            pass
        return ''

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