"""
Servicio de Predicción de Diabetes usando árbol de decisión
Realiza predicciones individuales y maneja el ciclo de vida del modelo
"""
import os
import joblib
import logging
from typing import Dict, List, Optional
from datetime import datetime
from django.core.cache import cache
from django.conf import settings
from ..models import DiabetesPrediction, DiabetesPredictionModel
from .diabetes_data_extractor import extract_patient_features, normalize_features

logger = logging.getLogger(__name__)

# Cache del modelo en memoria
_model_cache = None
_model_version_cache = None


def load_latest_model():
    """
    Carga el modelo más reciente desde archivos
    Utiliza cache en memoria para rapidez
    
    Returns:
        tuple: (modelo, versión, path del archivo)
    """
    global _model_cache, _model_version_cache
    
    # Intentar obtener del cache
    cached = cache.get('diabetes_model')
    if cached:
        return cached
    
    try:
        # Obtener la última versión del modelo de la BD
        latest_model = DiabetesPredictionModel.objects.filter(
            is_active=True
        ).order_by('-created_at').first()
        
        if not latest_model:
            logger.error("No hay modelo de diabetes activo")
            return None, None, None
        
        # Ruta del archivo del modelo
        model_path = os.path.join(
            settings.MEDIA_ROOT,
            'models',
            f'diabetes_model_v{latest_model.version}.pkl'
        )
        
        if not os.path.exists(model_path):
            logger.error(f"Archivo del modelo no encontrado: {model_path}")
            return None, None, None
        
        # Cargar modelo
        model = joblib.load(model_path)
        
        # Cachear durante 1 hora
        cache.set('diabetes_model', (model, latest_model.version, model_path), 3600)
        
        logger.info(f"Modelo cargado: versión {latest_model.version}")
        return model, latest_model.version, model_path
        
    except Exception as e:
        logger.exception(f"Error al cargar modelo: {str(e)}")
        return None, None, None


def predict_diabetes_risk(patient_id: str) -> Dict:
    """
    Realiza predicción de riesgo de diabetes para un paciente
    
    Args:
        patient_id: UUID del paciente
        
    Returns:
        dict: {
            "success": bool,
            "patient_id": str,
            "has_diabetes_risk": bool,
            "probability": float,  # 0.0 - 1.0
            "risk_level": str,  # "Bajo" / "Medio" / "Alto"
            "contributing_factors": list,
            "recommendations": list,
            "timestamp": datetime,
            "model_version": str
        }
    """
    try:
        # Cargar modelo
        model, model_version, _ = load_latest_model()
        if not model:
            return {
                "success": False,
                "error": "Modelo no disponible",
                "patient_id": patient_id
            }
        
        # Extraer características del paciente
        features_dict = extract_patient_features(patient_id)
        if not features_dict.get("success"):
            return {
                "success": False,
                "error": "No se pudieron extraer características del paciente",
                "patient_id": patient_id,
                "details": features_dict.get("error")
            }
        
        features_data = features_dict["features"]
        
        # Normalizar datos
        X, feature_names = normalize_features([features_data])
        
        # Hacer predicción
        prediction = model.predict(X)[0]  # 0 = No diabetes, 1 = Diabetes
        probability = model.predict_proba(X)[0][1]  # Probabilidad de diabetes
        
        # Determinar nivel de riesgo
        if probability < 0.33:
            risk_level = "Bajo"
        elif probability < 0.67:
            risk_level = "Medio"
        else:
            risk_level = "Alto"
        
        # Obtener factores contribuyentes
        contributing_factors = get_contributing_factors(
            model, X[0], feature_names, features_data
        )
        
        # Obtener recomendaciones basadas en factores
        recommendations = get_recommendations(contributing_factors, features_data)
        
        # Preparar resultado
        result = {
            "success": True,
            "patient_id": patient_id,
            "has_diabetes_risk": bool(prediction),
            "probability": float(probability),
            "risk_level": risk_level,
            "contributing_factors": contributing_factors,
            "recommendations": recommendations,
            "timestamp": datetime.now(),
            "model_version": model_version
        }
        
        # Guardar predicción en BD
        save_prediction(patient_id, result)
        
        logger.info(
            f"Predicción realizada para paciente {patient_id}: "
            f"Riesgo={probability:.2%}, Nivel={risk_level}"
        )
        
        return result
        
    except Exception as e:
        logger.exception(f"Error durante predicción para paciente {patient_id}")
        return {
            "success": False,
            "error": str(e),
            "patient_id": patient_id
        }


def get_contributing_factors(model, features: List[float], 
                            feature_names: List[str],
                            features_dict: Dict) -> List[str]:
    """
    Determina qué factores más contribuyeron a la predicción
    Usa feature_importances_ del árbol de decisión
    
    Args:
        model: Modelo entrenado
        features: Array de características normalizadas
        feature_names: Nombres de las características
        features_dict: Dict original con valores
        
    Returns:
        list: Lista de factores ordenados por importancia
    """
    factors = []
    
    try:
        # Obtener importancias de características
        if hasattr(model, 'feature_importances_'):
            importances = model.feature_importances_
            
            # Ordenar por importancia
            sorted_indices = importances.argsort()[::-1]
            
            # Tomar los 3 más importantes
            for idx in sorted_indices[:3]:
                if importances[idx] > 0.01:  # Solo si es significativo
                    factor_name = feature_names[idx]
                    original_value = features_dict.get(
                        factor_name.lower().replace(' ', '_')
                    )
                    
                    # Crear descripción legible
                    if original_value is not None:
                        factors.append(f"{factor_name} ({original_value})")
                    else:
                        factors.append(factor_name)
        
        # Si no hay importancias, analizar manualmente los valores
        if not factors:
            # Detectar valores altos/bajos significativos
            if features_dict.get("bmi", 0) > 30:
                factors.append("IMC elevado (sobrepeso/obesidad)")
            if features_dict.get("fasting_glucose", 0) > 126:
                factors.append("Glucosa en ayunas elevada")
            if features_dict.get("family_history_diabetes"):
                factors.append("Antecedentes familiares de diabetes")
            if features_dict.get("systolic_bp", 0) > 140:
                factors.append("Presión arterial sistólica alta")
            if features_dict.get("age", 0) > 45:
                factors.append("Edad avanzada (>45 años)")
        
        return factors[:5]  # Máximo 5 factores
        
    except Exception as e:
        logger.warning(f"Error al extraer factores contribuyentes: {str(e)}")
        return []


def get_recommendations(factors: List[str], features_dict: Dict) -> List[str]:
    """
    Genera recomendaciones médicas basadas en factores de riesgo
    
    Args:
        factors: Lista de factores contribuyentes
        features_dict: Diccionario de características del paciente
        
    Returns:
        list: Lista de recomendaciones personalizadas
    """
    recommendations = []
    
    # Recomendaciones basadas en IMC
    if features_dict.get("bmi", 0) > 30:
        recommendations.append("Reducir peso mediante dieta balanceada y ejercicio")
        recommendations.append("Control de triglicéridos e hipertensión")
    
    # Recomendaciones basadas en glucosa
    if features_dict.get("fasting_glucose", 0) > 126:
        recommendations.append("Realizar prueba de glucosa cada 3 meses")
        recommendations.append("Reducir ingesta de carbohidratos simples")
    
    # Recomendaciones basadas en antecedentes familiares
    if features_dict.get("family_history_diabetes"):
        recommendations.append("Chequeos preventivos regulares de diabetes")
        recommendations.append("Mantener estilos de vida saludable")
    
    # Recomendaciones basadas en presión arterial
    if features_dict.get("systolic_bp", 0) > 140:
        recommendations.append("Controlar presión arterial regularmente")
        recommendations.append("Reducir ingesta de sodio")
    
    # Recomendación general
    if not recommendations:
        recommendations.append("Mantener estilo de vida saludable")
        recommendations.append("Realizar chequeos médicos anuales")
    
    recommendations.append("Consultar con endocrinólogo si hay sospecha de diabetes")
    
    return recommendations[:5]  # Máximo 5 recomendaciones


def save_prediction(patient_id: str, prediction_result: Dict) -> None:
    """
    Guarda la predicción en la base de datos
    
    Args:
        patient_id: UUID del paciente
        prediction_result: Resultado de la predicción
    """
    try:
        from django.contrib.auth import get_user_model
        from apps.patients.models import Patient
        
        Patient = Patient
        
        patient = Patient.objects.get(id=patient_id)
        model = DiabetesPredictionModel.objects.filter(
            is_active=True
        ).order_by('-created_at').first()
        
        if not model:
            logger.warning("No hay modelo activo para guardar predicción")
            return
        
        DiabetesPrediction.objects.create(
            patient=patient,
            model=model,
            has_diabetes_risk=prediction_result.get("has_diabetes_risk", False),
            probability=prediction_result.get("probability", 0.0),
            risk_level=prediction_result.get("risk_level", "Desconocido"),
            contributing_factors=prediction_result.get("contributing_factors", []),
            recommendations=prediction_result.get("recommendations", []),
            metadata={
                "model_version": prediction_result.get("model_version"),
                "timestamp": prediction_result.get("timestamp").isoformat()
            }
        )
        
        logger.info(f"Predicción guardada para paciente {patient_id}")
        
    except Exception as e:
        logger.exception(f"Error al guardar predicción: {str(e)}")


def get_model_info() -> Dict:
    """
    Obtiene información del modelo actual
    
    Returns:
        dict: Información del modelo (versión, accuracy, fecha)
    """
    try:
        model = DiabetesPredictionModel.objects.filter(
            is_active=True
        ).order_by('-created_at').first()
        
        if not model:
            return {"error": "No hay modelo activo"}
        
        return {
            "version": model.version,
            "accuracy": model.accuracy,
            "precision": model.precision,
            "recall": model.recall,
            "f1_score": model.f1_score,
            "created_at": model.created_at,
            "training_samples": model.training_samples,
            "is_active": model.is_active
        }
        
    except Exception as e:
        logger.exception("Error al obtener información del modelo")
        return {"error": str(e)}


def predict_batch(patient_ids: List[str]) -> List[Dict]:
    """
    Realiza predicciones para múltiples pacientes
    
    Args:
        patient_ids: Lista de UUIDs de pacientes
        
    Returns:
        list: Lista de resultados de predicción
    """
    results = []
    for patient_id in patient_ids:
        result = predict_diabetes_risk(patient_id)
        results.append(result)
    return results


def train_model() -> Dict:
    """
    Re-entrena el modelo de diabetes con los datos más recientes
    
    Returns:
        dict: Información sobre el entrenamiento (accuracy, precision, recall, f1_score)
    """
    try:
        from .diabetes_model_trainer import train_diabetes_model
        
        logger.info("Iniciando re-entrenamiento del modelo de diabetes...")
        
        # Entrenar nuevo modelo
        model_info = train_diabetes_model()
        
        if not model_info.get('success'):
            logger.error(f"Error en entrenamiento: {model_info.get('error')}")
            return {
                'success': False,
                'error': model_info.get('error', 'Error desconocido durante el entrenamiento')
            }
        
        # Limpiar cache
        cache.delete('diabetes_model')
        cache.delete('model_info')
        global _model_cache, _model_version_cache
        _model_cache = None
        _model_version_cache = None
        
        logger.info(f"Modelo re-entrenado exitosamente. Accuracy: {model_info.get('accuracy', 0):.2%}")
        
        return {
            'success': True,
            'message': 'Modelo re-entrenado exitosamente',
            'accuracy': model_info.get('accuracy'),
            'precision': model_info.get('precision'),
            'recall': model_info.get('recall'),
            'f1_score': model_info.get('f1_score'),
            'training_samples': model_info.get('training_samples'),
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.exception("Error al re-entrenar modelo de diabetes")
        return {
            'success': False,
            'error': str(e)
        }

