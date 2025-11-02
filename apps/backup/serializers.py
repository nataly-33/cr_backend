from rest_framework import serializers
from .models import BackupJob


class BackupJobSerializer(serializers.ModelSerializer):
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    size_mb = serializers.SerializerMethodField()
    
    class Meta:
        model = BackupJob
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_size_mb(self, obj):
        if obj.backup_size_bytes:
            return round(obj.backup_size_bytes / (1024 * 1024), 2)
        return None