"""
Vistas para el módulo de reportes AI
"""
import logging
import time
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse
from django.db.models import Count, Avg, Q
from datetime import datetime, timedelta
from drf_spectacular.utils import extend_schema, OpenApiParameter

from .models import (
    NaturalLanguageQuery,
    QueryExecution,
    QueryTemplate,
    QueryFeedback
)
from .serializers import (
    NaturalLanguageQuerySerializer,
    QueryExecutionSerializer,
    ParseQueryRequestSerializer,
    ParseQueryResponseSerializer,
    ExecuteQueryRequestSerializer,
    ExecuteQueryResponseSerializer,
    QueryHistorySerializer,
    QueryTemplateSerializer,
    QueryFeedbackSerializer,
    DirectQueryRequestSerializer,
    StatsSerializer,
)
from .nlp_service import NLPParserService
from .sql_executor import SQLExecutorService

logger = logging.getLogger(__name__)


@extend_schema(tags=['Reports AI'])
class ReportsAIViewSet(viewsets.ViewSet):
    """
    ViewSet principal para reportes con IA
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        request=ParseQueryRequestSerializer,
        responses={200: ParseQueryResponseSerializer},
        description="Parsear consulta en lenguaje natural a SQL"
    )
    @action(detail=False, methods=['post'], url_path='parse')
    def parse_query(self, request):
        """
        POST /api/reports-ai/parse/
        
        Parsea una consulta en lenguaje natural y genera SQL
        """
        serializer = ParseQueryRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        query_text = serializer.validated_data['query_text']
        language = serializer.validated_data['language']
        input_method = serializer.validated_data['input_method']
        ai_provider = serializer.validated_data['ai_provider']
        
        # Crear registro de consulta
        nl_query = NaturalLanguageQuery.objects.create(
            user=request.user,
            query_text=query_text,
            language=language,
            input_method=input_method,
            ai_model=ai_provider,
            status='pending'
        )
        
        try:
            start_time = time.time()
            
            # Parsear con servicio NLP
            parser = NLPParserService(ai_provider=ai_provider)
            result = parser.parse_query(query_text, language)
            
            processing_time = int((time.time() - start_time) * 1000)
            
            # Validar SQL generado
            is_valid, error_msg = parser.validate_sql(result.get('sql', ''))
            
            if not is_valid:
                nl_query.status = 'failed'
                nl_query.error_message = error_msg
                nl_query.processing_time_ms = processing_time
                nl_query.save()
                
                return Response(
                    {'error': error_msg},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Actualizar registro
            nl_query.generated_sql = result['sql']
            nl_query.inferred_params = result.get('params', {})
            nl_query.confidence_score = result.get('confidence', 0.0)
            nl_query.status = 'validated'
            nl_query.processing_time_ms = processing_time
            nl_query.save()
            
            response_data = {
                'query_id': nl_query.id,
                'sql': result['sql'],
                'params': result.get('params', {}),
                'confidence': result.get('confidence', 0.0),
                'table_name': result.get('table_name', ''),
                'explanation': result.get('explanation', ''),
                'estimated_rows': result.get('estimated_rows', 0),
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.exception("Error parsing query")
            
            nl_query.status = 'failed'
            nl_query.error_message = str(e)
            nl_query.save()
            
            return Response(
                {'error': f'Error parseando consulta: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        request=ExecuteQueryRequestSerializer,
        responses={200: ExecuteQueryResponseSerializer},
        description="Ejecutar consulta parseada"
    )
    @action(detail=False, methods=['post'], url_path='execute')
    def execute_query(self, request):
        """
        POST /api/reports-ai/execute/
        
        Ejecuta una consulta previamente parseada
        """
        serializer = ExecuteQueryRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        query_id = serializer.validated_data['query_id']
        output_format = serializer.validated_data['output_format']
        row_limit = serializer.validated_data['row_limit']
        override_sql = serializer.validated_data.get('override_sql')
        
        try:
            # Obtener consulta NL
            nl_query = NaturalLanguageQuery.objects.get(
                id=query_id,
                user=request.user
            )
            
            # Determinar SQL a ejecutar
            sql_to_execute = override_sql if override_sql else nl_query.generated_sql
            
            if not sql_to_execute:
                return Response(
                    {'error': 'No hay SQL para ejecutar'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Crear registro de ejecución
            execution = QueryExecution.objects.create(
                nl_query=nl_query,
                executed_sql=sql_to_execute,
                output_format=output_format,
                row_limit=row_limit,
                status='executing',
                execution_time_ms=0  # Se actualizará después
            )
            
            # Ejecutar consulta
            executor = SQLExecutorService()
            result = executor.execute_query(
                sql_to_execute,
                nl_query.inferred_params,
                row_limit
            )
            
            # Actualizar ejecución
            execution.result_count = result['row_count']
            execution.result_data = {
                'columns': result['columns'],
                'data': result['data'][:100]  # Guardar solo primeras 100
            }
            execution.execution_time_ms = result['execution_time_ms']
            execution.status = 'completed'
            execution.save()
            
            # Si el formato no es JSON, generar archivo
            download_url = None
            if output_format != 'json':
                file_content = executor.export_to_format(result, output_format)
                
                # Guardar archivo
                import os
                from django.conf import settings
                
                reports_dir = os.path.join(settings.MEDIA_ROOT, 'reports_ai')
                os.makedirs(reports_dir, exist_ok=True)
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                ext = 'xlsx' if output_format == 'excel' else output_format
                filename = f'report_{execution.id}_{timestamp}.{ext}'
                filepath = os.path.join(reports_dir, filename)
                
                # Escribir archivo
                mode = 'wb' if isinstance(file_content, bytes) else 'w'
                with open(filepath, mode) as f:
                    f.write(file_content)
                
                # Guardar solo la ruta relativa a MEDIA_ROOT
                execution.file_path = f'reports_ai/{filename}'
                execution.file_size_bytes = os.path.getsize(filepath)
                execution.save()
                
                # Para el response, devolver la URL correcta
                download_url = f'/media/reports_ai/{filename}'
            
            response_data = {
                'execution_id': execution.id,
                'status': 'completed',
                'result_count': result['row_count'],
                'execution_time_ms': result['execution_time_ms'],
                'columns': result['columns'],
                'data': result['data'],
                'truncated': result['truncated'],
                'download_url': download_url,
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
        
        except NaturalLanguageQuery.DoesNotExist:
            return Response(
                {'error': 'Consulta no encontrada'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.exception("Error executing query")
            
            if 'execution' in locals():
                execution.status = 'failed'
                execution.error_message = str(e)
                execution.save()
            
            return Response(
                {'error': f'Error ejecutando consulta: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        request=DirectQueryRequestSerializer,
        responses={200: ExecuteQueryResponseSerializer},
        description="Parsear y ejecutar consulta en un solo paso"
    )
    @action(detail=False, methods=['post'], url_path='direct')
    def direct_query(self, request):
        """
        POST /api/reports-ai/direct/

        Parsea y ejecuta una consulta en lenguaje natural en un solo paso
        """
        serializer = DirectQueryRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        query_text = serializer.validated_data['query_text']
        language = serializer.validated_data.get('language', 'es')
        input_method = serializer.validated_data.get('input_method', 'text')
        ai_provider = serializer.validated_data.get('ai_provider', 'local')
        output_format = serializer.validated_data.get('output_format', 'json')
        row_limit = serializer.validated_data.get('row_limit', 100)

        # Crear registro de consulta
        nl_query = NaturalLanguageQuery.objects.create(
            user=request.user,
            query_text=query_text,
            language=language,
            input_method=input_method,
            ai_model=ai_provider,
            status='pending'
        )

        try:
            start_time = time.time()

            # Paso 1: Parsear con servicio NLP
            parser = NLPParserService(ai_provider=ai_provider)
            result = parser.parse_query(query_text, language)

            processing_time = int((time.time() - start_time) * 1000)

            # Validar SQL generado
            is_valid, error_msg = parser.validate_sql(result.get('sql', ''))

            if not is_valid:
                nl_query.status = 'failed'
                nl_query.error_message = error_msg
                nl_query.processing_time_ms = processing_time
                nl_query.save()

                return Response(
                    {'error': error_msg},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Actualizar registro
            nl_query.generated_sql = result['sql']
            nl_query.inferred_params = result.get('params', {})
            nl_query.confidence_score = result.get('confidence', 0.0)
            nl_query.status = 'validated'
            nl_query.processing_time_ms = processing_time
            nl_query.save()

            # Paso 2: Ejecutar consulta
            execution = QueryExecution.objects.create(
                nl_query=nl_query,
                executed_sql=result['sql'],
                output_format=output_format,
                row_limit=row_limit,
                status='executing',
                execution_time_ms=0
            )

            executor = SQLExecutorService()
            exec_result = executor.execute_query(
                result['sql'],
                result.get('params', {}),
                row_limit
            )

            # Actualizar ejecución
            execution.result_count = exec_result['row_count']
            execution.result_data = {
                'columns': exec_result['columns'],
                'data': exec_result['data'][:100]
            }
            execution.execution_time_ms = exec_result['execution_time_ms']
            execution.status = 'completed'
            execution.save()

            # Si el formato no es JSON, generar archivo
            download_url = None
            if output_format != 'json':
                file_content = executor.export_to_format(exec_result, output_format)

                import os
                from django.conf import settings

                reports_dir = os.path.join(settings.MEDIA_ROOT, 'reports_ai')
                os.makedirs(reports_dir, exist_ok=True)

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                ext = 'xlsx' if output_format == 'excel' else output_format
                filename = f'report_{execution.id}_{timestamp}.{ext}'
                filepath = os.path.join(reports_dir, filename)

                mode = 'wb' if isinstance(file_content, bytes) else 'w'
                with open(filepath, mode) as f:
                    f.write(file_content)

                execution.file_path = f'reports_ai/{filename}'
                execution.file_size_bytes = os.path.getsize(filepath)
                execution.save()

                download_url = f'/media/reports_ai/{filename}'

            response_data = {
                'execution_id': execution.id,
                'query_id': nl_query.id,
                'status': 'completed',
                'sql': result['sql'],
                'confidence': result.get('confidence', 0.0),
                'result_count': exec_result['row_count'],
                'execution_time_ms': exec_result['execution_time_ms'],
                'columns': exec_result['columns'],
                'data': exec_result['data'],
                'truncated': exec_result['truncated'],
                'download_url': download_url,
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception("Error in direct query")

            nl_query.status = 'failed'
            nl_query.error_message = str(e)
            nl_query.save()

            if 'execution' in locals():
                execution.status = 'failed'
                execution.error_message = str(e)
                execution.save()

            return Response(
                {'error': f'Error ejecutando consulta: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        responses={200: QueryHistorySerializer(many=True)},
        description="Obtener historial de consultas del usuario"
    )
    @action(detail=False, methods=['get'], url_path='history')
    def query_history(self, request):
        """
        GET /api/reports-ai/history/
        
        Obtiene el historial de consultas del usuario
        """
        limit = int(request.query_params.get('limit', 50))
        
        queries = NaturalLanguageQuery.objects.filter(
            user=request.user
        ).annotate(
            executions_count=Count('executions')
        ).order_by('-created_at')[:limit]
        
        history = []
        for query in queries:
            last_exec = query.executions.order_by('-created_at').first()
            
            history.append({
                'query_id': query.id,
                'query_text': query.query_text,
                'created_at': query.created_at,
                'status': query.status,
                'confidence': query.confidence_score,
                'executions_count': query.executions_count,
                'last_execution': last_exec.created_at if last_exec else None,
            })
        
        return Response(history, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'], url_path='stats')
    def statistics(self, request):
        """
        GET /api/reports-ai/stats/
        
        Obtiene estadísticas del sistema de reportes AI
        """
        # Total de consultas
        total_queries = NaturalLanguageQuery.objects.filter(
            user=request.user
        ).count()
        
        # Total de ejecuciones
        total_executions = QueryExecution.objects.filter(
            nl_query__user=request.user
        ).count()
        
        # Promedio de confianza
        avg_confidence = NaturalLanguageQuery.objects.filter(
            user=request.user,
            status='validated'
        ).aggregate(avg=Avg('confidence_score'))['avg'] or 0.0
        
        # Promedio de tiempo de ejecución
        avg_exec_time = QueryExecution.objects.filter(
            nl_query__user=request.user,
            status='completed'
        ).aggregate(avg=Avg('execution_time_ms'))['avg'] or 0.0
        
        # Consultas exitosas vs fallidas
        successful = NaturalLanguageQuery.objects.filter(
            user=request.user,
            status='validated'
        ).count()
        
        failed = NaturalLanguageQuery.objects.filter(
            user=request.user,
            status='failed'
        ).count()
        
        # Top tablas consultadas (basado en inferred_params)
        # Esto requeriría parsing del SQL, simplificamos
        top_tables = []
        
        # Consultas por día (últimos 7 días)
        queries_by_day = []
        for i in range(7):
            date = datetime.now().date() - timedelta(days=i)
            count = NaturalLanguageQuery.objects.filter(
                user=request.user,
                created_at__date=date
            ).count()
            queries_by_day.append({
                'date': date.isoformat(),
                'count': count
            })
        
        stats = {
            'total_queries': total_queries,
            'total_executions': total_executions,
            'avg_confidence': round(avg_confidence, 2),
            'avg_execution_time_ms': round(avg_exec_time, 2),
            'successful_queries': successful,
            'failed_queries': failed,
            'top_tables': top_tables,
            'queries_by_day': queries_by_day,
        }
        
        return Response(stats, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['get'], url_path='download')
    def download_execution(self, request, pk=None):
        """
        GET /api/reports-ai/{execution_id}/download/
        
        Descargar resultado de una ejecución
        """
        try:
            execution = QueryExecution.objects.get(
                id=pk,
                nl_query__user=request.user
            )
            
            if not execution.file_path:
                return Response(
                    {'error': 'No hay archivo disponible'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            import os
            from django.conf import settings
            
            # Construir ruta completa
            if execution.file_path.startswith('/media/'):
                file_path = os.path.join(
                    settings.MEDIA_ROOT,
                    execution.file_path[7:]
                )
            else:
                file_path = os.path.join(
                    settings.MEDIA_ROOT,
                    execution.file_path
                )
            
            if not os.path.exists(file_path):
                return Response(
                    {'error': 'Archivo no encontrado'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Determinar content type
            content_types = {
                '.pdf': 'application/pdf',
                '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                '.csv': 'text/csv'
            }
            
            _, ext = os.path.splitext(file_path)
            content_type = content_types.get(ext.lower(), 'application/octet-stream')
            
            # Leer y retornar archivo
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            response = HttpResponse(file_content, content_type=content_type)
            filename = os.path.basename(file_path)
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            return response
        
        except QueryExecution.DoesNotExist:
            return Response(
                {'error': 'Ejecución no encontrada'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.exception("Error downloading execution")
            return Response(
                {'error': f'Error descargando archivo: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@extend_schema(tags=['Reports AI - Templates'])
class QueryTemplateViewSet(viewsets.ModelViewSet):
    """
    ViewSet para plantillas de consultas
    """
    queryset = QueryTemplate.objects.all()
    serializer_class = QueryTemplateSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtrar por categoría si se especifica
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)
        
        # Solo activas por defecto
        if self.action == 'list':
            queryset = queryset.filter(is_active=True)
        
        return queryset.order_by('-usage_count', 'name')


@extend_schema(tags=['Reports AI - Feedback'])
class QueryFeedbackViewSet(viewsets.ModelViewSet):
    """
    ViewSet para feedback de consultas
    """
    queryset = QueryFeedback.objects.all()
    serializer_class = QueryFeedbackSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return super().get_queryset().filter(
            execution__nl_query__user=self.request.user
        )
