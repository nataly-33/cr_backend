from django.db import models
from django.utils.translation import gettext_lazy as _
import uuid


class AIConversation(models.Model):
    """Historial de conversaciones con el asistente IA"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='ai_conversations',
        verbose_name=_('Usuario')
    )
    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_('Tenant')
    )
    
    title = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_('Título de la conversación')
    )
    
    context_type = models.CharField(
        max_length=50,
        choices=[
            ('general', 'Ayuda General'),
            ('patient', 'Información Paciente'),
            ('document', 'Análisis Documento'),
            ('report', 'Generación Reporte'),
        ],
        default='general',
        verbose_name=_('Tipo de contexto')
    )
    context_id = models.UUIDField(
        null=True,
        blank=True,
        verbose_name=_('ID de contexto'),
        help_text=_('ID del paciente, documento, etc.')
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'ai_conversations'
        verbose_name = _('Conversación IA')
        verbose_name_plural = _('Conversaciones IA')
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.title or 'Sin título'} - {self.user.email}"


class AIMessage(models.Model):
    """Mensaje en una conversación con IA"""
    
    ROLE_CHOICES = [
        ('user', 'Usuario'),
        ('assistant', 'Asistente'),
        ('system', 'Sistema'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(
        AIConversation,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name=_('Conversación')
    )
    
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        verbose_name=_('Rol')
    )
    
    content = models.TextField(
        verbose_name=_('Contenido del mensaje')
    )
    
    # Metadata
    tokens_used = models.IntegerField(
        default=0,
        verbose_name=_('Tokens utilizados')
    )
    
    confidence_score = models.FloatField(
        default=0.0,
        verbose_name=_('Confianza de la respuesta'),
        help_text=_('0.0 a 1.0')
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'ai_messages'
        verbose_name = _('Mensaje IA')
        verbose_name_plural = _('Mensajes IA')
        ordering = ['created_at']
    
    def __str__(self):
        preview = self.content[:50] + ('...' if len(self.content) > 50 else '')
        return f"{self.role}: {preview}"


class AIKnowledgeBase(models.Model):
    """Base de conocimiento para entrenar al asistente"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    category = models.CharField(
        max_length=100,
        verbose_name=_('Categoría'),
        help_text=_('ej: procesos, diagnósticos, etc.')
    )
    
    question = models.TextField(
        verbose_name=_('Pregunta/Tema')
    )
    
    answer = models.TextField(
        verbose_name=_('Respuesta/Información')
    )
    
    keywords = models.CharField(
        max_length=500,
        blank=True,
        verbose_name=_('Palabras clave (separadas por comas)')
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Activo')
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'ai_knowledge_base'
        verbose_name = _('Base de Conocimiento IA')
        verbose_name_plural = _('Bases de Conocimiento IA')
        indexes = [
            models.Index(fields=['category', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.category}: {self.question[:50]}"
