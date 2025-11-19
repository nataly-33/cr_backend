"""
Permisos personalizados para la API de AI
"""
from rest_framework.permissions import BasePermission, IsAdminUser


class IsAdminForRetrain(BasePermission):
    """
    Permiso personalizado que requiere que el usuario sea admin/staff
    para acceder al endpoint de re-entrenamiento del modelo
    """
    message = "Solo administradores pueden entrenar/re-entrenar modelos"

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_staff)


class IsAuthenticatedForPrediction(BasePermission):
    """
    Permiso que requiere autenticación para hacer predicciones
    """
    message = "Debe estar autenticado para hacer predicciones"

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)
