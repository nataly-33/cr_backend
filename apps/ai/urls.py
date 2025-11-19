"""
Configuración de URLs para la API de predicción de diabetes
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import DiabetesPredictionViewSet

# Router para el ViewSet
router = DefaultRouter()
router.register(r'diabetes', DiabetesPredictionViewSet, basename='diabetes-prediction')

app_name = 'ai'

urlpatterns = [
    path('', include(router.urls)),
]
