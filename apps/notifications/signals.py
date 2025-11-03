from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.documents.models import ClinicalDocument
from apps.clinical_records.models import ClinicalRecord
from apps.accounts.models import User
from .services import NotificationService


@receiver(post_save, sender=ClinicalDocument)
def notify_on_document_upload(sender, instance, created, **kwargs):
    """Dispara notificación cuando se carga un documento"""
    if created:
        try:
            service = NotificationService()
            
            # Obtener staff del mismo tenant
            recipients = User.objects.filter(
                tenant=instance.tenant,
                is_staff=True
            ).exclude(id=instance.created_by_id if hasattr(instance, 'created_by_id') else None)
            
            service.notify_document_uploaded(instance, recipients)
        except Exception as e:
            print(f"Error en notify_on_document_upload: {e}")


@receiver(post_save, sender=ClinicalRecord)
def notify_on_record_created(sender, instance, created, **kwargs):
    """Dispara notificación cuando se crea una historia clínica"""
    if created:
        try:
            service = NotificationService()
            
            # Obtener staff del mismo tenant
            recipients = User.objects.filter(
                tenant=instance.tenant,
                is_staff=True
            ).exclude(id=instance.created_by_id if hasattr(instance, 'created_by_id') else None)
            
            service.notify_record_created(instance, recipients)
        except Exception as e:
            print(f"Error en notify_on_record_created: {e}")
