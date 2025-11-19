from rest_framework import serializers
from apps.ai.models import DiabetesPrediction, DiabetesPredictionModel


class DiabetesPredictionModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiabetesPredictionModel
        fields = ['id', 'version', 'algorithm', 'accuracy', 'precision', 'recall', 'f1_score', 'is_active', 'created_at']


class DiabetesPredictionSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField()
    model_version = serializers.CharField(source='model.version', read_only=True)
    
    class Meta:
        model = DiabetesPrediction
        fields = '__all__'
    
    def get_patient_name(self, obj):
        return obj.patient.get_full_name()


class PredictDiabetesRequestSerializer(serializers.Serializer):
    patient_id = serializers.UUIDField(required=True)
