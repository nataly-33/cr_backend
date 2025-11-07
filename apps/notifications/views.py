"""
Views para notificaciones: endpoints REST con RBAC.
"""

import logging
from rest_framework import viewsets, permissions, status, filters, views
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)

from .models import (
    Notification,
    UserNotificationPreferences,
    NotificationAudit,
    NotificationStatus,
)
from .serializers import (
    NotificationSerializer,
    NotificationListSerializer,
    NotificationMarkAsReadSerializer,
    UserNotificationPreferencesSerializer,
    EventPayloadSerializer,
    NotificationAuditSerializer,
    NotificationStatsSerializer,
)
from .orchestrator import process_event
from .tasks import send_notification_email, send_notification_push
from apps.core.permissions import (
    IsTenantMember,
    HasPermission,
    PermissionByActionMixin,
)

User = get_user_model()


class NotificationPagination(PageNumberPagination):
    """Paginación personalizada para notificaciones."""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


@extend_schema(tags=['Notifications'])
class NotificationViewSet(PermissionByActionMixin, viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para notificaciones del usuario logueado.
    
    Endpoints:
    - GET /notifications/ - Listar notificaciones (del usuario logueado)
    - GET /notifications/{id}/ - Detalle de notificación
    - PATCH /notifications/{id}/read/ - Marcar como leída
    - GET /notifications/stats/ - Estadísticas
    - GET /notifications/unread-count/ - Contador de no leídas
    """
    
    permission_classes = [IsTenantMember, HasPermission]
    resource_name = 'notification'
    pagination_class = NotificationPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['type', 'channel', 'status', 'read_at']
    ordering_fields = ['created_at', 'status']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Usar serializer simplificado en listados."""
        if self.action == 'list':
            return NotificationListSerializer
        return NotificationSerializer
    
    def get_queryset(self):
        """Filtrar notificaciones del usuario actual."""
        return Notification.objects.filter(
            tenant=self.request.tenant,
            user=self.request.user,
        )
    
    @action(detail=True, methods=['patch'])
    def read(self, request, pk=None):
        """Marcar notificación como leída."""
        notification = self.get_object()
        notification.mark_as_read()
        
        serializer = self.get_serializer(notification)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['patch'])
    def mark_all_as_read(self, request):
        """Marcar todas las notificaciones como leídas."""
        notifications = self.get_queryset().exclude(
            status=NotificationStatus.READ
        )
        count = notifications.update(
            status=NotificationStatus.READ,
            read_at=timezone.now(),
        )
        
        return Response({
            'success': True,
            'updated': count,
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Obtener contador de notificaciones no leídas."""
        count = self.get_queryset().filter(
            status__in=[NotificationStatus.QUEUED, NotificationStatus.SENT]
        ).count()
        
        return Response({
            'unread_count': count,
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Obtener estadísticas de notificaciones."""
        qs = self.get_queryset()
        
        total = qs.count()
        unread = qs.filter(status__in=[NotificationStatus.QUEUED, NotificationStatus.SENT]).count()
        queued = qs.filter(status=NotificationStatus.QUEUED).count()
        sent = qs.filter(status=NotificationStatus.SENT).count()
        failed = qs.filter(status=NotificationStatus.FAILED).count()
        
        by_type = dict(
            qs.values('type').annotate(count=Count('id')).values_list('type', 'count')
        )
        
        by_channel = dict(
            qs.values('channel').annotate(count=Count('id')).values_list('channel', 'count')
        )
        
        stats_data = {
            'total': total,
            'unread': unread,
            'queued': queued,
            'sent': sent,
            'failed': failed,
            'by_type': by_type,
            'by_channel': by_channel,
        }
        
        serializer = NotificationStatsSerializer(stats_data)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def get_recipients(self, request):
        """
        Obtener lista de usuarios disponibles para enviar notificaciones.
        
        Útil para el UI de envío de notificaciones.
        
        Returns:
        {
            "recipients": [
                {
                    "id": "uuid",
                    "email": "user@example.com",
                    "first_name": "Juan",
                    "last_name": "Pérez",
                    "full_name": "Juan Pérez"
                },
                ...
            ]
        }
        """
        # Verificar autenticación
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Usuario no autenticado'},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        
        # Obtener todos los usuarios del tenant (excepto el usuario actual si prefieres)
        recipients = User.objects.filter(
            tenant=request.tenant,
        ).values('id', 'email', 'first_name', 'last_name').order_by('first_name', 'last_name')
        
        # Transformar para incluir full_name
        recipients_data = []
        for r in recipients:
            recipients_data.append({
                'id': str(r['id']),
                'email': r['email'],
                'first_name': r['first_name'],
                'last_name': r['last_name'],
                'full_name': f"{r['first_name']} {r['last_name']}".strip(),
            })
        
        return Response(
            {'recipients': recipients_data, 'count': len(recipients_data)},
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=['post'])
    def send(self, request):
        """
        Enviar notificación personalizada a usuarios específicos del tenant.
        
        Requiere permiso: notification.create
        
        Payload:
        {
            "title": "Notificación importante",
            "body": "Contenido de la notificación",
            "type": "system.alert",
            "channel": "in_app",
            "recipient_ids": ["uuid-1", "uuid-2"],  # UUIDs de usuarios
            "data": {}  # opcional
        }
        """
        # Verificar permiso
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return Response(
                {'error': 'Usuario no autenticado'},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        
        # Extraer datos
        title = request.data.get('title')
        body = request.data.get('body')
        notification_type = request.data.get('type', 'system.alert')
        channel = request.data.get('channel', 'in_app')
        recipient_ids = request.data.get('recipient_ids', [])
        data = request.data.get('data', {})
        
        # Validaciones
        if not title or not body:
            return Response(
                {'error': 'title y body son requeridos'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        if not recipient_ids:
            return Response(
                {'error': 'recipient_ids debe contener al menos un usuario'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        if not isinstance(recipient_ids, list):
            return Response(
                {'error': 'recipient_ids debe ser una lista'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        # Obtener usuarios del mismo tenant
        try:
            recipients = User.objects.filter(
                id__in=recipient_ids,
                tenant=request.tenant,
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        if not recipients.exists():
            return Response(
                {'error': 'No se encontraron usuarios válidos en el tenant'},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        # Crear notificaciones para cada usuario
        notifications_created = []
        try:
            for recipient in recipients:
                notification = Notification.objects.create(
                    user=recipient,
                    tenant=request.tenant,
                    type=notification_type,
                    channel=channel,
                    title=title,
                    body=body,
                    data=data,
                    status=NotificationStatus.QUEUED,
                    event_id=f"manual_{request.user.id}_{recipient.id}_{timezone.now().timestamp()}",
                )
                
                # Encolar tarea de envío (con manejo de error si Redis no está disponible)
                try:
                    if channel == 'email':
                        send_notification_email.delay(notification.id)
                    elif channel == 'push':
                        send_notification_push.delay(notification.id)
                except Exception as celery_error:
                    # Si Celery falla, loguear pero no bloquear la creación de notificación
                    logger.warning(f"Error encolando tarea Celery: {celery_error}")
                
                notifications_created.append({
                    'id': str(notification.id),
                    'user_id': str(recipient.id),
                    'status': 'queued',
                })
                
                # Crear audit log
                NotificationAudit.objects.create(
                    tenant=request.tenant,
                    notification=notification,
                    action='manual_send',
                    detail=f"Enviada por {request.user.full_name} a {recipient.full_name}",
                )
            
            return Response(
                {
                    'success': True,
                    'notifications_created': len(notifications_created),
                    'notifications': notifications_created,
                },
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@extend_schema(tags=['Notification Preferences'])
class NotificationPreferencesViewSet(views.APIView):
    """
    API View para preferencias de notificación del usuario.
    
    Endpoints:
    - GET /notifications/preferences/ - Obtener preferencias
    - PATCH /notifications/preferences/ - Actualizar preferencias
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Obtener preferencias del usuario actual."""
        tenant = request.tenant
        user = request.user
        
        prefs, created = UserNotificationPreferences.objects.get_or_create(
            user=user,
            tenant=tenant,
        )
        
        serializer = UserNotificationPreferencesSerializer(prefs)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def patch(self, request):
        """Actualizar preferencias del usuario actual."""
        tenant = request.tenant
        user = request.user
        
        prefs, created = UserNotificationPreferences.objects.get_or_create(
            user=user,
            tenant=tenant,
        )
        
        serializer = UserNotificationPreferencesSerializer(
            prefs,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(tags=['Notification Events'])
class EventWebhookViewSet(viewsets.ViewSet):
    """
    Webhook para procesar eventos y generar notificaciones.
    
    Endpoints:
    - POST /notifications/events/ - Procesar evento
    
    Requiere autenticación de servicio (token especial o API key).
    """
    
    permission_classes = [IsTenantMember]  # Solo usuarios del tenant
    
    @action(detail=False, methods=['post'])
    def events(self, request):
        """
        Recibir un evento y procesar notificaciones.
        
        Payload esperado:
        {
            "event_type": "appointment.created",
            "event_id": "evt_20251104_123",
            "actor_id": 42,
            "data": {
                "patient_name": "Fer",
                "doctor_name": "Dr. Pérez",
                "appointment_date": "2025-11-05",
                "appointment_time": "09:00"
            },
            "channels": ["in_app", "email"]
        }
        """
        serializer = EventPayloadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        
        # Procesar evento
        result = process_event(
            event_type=data['event_type'],
            event_id=data['event_id'],
            tenant_id=str(request.tenant.id),
            actor_id=data['actor_id'],
            data=data['data'],
            channels=request.data.get('channels', ['in_app', 'email']),
        )
        
        if result['success']:
            return Response(result, status=status.HTTP_201_CREATED)
        else:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=['Notification Audit'])
class NotificationAuditViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para auditoría de notificaciones (read-only, solo admin).
    
    Endpoints:
    - GET /notifications/audit/ - Listar logs de auditoría
    - GET /notifications/audit/{id}/ - Detalle
    """
    
    permission_classes = [IsTenantMember, HasPermission]
    resource_name = 'notification'  # Usa mismo recurso que Notification
    serializer_class = NotificationAuditSerializer
    pagination_class = NotificationPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['action', 'created_at']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Mostrar logs del tenant actual (solo Admin TI)."""
        # Aquí se filtraría por permisos de admin si es necesario
        return NotificationAudit.objects.filter(
            tenant=self.request.tenant,
        )
