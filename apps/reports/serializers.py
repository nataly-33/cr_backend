from rest_framework import serializers
from .models import ReportTemplate, ReportExecution


class ReportTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportTemplate
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'tenant', 'created_by']


class ReportExecutionSerializer(serializers.ModelSerializer):
    template_name = serializers.CharField(source='template.name', read_only=True)
    executed_by_name = serializers.CharField(source='executed_by.full_name', read_only=True)
    
    class Meta:
        model = ReportExecution
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'tenant', 'executed_by']


class GenerateReportSerializer(serializers.Serializer):
    """Serializer para solicitud de generación de reporte"""
    report_type = serializers.ChoiceField(choices=['documents', 'patients', 'analytics'])
    output_format = serializers.ChoiceField(choices=['pdf', 'excel', 'csv'])
    filters = serializers.JSONField(required=False, default=dict)
    
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)
    document_type = serializers.CharField(required=False, allow_blank=True)
    specialty = serializers.CharField(required=False, allow_blank=True)