"""
Servicio para extraer datos del historial clínico del paciente
y transformarlos al formato requerido por el modelo de predicción de diabetes
"""
from datetime import datetime
from typing import Dict, Optional
import re
from apps.patients.models import Patient
from apps.clinical_records.models import ClinicalRecord, ClinicalForm


class DiabetesDataExtractor:
    """Extrae y procesa datos clínicos para predicción de diabetes"""

    # Valores por defecto para datos faltantes
    DEFAULT_VALUES = {
        'glucose': 120.0,
        'insulin': 100.0,
        'skin_thickness': 20.0,
        'pregnancies': 0,
        'diabetes_pedigree_function': 0.5,
        'blood_pressure': 80.0,
        'bmi': 25.0,
    }

    # Rangos normales/esperados
    FEATURE_RANGES = {
        'age': (18, 100),
        'bmi': (15, 60),
        'glucose': (50, 400),
        'blood_pressure': (40, 150),
        'insulin': (0, 900),
        'skin_thickness': (0, 100),
        'pregnancies': (0, 20),
        'diabetes_pedigree_function': (0.0, 2.5)
    }

    @staticmethod
    def extract_patient_features(patient_id: str) -> Dict:
        """
        Extrae todas las características necesarias de un paciente

        Args:
            patient_id: UUID del paciente

        Returns:
            Dict con las features extraídas
        """
        try:
            patient = Patient.objects.get(id=patient_id)
        except Patient.DoesNotExist:
            raise ValueError(f"Paciente con ID {patient_id} no encontrado")

        # Obtener historial clínico
        clinical_record = ClinicalRecord.objects.filter(
            patient=patient,
            status='active'
        ).first()

        # Extraer edad
        age = patient.get_age()

        # Extraer datos demográficos
        gender = patient.gender  # M o F

        # Inicializar features con valores por defecto
        features = {
            'age': age,
            'pregnancies': 0,
            'glucose': DiabetesDataExtractor.DEFAULT_VALUES['glucose'],
            'blood_pressure': DiabetesDataExtractor.DEFAULT_VALUES['blood_pressure'],
            'skin_thickness': DiabetesDataExtractor.DEFAULT_VALUES['skin_thickness'],
            'insulin': DiabetesDataExtractor.DEFAULT_VALUES['insulin'],
            'bmi': DiabetesDataExtractor.DEFAULT_VALUES['bmi'],
            'diabetes_pedigree_function': DiabetesDataExtractor.DEFAULT_VALUES['diabetes_pedigree_function'],
        }

        if clinical_record:
            # Extraer antecedentes familiares
            if clinical_record.family_history:
                features['diabetes_pedigree_function'] = DiabetesDataExtractor.parse_family_history(
                    clinical_record.family_history
                )

            # Obtener último triaje (signos vitales)
            latest_triage = DiabetesDataExtractor.get_latest_triage(patient)
            if latest_triage:
                features.update(latest_triage)

            # Obtener últimos valores de laboratorio
            latest_lab = DiabetesDataExtractor.get_latest_lab_values(patient)
            if latest_lab:
                features.update(latest_lab)

        # Si es mujer, intentar obtener número de embarazos
        if gender == 'F':
            pregnancies = DiabetesDataExtractor.extract_pregnancies(patient)
            if pregnancies is not None:
                features['pregnancies'] = pregnancies

        # Validar y normalizar rangos
        features = DiabetesDataExtractor.validate_features(features)

        return features

    @staticmethod
    def get_latest_triage(patient: Patient) -> Optional[Dict]:
        """
        Obtiene los últimos signos vitales del triaje

        Returns:
            Dict con weight, height, bmi, blood_pressure
        """
        triage_form = ClinicalForm.objects.filter(
            clinical_record__patient=patient,
            form_type='triage'
        ).order_by('-form_date').first()

        if not triage_form or not triage_form.form_data:
            return None

        data = triage_form.form_data
        result = {}

        # Extraer peso y altura para calcular BMI
        weight = data.get('weight')  # en kg
        height = data.get('height')  # en cm

        if weight and height:
            bmi = DiabetesDataExtractor.calculate_bmi(weight, height)
            result['bmi'] = bmi

        # Extraer presión arterial diastólica
        blood_pressure_diastolic = data.get('blood_pressure_diastolic')
        if blood_pressure_diastolic:
            result['blood_pressure'] = float(blood_pressure_diastolic)

        return result if result else None

    @staticmethod
    def get_latest_lab_values(patient: Patient) -> Optional[Dict]:
        """
        Obtiene los últimos valores de laboratorio

        Returns:
            Dict con glucose, insulin
        """
        lab_form = ClinicalForm.objects.filter(
            clinical_record__patient=patient,
            form_type='lab_order'
        ).order_by('-form_date').first()

        if not lab_form or not lab_form.form_data:
            return None

        data = lab_form.form_data
        result = {}

        # Extraer glucosa
        glucose = data.get('glucose') or data.get('glucose_fasting')
        if glucose:
            result['glucose'] = float(glucose)

        # Extraer insulina
        insulin = data.get('insulin')
        if insulin:
            result['insulin'] = float(insulin)

        return result if result else None

    @staticmethod
    def calculate_bmi(weight_kg: float, height_cm: float) -> float:
        """
        Calcula el Índice de Masa Corporal

        Formula: BMI = peso (kg) / (altura (m))^2
        """
        if not weight_kg or not height_cm or height_cm == 0:
            return DiabetesDataExtractor.DEFAULT_VALUES['bmi']

        height_m = height_cm / 100.0
        bmi = weight_kg / (height_m ** 2)

        # Validar rango razonable
        if bmi < 10 or bmi > 70:
            return DiabetesDataExtractor.DEFAULT_VALUES['bmi']

        return round(bmi, 1)

    @staticmethod
    def parse_family_history(family_history_text: str) -> float:
        """
        Analiza el texto de antecedentes familiares y calcula
        una función de pedigrí de diabetes simplificada

        Returns:
            Float entre 0.0 y 2.5 (mayor = más riesgo genético)
        """
        if not family_history_text:
            return 0.5  # Valor neutral

        text_lower = family_history_text.lower()

        # Palabras clave de diabetes
        diabetes_keywords = ['diabetes', 'diabético', 'diabética', 'diabetico', 'diabetica']

        # Familiares de primer grado
        first_degree = ['padre', 'madre', 'hermano', 'hermana', 'hijo', 'hija']

        # Familiares de segundo grado
        second_degree = ['abuelo', 'abuela', 'tío', 'tía', 'tio', 'tia', 'primo', 'prima']

        score = 0.5  # Base neutral

        # Verificar si menciona diabetes
        has_diabetes = any(keyword in text_lower for keyword in diabetes_keywords)

        if has_diabetes:
            # Verificar si es familiar de primer grado (+0.8)
            if any(relative in text_lower for relative in first_degree):
                score = 1.5
            # Verificar si es familiar de segundo grado (+0.4)
            elif any(relative in text_lower for relative in second_degree):
                score = 0.9
            else:
                # Menciona diabetes pero no especifica familiar
                score = 1.0

            # Si menciona "ambos padres" o "padre y madre"
            if 'ambos padres' in text_lower or ('padre' in text_lower and 'madre' in text_lower):
                score = 2.0

        return min(score, 2.5)  # Cap en 2.5

    @staticmethod
    def extract_pregnancies(patient: Patient) -> Optional[int]:
        """
        Extrae el número de embarazos de una paciente
        Busca en el historial clínico
        """
        clinical_record = ClinicalRecord.objects.filter(
            patient=patient,
            status='active'
        ).first()

        if not clinical_record:
            return None

        # Buscar en family_history o social_history
        family_history = clinical_record.family_history or ""
        social_history = clinical_record.social_history or ""

        combined_text = f"{family_history} {social_history}".lower()

        # Buscar patrones como "3 embarazos", "gesta 2", "G2P1A0"
        patterns = [
            r'(\d+)\s*embarazos?',
            r'gesta\s*(\d+)',
            r'g(\d+)p',
        ]

        for pattern in patterns:
            match = re.search(pattern, combined_text)
            if match:
                return int(match.group(1))

        return None

    @staticmethod
    def validate_features(features: Dict) -> Dict:
        """
        Valida que las features estén en rangos razonables
        Si están fuera de rango, ajusta al límite más cercano
        """
        validated = features.copy()

        for feature, (min_val, max_val) in DiabetesDataExtractor.FEATURE_RANGES.items():
            if feature in validated:
                value = validated[feature]

                # Ajustar al rango
                if value < min_val:
                    validated[feature] = min_val
                elif value > max_val:
                    validated[feature] = max_val

        return validated

    @staticmethod
    def features_to_array(features: Dict) -> list:
        """
        Convierte el dict de features a un array en el orden correcto
        para el modelo (orden del dataset Pima Indians)

        Orden: [Pregnancies, Glucose, BloodPressure, SkinThickness,
                Insulin, BMI, DiabetesPedigreeFunction, Age]
        """
        return [
            features.get('pregnancies', 0),
            features.get('glucose', 120.0),
            features.get('blood_pressure', 80.0),
            features.get('skin_thickness', 20.0),
            features.get('insulin', 100.0),
            features.get('bmi', 25.0),
            features.get('diabetes_pedigree_function', 0.5),
            features.get('age', 30),
        ]

    @staticmethod
    def get_feature_names() -> list:
        """Retorna los nombres de las features en orden"""
        return [
            'pregnancies',
            'glucose',
            'blood_pressure',
            'skin_thickness',
            'insulin',
            'bmi',
            'diabetes_pedigree_function',
            'age'
        ]
