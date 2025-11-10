from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from .models import ClinicalRecord, ClinicalForm
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

    @extend_schema_field(serializers.IntegerField)
    def get_documents_count(self, obj) -> int:
        """Cuenta los documentos de esta historia clínica"""
        return obj.clinicaldocument_set.filter(deleted_at__isnull=True).count()


class ClinicalRecordCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear historias clínicas"""

    class Meta:
        model = ClinicalRecord
        fields = [
            'id', 'patient', 'blood_type', 'allergies',
            'chronic_conditions', 'medications',
            'family_history', 'social_history', 'record_number'
        ]
        read_only_fields = ['id', 'record_number']

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


class ClinicalFormSerializer(serializers.ModelSerializer):
    """Serializer completo para formularios clínicos"""
    filled_by_name = serializers.CharField(
        source='filled_by.get_full_name',
        read_only=True
    )
    form_type_display = serializers.CharField(
        source='get_form_type_display',
        read_only=True
    )
    record_number = serializers.CharField(
        source='clinical_record.record_number',
        read_only=True
    )
    patient_name = serializers.CharField(
        source='clinical_record.patient.get_full_name',
        read_only=True
    )

    class Meta:
        model = ClinicalForm
        fields = [
            'id', 'clinical_record', 'record_number', 'patient_name',
            'form_type', 'form_type_display', 'form_template_id',
            'form_data', 'filled_by', 'filled_by_name',
            'doctor_name', 'doctor_specialty', 'form_date',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_form_data(self, value):
        """Validar estructura del form_data según el tipo"""
        if not isinstance(value, dict):
            raise serializers.ValidationError('form_data debe ser un objeto JSON')
        return value


class ClinicalFormCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear formularios clínicos"""

    class Meta:
        model = ClinicalForm
        fields = [
            'id', 'clinical_record', 'form_type', 'form_template_id',
            'form_data', 'filled_by', 'doctor_name', 'doctor_specialty',
            'form_date'
        ]
        read_only_fields = ['id', 'filled_by']

    def validate_clinical_record(self, value):
        """Validar que la historia clínica esté activa"""
        if value.status == 'closed':
            raise serializers.ValidationError(
                'No se pueden agregar formularios a una historia clínica cerrada'
            )
        return value

    def create(self, validated_data):
        """Crear formulario con tenant del request"""
        validated_data['tenant'] = self.context['request'].tenant
        return super().create(validated_data)


class ClinicalFormUpdateSerializer(serializers.ModelSerializer):
    """Serializer para actualizar formularios clínicos"""

    class Meta:
        model = ClinicalForm
        fields = [
            'id', 'clinical_record', 'form_type', 'form_template_id',
            'form_data', 'doctor_name', 'doctor_specialty',
            'form_date'
        ]
        read_only_fields = ['id', 'form_type', 'clinical_record']