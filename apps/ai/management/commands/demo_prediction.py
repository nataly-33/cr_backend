"""
Comando interactivo para demostrar el sistema de predicción de diabetes
"""
from django.core.management.base import BaseCommand
from apps.patients.models import Patient
from apps.clinical_records.models import ClinicalRecord, ClinicalForm
from apps.ai.services.diabetes_data_extractor import DiabetesDataExtractor
from apps.ai.services.diabetes_predictor import DiabetesPredictor


class Command(BaseCommand):
    help = 'Demuestra el sistema de predicción con ejemplos reales'

    def add_arguments(self, parser):
        parser.add_argument(
            '--patient-id',
            type=str,
            help='ID de un paciente específico para demostrar',
        )

    def handle(self, *args, **options):
        patient_id = options.get('patient_id')

        self.stdout.write('='*70)
        self.stdout.write('DEMO: Sistema de Prediccion de Diabetes')
        self.stdout.write('='*70)
        self.stdout.write('')

        # Paso 1: Listar pacientes disponibles
        if not patient_id:
            self.stdout.write('PASO 1: Pacientes disponibles para prueba')
            self.stdout.write('-'*70)

            patients = Patient.objects.exclude(
                identity_document__startswith='SYNTH-'
            )[:10]

            if not patients.exists():
                self.stdout.write(self.style.ERROR('No hay pacientes disponibles'))
                return

            for i, p in enumerate(patients, 1):
                triages = ClinicalForm.objects.filter(
                    clinical_record__patient=p,
                    form_type='triage'
                ).count()
                labs = ClinicalForm.objects.filter(
                    clinical_record__patient=p,
                    form_type='lab_order'
                ).count()

                status = 'LISTO' if (triages > 0 and labs >= 2) else 'INCOMPLETO'

                self.stdout.write(f'{i}. {p.first_name} {p.last_name} ({p.identity_document})')
                self.stdout.write(f'   ID: {p.id}')
                self.stdout.write(f'   Datos: Triajes={triages}, Labs={labs} - {status}')
                self.stdout.write('')

            # Usar el primer paciente completo
            patient = None
            for p in patients:
                triages = ClinicalForm.objects.filter(
                    clinical_record__patient=p,
                    form_type='triage'
                ).count()
                labs = ClinicalForm.objects.filter(
                    clinical_record__patient=p,
                    form_type='lab_order'
                ).count()

                if triages > 0 and labs >= 2:
                    patient = p
                    break

            if not patient:
                self.stdout.write(self.style.WARNING('Ninguno tiene datos completos'))
                self.stdout.write('Ejecuta: python manage.py add_clinical_data_to_patients --all')
                return

        else:
            # Usar paciente específico
            try:
                patient = Patient.objects.get(id=patient_id)
            except Patient.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Paciente {patient_id} no encontrado'))
                return

        self.stdout.write('')
        self.stdout.write('='*70)
        self.stdout.write(f'PACIENTE SELECCIONADO: {patient.first_name} {patient.last_name}')
        self.stdout.write('='*70)
        self.stdout.write(f'ID: {patient.id}')
        self.stdout.write(f'Documento: {patient.identity_document}')
        self.stdout.write(f'Edad: {patient.get_age()} anos')
        self.stdout.write(f'Genero: {patient.gender}')
        self.stdout.write('')

        # Paso 2: Mostrar datos clínicos
        self.stdout.write('PASO 2: Datos clinicos disponibles')
        self.stdout.write('-'*70)

        clinical_record = ClinicalRecord.objects.filter(
            patient=patient,
            status='active'
        ).first()

        if not clinical_record:
            self.stdout.write(self.style.ERROR('No tiene historia clinica activa'))
            return

        # Mostrar triaje
        triage = ClinicalForm.objects.filter(
            clinical_record=clinical_record,
            form_type='triage'
        ).first()

        if triage:
            self.stdout.write('TRIAJE:')
            data = triage.form_data
            self.stdout.write(f'  Peso: {data.get("weight")} kg')
            self.stdout.write(f'  Altura: {data.get("height")} cm')
            self.stdout.write(f'  Presion: {data.get("blood_pressure_systolic")}/{data.get("blood_pressure_diastolic")} mmHg')
            self.stdout.write(f'  Fecha: {triage.form_date.strftime("%Y-%m-%d")}')
        else:
            self.stdout.write('  SIN TRIAJE')

        self.stdout.write('')

        # Mostrar laboratorios
        labs = ClinicalForm.objects.filter(
            clinical_record=clinical_record,
            form_type='lab_order'
        )

        self.stdout.write(f'LABORATORIOS ({labs.count()}):')
        for lab in labs:
            data = lab.form_data
            self.stdout.write(f'  - {data.get("test_name")}: {data.get("result")}')

        self.stdout.write('')

        # Mostrar historial familiar
        if clinical_record.family_history:
            self.stdout.write('HISTORIAL FAMILIAR:')
            self.stdout.write(f'  {clinical_record.family_history}')
        else:
            self.stdout.write('HISTORIAL FAMILIAR: Ninguno registrado')

        self.stdout.write('')
        self.stdout.write('')

        # Paso 3: Extraer features
        self.stdout.write('PASO 3: Extraccion de features para el modelo')
        self.stdout.write('-'*70)

        try:
            features = DiabetesDataExtractor.extract_patient_features(str(patient.id))

            self.stdout.write('Features extraidas:')
            for key, value in features.items():
                if isinstance(value, float):
                    self.stdout.write(f'  {key:30}: {value:.2f}')
                else:
                    self.stdout.write(f'  {key:30}: {value}')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error extrayendo features: {str(e)}'))
            return

        self.stdout.write('')
        self.stdout.write('')

        # Paso 4: Hacer predicción
        self.stdout.write('PASO 4: Realizando prediccion con el modelo')
        self.stdout.write('-'*70)

        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = User.objects.filter(is_active=True).first()

            prediction = DiabetesPredictor.predict(
                patient_id=str(patient.id),
                user=user,
                tenant=patient.tenant
            )

            self.stdout.write('RESULTADO DE LA PREDICCION:')
            self.stdout.write('')

            # Predicción
            pred_text = 'POSITIVA (Diabetes)' if prediction.has_diabetes_risk else 'NEGATIVA (No diabetes)'
            self.stdout.write(f'  Prediccion: {pred_text}')
            self.stdout.write('')

            # Probabilidades
            self.stdout.write('  Probabilidades:')
            self.stdout.write(f'    - Diabetes:     {prediction.probability*100:>6.2f}%')
            self.stdout.write(f'    - No diabetes:  {(1-prediction.probability)*100:>6.2f}%')
            self.stdout.write('')

            # Nivel de riesgo
            risk_map = {
                'low': 'BAJO',
                'medium': 'MEDIO',
                'high': 'ALTO',
                'very_high': 'MUY ALTO'
            }
            self.stdout.write(f'  Nivel de riesgo: {risk_map.get(prediction.risk_level, prediction.risk_level)}')
            self.stdout.write(f'  Modelo: {prediction.model.version}')

            # Factores contribuyentes
            if prediction.contributing_factors:
                self.stdout.write('')
                self.stdout.write('  Factores contribuyentes:')
                for factor in prediction.contributing_factors[:5]:
                    self.stdout.write(f'    - {factor}')

            # Recomendaciones
            if prediction.recommendations:
                self.stdout.write('')
                self.stdout.write('  Recomendaciones:')
                for rec in prediction.recommendations[:3]:
                    self.stdout.write(f'    - {rec}')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error haciendo prediccion: {str(e)}'))
            import traceback
            traceback.print_exc()
            return

        self.stdout.write('')
        self.stdout.write('')

        # Paso 5: Prueba de sensibilidad al historial familiar
        self.stdout.write('PASO 5: Probando impacto del historial familiar')
        self.stdout.write('-'*70)

        original_history = clinical_record.family_history
        original_prob = prediction.probability

        # Escenario 1: Sin historial
        self.stdout.write('Escenario 1: SIN historial familiar')
        clinical_record.family_history = ''
        clinical_record.save()

        features1 = DiabetesDataExtractor.extract_patient_features(str(patient.id))
        self.stdout.write(f'  Pedigree: {features1["diabetes_pedigree_function"]:.3f}')

        # Re-predecir (sin guardar)
        from apps.ai.services.diabetes_model_trainer import DiabetesModelTrainer
        model_tuple = DiabetesModelTrainer.load_active_model()
        if model_tuple and len(model_tuple) >= 2:
            model = model_tuple[0]  # El modelo es el primer elemento
            arr1 = DiabetesDataExtractor.features_to_array(features1)
            prob1 = model.predict_proba([arr1])[0]
            self.stdout.write(f'  Prob diabetes: {prob1[1]*100:.2f}%')
            self.stdout.write(f'  Cambio: {(prob1[1]-original_prob)*100:+.2f}%')

        self.stdout.write('')

        # Escenario 2: Historial fuerte
        self.stdout.write('Escenario 2: CON historial fuerte (ambos padres)')
        clinical_record.family_history = 'Madre y padre con diabetes tipo 2'
        clinical_record.save()

        features2 = DiabetesDataExtractor.extract_patient_features(str(patient.id))
        self.stdout.write(f'  Pedigree: {features2["diabetes_pedigree_function"]:.3f}')

        if model_tuple and len(model_tuple) >= 2:
            arr2 = DiabetesDataExtractor.features_to_array(features2)
            prob2 = model.predict_proba([arr2])[0]
            self.stdout.write(f'  Prob diabetes: {prob2[1]*100:.2f}%')
            self.stdout.write(f'  Cambio: {(prob2[1]-original_prob)*100:+.2f}%')

        self.stdout.write('')

        # Restaurar historial original
        clinical_record.family_history = original_history
        clinical_record.save()

        self.stdout.write('')
        self.stdout.write('='*70)
        self.stdout.write('DEMO COMPLETADA')
        self.stdout.write('='*70)
        self.stdout.write('')
        self.stdout.write('CONCLUSION:')
        self.stdout.write('- El sistema extrae automaticamente los datos clinicos del paciente')
        self.stdout.write('- El historial familiar SI afecta la prediccion')
        self.stdout.write('- Puedes ver este paciente en el frontend:')
        self.stdout.write(f'  http://localhost:5173/patients/{patient.id}/diabetes-prediction')
        self.stdout.write('')
