"""
Signals para notificaciones automáticas de documentos.
"""
import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone

from .models import ClinicalDocument
from apps.notifications.orchestrator import NotificationOrchestrator
from apps.accounts.models import User

logger = logging.getLogger(__name__)


@receiver(post_save, sender=ClinicalDocument)
def notify_document_created_or_updated(sender, instance, created, **kwargs):
    """
    Notificar al Admin cuando se crea o actualiza un documento.
    """
    # Evitar notificaciones en migraciones o fixtures
    if kwargs.get('raw', False):
        return
    
    try:
        # Obtener el usuario actual (el que hizo la acción)
        from crum import get_current_user
        actor = get_current_user()
        
        if not actor:
            logger.warning("No se pudo determinar el usuario actual")
            return
        
        # Determinar tipo de evento
        event_type = 'document.created' if created else 'document.updated'
        event_id = f"{event_type}:{instance.id}:{timezone.now().timestamp()}"
        
        # Preparar datos para la notificación
        data = {
            'document_id': str(instance.id),
            'document_title': instance.title,
            'document_type': instance.get_document_type_display(),
            'patient_name': instance.clinical_record.patient.get_full_name(),
            'actor_name': actor.get_full_name(),
            'created_at': instance.created_at.isoformat(),
        }
        
        # Obtener Admin TI del tenant
        orchestrator = NotificationOrchestrator(instance.tenant)
        admin_ids = orchestrator._get_admin_user_ids()
        
        if not admin_ids:
            logger.warning(f"No se encontraron admins en tenant {instance.tenant.id}")
            return
        
        # Solo notificar si el actor NO es admin (evitar auto-notificaciones)
        if actor.id in admin_ids:
            logger.debug("Actor es admin, no se envía notificación")
            return
        
        # Procesar evento
        result = orchestrator.process_event(
            event_type=event_type,
            event_id=event_id,
            actor_id=str(actor.id),  # Convertir UUID a string
            data=data,
            channels=['in_app', 'push']  # Email sería spam
        )
        
        logger.info(
            f"Notificación de documento procesada: {result['notifications_created']} creadas"
        )
    
    except Exception as e:
        logger.exception(f"Error al notificar documento: {e}")


@receiver(post_delete, sender=ClinicalDocument)
def notify_document_deleted(sender, instance, **kwargs):
    """
    Notificar al Admin cuando se elimina un documento (CRÍTICO).
    """
    try:
        from crum import get_current_user
        actor = get_current_user()
        
        if not actor:
            logger.warning("No se pudo determinar el usuario que eliminó el documento")
            return
        
        event_type = 'document.deleted'
        event_id = f"{event_type}:{instance.id}:{timezone.now().timestamp()}"
        
        data = {
            'document_id': str(instance.id),
            'document_title': instance.title,
            'document_type': instance.get_document_type_display(),
            'patient_name': instance.clinical_record.patient.get_full_name(),
            'actor_name': actor.get_full_name(),
            'deleted_at': timezone.now().isoformat(),
        }
        
        orchestrator = NotificationOrchestrator(instance.tenant)
        admin_ids = orchestrator._get_admin_user_ids()
        
        if not admin_ids:
            logger.warning(f"No se encontraron admins en tenant {instance.tenant.id}")
            return
        
        # SIEMPRE notificar eliminaciones, incluso si es admin
        result = orchestrator.process_event(
            event_type=event_type,
            event_id=event_id,
            actor_id=str(actor.id),  # Convertir UUID a string
            data=data,
            channels=['in_app', 'push', 'email']  # Email porque es crítico
        )
        
        logger.warning(
            f"DOCUMENTO ELIMINADO - Notificación enviada a {result['notifications_created']} admins"
        )
    
    except Exception as e:
        logger.exception(f"Error al notificar eliminación de documento: {e}")
