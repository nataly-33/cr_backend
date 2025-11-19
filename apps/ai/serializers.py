"""
Serializers para la API de predicción de diabetes
"""
from rest_framework import serializers
from ..models import DiabetesPrediction, DiabetesPredictionModel


class DiabetesPredictionModelSerializer(serializers.ModelSerializer):
    """Serializer para información del modelo"""
    
    class Meta:
        model = DiabetesPredictionModel
        fields = [
            'id', 'version', 'accuracy', 'precision', 'recall', 'f1_score',
            'training_samples', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class DiabetesPredictionSerializer(serializers.ModelSerializer):
    """Serializer para predicciones guardadas"""
    patient_name = serializers.CharField(source='patient.full_name', read_only=True)
    model_version = serializers.CharField(source='model.version', read_only=True)
    
    class Meta:
        model = DiabetesPrediction
        fields = [
            'id', 'patient', 'patient_name', 'model', 'model_version',
            'has_diabetes_risk', 'probability', 'risk_level',
            'contributing_factors', 'recommendations', 'metadata',
            'created_at'
        ]
        read_only_fields = ['created_at']


class DiabetesPredictionRequestSerializer(serializers.Serializer):
    """Serializer para solicitud de predicción"""
    patient_id = serializers.UUIDField(required=True)


class DiabetesPredictionResponseSerializer(serializers.Serializer):
    """Serializer para respuesta de predicción"""
    success = serializers.BooleanField()
    patient_id = serializers.UUIDField()
    has_diabetes_risk = serializers.BooleanField()
    probability = serializers.FloatField()
    risk_level = serializers.CharField()
    contributing_factors = serializers.ListField(
        child=serializers.CharField()
    )
    recommendations = serializers.ListField(
        child=serializers.CharField()
    )
    timestamp = serializers.DateTimeField()
    model_version = serializers.CharField()


class BatchPredictionRequestSerializer(serializers.Serializer):
    """Serializer para predicción por lotes"""
    patient_ids = serializers.ListField(
        child=serializers.UUIDField()
    )


class BatchPredictionResponseSerializer(serializers.Serializer):
    """Serializer para respuesta de predicción por lotes"""
    total = serializers.IntegerField()
    successful = serializers.IntegerField()
    failed = serializers.IntegerField()
    results = DiabetesPredictionResponseSerializer(many=True)
