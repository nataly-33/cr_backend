from rest_framework import serializers
from .models import ClinicalRecord
from apps.patients.serializers import PatientListSerializer


class ClinicalRecordSerializer(serializers.ModelSerializer):
    """Serializer completo para historias clínicas"""
    patient_info = PatientListSerializer(source='patient', read_only=True)
    created_by_name = serializers.CharField(
        source='created_by.get_full_name',
        read_only=True
    )
    documents_count = serializers.SerializerMethodField()

    class Meta:
        model = ClinicalRecord
        fields = [
            'id', 'patient', 'patient_info', 'record_number',
            'status', 'blood_type', 'allergies',
            'chronic_conditions', 'medications',
            'family_history', 'social_history',
            'documents_count',
            'created_by', 'created_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'record_number', 'created_at', 'updated_at', 'created_by']

    def get_documents_count(self, obj):
        """Cuenta los documentos de esta historia clínica"""
        return obj.clinicaldocument_set.filter(deleted_at__isnull=True).count()


class ClinicalRecordCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear historias clínicas"""

    class Meta:
        model = ClinicalRecord
        fields = [
            'patient', 'blood_type', 'allergies',
            'chronic_conditions', 'medications',
            'family_history', 'social_history'
        ]

    def validate_patient(self, value):
        """Validar que el paciente no tenga ya una historia clínica activa"""
        tenant = self.context['request'].tenant

        if ClinicalRecord.objects.filter(
            tenant=tenant,
            patient=value,
            status='active',
            deleted_at__isnull=True
        ).exists():
            raise serializers.ValidationError(
                'Este paciente ya tiene una historia clínica activa'
            )

        return value