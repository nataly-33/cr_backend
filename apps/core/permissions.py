"""
Sistema de permisos RBAC (Role-Based Access Control)
Define todos los permisos disponibles en el sistema y las clases
para validar permisos en los ViewSets.
"""

from rest_framework.permissions import BasePermission
from django.core.exceptions import PermissionDenied


# ============================================================================
# DEFINICIÓN DE TODOS LOS PERMISOS DEL SISTEMA
# ============================================================================

class PermissionCodes:
    """Códigos de permisos centralizados"""
    
    # Pacientes
    PATIENT_CREATE = 'patient.create'
    PATIENT_READ = 'patient.read'
    PATIENT_UPDATE = 'patient.update'
    PATIENT_DELETE = 'patient.delete'
    PATIENT_EXPORT = 'patient.export'
    
    # Historias Clínicas
    CLINICAL_RECORD_CREATE = 'clinical_record.create'
    CLINICAL_RECORD_READ = 'clinical_record.read'
    CLINICAL_RECORD_UPDATE = 'clinical_record.update'
    CLINICAL_RECORD_DELETE = 'clinical_record.delete'
    CLINICAL_RECORD_EXPORT = 'clinical_record.export'
    
    # Formularios Clínicos
    CLINICAL_FORM_CREATE = 'clinical_form.create'
    CLINICAL_FORM_READ = 'clinical_form.read'
    CLINICAL_FORM_UPDATE = 'clinical_form.update'
    CLINICAL_FORM_DELETE = 'clinical_form.delete'
    
    # Documentos
    DOCUMENT_CREATE = 'document.create'
    DOCUMENT_READ = 'document.read'
    DOCUMENT_UPDATE = 'document.update'
    DOCUMENT_DELETE = 'document.delete'
    DOCUMENT_EXPORT = 'document.export'
    DOCUMENT_SIGN = 'document.sign'
    
    # Usuarios
    USER_CREATE = 'user.create'
    USER_READ = 'user.read'
    USER_UPDATE = 'user.update'
    USER_DELETE = 'user.delete'
    USER_EXPORT = 'user.export'
    
    # Roles
    ROLE_CREATE = 'role.create'
    ROLE_READ = 'role.read'
    ROLE_UPDATE = 'role.update'
    ROLE_DELETE = 'role.delete'
    
    # Reportes
    REPORT_CREATE = 'report.create'
    REPORT_READ = 'report.read'
    REPORT_EXPORT = 'report.export'
    REPORT_ANALYZE = 'report.analyze'
    REPORT_SUMMARIZE = 'report.summarize'
    REPORT_RECOMMEND = 'report.recommend'
    
    # Auditoría
    AUDIT_READ = 'audit.read'
    AUDIT_EXPORT = 'audit.export'
    
    # Notificaciones
    NOTIFICATION_CREATE = 'notification.create'
    NOTIFICATION_READ = 'notification.read'
    NOTIFICATION_UPDATE = 'notification.update'
    NOTIFICATION_DELETE = 'notification.delete'
    NOTIFICATION_MANAGE = 'notification.manage'
    
    # Pagos y Facturación
    PAYMENT_CREATE = 'payment.create'
    PAYMENT_READ = 'payment.read'
    PAYMENT_UPDATE = 'payment.update'
    PAYMENT_DELETE = 'payment.delete'
    PAYMENT_REFUND = 'payment.refund'
    
    INVOICE_CREATE = 'invoice.create'
    INVOICE_READ = 'invoice.read'
    INVOICE_UPDATE = 'invoice.update'
    INVOICE_DELETE = 'invoice.delete'
    INVOICE_DOWNLOAD = 'invoice.download'
    
    # Dashboard
    DASHBOARD_VIEW = 'dashboard.view'
    DASHBOARD_VIEW_GLOBAL = 'dashboard.view_global'

    # DICOM (Estudios de Imagenología)
    DICOM_CREATE = 'dicom.create'
    DICOM_READ = 'dicom.read'
    DICOM_UPDATE = 'dicom.update'
    DICOM_DELETE = 'dicom.delete'
    DICOM_EXPORT = 'dicom.export'
    DICOM_STREAM = 'dicom.stream'


# ============================================================================
# PERMISOS BASE
# ============================================================================

class IsTenantMember(BasePermission):
    """
    Permiso base: El usuario debe pertenecer al tenant actual
    """
    message = "No perteneces a este tenant."
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Superusuarios pueden acceder a todo sin tenant
        if request.user.is_superuser:
            return True
        
        if not hasattr(request, 'tenant') or not request.tenant:
            return False
        
        return request.user.tenant_id == request.tenant.id


class IsSuperAdmin(BasePermission):
    """
    Permiso: Solo superusuarios (ASU - Admin Super Usuario)
    """
    message = "Solo los administradores del sistema pueden acceder."
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_superuser


class HasPermission(BasePermission):
    """
    Permiso genérico que verifica si el usuario tiene un permiso específico.
    Se debe usar con required_permission en el ViewSet.
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Superusuarios tienen todos los permisos
        if request.user.is_superuser:
            return True
        
        # Verificar tenant
        if not hasattr(request, 'tenant') or not request.tenant:
            return False
        
        if request.user.tenant_id != request.tenant.id:
            return False
        
        # Obtener el permiso requerido según el método HTTP y la acción
        required_permission = self._get_required_permission(request, view)
        
        if not required_permission:
            return True  # Si no hay permiso definido, permitir
        
        # Verificar si el usuario tiene el permiso
        return request.user.has_permission(required_permission)
    
    def _get_required_permission(self, request, view):
        """
        Determina el permiso requerido basado en la acción del ViewSet
        """
        # Si el ViewSet define permission_map, usarlo
        if hasattr(view, 'permission_map'):
            action = getattr(view, 'action', None)
            if action and action in view.permission_map:
                return view.permission_map[action]
        
        # Mapeo por defecto basado en métodos HTTP
        action = getattr(view, 'action', None)
        
        if not action:
            # Fallback a método HTTP
            method = request.method.lower()
            action = {
                'get': 'list',
                'post': 'create',
                'put': 'update',
                'patch': 'update',
                'delete': 'destroy'
            }.get(method, None)
        
        # Obtener resource_name del ViewSet
        resource = getattr(view, 'resource_name', None)
        
        if not resource or not action:
            return None
        
        # Mapear acción a código de permiso
        action_map = {
            'list': 'read',
            'retrieve': 'read',
            'create': 'create',
            'update': 'update',
            'partial_update': 'update',
            'destroy': 'delete',
        }
        
        permission_action = action_map.get(action)
        
        if permission_action:
            return f"{resource}.{permission_action}"
        
        return None


# ============================================================================
# PERMISOS ESPECÍFICOS POR RECURSO
# ============================================================================

class CanCreatePatient(BasePermission):
    """Permiso: Crear pacientes"""
    message = "No tienes permiso para crear pacientes."
    
    def has_permission(self, request, view):
        return (request.user.is_authenticated and 
                request.user.has_permission(PermissionCodes.PATIENT_CREATE))


class CanReadPatient(BasePermission):
    """Permiso: Ver pacientes"""
    message = "No tienes permiso para ver pacientes."
    
    def has_permission(self, request, view):
        return (request.user.is_authenticated and 
                request.user.has_permission(PermissionCodes.PATIENT_READ))


class CanUpdatePatient(BasePermission):
    """Permiso: Actualizar pacientes"""
    message = "No tienes permiso para actualizar pacientes."
    
    def has_permission(self, request, view):
        return (request.user.is_authenticated and 
                request.user.has_permission(PermissionCodes.PATIENT_UPDATE))


class CanDeletePatient(BasePermission):
    """Permiso: Eliminar pacientes"""
    message = "No tienes permiso para eliminar pacientes."
    
    def has_permission(self, request, view):
        return (request.user.is_authenticated and 
                request.user.has_permission(PermissionCodes.PATIENT_DELETE))


class CanManageClinicalRecords(BasePermission):
    """Permiso: Gestionar historias clínicas (CRUD completo)"""
    message = "No tienes permiso para gestionar historias clínicas."
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Determinar la acción requerida
        action = getattr(view, 'action', None)
        
        if action in ['list', 'retrieve']:
            return request.user.has_permission(PermissionCodes.CLINICAL_RECORD_READ)
        elif action == 'create':
            return request.user.has_permission(PermissionCodes.CLINICAL_RECORD_CREATE)
        elif action in ['update', 'partial_update']:
            return request.user.has_permission(PermissionCodes.CLINICAL_RECORD_UPDATE)
        elif action == 'destroy':
            return request.user.has_permission(PermissionCodes.CLINICAL_RECORD_DELETE)
        
        return False
    
    def has_object_permission(self, request, view, obj):
        """
        Validación a nivel de objeto:
        - Pacientes solo pueden ver SU propia historia clínica
        - Doctores pueden ver/editar todas las historias de su tenant
        """
        if not request.user.is_authenticated:
            return False
        
        # Superusuarios y admins pueden todo
        if request.user.is_superuser:
            return True
        
        # Verificar tenant
        if obj.tenant_id != request.user.tenant_id:
            return False
        
        # Si el usuario es el paciente dueño, solo puede leer
        if hasattr(obj, 'patient') and obj.patient.email == request.user.email:
            return request.method in ['GET', 'HEAD', 'OPTIONS']
        
        # Para otros usuarios, verificar permisos RBAC normalmente
        action = getattr(view, 'action', None)
        
        if action in ['retrieve']:
            return request.user.has_permission(PermissionCodes.CLINICAL_RECORD_READ)
        elif action in ['update', 'partial_update']:
            return request.user.has_permission(PermissionCodes.CLINICAL_RECORD_UPDATE)
        elif action == 'destroy':
            return request.user.has_permission(PermissionCodes.CLINICAL_RECORD_DELETE)
        
        return False


class CanManageDocuments(BasePermission):
    """Permiso: Gestionar documentos clínicos"""
    message = "No tienes permiso para gestionar documentos."
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        action = getattr(view, 'action', None)
        
        if action in ['list', 'retrieve', 'download', 'view']:
            return request.user.has_permission(PermissionCodes.DOCUMENT_READ)
        elif action in ['create', 'upload']:
            return request.user.has_permission(PermissionCodes.DOCUMENT_CREATE)
        elif action in ['update', 'partial_update']:
            return request.user.has_permission(PermissionCodes.DOCUMENT_UPDATE)
        elif action == 'destroy':
            return request.user.has_permission(PermissionCodes.DOCUMENT_DELETE)
        elif action == 'sign':
            return request.user.has_permission(PermissionCodes.DOCUMENT_SIGN)
        elif action in ['process_ocr', 'enhance', 'access_log']:
            # Acciones especiales - permitir a cualquiera con permiso de lectura
            return request.user.has_permission(PermissionCodes.DOCUMENT_READ)
        
        return False


class CanManageUsers(BasePermission):
    """Permiso: Gestionar usuarios (solo Admins)"""
    message = "No tienes permiso para gestionar usuarios."
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        action = getattr(view, 'action', None)
        
        # Acciones permitidas para cualquier usuario autenticado
        if action in ['me', 'get_preferences', 'update_preferences']:
            return True
        
        # Acciones que requieren permisos específicos
        if action in ['list', 'retrieve']:
            return request.user.has_permission(PermissionCodes.USER_READ)
        elif action == 'create':
            return request.user.has_permission(PermissionCodes.USER_CREATE)
        elif action in ['update', 'partial_update']:
            return request.user.has_permission(PermissionCodes.USER_UPDATE)
        elif action == 'destroy':
            return request.user.has_permission(PermissionCodes.USER_DELETE)
        
        return False


class CanManageRoles(BasePermission):
    """Permiso: Gestionar roles (solo Admins)"""
    message = "No tienes permiso para gestionar roles."
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        action = getattr(view, 'action', None)
        
        # Superadmins pueden hacer cualquier cosa
        if request.user.is_superuser:
            return True
        
        # Para usuarios normales, verificar que solo gestionen roles de su tenant
        if action in ['list', 'retrieve']:
            return request.user.has_permission(PermissionCodes.ROLE_READ)
        elif action == 'create':
            return request.user.has_permission(PermissionCodes.ROLE_CREATE)
        elif action in ['update', 'partial_update']:
            return request.user.has_permission(PermissionCodes.ROLE_UPDATE)
        elif action == 'destroy':
            return request.user.has_permission(PermissionCodes.ROLE_DELETE)
        
        return False


class CanViewAuditLogs(BasePermission):
    """Permiso: Ver logs de auditoría (solo Admins)"""
    message = "No tienes permiso para ver logs de auditoría."
    
    def has_permission(self, request, view):
        return (request.user.is_authenticated and 
                request.user.has_permission(PermissionCodes.AUDIT_READ))


class CanGenerateReports(BasePermission):
    """Permiso: Generar reportes"""
    message = "No tienes permiso para generar reportes."

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        action = getattr(view, 'action', None)

        if action in ['list', 'retrieve']:
            return request.user.has_permission(PermissionCodes.REPORT_READ)
        elif action == 'create' or action == 'generate':
            return request.user.has_permission(PermissionCodes.REPORT_CREATE)

        return False


class CanManageDicom(BasePermission):
    """Permiso: Gestionar estudios DICOM"""
    message = "No tienes permiso para gestionar estudios DICOM."

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        action = getattr(view, 'action', None)

        if action in ['list', 'retrieve', 'metadata', 'image_ids', 'file']:
            return request.user.has_permission(PermissionCodes.DICOM_READ)
        elif action in ['upload', 'upload_zip', 'create']:
            return request.user.has_permission(PermissionCodes.DICOM_CREATE)
        elif action in ['update', 'partial_update']:
            return request.user.has_permission(PermissionCodes.DICOM_UPDATE)
        elif action == 'destroy':
            return request.user.has_permission(PermissionCodes.DICOM_DELETE)
        elif action in ['stream', 'download']:
            return request.user.has_permission(PermissionCodes.DICOM_STREAM)
        elif action in ['access_log']:
            return request.user.has_permission(PermissionCodes.DICOM_READ)

        return False


# ============================================================================
# MIXIN PARA VIEWSETS
# ============================================================================

class PermissionByActionMixin:
    """
    Mixin para ViewSets que permite definir permisos diferentes por acción.
    
    Uso en ViewSet:
        class MyViewSet(PermissionByActionMixin, viewsets.ModelViewSet):
            resource_name = 'patient'  # Nombre del recurso
            permission_classes = [IsTenantMember, HasPermission]
            
            # Opcional: mapeo personalizado
            permission_map = {
                'list': PermissionCodes.PATIENT_READ,
                'create': PermissionCodes.PATIENT_CREATE,
                'update': PermissionCodes.PATIENT_UPDATE,
                'destroy': PermissionCodes.PATIENT_DELETE,
            }
    """
    
    def get_permissions(self):
        """
        Retorna los permisos según la acción actual
        """
        # Si se define permission_classes_by_action, usarlo
        if hasattr(self, 'permission_classes_by_action'):
            action = getattr(self, 'action', None)
            if action and action in self.permission_classes_by_action:
                return [permission() for permission in self.permission_classes_by_action[action]]
        
        # Caso por defecto
        return super().get_permissions()


# ============================================================================
# UTILIDADES
# ============================================================================

def check_permission(user, permission_code):
    """
    Función auxiliar para verificar permisos en vistas o servicios
    
    Args:
        user: Usuario a verificar
        permission_code: Código del permiso (ej: 'patient.create')
    
    Returns:
        bool: True si tiene el permiso
    
    Raises:
        PermissionDenied: Si no tiene el permiso
    """
    if not user.is_authenticated:
        raise PermissionDenied("Usuario no autenticado")
    
    if user.is_superuser:
        return True
    
    if not user.has_permission(permission_code):
        raise PermissionDenied(f"No tienes el permiso: {permission_code}")
    
    return True
