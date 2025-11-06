import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from django.template.loader import render_to_string
from django.utils import timezone
from .models import Notification, NotificationPreference, EmailLog


class NotificationService:
    def __init__(self):
        api_key = os.environ.get('SENDGRID_API_KEY')
        if not api_key:
            raise ValueError("SENDGRID_API_KEY no configurada en .env")
        self.sg = SendGridAPIClient(api_key)
        self.from_email = os.environ.get('SENDGRID_FROM_EMAIL', 'noreply@clinicalrecords.com')
    
    def send_email(self, to_email, subject, template_name, context):
        """
        Enviar email usando SendGrid
        
        Args:
            to_email: Email del destinatario
            subject: Asunto del email
            template_name: Nombre del template HTML
            context: Contexto para renderizar template
        
        Returns:
            bool: True si fue exitoso
        """
        try:
            # Renderizar template
            html_content = render_to_string(
                f'emails/{template_name}',
                context
            )
            
            # Crear mensaje
            message = Mail(
                from_email=self.from_email,
                to_emails=to_email,
                subject=subject,
                html_content=html_content
            )
            
            # Enviar
            response = self.sg.send(message)
            
            # Log
            EmailLog.objects.create(
                user_email=to_email,
                subject=subject,
                notification_type=context.get('type', 'other'),
                status='sent',
                sent_at=timezone.now()
            )
            
            return response.status_code in [200, 202]
        
        except Exception as e:
            # Log error
            EmailLog.objects.create(
                user_email=to_email,
                subject=subject,
                notification_type=context.get('type', 'other'),
                status='failed',
                error_message=str(e)
            )
            print(f"Error enviando email: {e}")
            return False
    
    def can_send_email(self, user):
        """Verificar si se puede enviar email (respeta límites)"""
        prefs, created = NotificationPreference.objects.get_or_create(user=user)
        
        # Verificar limit diario
        today_start = timezone.now().replace(hour=0, minute=0, second=0)
        today_emails = EmailLog.objects.filter(
            user_email=user.email,
            status='sent',
            sent_at__gte=today_start
        ).count()
        
        if today_emails >= prefs.max_emails_per_day:
            return False
        
        return True
    
    def notify_document_uploaded(self, document, recipients):
        """Notificar cuando se carga un documento"""
        for recipient in recipients:
            # Verificar preferencias
            prefs, created = NotificationPreference.objects.get_or_create(user=recipient)
            if not prefs.document_uploaded_email:
                continue
            
            if not self.can_send_email(recipient):
                continue
            
            # Crear notificación in-app
            Notification.objects.create(
                tenant=document.tenant,
                user=recipient,
                type='document_uploaded',
                title=f'Nuevo documento: {document.name}',
                message=f'Se cargó el documento {document.name}',
                related_model='ClinicalDocument',
                related_id=str(document.id),
                icon='file',
                color='blue'
            )
            
            # Enviar email
            context = {
                'user': recipient,
                'document': document,
                'type': 'document_uploaded'
            }
            
            self.send_email(
                recipient.email,
                f'Nuevo documento cargado: {document.name}',
                'document_uploaded.html',
                context
            )
    
    def notify_record_created(self, record, recipients):
        """Notificar cuando se crea una historia clínica"""
        for recipient in recipients:
            prefs, created = NotificationPreference.objects.get_or_create(user=recipient)
            if not prefs.record_created_email:
                continue
            
            if not self.can_send_email(recipient):
                continue
            
            Notification.objects.create(
                tenant=record.tenant,
                user=recipient,
                type='record_created',
                title=f'Nueva historia clínica para {record.patient.full_name}',
                message=f'Se creó una nueva historia clínica',
                related_model='ClinicalRecord',
                related_id=str(record.id),
                icon='file-medical',
                color='green'
            )
            
            context = {
                'user': recipient,
                'record': record,
                'type': 'record_created'
            }
            
            self.send_email(
                recipient.email,
                f'Nueva historia clínica para {record.patient.full_name}',
                'record_created.html',
                context
            )
