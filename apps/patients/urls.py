from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PatientViewSet

# Importar URLs anidadas de DICOM
from apps.dicom.urls import get_patient_dicom_urls

router = DefaultRouter()
router.register(r'', PatientViewSet, basename='patient')

urlpatterns = [
    path('', include(router.urls)),
]

# Agregar rutas anidadas de DICOM para pacientes
# GET /api/patients/{patient_id}/dicom-studies/
urlpatterns += get_patient_dicom_urls()