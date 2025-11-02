from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TenantViewSet,
    PublicSubscriptionPlanViewSet,
    public_register_tenant,
    public_simulate_payment,
    public_activate_tenant,
    check_subdomain_availability
)

router = DefaultRouter()
router.register(r'', TenantViewSet, basename='tenant')

public_patterns = [
    path('plans/', 
         PublicSubscriptionPlanViewSet.as_view({'get': 'list'}), 
         name='public-plans'),
    path('register/', 
         public_register_tenant, 
         name='public-register'),
    path('registrations/<int:registration_id>/simulate-payment/', 
         public_simulate_payment, 
         name='simulate-payment'),
    path('activate/', 
         public_activate_tenant, 
         name='activate-tenant'),
    path('check-subdomain/', 
         check_subdomain_availability,
         name='check-subdomain'),
]

urlpatterns = [
    path('public/', include(public_patterns)),  # Rutas públicas
    path('', include(router.urls)),  # Rutas protegidas
]