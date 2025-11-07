"""
App de Notificaciones: envío de notificaciones a usuarios según eventos y preferencias.

Características:
- Canales: in-app, email, push
- Preferencias: opt-in/out por tipo y canal
- Auditoría completa
- Reintentos automáticos con Celery
- Idempotencia
- Multi-tenant
"""

default_app_config = 'apps.notifications.apps.NotificationsConfig'
