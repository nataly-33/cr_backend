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


class DiabetesPredictionModel(models.Model):
    """Modelo de predicción de diabetes entrenado"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    version = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_('Versión del modelo'),
        help_text=_('ej: 1.0, 1.1, 2.0')
    )

    model_file = models.CharField(
        max_length=500,
        verbose_name=_('Ruta del archivo del modelo'),
        help_text=_('Ruta relativa al archivo .pkl del modelo')
    )

    algorithm = models.CharField(
        max_length=100,
        default='DecisionTreeClassifier',
        verbose_name=_('Algoritmo utilizado')
    )

    # Métricas de evaluación
    accuracy = models.FloatField(
        verbose_name=_('Exactitud (Accuracy)'),
        help_text=_('0.0 a 1.0')
    )

    precision = models.FloatField(
        verbose_name=_('Precisión'),
        help_text=_('0.0 a 1.0')
    )

    recall = models.FloatField(
        verbose_name=_('Recall (Sensibilidad)'),
        help_text=_('0.0 a 1.0')
    )

    f1_score = models.FloatField(
        verbose_name=_('F1-Score'),
        help_text=_('0.0 a 1.0')
    )

    # Información del entrenamiento
    training_samples = models.IntegerField(
        verbose_name=_('Muestras de entrenamiento'),
        help_text=_('Número de registros usados para entrenar')
    )

    test_samples = models.IntegerField(
        verbose_name=_('Muestras de prueba'),
        help_text=_('Número de registros usados para evaluar')
    )

    features_used = models.JSONField(
        default=list,
        verbose_name=_('Features utilizadas'),
        help_text=_('["age", "bmi", "glucose", ...]')
    )

    hyperparameters = models.JSONField(
        default=dict,
        verbose_name=_('Hiperparámetros'),
        help_text=_('{"max_depth": 5, "min_samples_split": 10, ...}')
    )

    confusion_matrix = models.JSONField(
        default=list,
        verbose_name=_('Matriz de confusión'),
        help_text=_('[[TN, FP], [FN, TP]]')
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Modelo activo'),
        help_text=_('Solo un modelo puede estar activo a la vez')
    )

    trained_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='diabetes_models_trained',
        verbose_name=_('Entrenado por')
    )

    notes = models.TextField(
        blank=True,
        verbose_name=_('Notas'),
        help_text=_('Observaciones sobre este modelo')
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'diabetes_prediction_model'
        verbose_name = _('Modelo de Predicción de Diabetes')
        verbose_name_plural = _('Modelos de Predicción de Diabetes')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_active']),
            models.Index(fields=['version']),
        ]

    def __str__(self):
        return f"Modelo v{self.version} - Accuracy: {self.accuracy:.2%}"


class DiabetesPrediction(models.Model):
    """Predicción de diabetes realizada para un paciente"""

    RISK_LEVEL_CHOICES = [
        ('low', 'Bajo'),
        ('medium', 'Medio'),
        ('high', 'Alto'),
        ('very_high', 'Muy Alto'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    patient = models.ForeignKey(
        'patients.Patient',
        on_delete=models.CASCADE,
        related_name='diabetes_predictions',
        verbose_name=_('Paciente')
    )

    model = models.ForeignKey(
        DiabetesPredictionModel,
        on_delete=models.PROTECT,
        related_name='predictions',
        verbose_name=_('Modelo utilizado')
    )

    # Resultado de la predicción
    has_diabetes_risk = models.BooleanField(
        verbose_name=_('Riesgo de diabetes'),
        help_text=_('True si el modelo predice riesgo de diabetes')
    )

    probability = models.FloatField(
        verbose_name=_('Probabilidad'),
        help_text=_('Probabilidad de tener diabetes (0.0 a 1.0)')
    )

    risk_level = models.CharField(
        max_length=20,
        choices=RISK_LEVEL_CHOICES,
        verbose_name=_('Nivel de riesgo')
    )

    # Features usadas en la predicción
    input_features = models.JSONField(
        verbose_name=_('Features de entrada'),
        help_text=_('{{"age": 45, "bmi": 28.5, "glucose": 140, ...}}')
    )

    # Factores contribuyentes
    contributing_factors = models.JSONField(
        default=list,
        verbose_name=_('Factores contribuyentes'),
        help_text=_('["IMC alto (32.5)", "Glucosa elevada (155)", ...]')
    )

    # Importancia de features
    feature_importance = models.JSONField(
        default=dict,
        verbose_name=_('Importancia de features'),
        help_text=_('{{"glucose": 0.35, "bmi": 0.25, ...}}')
    )

    # Recomendaciones
    recommendations = models.JSONField(
        default=list,
        verbose_name=_('Recomendaciones'),
        help_text=_('["Control de glucosa mensual", "Reducir peso", ...]')
    )

    # Metadata
    predicted_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='diabetes_predictions_made',
        verbose_name=_('Predicción realizada por')
    )

    tenant = models.ForeignKey(
        'core.Tenant',
        on_delete=models.CASCADE,
        verbose_name=_('Tenant')
    )

    notes = models.TextField(
        blank=True,
        verbose_name=_('Notas médicas'),
        help_text=_('Observaciones del médico sobre la predicción')
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'diabetes_prediction'
        verbose_name = _('Predicción de Diabetes')
        verbose_name_plural = _('Predicciones de Diabetes')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant', 'patient']),
            models.Index(fields=['risk_level']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"{self.patient.get_full_name()} - Riesgo {self.get_risk_level_display()} ({self.probability:.0%})"


class DiabetesDataset(models.Model):
    """Dataset para entrenar el modelo de predicción de diabetes"""

    SOURCE_CHOICES = [
        ('pima', 'Pima Indians Dataset'),
        ('synthetic', 'Datos Sintéticos'),
        ('clinical', 'Datos Clínicos Reales'),
        ('mixed', 'Mixto'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    source = models.CharField(
        max_length=50,
        choices=SOURCE_CHOICES,
        verbose_name=_('Fuente de datos')
    )

    # Features del dataset (siguiendo Pima Indians)
    pregnancies = models.IntegerField(
        verbose_name=_('Número de embarazos'),
        help_text=_('0 para hombres')
    )

    glucose = models.FloatField(
        verbose_name=_('Glucosa en plasma (mg/dL)')
    )

    blood_pressure = models.FloatField(
        verbose_name=_('Presión arterial diastólica (mm Hg)')
    )

    skin_thickness = models.FloatField(
        verbose_name=_('Grosor del pliegue cutáneo del tríceps (mm)')
    )

    insulin = models.FloatField(
        verbose_name=_('Insulina sérica (mu U/ml)')
    )

    bmi = models.FloatField(
        verbose_name=_('Índice de Masa Corporal (kg/m²)')
    )

    diabetes_pedigree_function = models.FloatField(
        verbose_name=_('Función de pedigrí de diabetes'),
        help_text=_('Probabilidad genética de diabetes')
    )

    age = models.IntegerField(
        verbose_name=_('Edad (años)')
    )

    # Target
    outcome = models.BooleanField(
        verbose_name=_('Tiene diabetes'),
        help_text=_('True = Diabetes, False = No diabetes')
    )

    # Metadata
    patient = models.ForeignKey(
        'patients.Patient',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='diabetes_dataset_records',
        verbose_name=_('Paciente (si es dato real)')
    )

    is_training_data = models.BooleanField(
        default=True,
        verbose_name=_('Dato de entrenamiento'),
        help_text=_('False si es dato de validación/test')
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'diabetes_dataset'
        verbose_name = _('Registro de Dataset de Diabetes')
        verbose_name_plural = _('Registros de Dataset de Diabetes')
        ordering = ['id']
        indexes = [
            models.Index(fields=['source']),
            models.Index(fields=['outcome']),
            models.Index(fields=['is_training_data']),
        ]

    def __str__(self):
        return f"{self.source} - Edad: {self.age}, Diabetes: {self.outcome}"
