# El sistema tiene SOLO 2 roles fijos e inmutables:
#
# 1. ASU (Admin Super Usuario):
#    - Rol GLOBAL (tenant=NULL)
#    - Gestiona todos los tenants del SaaS
#    - Puede crear nuevos tenants
#    - Puede crear usuarios "Administrador TI" para cada tenant
#    - Gestiona suscripciones y pagos con Stripe

# 2. Administrador TI:
#    - Rol POR TENANT (tenant=ID)
#    - Se crea automáticamente al registrar un nuevo tenant
#    - Tiene acceso completo a TODOS los permisos de su tenant
#    - Puede crear CUALQUIER rol personalizado (Doctor, Enfermera, etc.)
#    - Puede asignar permisos a esos roles según necesite

class SystemRoles:
    """
    Nombres de los 2 únicos roles fijos del sistema.
    - Solo estos 2 roles son constantes y obligatorios
    """
    ASU = "ASU"

    ADMIN_TI = "Administrador TI"

def get_admin_email(subdomain: str, base_domain: str) -> str:
    """
    Genera el email del administrador TI para un tenant.

    Args:
        subdomain: Subdominio del tenant (ej: 'hospital-santacruz')
        base_domain: Dominio base (ej: 'com')

    Returns:
        Email formato: admin@{subdomain}.{base_domain}
        Ejemplo: admin@hospital-santacruz.com
    """
    return f"admin@{subdomain}.{base_domain}"


def get_user_email(username: str, subdomain: str, base_domain: str) -> str:
    """
    Genera el email de un usuario para un tenant.

    Args:
        username: Nombre de usuario (ej: 'doctor.perez')
        subdomain: Subdominio del tenant (ej: 'hospital-santacruz')
        base_domain: Dominio base (ej: 'com')

    Returns:
        Email formato: {username}@{subdomain}.{base_domain}
        Ejemplo: doctor.perez@hospital-santacruz.com
    """
    return f"{username}@{subdomain}.{base_domain}"


def is_system_admin(user) -> bool:
    """
    Verifica si un usuario es ASU (Admin Super Usuario).

    Args:
        user: Instancia de User

    Returns:
        True si es ASU, False en caso contrario
    """
    return user.is_superuser and user.tenant_id is None


def is_tenant_admin(user) -> bool:
    """
    Verifica si un usuario es Administrador TI de su tenant.

    Args:
        user: Instancia de User

    Returns:
        True si es Admin TI, False en caso contrario
    """
    return (
        user.tenant_id is not None and
        user.role is not None and
        user.role.name == SystemRoles.ADMIN_TI
    )


def can_create_roles(user) -> bool:
    """
    Determina si un usuario puede crear roles.

    Solo ASU y Admin TI pueden crear roles:
    - ASU: puede crear "Administrador TI" para nuevos tenants
    - Admin TI: puede crear cualquier rol dentro de su tenant

    Args:
        user: Instancia de User

    Returns:
        True si puede crear roles, False en caso contrario
    """
    return is_system_admin(user) or is_tenant_admin(user)


def can_create_permissions(user) -> bool:
    """
    Determina si un usuario puede crear permisos.

    Solo ASU y Admin TI pueden crear permisos:
    - ASU: puede crear permisos globales (poco común)
    - Admin TI: puede crear permisos dentro de su tenant

    Args:
        user: Instancia de User

    Returns:
        True si puede crear permisos, False en caso contrario
    """
    return is_system_admin(user) or is_tenant_admin(user)


# Los permisos se definen con el formato: {resource}.{action}
#
# RECURSOS comunes (definidos en apps/core/permissions.py):
# - patient: Gestión de pacientes
# - clinical_record: Historias clínicas
# - document: Documentos clínicos
# - user: Usuarios del tenant
# - role: Roles del tenant
# - report: Reportes y estadísticas
# - audit: Auditoría del sistema
#
# ACCIONES comunes:
# - create: Crear nuevos registros
# - read: Leer/consultar registros
# - update: Actualizar registros existentes
# - delete: Eliminar registros
# - export: Exportar datos
# - sign: Firmar documentos (solo para 'document')
#
# Ejemplos de permisos:
# - patient.create: Crear pacientes
# - clinical_record.read: Leer historias clínicas
# - document.sign: Firmar documentos
# - user.delete: Eliminar usuarios
#
# Los permisos se crean en el seeder (scripts/seed_data.py) y el Admin TI
# puede asignarlos a los roles que cree según las necesidades de su clínica.
