from rest_framework import serializers
from .models import ClinicalDocument, MedicalImage, DocumentAccessLog


class ClinicalDocumentSerializer(serializers.ModelSerializer):
    """Serializer completo para documentos clínicos"""
    clinical_record_info = serializers.SerializerMethodField()
    patient_name = serializers.CharField(
        source='clinical_record.patient.get_full_name',
        read_only=True
    )
    created_by_name = serializers.CharField(
        source='created_by.get_full_name',
        read_only=True
    )
    signed_by_name = serializers.CharField(
        source='signed_by.get_full_name',
        read_only=True
    )
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = ClinicalDocument
        fields = [
            'id', 'clinical_record', 'clinical_record_info', 'patient_name',
            'document_type', 'title', 'description',
            'document_date', 'specialty', 'doctor_name', 'doctor_license',
            'content', 'file_path', 'file_name', 'file_size_bytes',
            'mime_type', 'file_hash', 'file_url',
            'ocr_text', 'ocr_confidence', 'ocr_processed',
            'is_signed', 'signed_at', 'signed_by', 'signed_by_name',
            'digital_signature', 'is_locked', 'tags',
            'created_by', 'created_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'file_hash', 'ocr_text', 'ocr_confidence', 'ocr_processed',
            'is_signed', 'signed_at', 'signed_by', 'digital_signature',
            'created_at', 'updated_at', 'created_by'
        ]

    def get_clinical_record_info(self, obj):
        """Info resumida de la historia clínica"""
        return {
            'id': str(obj.clinical_record.id),
            'record_number': obj.clinical_record.record_number,
            'patient_name': obj.clinical_record.patient.get_full_name()
        }

    def get_file_url(self, obj):
        """Genera URL firmada para descarga"""
        if not obj.file_path:
            return None

        from .storage import S3Storage
        storage = S3Storage()
        return storage.get_presigned_url(obj.file_path, expiration=3600)


class ClinicalDocumentListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listados"""
    patient_name = serializers.CharField(
        source='clinical_record.patient.get_full_name',
        read_only=True
    )
    created_by_name = serializers.CharField(
        source='created_by.get_full_name',
        read_only=True
    )

    class Meta:
        model = ClinicalDocument
        fields = [
            'id', 'document_type', 'title', 'document_date',
            'patient_name', 'specialty', 'doctor_name',
            'is_signed', 'is_locked', 'file_name',
            'created_by_name', 'created_at'
        ]


class ClinicalDocumentUploadSerializer(serializers.ModelSerializer):
    """Serializer para upload de documentos"""
    file = serializers.FileField(write_only=True, required=True)

    class Meta:
        model = ClinicalDocument
        fields = [
            'clinical_record', 'document_type', 'title', 'description',
            'document_date', 'specialty', 'doctor_name', 'doctor_license',
            'content', 'tags', 'file'
        ]

    def validate_file(self, value):
        """Validar tipo y tamaño de archivo"""
        # Validar tamaño (máximo 50MB)
        max_size = 50 * 1024 * 1024  # 50MB
        if value.size > max_size:
            raise serializers.ValidationError(
                f'El archivo es demasiado grande. Máximo permitido: 50MB'
            )

        # Validar tipo de archivo
        allowed_types = [
            'application/pdf',
            'image/jpeg',
            'image/png',
            'image/tiff',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        ]

        if value.content_type not in allowed_types:
            raise serializers.ValidationError(
                f'Tipo de archivo no permitido: {value.content_type}'
            )

        return value


class MedicalImageSerializer(serializers.ModelSerializer):
    """Serializer para imágenes médicas"""
    clinical_record_info = serializers.SerializerMethodField()
    created_by_name = serializers.CharField(
        source='created_by.get_full_name',
        read_only=True
    )
    file_url = serializers.SerializerMethodField()
    enhanced_url = serializers.SerializerMethodField()

    class Meta:
        model = MedicalImage
        fields = [
            'id', 'clinical_record', 'clinical_record_info', 'document',
            'image_type', 'title', 'study_date', 'modality', 'body_part',
            'file_path', 'file_name', 'file_size_bytes', 'file_url',
            'dicom_metadata', 'enhanced_image_path', 'enhancement_applied',
            'enhancement_params', 'enhanced_url',
            'created_by', 'created_by_name', 'created_at'
        ]
        read_only_fields = [
            'id', 'enhanced_image_path', 'enhancement_applied',
            'created_at', 'created_by'
        ]

    def get_clinical_record_info(self, obj):
        return {
            'id': str(obj.clinical_record.id),
            'record_number': obj.clinical_record.record_number
        }

    def get_file_url(self, obj):
        if not obj.file_path:
            return None
        from .storage import S3Storage
        storage = S3Storage()
        return storage.get_presigned_url(obj.file_path)

    def get_enhanced_url(self, obj):
        if not obj.enhanced_image_path:
            return None
        from .storage import S3Storage
        storage = S3Storage()
        return storage.get_presigned_url(obj.enhanced_image_path)


class DocumentAccessLogSerializer(serializers.ModelSerializer):
    """Serializer para logs de acceso"""
    document_title = serializers.CharField(source='document.title', read_only=True)

    class Meta:
        model = DocumentAccessLog
        fields = [
            'id', 'document', 'document_title', 'user', 'user_name',
            'user_email', 'access_type', 'ip_address', 'user_agent',
            'access_reason', 'accessed_at'
        ]
        read_only_fields = ['id', 'accessed_at']