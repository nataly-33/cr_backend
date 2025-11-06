from django.urls import path, include
from rest_framework.routers import DefaultRouter
<<<<<<< HEAD
from .views import ReportTemplateViewSet, ReportExecutionViewSet, ReportGeneratorViewSet, QBEViewSet
from .seeders import SeederViewSet
=======
from .views import ReportTemplateViewSet, ReportExecutionViewSet, ReportGeneratorViewSet
from .analytics import AnalyticsViewSet
>>>>>>> d06b261f51cf0df03e855522ca396a5614d56582

router = DefaultRouter()
router.register(r'templates', ReportTemplateViewSet, basename='report-template')
router.register(r'executions', ReportExecutionViewSet, basename='report-execution')
router.register(r'generator', ReportGeneratorViewSet, basename='report-generator')
<<<<<<< HEAD
router.register(r'qbe', QBEViewSet, basename='qbe')
router.register(r'seeders', SeederViewSet, basename='seeder')
=======
router.register(r'analytics', AnalyticsViewSet, basename='analytics')
>>>>>>> d06b261f51cf0df03e855522ca396a5614d56582

urlpatterns = [
    path('', include(router.urls)),
]