"""
Signals para notificaciones automáticas de historias clínicas.
"""
import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone

from .models import ClinicalRecord, ClinicalForm
from apps.notifications.orchestrator import NotificationOrchestrator

logger = logging.getLogger(__name__)


@receiver(post_save, sender=ClinicalRecord)
def notify_clinical_record_created_or_updated(sender, instance, created, **kwargs):
    """
    Notificar al Admin cuando se crea o actualiza una historia clínica.
    """
    if kwargs.get('raw', False):
        return
    
    try:
        from crum import get_current_user
        actor = get_current_user()
        
        if not actor:
            return
        
        event_type = 'clinical_record.created' if created else 'clinical_record.updated'
        event_id = f"{event_type}:{instance.id}:{timezone.now().timestamp()}"
        
        data = {
            'record_id': str(instance.id),
            'record_number': instance.record_number,
            'patient_name': instance.patient.get_full_name(),
            'status': instance.get_status_display(),
            'actor_name': actor.get_full_name(),
            'timestamp': timezone.now().isoformat(),
        }
        
        orchestrator = NotificationOrchestrator(instance.tenant)
        admin_ids = orchestrator._get_admin_user_ids()
        
        if not admin_ids or actor.id in admin_ids:
            return
        
        result = orchestrator.process_event(
            event_type=event_type,
            event_id=event_id,
            actor_id=str(actor.id),  # Convertir UUID a string
            data=data,
            channels=['in_app', 'push']
        )
        
        logger.info(f"Notificación de historia clínica: {result['notifications_created']} creadas")
    
    except Exception as e:
        logger.exception(f"Error al notificar historia clínica: {e}")


@receiver(post_delete, sender=ClinicalRecord)
def notify_clinical_record_deleted(sender, instance, **kwargs):
    """
    Notificar al Admin cuando se elimina una historia clínica (MUY CRÍTICO).
    """
    try:
        from crum import get_current_user
        actor = get_current_user()
        
        if not actor:
            return
        
        event_type = 'clinical_record.deleted'
        event_id = f"{event_type}:{instance.id}:{timezone.now().timestamp()}"
        
        data = {
            'record_id': str(instance.id),
            'record_number': instance.record_number,
            'patient_name': instance.patient.get_full_name(),
            'actor_name': actor.get_full_name(),
            'deleted_at': timezone.now().isoformat(),
        }
        
        orchestrator = NotificationOrchestrator(instance.tenant)
        
        # SIEMPRE notificar eliminaciones
        result = orchestrator.process_event(
            event_type=event_type,
            event_id=event_id,
            actor_id=str(actor.id),  # Convertir UUID a string
            data=data,
            channels=['in_app', 'push', 'email']
        )
        
        logger.warning(
            f"HISTORIA CLÍNICA ELIMINADA - Notificación enviada a {result['notifications_created']} admins"
        )
    
    except Exception as e:
        logger.exception(f"Error al notificar eliminación de historia clínica: {e}")


@receiver(post_save, sender=ClinicalForm)
def notify_clinical_form_created_or_updated(sender, instance, created, **kwargs):
    """
    Notificar al Admin cuando se crea o actualiza un formulario clínico.
    """
    if kwargs.get('raw', False):
        return
    
    try:
        from crum import get_current_user
        actor = get_current_user()
        
        if not actor:
            return
        
        event_type = 'clinical_form.created' if created else 'clinical_form.updated'
        event_id = f"{event_type}:{instance.id}:{timezone.now().timestamp()}"
        
        data = {
            'form_id': str(instance.id),
            'form_type': instance.get_form_type_display(),
            'clinical_record': instance.clinical_record.record_number,
            'patient_name': instance.clinical_record.patient.get_full_name(),
            'actor_name': actor.get_full_name(),
            'timestamp': timezone.now().isoformat(),
        }
        
        orchestrator = NotificationOrchestrator(instance.tenant)
        admin_ids = orchestrator._get_admin_user_ids()
        
        if not admin_ids or actor.id in admin_ids:
            return
        
        result = orchestrator.process_event(
            event_type=event_type,
            event_id=event_id,
            actor_id=str(actor.id),  # Convertir UUID a string
            data=data,
            channels=['in_app', 'push']
        )
        
        logger.info(f"Notificación de formulario clínico: {result['notifications_created']} creadas")
    
    except Exception as e:
        logger.exception(f"Error al notificar formulario clínico: {e}")


@receiver(post_delete, sender=ClinicalForm)
def notify_clinical_form_deleted(sender, instance, **kwargs):
    """
    Notificar al Admin cuando se elimina un formulario clínico (CRÍTICO).
    """
    try:
        from crum import get_current_user
        actor = get_current_user()
        
        if not actor:
            return
        
        event_type = 'clinical_form.deleted'
        event_id = f"{event_type}:{instance.id}:{timezone.now().timestamp()}"
        
        data = {
            'form_id': str(instance.id),
            'form_type': instance.get_form_type_display(),
            'clinical_record': instance.clinical_record.record_number,
            'patient_name': instance.clinical_record.patient.get_full_name(),
            'actor_name': actor.get_full_name(),
            'deleted_at': timezone.now().isoformat(),
        }
        
        orchestrator = NotificationOrchestrator(instance.tenant)
        
        # SIEMPRE notificar eliminaciones
        result = orchestrator.process_event(
            event_type=event_type,
            event_id=event_id,
            actor_id=str(actor.id),  # Convertir UUID a string
            data=data,
            channels=['in_app', 'push', 'email']
        )
        
        logger.warning(
            f"FORMULARIO CLÍNICO ELIMINADO - Notificación enviada a {result['notifications_created']} admins"
        )
    
    except Exception as e:
        logger.exception(f"Error al notificar eliminación de formulario clínico: {e}")
