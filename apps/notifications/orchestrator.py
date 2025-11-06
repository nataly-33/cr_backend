"""
Orquestador de notificaciones: lógica central de procesamiento de eventos.

Responsable de:
- Recibir eventos del dominio
- Resolver destinatarios según reglas
- Filtrar por preferencias y horarios
- Renderizar templates
- Encolar tareas de envío
- Mantener idempotencia
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, time

from django.utils import timezone
from django.db import transaction

from .models import (
    Notification,
    UserNotificationPreferences,
    NotificationAudit,
    NotificationChannel,
    NotificationStatus,
)
from .templates import render_notification
from apps.accounts.models import User
from apps.core.models import Tenant

logger = logging.getLogger(__name__)


class NotificationOrchestrator:
    """
    Orquestador de notificaciones: procesa eventos y genera notificaciones.
    """
    
    # Reglas de destinatarios por tipo de evento
    RECIPIENT_RULES = {
        'appointment.created': lambda event: [
            # Doctor de la cita
            event['data'].get('doctor_id'),
            # Paciente (opcional)
            event['data'].get('patient_id'),
        ],
        'appointment.canceled': lambda event: [
            event['data'].get('doctor_id'),
            event['data'].get('patient_id'),
        ],
        'appointment.reminder': lambda event: [
            event['data'].get('patient_id'),
            event['data'].get('doctor_id'),
        ],
        'clinical_record.result': lambda event: [
            event['data'].get('patient_id'),
            event['data'].get('doctor_id'),
        ],
        'document.uploaded': lambda event: [
            event['data'].get('patient_id'),
            event['data'].get('doctor_id'),
        ],
        'inventory.low_stock': lambda event: [
            # Admin TI del tenant
            None,  # Se resuelve en get_admin_users()
        ],
        'user.added': lambda event: [
            event['data'].get('user_id'),
        ],
        'system.alert': lambda event: [
            # Admin TI del tenant
            None,
        ],
    }
    
    def __init__(self, tenant: Tenant):
        """Inicializar con tenant."""
        self.tenant = tenant
    
    def process_event(
        self,
        event_type: str,
        event_id: str,
        actor_id: int,
        data: Dict[str, Any],
        channels: List[str] = None,
    ) -> Dict[str, Any]:
        """
        Procesar un evento y generar notificaciones.
        
        Args:
            event_type: tipo de evento (ej: 'appointment.created')
            event_id: ID único del evento para idempotencia
            actor_id: ID del usuario que causó el evento
            data: payload con variables para templates
            channels: lista de canales ['in_app', 'email', 'push']
        
        Returns:
            {
                'success': bool,
                'notifications_created': int,
                'notifications_skipped': int,
                'errors': list,
            }
        """
        channels = channels or [NotificationChannel.IN_APP, NotificationChannel.EMAIL]
        result = {
            'success': True,
            'notifications_created': 0,
            'notifications_skipped': 0,
            'errors': [],
        }
        
        try:
            # 1. Validar idempotencia
            if Notification.objects.filter(event_id=event_id).exists():
                logger.info(f"Evento duplicado ignorado: {event_id}")
                self._create_audit_log(
                    notification=None,
                    action='duplicate_ignored',
                    detail=f"Event ID: {event_id}",
                )
                return {
                    **result,
                    'notifications_skipped': 1,
                }
            
            # 2. Resolver destinatarios
            recipient_ids = self._get_recipients(event_type, data)
            
            if not recipient_ids:
                logger.warning(f"No recipients found for {event_type}")
                result['notifications_skipped'] = 1
                return result
            
            # 3. Crear notificación por destinatario × canal
            with transaction.atomic():
                for recipient_id in recipient_ids:
                    if not recipient_id:
                        continue
                    
                    try:
                        user = User.objects.get(id=recipient_id, tenant=self.tenant)
                    except User.DoesNotExist:
                        logger.warning(f"User {recipient_id} not found")
                        result['notifications_skipped'] += 1
                        continue
                    
                    # Validar preferencias
                    prefs = self._get_preferences(user)
                    
                    for channel in channels:
                        if not prefs.is_enabled(event_type, channel):
                            logger.debug(f"Skipped {event_type} for {user.email} on {channel}")
                            result['notifications_skipped'] += 1
                            self._create_audit_log(
                                notification=None,
                                action='preference_skipped',
                                detail=f"User: {user.email}, Channel: {channel}",
                            )
                            continue
                        
                        # Validar horarios de silencio
                        if self._is_in_quiet_hours(prefs):
                            logger.debug(f"In quiet hours for {user.email}")
                            result['notifications_skipped'] += 1
                            self._create_audit_log(
                                notification=None,
                                action='quiet_hours',
                                detail=f"User: {user.email}",
                            )
                            continue
                        
                        # Renderizar template
                        try:
                            title, body, icon, color = render_notification(
                                event_type,
                                language=self._get_user_language(user),
                                variables=data,
                            )
                        except ValueError as e:
                            logger.error(f"Template render error: {e}")
                            result['errors'].append(str(e))
                            continue
                        
                        # Crear notificación
                        notification = Notification.objects.create(
                            tenant=self.tenant,
                            user=user,
                            type=event_type,
                            channel=channel,
                            title=title,
                            body=body,
                            data=data,
                            extra_metadata={
                                'icon': icon,
                                'color': color,
                                'actor_id': actor_id,
                            },
                            event_id=event_id,
                            status=NotificationStatus.QUEUED,
                        )
                        
                        result['notifications_created'] += 1
                        
                        # Crear audit log
                        self._create_audit_log(
                            notification=notification,
                            action='created',
                            detail=f"Type: {event_type}, Channel: {channel}",
                        )
                        
                        logger.info(
                            f"Notification created: {notification.id} "
                            f"({event_type}/{channel}) for {user.email}"
                        )
        
        except Exception as e:
            logger.exception(f"Error processing event {event_id}")
            result['success'] = False
            result['errors'].append(str(e))
        
        return result
    
    def _get_recipients(self, event_type: str, data: Dict[str, Any]) -> List[int]:
        """Resolver lista de destinatarios para el tipo de evento."""
        rule = self.RECIPIENT_RULES.get(event_type)
        if not rule:
            logger.warning(f"Unknown event type: {event_type}")
            return []
        
        recipient_ids = rule({'data': data})
        
        # Filtrar Nones y admin users para eventos del sistema
        if event_type in ['inventory.low_stock', 'system.alert']:
            admin_ids = self._get_admin_user_ids()
            recipient_ids = [id for id in (recipient_ids + admin_ids) if id]
        else:
            recipient_ids = [id for id in recipient_ids if id]
        
        # Remover duplicados manteniendo orden
        seen = set()
        unique_ids = []
        for id in recipient_ids:
            if id not in seen:
                seen.add(id)
                unique_ids.append(id)
        
        return unique_ids
    
    def _get_admin_user_ids(self) -> List[int]:
        """Obtener IDs de usuarios Admin TI del tenant."""
        try:
            # Buscar rol 'Administrador' o 'Admin TI'
            from apps.accounts.models import Role
            admin_role = Role.objects.filter(
                tenant=self.tenant,
                name__in=['Administrador', 'Admin TI']
            ).first()
            
            if not admin_role:
                return []
            
            user_ids = list(
                User.objects.filter(role=admin_role).values_list('id', flat=True)
            )
            return user_ids
        except Exception as e:
            logger.error(f"Error getting admin user IDs: {e}")
            return []
    
    def _get_preferences(self, user: User) -> UserNotificationPreferences:
        """Obtener o crear preferencias del usuario."""
        prefs, created = UserNotificationPreferences.objects.get_or_create(
            user=user,
            tenant=self.tenant,
        )
        return prefs
    
    def _is_in_quiet_hours(self, prefs: UserNotificationPreferences) -> bool:
        """Verificar si está dentro de horarios de silencio."""
        if not prefs.quiet_hours_enabled:
            return False
        
        if not prefs.quiet_hours_from or not prefs.quiet_hours_to:
            return False
        
        now = timezone.now().time()
        
        # Si from > to (ej: 22:00 - 08:00, cruza medianoche)
        if prefs.quiet_hours_from > prefs.quiet_hours_to:
            return now >= prefs.quiet_hours_from or now < prefs.quiet_hours_to
        else:
            return prefs.quiet_hours_from <= now < prefs.quiet_hours_to
    
    def _get_user_language(self, user: User) -> str:
        """Obtener idioma del usuario (de preferencias)."""
        try:
            from apps.accounts.models import UserPreferences
            user_prefs = UserPreferences.objects.get(user=user)
            return user_prefs.language or 'es'
        except:
            return 'es'  # Default
    
    def _create_audit_log(
        self,
        notification: Optional[Notification] = None,
        action: str = 'created',
        detail: str = '',
    ) -> NotificationAudit:
        """Crear entrada de auditoría."""
        return NotificationAudit.objects.create(
            tenant=self.tenant,
            notification=notification,
            action=action,
            detail=detail,
        )


def process_event(
    event_type: str,
    event_id: str,
    tenant_id: str,
    actor_id: int,
    data: Dict[str, Any],
    channels: List[str] = None,
) -> Dict[str, Any]:
    """
    Función de entrada para procesar un evento.
    
    Típicamente llamada desde una tarea de Celery o webhook.
    """
    try:
        tenant = Tenant.objects.get(id=tenant_id)
    except Tenant.DoesNotExist:
        logger.error(f"Tenant not found: {tenant_id}")
        return {
            'success': False,
            'error': f'Tenant not found: {tenant_id}',
        }
    
    orchestrator = NotificationOrchestrator(tenant)
    return orchestrator.process_event(
        event_type=event_type,
        event_id=event_id,
        actor_id=actor_id,
        data=data,
        channels=channels,
    )
