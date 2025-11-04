from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ReportTemplateViewSet, ReportExecutionViewSet, ReportGeneratorViewSet
from .analytics import AnalyticsViewSet

router = DefaultRouter()
router.register(r'templates', ReportTemplateViewSet, basename='report-template')
router.register(r'executions', ReportExecutionViewSet, basename='report-execution')
router.register(r'generator', ReportGeneratorViewSet, basename='report-generator')
router.register(r'analytics', AnalyticsViewSet, basename='analytics')

urlpatterns = [
    path('', include(router.urls)),
]