from rest_framework import serializers
from .models import Notification, NotificationPreference


class NotificationSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = Notification
        fields = [
            'id', 'type', 'title', 'message', 'is_read',
            'icon', 'color', 'related_model', 'related_id',
            'user_email', 'created_at', 'read_at'
        ]
        read_only_fields = ['id', 'created_at']


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPreference
        fields = [
            'document_uploaded_email',
            'record_created_email',
            'record_updated_email',
            'access_granted_email',
            'comment_added_email',
            'max_emails_per_day',
            'quiet_hours_start',
            'quiet_hours_end',
            'send_daily_digest'
        ]
