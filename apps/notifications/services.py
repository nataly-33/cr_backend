import os
import uuid
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from .models import (
    Notification,
    NotificationType,
    NotificationChannel,
    NotificationStatus,
    UserNotificationPreferences,
    NotificationAudit,
)


class NotificationService:
    """Servicio para crear y gestionar notificaciones."""
    
    def create_notification(
        self,
        tenant,
        user,
        title,
        body,
        notification_type=NotificationType.SYSTEM_ALERT,
        channel=NotificationChannel.IN_APP,
        data=None,
        extra_metadata=None,
    ):
        """
        Crear una notificación.
        
        Args:
            tenant: Tenant del usuario
            user: Usuario destinatario
            title: Título de la notificación
            body: Cuerpo del mensaje
            notification_type: Tipo de notificación
            channel: Canal de entrega
            data: Datos adicionales (dict)
            extra_metadata: Metadatos flexibles (dict)
        
        Returns:
            Notification: Notificación creada
        """
        # Generar event_id único
        event_id = f"{notification_type}_{user.id}_{timezone.now().timestamp()}_{uuid.uuid4().hex[:8]}"
        
        # Verificar si ya existe (idempotencia)
        try:
            existing = Notification.objects.get(event_id=event_id)
            return existing
        except Notification.DoesNotExist:
            pass
        
        # Crear notificación
        notification = Notification.objects.create(
            tenant=tenant,
            user=user,
            type=notification_type,
            channel=channel,
            title=title,
            body=body,
            data=data or {},
            extra_metadata=extra_metadata or {},
            event_id=event_id,
            status=NotificationStatus.QUEUED,
        )
        
        # Log en auditoría
        NotificationAudit.objects.create(
            tenant=tenant,
            notification=notification,
            action='created',
            detail=f"Notificación {notification_type} creada automáticamente",
        )
        
        return notification
    
    def notify_document_uploaded(self, document, recipients):
        """
        Notificar cuando se carga un documento.
        
        Args:
            document: ClinicalDocument instance
            recipients: Queryset de Users o lista de Users
        """
        if not hasattr(recipients, '__iter__'):
            recipients = [recipients]
        
        for recipient in recipients:
            # Verificar preferencias del usuario
            prefs, _ = UserNotificationPreferences.objects.get_or_create(
                tenant=document.tenant,
                user=recipient
            )
            
            # Crear notificación in-app
            notification = self.create_notification(
                tenant=document.tenant,
                user=recipient,
                title=f"Nuevo documento: {document.document_type}",
                body=f"Se cargó un documento de tipo {document.document_type}",
                notification_type=NotificationType.DOCUMENT_UPLOADED,
                channel=NotificationChannel.IN_APP,
                data={
                    'document_id': str(document.id),
                    'document_type': document.document_type,
                    'created_by': str(document.created_by_id) if document.created_by else None,
                },
                extra_metadata={
                    'icon': 'file',
                    'color': 'blue',
                    'link': f"/documents/{document.id}",
                }
            )
            
            # Marcar como enviada
            notification.mark_as_sent()
            
            # Log en auditoría
            NotificationAudit.objects.create(
                tenant=document.tenant,
                notification=notification,
                action='sent',
                detail=f"Documento cargado notificado a {recipient.email}",
            )
    
    def notify_record_created(self, record, recipients):
        """
        Notificar cuando se crea una historia clínica.
        
        Args:
            record: ClinicalRecord instance
            recipients: Queryset de Users o lista de Users
        """
        if not hasattr(recipients, '__iter__'):
            recipients = [recipients]
        
        for recipient in recipients:
            # Crear notificación
            notification = self.create_notification(
                tenant=record.tenant,
                user=recipient,
                title=f"Nueva historia clínica para {record.patient.get_full_name()}",
                body=f"Se creó una nueva historia clínica",
                notification_type=NotificationType.CLINICAL_RESULT,
                channel=NotificationChannel.IN_APP,
                data={
                    'record_id': str(record.id),
                    'record_number': record.record_number,
                    'patient_name': record.patient.get_full_name(),
                },
                extra_metadata={
                    'icon': 'file-medical',
                    'color': 'green',
                    'link': f"/clinical-records/{record.id}",
                }
            )
            
            # Marcar como enviada
            notification.mark_as_sent()
            
            # Log en auditoría
            NotificationAudit.objects.create(
                tenant=record.tenant,
                notification=notification,
                action='sent',
                detail=f"Historia clínica creada notificada a {recipient.email}",
            )
