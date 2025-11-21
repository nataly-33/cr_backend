from django.contrib import admin
from .models import (
    NaturalLanguageQuery,
    QueryExecution,
    QueryTemplate,
    QueryFeedback
)


@admin.register(NaturalLanguageQuery)
class NaturalLanguageQueryAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'query_text_short', 'status', 'confidence_score', 'created_at']
    list_filter = ['status', 'language', 'input_method', 'ai_model', 'created_at']
    search_fields = ['query_text', 'user__email']
    readonly_fields = ['created_at', 'updated_at']
    
    def query_text_short(self, obj):
        return obj.query_text[:50] + '...' if len(obj.query_text) > 50 else obj.query_text
    query_text_short.short_description = 'Query'


@admin.register(QueryExecution)
class QueryExecutionAdmin(admin.ModelAdmin):
    list_display = ['id', 'nl_query_text_short', 'status', 'result_count', 'execution_time_ms', 'created_at']
    list_filter = ['status', 'output_format', 'created_at']
    search_fields = ['nl_query__query_text', 'executed_sql']
    readonly_fields = ['created_at', 'updated_at']
    
    def nl_query_text_short(self, obj):
        text = obj.nl_query.query_text
        return text[:40] + '...' if len(text) > 40 else text
    nl_query_text_short.short_description = 'Query'


@admin.register(QueryTemplate)
class QueryTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'usage_count', 'is_active', 'created_at']
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['name', 'description']


@admin.register(QueryFeedback)
class QueryFeedbackAdmin(admin.ModelAdmin):
    list_display = ['id', 'execution', 'rating', 'was_useful', 'created_at']
    list_filter = ['rating', 'was_useful', 'created_at']
    search_fields = ['comments']
    readonly_fields = ['created_at', 'updated_at']
