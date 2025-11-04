from rest_framework import serializers
from .models import ReportTemplate, ReportExecution, AIAnalysis


class ReportTemplateSerializer(serializers.ModelSerializer):
    output_formats = serializers.JSONField(required=False)
    allowed_roles = serializers.JSONField(required=False)

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
    report_type = serializers.ChoiceField(
        choices=['documents', 'patients', 'clinical_records', 'analytics', 'audit', 'users']
    )
    output_format = serializers.ChoiceField(choices=['pdf', 'excel', 'csv'])
    filters = serializers.JSONField(required=False, default=dict)
    
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)
    document_type = serializers.CharField(required=False, allow_blank=True)
    specialty = serializers.CharField(required=False, allow_blank=True)


class QBEExampleSerializer(serializers.Serializer):
    """
    Serializer para Query By Example (QBE)
    
    Ejemplo:
    {
        'model': 'documents',
        'example': {
            'specialty': 'Cardiología',
            'document_type': 'Historia Clínica',
            'created_at_from': '2025-10-01',
            'created_at_to': '2025-10-31'
        },
        'limit': 100,
        'offset': 0
    }
    """
    model = serializers.ChoiceField(
        choices=['documents', 'patients', 'clinical_records', 'users', 'audit_logs'],
        help_text="Modelo sobre el cual hacer la búsqueda"
    )
    example = serializers.JSONField(
        help_text="Diccionario con criterios de búsqueda (ejemplo para búsqueda por ejemplo)"
    )
    limit = serializers.IntegerField(
        default=100,
        min_value=1,
        max_value=1000,
        help_text="Máximo número de resultados"
    )
    offset = serializers.IntegerField(
        default=0,
        min_value=0,
        help_text="Número de resultados a saltar (para paginación)"
    )


class FilterItemSerializer(serializers.Serializer):
    """Serializer para un item de filtro individual"""
    field = serializers.CharField(help_text="Nombre del campo a filtrar")
    operator = serializers.ChoiceField(
        choices=['eq', 'ne', 'lt', 'lte', 'gt', 'gte', 'in', 'contains', 
                 'startswith', 'endswith', 'isnull', 'regex', 'range'],
        help_text="Operador de comparación"
    )
    value = serializers.JSONField(help_text="Valor a comparar")


class DynamicFilterSerializer(serializers.Serializer):
    """
    Serializer para filtros dinámicos
    
    Ejemplo:
    {
        'filters': [
            {'field': 'specialty', 'operator': 'eq', 'value': 'Cardiología'},
            {'field': 'created_at', 'operator': 'gte', 'value': '2025-10-01'}
        ],
        'exclude': [
            {'field': 'status', 'operator': 'eq', 'value': 'deleted'}
        ],
        'group_by': ['specialty'],
        'order_by': ['-created_at'],
        'limit': 100,
        'offset': 0,
        'distinct': True
    }
    """
    filters = FilterItemSerializer(many=True, required=False, default=[])
    exclude = FilterItemSerializer(many=True, required=False, default=[])
    group_by = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text="Campos para agrupar resultados (GROUP BY)"
    )
    order_by = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text="Campos para ordenar (- para DESC)"
    )
    limit = serializers.IntegerField(default=100, min_value=1, max_value=1000)
    offset = serializers.IntegerField(default=0, min_value=0)
    distinct = serializers.BooleanField(default=False, help_text="DISTINCT")


class QBEResponseItemSerializer(serializers.Serializer):
    """Serializer para un item en la respuesta de QBE"""
    # Este es dinámico, así que usamos JSON directamente
    pass


class QBEResponseSerializer(serializers.Serializer):
    """Serializer para la respuesta del endpoint QBE"""
    count = serializers.IntegerField(help_text="Total de resultados encontrados")
    results = serializers.ListField(
        child=serializers.JSONField(),
        help_text="Resultados paginados"
    )
    next = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="URL para siguiente página (si existe)"
    )
    previous = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="URL para página anterior (si existe)"
    )
    filter_spec = serializers.JSONField(
        help_text="Especificación de filtros aplicados (para reusar)"
    )
    fields_used = serializers.ListField(
        child=serializers.CharField(),
        help_text="Campos utilizados en la búsqueda"
    )


class DynamicReportSerializer(serializers.Serializer):
    """
    Serializer para solicitud de generación de reporte dinámico
    
    Ejemplo:
    {
        'data_sources': ['documents', 'patients'],
        'columns': {
            'documents': ['specialty', 'document_type', 'created_at'],
            'patients': ['full_name', 'date_of_birth']
        },
        'filters': [
            {'field': 'specialty', 'operator': 'eq', 'value': 'Cardiología'},
            {'field': 'created_at', 'operator': 'gte', 'value': '2025-10-01'}
        ],
        'group_by': ['specialty'],
        'order_by': ['-created_at'],
        'limit': 1000,
        'output_format': 'pdf'
    }
    """
    data_sources = serializers.ListField(
        child=serializers.CharField(),
        help_text="['documents', 'patients', 'clinical_records', 'users']"
    )
    columns = serializers.DictField(
        help_text="Columnas a incluir por data_source"
    )
    filters = FilterItemSerializer(
        many=True,
        required=False,
        default=[],
        help_text="Filtros a aplicar (usa QBE internamente)"
    )
    group_by = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=[],
        help_text="Campos para agrupar"
    )
    order_by = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=[],
        help_text="Campos para ordenar (- para DESC)"
    )
    limit = serializers.IntegerField(
        default=1000,
        min_value=1,
        max_value=10000,
        help_text="Máximo número de filas por tabla"
    )
    output_format = serializers.ChoiceField(
        choices=['pdf', 'excel', 'csv'],
        help_text="Formato del reporte"
    )


# ==================== AI Analysis Serializers ====================

class AIAnalysisResultSerializer(serializers.Serializer):
    """Serializer para resultado de análisis de IA"""
    id = serializers.CharField()
    report_id = serializers.CharField()
    analysis = serializers.CharField()
    insights = serializers.ListField(child=serializers.CharField())
    key_findings = serializers.ListField(child=serializers.CharField())
    confidence_score = serializers.FloatField()
    generated_at = serializers.DateTimeField()


class AISummarySerializer(serializers.Serializer):
    """Serializer para resumen generado por IA"""
    id = serializers.CharField()
    summary = serializers.CharField()
    key_points = serializers.ListField(child=serializers.CharField())
    length = serializers.IntegerField()
    generated_at = serializers.DateTimeField()


class AIRecommendationSerializer(serializers.Serializer):
    """Serializer para recomendación generada por IA"""
    id = serializers.CharField()
    recommendation = serializers.CharField()
    priority = serializers.ChoiceField(choices=['critical', 'high', 'medium', 'low'])
    category = serializers.CharField()
    action_items = serializers.ListField(child=serializers.CharField(), required=False)


class AIInsightsResponseSerializer(serializers.Serializer):
    """Serializer para respuesta completa de insights de IA"""
    analysis = AIAnalysisResultSerializer(required=False, allow_null=True)
    summary = AISummarySerializer(required=False, allow_null=True)
    recommendations = AIRecommendationSerializer(many=True, required=False)
    status = serializers.CharField(required=False)
    message = serializers.CharField(required=False, allow_null=True)


class AIAnalysisModelSerializer(serializers.ModelSerializer):
    """Serializer para modelo AIAnalysis"""
    generated_at = serializers.DateTimeField(source='created_at', read_only=True)
    report_id = serializers.CharField(source='report_execution_id', read_only=True)
    
    class Meta:
        model = AIAnalysis
        fields = [
            'id', 'report_id', 'analysis', 'insights',
            'key_findings', 'confidence_score', 'generated_at',
            'summary', 'summary_key_points', 'recommendations',
            'status', 'error_message'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'tenant']