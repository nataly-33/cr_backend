from rest_framework import serializers
from apps.core.models import Tenant


class TenantSerializer(serializers.ModelSerializer):
    """Serializer para tenants"""
    users_count = serializers.SerializerMethodField()
    is_active_status = serializers.BooleanField(source='is_active', read_only=True)

    class Meta:
        model = Tenant
        fields = [
            'id', 'name', 'slug', 'subdomain',
            'subscription_plan', 'subscription_status',
            'subscription_start', 'subscription_end',
            'email', 'phone', 'address',
            'max_users', 'max_storage_gb',
            'users_count', 'is_active_status',
            'settings', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']

    def get_users_count(self, obj):
        return obj.users.filter(is_active=True).count()