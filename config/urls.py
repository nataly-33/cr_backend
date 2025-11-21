from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from apps.core.views.health import health_check, readiness_check, liveness_check

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Health Checks (para ALB/monitoring)
    path('api/health/', health_check, name='health-check'),
    path('api/readiness/', readiness_check, name='readiness-check'),
    path('api/liveness/', liveness_check, name='liveness-check'),

    # API Schema & Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # API Routes Públicas (incluye /api/tenants/public/)
    path('api/tenants/', include('apps.tenants.urls')),

    # API Routes Protegidas
    path('api/', include('apps.accounts.urls')),
    path('api/', include('apps.core.urls')),
    path('api/patients/', include('apps.patients.urls')),
    path('api/clinical-records/', include('apps.clinical_records.urls')),
    path('api/documents/', include('apps.documents.urls')),
    path('api/audit/', include('apps.audit.urls')),
    path('api/reports/', include('apps.reports.urls')),
    path('api/reports-ai/', include('apps.reports_ai.urls')),
    path('api/backup/', include('apps.backup.urls')),
    path('api/seed/', include('apps.seed.urls')),
    path('api/notifications/', include('apps.notifications.urls')),
    path('api/payments/', include('apps.payments.urls')),
    path('api/ai/', include('apps.ai.urls')),

]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Customize admin
admin.site.site_header = "Clinic Records Administration"
admin.site.site_title = "Clinic Records Admin"
admin.site.index_title = "Bienvenido a Clinic Records Administration"