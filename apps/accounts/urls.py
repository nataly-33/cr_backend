from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    CustomTokenObtainPairView,
    RegisterView,
    UserViewSet,
    RoleViewSet,
    PermissionViewSet
)

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'roles', RoleViewSet, basename='role')
router.register(r'permissions', PermissionViewSet, basename='permission')

urlpatterns = [
    # Authentication
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', RegisterView.as_view({'post': 'register'}), name='register'),

    # Rutas adicionales - IMPORTANTE: Ir antes del router para que tengan prioridad
    path('users/me/', UserViewSet.as_view({'get': 'me'}), name='user-me'),
    path('users/me/preferences/', UserViewSet.as_view({'get': 'get_preferences', 'put': 'update_preferences'}), name='user-preferences'),

    # User management
    path('', include(router.urls)),
]