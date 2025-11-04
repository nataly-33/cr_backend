"""
URLs para notificaciones.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    NotificationViewSet,
    NotificationPreferencesViewSet,
    EventWebhookViewSet,
    NotificationAuditViewSet,
)

router = DefaultRouter()
router.register(r'', NotificationViewSet, basename='notification')
router.register(r'events', EventWebhookViewSet, basename='notification-events')
router.register(r'audit', NotificationAuditViewSet, basename='notification-audit')

urlpatterns = [
    path('preferences/', NotificationPreferencesViewSet.as_view(), name='notification-preferences'),
    path('', include(router.urls)),
]
