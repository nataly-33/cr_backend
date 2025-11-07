from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ClinicalRecordViewSet, ClinicalFormViewSet

router = DefaultRouter()
# Forms en /api/clinical-records/forms/
router.register(r'forms', ClinicalFormViewSet, basename='clinical-form')
# Records en la raíz /api/clinical-records/
router.register(r'', ClinicalRecordViewSet, basename='clinical-record')

urlpatterns = [
    path('', include(router.urls)),
]