"""
URLs para el módulo de reportes AI
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ReportsAIViewSet,
    QueryTemplateViewSet,
    QueryFeedbackViewSet
)

router = DefaultRouter()
router.register(r'', ReportsAIViewSet, basename='reports-ai')
router.register(r'templates', QueryTemplateViewSet, basename='query-template')
router.register(r'feedback', QueryFeedbackViewSet, basename='query-feedback')

urlpatterns = [
    path('', include(router.urls)),
]
