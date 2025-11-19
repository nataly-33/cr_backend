from django.contrib import admin
from apps.ai.models import DiabetesPredictionModel, DiabetesPrediction, DiabetesDataset


@admin.register(DiabetesPredictionModel)
class DiabetesPredictionModelAdmin(admin.ModelAdmin):
    list_display = ['version', 'algorithm', 'accuracy', 'precision', 'recall', 'is_active', 'created_at']
    list_filter = ['is_active', 'algorithm']
    search_fields = ['version']
    readonly_fields = ['created_at']


@admin.register(DiabetesPrediction)
class DiabetesPredictionAdmin(admin.ModelAdmin):
    list_display = ['patient', 'risk_level', 'probability', 'has_diabetes_risk', 'created_at']
    list_filter = ['risk_level', 'has_diabetes_risk', 'created_at']
    search_fields = ['patient__first_name', 'patient__last_name']
    readonly_fields = ['created_at']


@admin.register(DiabetesDataset)
class DiabetesDatasetAdmin(admin.ModelAdmin):
    list_display = ['source', 'age', 'glucose', 'bmi', 'outcome', 'is_training_data']
    list_filter = ['source', 'outcome', 'is_training_data']
    search_fields = ['patient__first_name']
