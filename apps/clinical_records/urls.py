from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ClinicalRecordViewSet, ClinicalFormViewSet

router = DefaultRouter()
router.register(r'records', ClinicalRecordViewSet, basename='clinical-record')
router.register(r'forms', ClinicalFormViewSet, basename='clinical-form')

urlpatterns = [
    path('', include(router.urls)),
]