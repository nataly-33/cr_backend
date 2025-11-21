"""
Modelos para reportes generados con IA desde lenguaje natural
"""
from django.db import models
from apps.core.models import TenantAwareModel


class NaturalLanguageQuery(TenantAwareModel):
    """
    Consulta en lenguaje natural ingresada por el usuario
    """
    # Usuario que hizo la consulta
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='nl_queries'
    )
    
    # Texto original en lenguaje natural
    query_text = models.TextField(
        help_text="Texto original ingresado por el usuario (voz o escrito)"
    )
    
    # Idioma detectado
    language = models.CharField(
        max_length=10,
        default='es',
        help_text="Idioma del query (es, en, etc.)"
    )
    
    # Metadata de entrada
    input_method = models.CharField(
        max_length=20,
        choices=[
            ('text', 'Texto'),
            ('voice', 'Voz'),
        ],
        default='text'
    )
    
    # SQL generado
    generated_sql = models.TextField(
        blank=True,
        help_text="Consulta SQL generada por IA"
    )
    
    # Parámetros inferidos
    inferred_params = models.JSONField(
        default=dict,
        help_text="Parámetros extraídos del lenguaje natural"
    )
    
    # Confianza del parseo
    confidence_score = models.FloatField(
        default=0.0,
        help_text="Puntuación de confianza (0-1) de la interpretación"
    )
    
    # Estado del parseo
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('parsed', 'Parseado'),
        ('validated', 'Validado'),
        ('failed', 'Fallido'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    # Errores si los hay
    error_message = models.TextField(blank=True)
    
    # Modelo de IA usado
    ai_model = models.CharField(
        max_length=50,
        default='gpt-4',
        help_text="Modelo de IA usado para parsear (gpt-4, claude, bedrock, etc.)"
    )
    
    # Tiempo de procesamiento
    processing_time_ms = models.IntegerField(
        null=True,
        blank=True,
        help_text="Tiempo de procesamiento en milisegundos"
    )
    
    class Meta:
        db_table = 'nl_query'
        ordering = ['-created_at']
        verbose_name = 'Consulta en Lenguaje Natural'
        verbose_name_plural = 'Consultas en Lenguaje Natural'
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.user.email}: {self.query_text[:50]}..."


class QueryExecution(TenantAwareModel):
    """
    Ejecución de una consulta parseada
    """
    # Referencia a la consulta NL
    nl_query = models.ForeignKey(
        NaturalLanguageQuery,
        on_delete=models.CASCADE,
        related_name='executions'
    )
    
    # SQL ejecutado (puede ser modificado del original)
    executed_sql = models.TextField(
        help_text="SQL realmente ejecutado (puede incluir límites, etc.)"
    )
    
    # Resultados
    result_count = models.IntegerField(
        default=0,
        help_text="Número de filas retornadas"
    )
    
    result_data = models.JSONField(
        default=dict,
        help_text="Datos del resultado (puede ser un subset)"
    )
    
    # Metadata de ejecución
    execution_time_ms = models.IntegerField(
        help_text="Tiempo de ejecución de la consulta en ms"
    )
    
    # Formato de salida
    output_format = models.CharField(
        max_length=20,
        choices=[
            ('json', 'JSON'),
            ('csv', 'CSV'),
            ('excel', 'Excel'),
            ('pdf', 'PDF'),
        ],
        default='json'
    )
    
    # Límite de filas aplicado
    row_limit = models.IntegerField(
        default=100,
        help_text="Límite de filas aplicado en la consulta"
    )
    
    # Archivo generado (si aplica)
    file_path = models.CharField(
        max_length=500,
        blank=True,
        help_text="Ruta al archivo generado (para CSV, Excel, PDF)"
    )
    
    file_size_bytes = models.BigIntegerField(
        null=True,
        blank=True
    )
    
    # Estado
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('executing', 'Ejecutando'),
        ('completed', 'Completado'),
        ('failed', 'Fallido'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    error_message = models.TextField(blank=True)
    
    class Meta:
        db_table = 'query_execution'
        ordering = ['-created_at']
        verbose_name = 'Ejecución de Consulta'
        verbose_name_plural = 'Ejecuciones de Consultas'
        indexes = [
            models.Index(fields=['nl_query', '-created_at']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"Execution {self.id} - {self.status} ({self.result_count} rows)"


class QueryTemplate(TenantAwareModel):
    """
    Plantillas de consultas frecuentes para mejorar el parseo
    """
    # Nombre de la plantilla
    name = models.CharField(max_length=200)
    
    # Descripción
    description = models.TextField(blank=True)
    
    # Ejemplos de frases que matchean
    example_phrases = models.JSONField(
        default=list,
        help_text="Lista de frases ejemplo que usan esta plantilla"
    )
    
    # SQL template con placeholders
    sql_template = models.TextField(
        help_text="Template SQL con placeholders: {table}, {date_from}, etc."
    )
    
    # Parámetros requeridos
    required_params = models.JSONField(
        default=list,
        help_text="Lista de parámetros requeridos: ['table', 'date_from', ...]"
    )
    
    # Categoría
    category = models.CharField(
        max_length=50,
        choices=[
            ('patients', 'Pacientes'),
            ('clinical_forms', 'Formularios Clínicos'),
            ('documents', 'Documentos'),
            ('users', 'Usuarios'),
            ('analytics', 'Analíticas'),
        ],
        default='patients'
    )
    
    # Popularidad (cuántas veces se ha usado)
    usage_count = models.IntegerField(default=0)
    
    # Activo
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'query_template'
        ordering = ['-usage_count', 'name']
        verbose_name = 'Plantilla de Consulta'
        verbose_name_plural = 'Plantillas de Consultas'
    
    def __str__(self):
        return self.name


class QueryFeedback(TenantAwareModel):
    """
    Feedback del usuario sobre los resultados del reporte
    """
    execution = models.OneToOneField(
        QueryExecution,
        on_delete=models.CASCADE,
        related_name='feedback'
    )
    
    # Calificación
    rating = models.IntegerField(
        choices=[
            (1, '⭐ Muy malo'),
            (2, '⭐⭐ Malo'),
            (3, '⭐⭐⭐ Regular'),
            (4, '⭐⭐⭐⭐ Bueno'),
            (5, '⭐⭐⭐⭐⭐ Excelente'),
        ],
        help_text="Calificación de 1-5 estrellas"
    )
    
    # ¿El resultado fue útil?
    was_useful = models.BooleanField(
        default=True,
        help_text="¿El resultado respondió la pregunta?"
    )
    
    # Comentarios
    comments = models.TextField(
        blank=True,
        help_text="Comentarios adicionales del usuario"
    )
    
    # SQL sugerido (si el usuario lo corrige)
    suggested_sql = models.TextField(
        blank=True,
        help_text="SQL sugerido por el usuario como mejora"
    )
    
    class Meta:
        db_table = 'query_feedback'
        ordering = ['-created_at']
        verbose_name = 'Feedback de Consulta'
        verbose_name_plural = 'Feedbacks de Consultas'
    
    def __str__(self):
        return f"Feedback {self.id} - {self.rating}⭐"
