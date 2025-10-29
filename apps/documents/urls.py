from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ClinicalDocumentViewSet,
    MedicalImageViewSet,
    DocumentAccessLogViewSet
)

router = DefaultRouter()
router.register(r'', ClinicalDocumentViewSet, basename='document')
router.register(r'images', MedicalImageViewSet, basename='medical-image')
router.register(r'access-logs', DocumentAccessLogViewSet, basename='access-log')

urlpatterns = [
    path('', include(router.urls)),
]