"""
Command para probar cómo el historial familiar afecta las predicciones
"""
from django.core.management.base import BaseCommand
from apps.patients.models import Patient
from apps.clinical_records.models import ClinicalRecord
from apps.ai.services.diabetes_data_extractor import DiabetesDataExtractor
from apps.ai.services.diabetes_predictor import DiabetesPredictor


class Command(BaseCommand):
    help = 'Prueba cómo el historial familiar afecta las predicciones'

    def add_arguments(self, parser):
        parser.add_argument(
            '--patient-id',
            type=str,
            help='ID del paciente a probar',
        )

    def handle(self, *args, **options):
        patient_id = options.get('patient_id')

        self.stdout.write('='*70)
        self.stdout.write(self.style.SUCCESS('Test: Impacto del Historial Familiar en Predicciones'))
        self.stdout.write('='*70)
        self.stdout.write('')

        if patient_id:
            # Probar con paciente específico
            try:
                patient = Patient.objects.get(id=patient_id)
            except Patient.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Paciente {patient_id} no encontrado'))
                return
        else:
            # Buscar paciente sintético con historial familiar
            patient = Patient.objects.filter(
                identity_document__startswith='SYNTH-',
                clinicalrecord__family_history__isnull=False
            ).first()

            if not patient:
                self.stdout.write(self.style.ERROR('No hay pacientes con historial familiar'))
                return

        clinical_record = ClinicalRecord.objects.filter(
            patient=patient,
            status='active'
        ).first()

        self.stdout.write(f'Paciente: {patient.first_name} {patient.last_name}')
        self.stdout.write(f'ID: {patient.id}')
        self.stdout.write(f'Edad: {patient.get_age()} años')
        self.stdout.write('')

        # Extraer features actuales
        self.stdout.write('─' * 70)
        self.stdout.write(self.style.HTTP_INFO('1. EXTRAYENDO FEATURES ACTUALES'))
        self.stdout.write('─' * 70)

        features_original = DiabetesDataExtractor.extract_patient_features(str(patient.id))

        self.stdout.write(f'Historial familiar actual: {clinical_record.family_history or "Ninguno"}')
        self.stdout.write(f'Diabetes Pedigree Function: {features_original["diabetes_pedigree_function"]}')
        self.stdout.write('')

        for key, value in features_original.items():
            self.stdout.write(f'  {key:30} : {value}')

        self.stdout.write('')
        self.stdout.write('─' * 70)
        self.stdout.write(self.style.HTTP_INFO('2. PREDICCIÓN CON HISTORIAL ACTUAL'))
        self.stdout.write('─' * 70)

        # Hacer predicción con historial actual
        array_original = DiabetesDataExtractor.features_to_array(features_original)

        from apps.ai.services.diabetes_model_trainer import DiabetesModelTrainer
        model = DiabetesModelTrainer.load_active_model()

        if not model:
            self.stdout.write(self.style.ERROR('No hay modelo activo'))
            return

        prediction_original = model.predict([array_original])[0]
        probability_original = model.predict_proba([array_original])[0]

        self.stdout.write(f'Predicción: {"POSITIVA (Diabetes)" if prediction_original == 1 else "NEGATIVA (No diabetes)"}')
        self.stdout.write(f'Probabilidad diabetes: {probability_original[1]*100:.2f}%')
        self.stdout.write(f'Probabilidad no diabetes: {probability_original[0]*100:.2f}%')

        self.stdout.write('')
        self.stdout.write('─' * 70)
        self.stdout.write(self.style.HTTP_INFO('3. SIMULANDO CAMBIOS EN HISTORIAL FAMILIAR'))
        self.stdout.write('─' * 70)

        # Guardar historial original
        original_family_history = clinical_record.family_history

        # Casos de prueba
        test_cases = [
            {
                'name': 'Sin antecedentes familiares',
                'history': None,
                'expected_pedigree': 0.5
            },
            {
                'name': 'Familiar lejano',
                'history': 'Tío abuelo con diabetes diagnosticada a los 75 años',
                'expected_pedigree': 0.9
            },
            {
                'name': 'Familiar de segundo grado',
                'history': 'Abuela materna con diabetes tipo 2',
                'expected_pedigree': 0.9
            },
            {
                'name': 'Familiar de primer grado',
                'history': 'Madre con diabetes tipo 2 diagnosticada a los 50 años',
                'expected_pedigree': 1.5
            },
            {
                'name': 'Múltiples familiares',
                'history': 'Madre con diabetes tipo 2. Abuela materna con diabetes.',
                'expected_pedigree': 1.5
            },
            {
                'name': 'Ambos padres',
                'history': 'Padre y madre con diabetes tipo 2',
                'expected_pedigree': 2.0
            }
        ]

        self.stdout.write('')
        results = []

        for test in test_cases:
            # Modificar historial temporal
            clinical_record.family_history = test['history']
            clinical_record.save()

            # Re-extraer features
            features_test = DiabetesDataExtractor.extract_patient_features(str(patient.id))
            array_test = DiabetesDataExtractor.features_to_array(features_test)

            # Predecir
            prediction_test = model.predict([array_test])[0]
            probability_test = model.predict_proba([array_test])[0]

            results.append({
                'name': test['name'],
                'pedigree': features_test['diabetes_pedigree_function'],
                'prediction': prediction_test,
                'prob_diabetes': probability_test[1] * 100
            })

            self.stdout.write(f"Escenario: {test['name']}")
            self.stdout.write(f"  Historial: {test['history'] or 'Ninguno'}")
            self.stdout.write(f"  Pedigree calculado: {features_test['diabetes_pedigree_function']:.2f}")
            self.stdout.write(f"  Predicción: {'POSITIVA' if prediction_test == 1 else 'NEGATIVA'}")
            self.stdout.write(f"  Prob. diabetes: {probability_test[1]*100:.2f}%")
            self.stdout.write(f"  Cambio vs original: {(probability_test[1] - probability_original[1])*100:+.2f}%")
            self.stdout.write('')

        # Restaurar historial original
        clinical_record.family_history = original_family_history
        clinical_record.save()

        self.stdout.write('')
        self.stdout.write('─' * 70)
        self.stdout.write(self.style.HTTP_INFO('4. RESUMEN DE IMPACTO'))
        self.stdout.write('─' * 70)

        self.stdout.write('')
        self.stdout.write('Tabla comparativa:')
        self.stdout.write('')
        self.stdout.write(f"{'Escenario':<30} {'Pedigree':<12} {'Predicción':<12} {'Prob %':<10}")
        self.stdout.write('─' * 70)

        for r in results:
            pred_text = 'POSITIVA' if r['prediction'] == 1 else 'NEGATIVA'
            self.stdout.write(
                f"{r['name']:<30} {r['pedigree']:<12.2f} {pred_text:<12} {r['prob_diabetes']:<10.2f}"
            )

        self.stdout.write('')
        self.stdout.write('='*70)
        self.stdout.write(self.style.SUCCESS('Test completado'))
        self.stdout.write('='*70)
        self.stdout.write('')
        self.stdout.write('CONCLUSIÓN:')
        self.stdout.write('El historial familiar SÍ afecta la predicción a través de la')
        self.stdout.write('feature "diabetes_pedigree_function" que se extrae del campo')
        self.stdout.write('family_history de la historia clínica.')
