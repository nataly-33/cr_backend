from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.http import FileResponse
from django.conf import settings
import os
from apps.ai.models import DiabetesPrediction, DiabetesPredictionModel
from apps.ai.serializers import (
    DiabetesPredictionSerializer,
    DiabetesPredictionModelSerializer,
    PredictDiabetesRequestSerializer
)
from apps.ai.services.diabetes_predictor import DiabetesPredictor
from apps.ai.services.tree_visualizer import TreeVisualizer
from apps.core.permissions import IsTenantMember


class DiabetesPredictionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para predicciones de diabetes
    """
    queryset = DiabetesPrediction.objects.all()
    serializer_class = DiabetesPredictionSerializer
    permission_classes = [IsAuthenticated, IsTenantMember]
    
    def get_queryset(self):
        # Filtrar por tenant del usuario
        return DiabetesPrediction.objects.filter(tenant=self.request.tenant)
    
    @action(detail=False, methods=['post'])
    def predict(self, request):
        """
        Endpoint para realizar una predicción de diabetes
        POST /api/ai/diabetes/predict/
        Body: {"patient_id": "uuid"}
        """
        serializer = PredictDiabetesRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        patient_id = serializer.validated_data['patient_id']
        
        try:
            # Realizar predicción
            prediction = DiabetesPredictor.predict(
                patient_id=str(patient_id),
                user=request.user,
                tenant=request.tenant
            )
            
            # Serializar resultado
            result_serializer = DiabetesPredictionSerializer(prediction)
            
            return Response({
                'success': True,
                'message': 'Predicción realizada exitosamente',
                'data': result_serializer.data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], url_path='patient/(?P<patient_id>[^/.]+)')
    def patient_history(self, request, patient_id=None):
        """
        Obtiene el historial de predicciones de un paciente
        GET /api/ai/diabetes/patient/{patient_id}/
        """
        predictions = DiabetesPredictor.get_prediction_history(patient_id)
        serializer = DiabetesPredictionSerializer(predictions, many=True)
        
        return Response({
            'success': True,
            'count': len(predictions),
            'data': serializer.data
        })
    
    @action(detail=False, methods=['get'], url_path='model/info')
    def model_info(self, request):
        """
        Obtiene información del modelo activo
        GET /api/ai/diabetes/model/info/
        """
        try:
            model = DiabetesPredictionModel.objects.filter(is_active=True).first()
            if not model:
                return Response({
                    'success': False,
                    'error': 'No hay modelo activo'
                }, status=status.HTTP_404_NOT_FOUND)
            
            serializer = DiabetesPredictionModelSerializer(model)
            return Response({
                'success': True,
                'data': serializer.data
            })
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], url_path='tree/visualization', permission_classes=[AllowAny])
    def tree_visualization(self, request):
        """
        Genera y retorna la imagen del árbol de decisión
        GET /api/ai/diabetes/tree/visualization/
        """
        try:
            # Generar visualización
            image_path = TreeVisualizer.visualize_tree()

            # Verificar que existe
            if not os.path.exists(image_path):
                return Response({
                    'success': False,
                    'error': 'No se pudo generar la visualización'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Retornar imagen
            return FileResponse(open(image_path, 'rb'), content_type='image/png')

        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], url_path='tree/rules')
    def tree_rules(self, request):
        """
        Obtiene las reglas del árbol de decisión
        GET /api/ai/diabetes/tree/rules/
        """
        try:
            rules_data = TreeVisualizer.get_tree_rules()

            return Response({
                'success': True,
                'data': rules_data
            })

        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], url_path='tree/feature-importance', permission_classes=[AllowAny])
    def feature_importance(self, request):
        """
        Genera y retorna el gráfico de importancia de características
        GET /api/ai/diabetes/tree/feature-importance/
        """
        try:
            # Generar gráfico
            image_path = TreeVisualizer.get_feature_importance_chart()

            # Verificar que existe
            if not os.path.exists(image_path):
                return Response({
                    'success': False,
                    'error': 'No se pudo generar el gráfico'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Retornar imagen
            return FileResponse(open(image_path, 'rb'), content_type='image/png')

        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
