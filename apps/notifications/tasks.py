"""
Tareas asíncronas (Celery) para el sistema de notificaciones.

Responsable de:
- Enviar emails
- Enviar push notifications
- Reintentos con backoff exponencial
- Manejo de fallos
"""

import logging
import smtplib
from typing import Dict, Any
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from celery import shared_task
from celery.exceptions import Retry
from django.conf import settings
from django.utils import timezone

from .models import Notification, NotificationStatus

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def send_notification_email(self, notification_id: str) -> Dict[str, Any]:
    """
    Enviar notificación por email.
    
    Reintenta hasta 3 veces con backoff exponencial: 60s, 300s, 900s.
    """
    try:
        notification = Notification.objects.get(id=notification_id)
    except Notification.DoesNotExist:
        logger.error(f"Notification not found: {notification_id}")
        return {'success': False, 'error': 'Notification not found'}
    
    try:
        # Preparar email
        sender_email = settings.DEFAULT_FROM_EMAIL or 'noreply@clinidocs.com'
        recipient_email = notification.user.email
        
        # Crear email HTML
        subject = notification.title
        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6;">
                <h2>{notification.title}</h2>
                <p>{notification.body}</p>
                <hr>
                <p style="font-size: 0.9em; color: #666;">
                    Enviado el {timezone.now().strftime('%d/%m/%Y %H:%M')} desde CliniDocs
                </p>
            </body>
        </html>
        """
        
        text_body = f"{notification.title}\n\n{notification.body}"
        
        # Crear mensaje MIME
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = sender_email
        msg['To'] = recipient_email
        
        msg.attach(MIMEText(text_body, 'plain'))
        msg.attach(MIMEText(html_body, 'html'))
        
        # Enviar (configuración según SMTP en settings)
        if getattr(settings, 'EMAIL_BACKEND', '') == 'django.core.mail.backends.locmem.EmailBackend':
            # En desarrollo con console backend
            logger.info(f"[DEV MODE] Email to {recipient_email}: {subject}")
        else:
            # Envío real SMTP
            with smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT) as server:
                if settings.EMAIL_USE_TLS:
                    server.starttls()
                if settings.EMAIL_HOST_USER:
                    server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
                
                server.sendmail(sender_email, recipient_email, msg.as_string())
        
        # Marcar como enviada
        notification.mark_as_sent()
        logger.info(f"Email sent: {notification_id} to {recipient_email}")
        
        return {
            'success': True,
            'notification_id': str(notification_id),
            'recipient': recipient_email,
        }
    
    except smtplib.SMTPException as e:
        logger.warning(f"SMTP error for {notification_id}: {e}")
        
        # Reintentar con backoff exponencial
        retry_count = self.request.retries
        countdown = (60 * (2 ** retry_count))  # 60s, 300s, 900s
        
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=countdown)
        else:
            # Marcar como fallida después de 3 intentos
            notification.mark_as_failed(f"SMTP error after 3 retries: {str(e)}")
            logger.error(f"Email failed permanently: {notification_id}")
            return {
                'success': False,
                'notification_id': str(notification_id),
                'error': str(e),
                'retries_exhausted': True,
            }
    
    except Exception as e:
        logger.exception(f"Unexpected error sending email for {notification_id}")
        notification.mark_as_failed(f"Unexpected error: {str(e)}")
        return {
            'success': False,
            'notification_id': str(notification_id),
            'error': str(e),
        }


@shared_task(bind=True, max_retries=3)
def send_notification_push(self, notification_id: str) -> Dict[str, Any]:
    """
    Enviar notificación push (Firebase Cloud Messaging).
    
    Flujo:
    1. Obtiene la notificación de BD
    2. Si user tiene fcm_token → envía a Firebase
    3. Si no tiene token → solo registra en BD (in-app)
    4. Reintentos automáticos si falla
    
    IMPORTANTE: Los datos van al request.user automáticamente del endpoint,
    no es necesario modificar nada cuando Luis envíe el token.
    """
    try:
        notification = Notification.objects.get(id=notification_id)
    except Notification.DoesNotExist:
        logger.error(f"Notification not found: {notification_id}")
        return {'success': False, 'error': 'Notification not found'}
    
    try:
        # 1️⃣ Verificar si el usuario tiene FCM token
        if not notification.user.fcm_token:
            logger.info(
                f"⏭️ No FCM token for {notification.user.email} - "
                f"Notification saved in-app only"
            )
            notification.mark_as_sent()
            return {
                'success': True,
                'notification_id': str(notification_id),
                'message': 'Saved in-app (no FCM token)',
                'sent_via': 'in_app_only',
            }
        
        # 2️⃣ Inicializar Firebase Admin SDK
        import firebase_admin
        from firebase_admin import credentials, messaging
        import json
        import os
        
        # Cargar credenciales
        cred_json = os.getenv('FIREBASE_SERVICE_ACCOUNT_KEY')
        if not cred_json:
            raise ValueError("FIREBASE_SERVICE_ACCOUNT_KEY not configured in .env")
        
        cred_dict = json.loads(cred_json)
        cred = credentials.Certificate(cred_dict)
        
        # Inicializar (solo si no está)
        try:
            firebase_admin.initialize_app(cred)
        except ValueError:
            pass  # Ya estaba inicializado
        
        # 3️⃣ Crear mensaje Firebase
        message = messaging.Message(
            notification=messaging.Notification(
                title=notification.title,
                body=notification.body,
            ),
            data={
                'notification_id': str(notification.id),
                'type': notification.type,
                **(notification.data or {})
            },
            token=notification.user.fcm_token,
        )
        
        # 4️⃣ Enviar a Firebase
        response = messaging.send(message)
        logger.info(
            f"✅ Push sent to {notification.user.email} - "
            f"Message ID: {response}"
        )
        
        # 5️⃣ Marcar como enviada
        notification.mark_as_sent()
        
        return {
            'success': True,
            'notification_id': str(notification_id),
            'message_id': response,
            'sent_via': 'firebase_push',
            'recipient': notification.user.email,
        }
    
    except Exception as e:
        logger.warning(f"⚠️ Error sending push for {notification_id}: {e}")
        
        # Reintentar 3 veces con backoff exponencial
        if self.request.retries < self.max_retries:
            countdown = 60 * (2 ** self.request.retries)  # 60s, 120s, 240s
            logger.info(f"Retrying in {countdown}s (attempt {self.request.retries + 1}/3)")
            raise self.retry(exc=e, countdown=countdown)
        else:
            # Falló 3 veces - marcar como fallida pero guardar en BD
            logger.error(
                f"❌ Push notification failed permanently for {notification.user.email}"
            )
            notification.mark_as_failed(f"Firebase error after 3 retries: {str(e)}")
            
            return {
                'success': False,
                'notification_id': str(notification_id),
                'error': str(e),
                'retries_exhausted': True,
                'fallback': 'saved_in_app',
            }


@shared_task
def send_notifications_batch(notification_ids: list, channel: str = 'email') -> Dict[str, Any]:
    """
    Enviar un lote de notificaciones por canal.
    
    Útil para procesamiento en batch.
    """
    results = {
        'channel': channel,
        'total': len(notification_ids),
        'successful': 0,
        'failed': 0,
        'errors': [],
    }
    
    for notif_id in notification_ids:
        try:
            if channel == 'email':
                send_notification_email.delay(notif_id)
            elif channel == 'push':
                send_notification_push.delay(notif_id)
            else:
                logger.warning(f"Unknown channel: {channel}")
                results['errors'].append(f"Unknown channel: {channel}")
                results['failed'] += 1
                continue
            
            results['successful'] += 1
        except Exception as e:
            logger.error(f"Error queueing notification {notif_id}: {e}")
            results['failed'] += 1
            results['errors'].append(str(e))
    
    return results


@shared_task
def requeue_failed_notifications(max_age_hours: int = 24) -> Dict[str, Any]:
    """
    Reintentar notificaciones que fallaron hace menos de max_age_hours.
    
    Útil como tarea programada de Celery Beat.
    """
    from datetime import timedelta
    
    cutoff_time = timezone.now() - timedelta(hours=max_age_hours)
    
    failed_notifications = Notification.objects.filter(
        status=NotificationStatus.FAILED,
        updated_at__gte=cutoff_time,
        retry_count__lt=3,
    )
    
    results = {
        'requeued': 0,
        'errors': [],
    }
    
    for notif in failed_notifications:
        try:
            notif.retry_count += 1
            notif.status = NotificationStatus.QUEUED
            notif.save(update_fields=['retry_count', 'status'])
            
            if notif.channel == 'email':
                send_notification_email.delay(str(notif.id))
            elif notif.channel == 'push':
                send_notification_push.delay(str(notif.id))
            
            results['requeued'] += 1
        except Exception as e:
            logger.error(f"Error requeueing notification {notif.id}: {e}")
            results['errors'].append(str(e))
    
    logger.info(f"Requeued {results['requeued']} failed notifications")
    return results


@shared_task
def cleanup_old_notifications(days: int = 90) -> Dict[str, Any]:
    """
    Limpiar notificaciones antiguas (mark_deleted pero no eliminar).
    
    Ejecutada semanalmente como tarea de Celery Beat.
    """
    from datetime import timedelta
    
    cutoff_date = timezone.now() - timedelta(days=days)
    
    old_notifications = Notification.objects.filter(
        read_at__lt=cutoff_date,
    )
    
    count = old_notifications.count()
    # En future: marcar como archived en lugar de eliminar
    # old_notifications.update(archived=True)
    
    logger.info(f"Identified {count} old notifications for cleanup (older than {days} days)")
    
    return {
        'cleaned_up': count,
        'cutoff_date': cutoff_date.isoformat(),
    }
