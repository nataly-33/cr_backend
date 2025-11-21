"""
Serializers para el módulo de reportes AI
"""
from rest_framework import serializers
from .models import (
    NaturalLanguageQuery,
    QueryExecution,
    QueryTemplate,
    QueryFeedback
)


class NaturalLanguageQuerySerializer(serializers.ModelSerializer):
    """Serializer para consultas en lenguaje natural"""
    
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    
    class Meta:
        model = NaturalLanguageQuery
        fields = [
            'id', 'user', 'user_email', 'user_name',
            'query_text', 'language', 'input_method',
            'generated_sql', 'inferred_params', 'confidence_score',
            'status', 'error_message', 'ai_model',
            'processing_time_ms', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user', 'generated_sql', 'inferred_params',
            'confidence_score', 'status', 'error_message',
            'processing_time_ms', 'created_at', 'updated_at'
        ]


class QueryExecutionSerializer(serializers.ModelSerializer):
    """Serializer para ejecuciones de consultas"""
    
    nl_query_text = serializers.CharField(
        source='nl_query.query_text',
        read_only=True
    )
    
    class Meta:
        model = QueryExecution
        fields = [
            'id', 'nl_query', 'nl_query_text',
            'executed_sql', 'result_count', 'result_data',
            'execution_time_ms', 'output_format', 'row_limit',
            'file_path', 'file_size_bytes', 'status',
            'error_message', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'result_count', 'result_data', 'execution_time_ms',
            'file_path', 'file_size_bytes', 'status',
            'error_message', 'created_at', 'updated_at'
        ]


class ParseQueryRequestSerializer(serializers.Serializer):
    """Serializer para solicitudes de parseo de consultas"""
    
    query_text = serializers.CharField(
        required=True,
        min_length=5,
        max_length=1000,
        help_text="Texto de la consulta en lenguaje natural"
    )
    
    language = serializers.ChoiceField(
        choices=['es', 'en'],
        default='es',
        help_text="Idioma de la consulta"
    )
    
    input_method = serializers.ChoiceField(
        choices=['text', 'voice'],
        default='text',
        help_text="Método de entrada"
    )
    
    ai_provider = serializers.ChoiceField(
        choices=['openai', 'local'],
        default='openai',
        help_text="Proveedor de IA: openai (recomendado) o local"
    )


class ParseQueryResponseSerializer(serializers.Serializer):
    """Serializer para respuestas de parseo"""
    
    query_id = serializers.UUIDField(help_text="ID de la consulta creada")
    sql = serializers.CharField(help_text="SQL generado")
    params = serializers.JSONField(help_text="Parámetros inferidos")
    confidence = serializers.FloatField(help_text="Nivel de confianza (0-1)")
    table_name = serializers.CharField(help_text="Tabla principal")
    explanation = serializers.CharField(help_text="Explicación de la consulta")
    estimated_rows = serializers.IntegerField(
        required=False,
        help_text="Estimación de filas"
    )


class ExecuteQueryRequestSerializer(serializers.Serializer):
    """Serializer para solicitudes de ejecución"""
    
    query_id = serializers.UUIDField(
        required=True,
        help_text="ID de la consulta NL parseada"
    )
    
    output_format = serializers.ChoiceField(
        choices=['json', 'csv', 'excel', 'pdf'],
        default='json',
        help_text="Formato de salida"
    )
    
    row_limit = serializers.IntegerField(
        default=100,
        min_value=1,
        max_value=1000,
        help_text="Límite de filas (1-1000)"
    )
    
    override_sql = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="SQL personalizado (opcional, para usuarios avanzados)"
    )


class ExecuteQueryResponseSerializer(serializers.Serializer):
    """Serializer para respuestas de ejecución"""
    
    execution_id = serializers.UUIDField(help_text="ID de la ejecución")
    status = serializers.CharField(help_text="Estado de la ejecución")
    result_count = serializers.IntegerField(help_text="Cantidad de filas")
    execution_time_ms = serializers.IntegerField(help_text="Tiempo de ejecución")
    columns = serializers.ListField(
        child=serializers.CharField(),
        help_text="Nombres de las columnas"
    )
    data = serializers.ListField(
        child=serializers.JSONField(),
        help_text="Datos de las filas"
    )
    truncated = serializers.BooleanField(
        help_text="Si los resultados fueron truncados"
    )
    download_url = serializers.CharField(
        required=False,
        allow_null=True,
        help_text="URL de descarga (para formatos no-JSON)"
    )


class QueryHistorySerializer(serializers.Serializer):
    """Serializer para historial de consultas"""
    
    query_id = serializers.UUIDField()
    query_text = serializers.CharField()
    created_at = serializers.DateTimeField()
    status = serializers.CharField()
    confidence = serializers.FloatField()
    executions_count = serializers.IntegerField()
    last_execution = serializers.DateTimeField(allow_null=True)


class QueryTemplateSerializer(serializers.ModelSerializer):
    """Serializer para plantillas de consultas"""
    
    class Meta:
        model = QueryTemplate
        fields = [
            'id', 'name', 'description', 'example_phrases',
            'sql_template', 'required_params', 'category',
            'usage_count', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'usage_count', 'created_at', 'updated_at']


class QueryFeedbackSerializer(serializers.ModelSerializer):
    """Serializer para feedback de consultas"""
    
    class Meta:
        model = QueryFeedback
        fields = [
            'id', 'execution', 'rating', 'was_useful',
            'comments', 'suggested_sql', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class DirectQueryRequestSerializer(serializers.Serializer):
    """
    Serializer para consultas directas (parseo + ejecución en un solo paso)
    """
    query_text = serializers.CharField(
        required=True,
        min_length=5,
        max_length=1000
    )
    
    language = serializers.ChoiceField(
        choices=['es', 'en'],
        default='es'
    )
    
    output_format = serializers.ChoiceField(
        choices=['json', 'csv', 'excel', 'pdf'],
        default='json'
    )
    
    row_limit = serializers.IntegerField(
        default=100,
        min_value=1,
        max_value=1000
    )
    
    ai_provider = serializers.ChoiceField(
        choices=['openai', 'local'],
        default='openai'
    )


class StatsSerializer(serializers.Serializer):
    """Serializer para estadísticas del sistema de reportes AI"""
    
    total_queries = serializers.IntegerField()
    total_executions = serializers.IntegerField()
    avg_confidence = serializers.FloatField()
    avg_execution_time_ms = serializers.FloatField()
    successful_queries = serializers.IntegerField()
    failed_queries = serializers.IntegerField()
    top_tables = serializers.ListField(
        child=serializers.JSONField()
    )
    queries_by_day = serializers.ListField(
        child=serializers.JSONField()
    )
