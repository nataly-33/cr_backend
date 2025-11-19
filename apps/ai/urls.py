from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.ai import views

router = DefaultRouter()
router.register(r'diabetes', views.DiabetesPredictionViewSet, basename='diabetes-prediction')

urlpatterns = [
    path('', include(router.urls)),
]
