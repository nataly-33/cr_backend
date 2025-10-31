from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ReportTemplateViewSet, ReportExecutionViewSet, ReportGeneratorViewSet

router = DefaultRouter()
router.register(r'templates', ReportTemplateViewSet, basename='report-template')
router.register(r'executions', ReportExecutionViewSet, basename='report-execution')
router.register(r'generator', ReportGeneratorViewSet, basename='report-generator')

urlpatterns = [
    path('', include(router.urls)),
]