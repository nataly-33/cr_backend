"""
URLs para pagos y facturación.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PaymentViewSet,
    CheckoutSessionViewSet,
    StripeWebhookViewSet,
    InvoiceViewSet,
)

router = DefaultRouter()
router.register(r'invoices', InvoiceViewSet, basename='invoice')
router.register(r'', PaymentViewSet, basename='payment')

urlpatterns = [
    path('checkout/', CheckoutSessionViewSet.as_view(), name='checkout-session'),
    path('webhook/', StripeWebhookViewSet.as_view(), name='stripe-webhook'),
    path('', include(router.urls)),
]
