"""
Servicio para realizar predicciones de diabetes en pacientes
"""
from typing import Dict
from apps.patients.models import Patient
from apps.ai.models import DiabetesPrediction
from apps.ai.services.diabetes_model_trainer import DiabetesModelTrainer
from apps.ai.services.diabetes_data_extractor import DiabetesDataExtractor


class DiabetesPredictor:
    """Realiza predicciones de diabetes para pacientes"""

    RISK_THRESHOLDS = {
        'low': 0.30,
        'medium': 0.60,
        'high': 0.80,
        'very_high': 1.0,
    }

    @staticmethod
    def predict(patient_id: str, user=None, tenant=None):
        patient = Patient.objects.get(id=patient_id)
        if not tenant:
            tenant = patient.tenant

        features = DiabetesDataExtractor.extract_patient_features(patient_id)
        model, model_db = DiabetesModelTrainer.load_active_model()
        X = [DiabetesDataExtractor.features_to_array(features)]

        prediction = model.predict(X)[0]
        probability = model.predict_proba(X)[0][1]
        risk_level = DiabetesPredictor._calculate_risk_level(probability)
        feature_importance = DiabetesModelTrainer.get_feature_importance(model)
        contributing_factors = DiabetesPredictor._identify_contributing_factors(features, feature_importance)
        recommendations = DiabetesPredictor._generate_recommendations(features, risk_level, contributing_factors)

        diabetes_prediction = DiabetesPrediction.objects.create(
            patient=patient,
            model=model_db,
            has_diabetes_risk=bool(prediction),
            probability=float(probability),
            risk_level=risk_level,
            input_features=features,
            contributing_factors=contributing_factors,
            feature_importance=feature_importance,
            recommendations=recommendations,
            predicted_by=user,
            tenant=tenant
        )

        return diabetes_prediction

    @staticmethod
    def _calculate_risk_level(probability):
        if probability <= 0.30:
            return 'low'
        elif probability <= 0.60:
            return 'medium'
        elif probability <= 0.80:
            return 'high'
        else:
            return 'very_high'

    @staticmethod
    def _identify_contributing_factors(features, feature_importance):
        factors = []
        glucose = features.get('glucose', 0)
        if glucose > 126:
            factors.append({'factor': 'Glucosa elevada', 'value': f'{glucose} mg/dL', 'normal': '< 100 mg/dL'})
        
        bmi = features.get('bmi', 0)
        if bmi > 30:
            factors.append({'factor': 'Obesidad', 'value': f'IMC {bmi}', 'normal': 'IMC 18.5-24.9'})
        
        age = features.get('age', 0)
        if age > 45:
            factors.append({'factor': 'Edad avanzada', 'value': f'{age} años'})
        
        return factors

    @staticmethod
    def _generate_recommendations(features, risk_level, contributing_factors):
        recommendations = []
        
        if features.get('glucose', 0) > 126:
            recommendations.append({'category': 'Glucosa', 'priority': 'high', 'recommendation': 'Realizar prueba HbA1c'})
        
        if features.get('bmi', 0) > 30:
            recommendations.append({'category': 'Peso', 'priority': 'high', 'recommendation': 'Programa de reducción de peso'})
        
        if risk_level == 'very_high':
            recommendations.append({'category': 'Seguimiento', 'priority': 'high', 'recommendation': 'Evaluación médica inmediata'})
        
        return recommendations

    @staticmethod
    def get_prediction_history(patient_id, limit=10):
        return DiabetesPrediction.objects.filter(patient_id=patient_id).select_related('model').order_by('-created_at')[:limit]
