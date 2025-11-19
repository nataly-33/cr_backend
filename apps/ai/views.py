"""
Views/Endpoints para la API de predicción de diabetes
"""
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Avg
from drf_spectacular.utils import extend_schema, OpenApiParameter

from ..models import DiabetesPrediction, DiabetesPredictionModel
from ..serializers import (
    DiabetesPredictionSerializer,
    DiabetesPredictionModelSerializer,
    DiabetesPredictionRequestSerializer,
    DiabetesPredictionResponseSerializer,
    BatchPredictionRequestSerializer
)
from ..services.diabetes_predictor import (
    predict_diabetes_risk,
    get_model_info,
    predict_batch,
    train_model
)
from .permissions import IsAdminForRetrain

logger = logging.getLogger(__name__)


class DiabetesPredictionViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar predicciones de diabetes
    
    Endpoints:
    - POST /api/ai/diabetes/predict/ - Hacer predicción
    - GET /api/ai/diabetes/predictions/{patient_id}/ - Historial de predicciones
    - GET /api/ai/diabetes/model/info/ - Información del modelo
    - POST /api/ai/diabetes/predict-batch/ - Predicción por lotes
    """
    
    serializer_class = DiabetesPredictionSerializer
    permission_classes = [IsAuthenticated]
    queryset = DiabetesPrediction.objects.all()
    
    @extend_schema(
        summary="Realizar predicción de diabetes para un paciente",
        request=DiabetesPredictionRequestSerializer,
        responses={200: DiabetesPredictionResponseSerializer},
        tags=["AI - Predicción de Diabetes"]
    )
    @action(detail=False, methods=['post'], url_path='predict')
    def predict(self, request):
        """
        Realiza predicción de riesgo de diabetes para un paciente específico
        
        Parámetros:
        - patient_id (uuid): ID del paciente
        
        Retorna:
        - success (bool): Si la predicción fue exitosa
        - has_diabetes_risk (bool): Si hay riesgo de diabetes
        - probability (float): Probabilidad de diabetes (0-1)
        - risk_level (str): Nivel de riesgo (Bajo/Medio/Alto)
        - contributing_factors (list): Factores que contribuyen
        - recommendations (list): Recomendaciones médicas
        """
        try:
            serializer = DiabetesPredictionRequestSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            patient_id = serializer.validated_data['patient_id']
            
            # Realizar predicción
            result = predict_diabetes_risk(str(patient_id))
            
            if not result.get('success'):
                return Response(
                    result,
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            return Response(result, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.exception("Error en endpoint de predicción")
            return Response(
                {
                    "success": False,
                    "error": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Obtener historial de predicciones de un paciente",
        responses=DiabetesPredictionSerializer(many=True),
        tags=["AI - Predicción de Diabetes"]
    )
    @action(detail=False, methods=['get'], url_path='predictions/(?P<patient_id>[^/.]+)')
    def get_predictions(self, request, patient_id=None):
        """
        Obtiene todas las predicciones previas de un paciente
        
        Parámetros:
        - patient_id: ID del paciente (en URL)
        
        Retorna:
        - Lista de predicciones ordenadas por fecha descendente
        """
        try:
            predictions = DiabetesPrediction.objects.filter(
                patient_id=patient_id
            ).order_by('-created_at')
            
            serializer = self.get_serializer(predictions, many=True)
            return Response(serializer.data)
            
        except Exception as e:
            logger.exception("Error al obtener predicciones")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Obtener información del modelo actual",
        responses={
            200: DiabetesPredictionModelSerializer
        },
        tags=["AI - Predicción de Diabetes"]
    )
    @action(detail=False, methods=['get'], url_path='model/info')
    def model_info(self, request):
        """
        Obtiene información del modelo de diabetes activo
        
        Retorna:
        - version: Versión del modelo
        - accuracy: Precisión general
        - precision: Precisión (TP/(TP+FP))
        - recall: Sensibilidad (TP/(TP+FN))
        - f1_score: Score F1
        - training_samples: Cantidad de muestras de entrenamiento
        - created_at: Fecha de creación
        - is_active: Si está activo
        """
        info = get_model_info()
        
        if 'error' in info:
            return Response(info, status=status.HTTP_404_NOT_FOUND)
        
        return Response(info, status=status.HTTP_200_OK)
    
    @extend_schema(
        summary="Realizar predicción para múltiples pacientes",
        request=BatchPredictionRequestSerializer,
        tags=["AI - Predicción de Diabetes"]
    )
    @action(detail=False, methods=['post'], url_path='predict-batch')
    def predict_batch(self, request):
        """
        Realiza predicciones para múltiples pacientes
        
        Parámetros:
        - patient_ids (list): Lista de UUIDs de pacientes
        
        Retorna:
        - total: Total de pacientes procesados
        - successful: Predicciones exitosas
        - failed: Predicciones fallidas
        - results: Array de resultados
        """
        try:
            serializer = BatchPredictionRequestSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            patient_ids = serializer.validated_data['patient_ids']
            
            # Realizar predicciones
            results = predict_batch([str(pid) for pid in patient_ids])
            
            # Contar exitosas y fallidas
            successful = sum(1 for r in results if r.get('success', False))
            failed = len(results) - successful
            
            return Response({
                'total': len(results),
                'successful': successful,
                'failed': failed,
                'results': results
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.exception("Error en predicción por lotes")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Obtener estadísticas de diabetes",
        tags=["AI - Predicción de Diabetes"]
    )
    @action(detail=False, methods=['get'], url_path='statistics')
    def statistics(self, request):
        """
        Obtiene estadísticas sobre predicciones de diabetes
        
        Retorna:
        - total_predictions: Total de predicciones realizadas
        - high_risk_count: Cantidad de pacientes con alto riesgo
        - medium_risk_count: Cantidad con riesgo medio
        - low_risk_count: Cantidad con riesgo bajo
        - average_probability: Probabilidad promedio
        """
        try:
            predictions = DiabetesPrediction.objects.all()
            
            total = predictions.count()
            if total == 0:
                return Response({
                    'total_predictions': 0,
                    'high_risk_count': 0,
                    'medium_risk_count': 0,
                    'low_risk_count': 0,
                    'average_probability': 0.0
                })
            
            high_risk = predictions.filter(risk_level='Alto').count()
            medium_risk = predictions.filter(risk_level='Medio').count()
            low_risk = predictions.filter(risk_level='Bajo').count()
            avg_prob = predictions.aggregate(
                avg=Avg('probability')
            )['avg'] or 0.0
            
            return Response({
                'total_predictions': total,
                'high_risk_count': high_risk,
                'medium_risk_count': medium_risk,
                'low_risk_count': low_risk,
                'average_probability': float(avg_prob)
            })
            
        except Exception as e:
            logger.exception("Error al obtener estadísticas")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Re-entrenar modelo de diabetes (Admin only)",
        tags=["AI - Predicción de Diabetes"]
    )
    @action(
        detail=False, 
        methods=['post'], 
        url_path='model/retrain',
        permission_classes=[IsAdminForRetrain]
    )
    def model_retrain(self, request):
        """
        Re-entrena el modelo de diabetes con los datos más recientes
        
        Requiere: Permisos de administrador
        
        Retorna:
        - success: Si el re-entrenamiento fue exitoso
        - accuracy: Precisión del nuevo modelo
        - precision: Precisión (TP/(TP+FP))
        - recall: Sensibilidad (TP/(TP+FN))
        - f1_score: Score F1
        - training_samples: Cantidad de muestras de entrenamiento
        - timestamp: Cuándo se realizó el entrenamiento
        """
        try:
            result = train_model()
            
            if not result.get('success'):
                return Response(
                    result,
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            return Response(result, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.exception("Error en re-entrenamiento del modelo")
            return Response(
                {
                    "success": False,
                    "error": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
