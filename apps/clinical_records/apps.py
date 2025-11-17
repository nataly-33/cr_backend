from django.apps import AppConfig


class ClinicalRecordsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.clinical_records'
    verbose_name = 'Clinical Records'
    
    def ready(self):
        """Import signals when app is ready."""
        import apps.clinical_records.signals  