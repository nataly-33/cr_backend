from rest_framework import serializers
from .models import Patient


class PatientSerializer(serializers.ModelSerializer):
    """Serializer completo para pacientes"""
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    age = serializers.IntegerField(source='get_age', read_only=True)
    created_by_name = serializers.CharField(
        source='created_by.get_full_name',
        read_only=True
    )

    class Meta:
        model = Patient
        fields = [
            'id', 'identity_document_type', 'identity_document',
            'first_name', 'last_name', 'full_name',
            'date_of_birth', 'age', 'gender',
            'phone', 'email', 'address', 'city',
            'emergency_contact',
            'created_by', 'created_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']

    def validate_identity_document(self, value):
        """Validar que el documento sea único en el tenant"""
        tenant = self.context['request'].tenant
        instance = self.instance

        query = Patient.objects.filter(
            tenant=tenant,
            identity_document=value
        )

        if instance:
            query = query.exclude(id=instance.id)

        if query.exists():
            raise serializers.ValidationError(
                'Ya existe un paciente con este número de documento'
            )

        return value


class PatientListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listados"""
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    age = serializers.IntegerField(source='get_age', read_only=True)

    class Meta:
        model = Patient
        fields = [
            'id', 'identity_document', 'full_name',
            'age', 'gender', 'phone', 'created_at'
        ]