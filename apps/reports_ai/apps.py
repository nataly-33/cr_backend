from django.apps import AppConfig


class ReportsAiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.reports_ai'
    verbose_name = 'Reportes con IA'
    
    def ready(self):
        """Import signals when app is ready"""
        try:
            import apps.reports_ai.signals  # noqa
        except ImportError:
            pass
