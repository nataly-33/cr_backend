from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ReportTemplateViewSet,
    ReportExecutionViewSet,
    ReportGeneratorViewSet,
    QBEViewSet,
    DynamicReportsViewSet
)
from .seeders import SeederViewSet
try:
    from .analytics import AnalyticsViewSet
except ImportError:
    AnalyticsViewSet = None

router = DefaultRouter()
router.register(r'templates', ReportTemplateViewSet, basename='report-template')
router.register(r'executions', ReportExecutionViewSet, basename='report-execution')
router.register(r'generator', ReportGeneratorViewSet, basename='report-generator')
router.register(r'qbe', QBEViewSet, basename='qbe')
router.register(r'seeders', SeederViewSet, basename='seeder')
router.register(r'dynamic', DynamicReportsViewSet, basename='dynamic-reports')

if AnalyticsViewSet:
    router.register(r'analytics', AnalyticsViewSet, basename='analytics')

urlpatterns = [
    path('', include(router.urls)),
]