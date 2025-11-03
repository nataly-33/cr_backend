from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone

from .models import Notification, NotificationPreference
from .serializers import NotificationSerializer, NotificationPreferenceSerializer


class NotificationViewSet(viewsets.ModelViewSet):
    """ViewSet para notificaciones del usuario"""
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer
    
    def get_queryset(self):
        """Solo mostrar notificaciones del usuario actual"""
        return Notification.objects.filter(
            user=self.request.user,
            tenant=self.request.tenant
        )
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Obtener cantidad de notificaciones sin leer"""
        count = Notification.objects.filter(
            user=request.user,
            tenant=request.tenant,
            is_read=False
        ).count()
        return Response({'unread_count': count})
    
    @action(detail=False, methods=['get'])
    def unread(self, request):
        """Listar notificaciones sin leer"""
        queryset = self.get_queryset().filter(is_read=False)[:10]
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def mark_all_as_read(self, request):
        """Marcar todas las notificaciones como leídas"""
        updated = Notification.objects.filter(
            user=request.user,
            tenant=request.tenant,
            is_read=False
        ).update(is_read=True, read_at=timezone.now())
        
        return Response({'updated': updated})
    
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """Marcar notificación específica como leída"""
        notification = self.get_object()
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save()
        
        return Response(NotificationSerializer(notification).data)


class NotificationPreferenceViewSet(viewsets.ViewSet):
    """ViewSet para preferencias de notificación"""
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get', 'put'])
    def my_preferences(self, request):
        """Obtener/actualizar preferencias del usuario"""
        prefs, created = NotificationPreference.objects.get_or_create(
            user=request.user,
            tenant=request.tenant
        )
        
        if request.method == 'PUT':
            serializer = NotificationPreferenceSerializer(
                prefs,
                data=request.data,
                partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        
        serializer = NotificationPreferenceSerializer(prefs)
        return Response(serializer.data)
