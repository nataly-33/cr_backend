from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ClinicalRecordViewSet, ClinicalFormViewSet

router = DefaultRouter()
# Records en la raíz /api/clinical-records/
router.register(r'', ClinicalRecordViewSet, basename='clinical-record')
# Forms en /api/clinical-records/forms/
router.register(r'forms', ClinicalFormViewSet, basename='clinical-form')

urlpatterns = [
    path('', include(router.urls)),
]