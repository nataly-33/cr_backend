"""
Management command para extraer datos de pacientes sintéticos y crear un dataset
para reentrenar el modelo
"""
from django.core.management.base import BaseCommand
from apps.patients.models import Patient
from apps.ai.services.diabetes_data_extractor import DiabetesDataExtractor
from apps.ai.models import DiabetesDataset
import json


class Command(BaseCommand):
    help = 'Extrae features de pacientes sintéticos y crea un dataset para entrenamiento'

    def handle(self, *args, **options):
        self.stdout.write('='*60)
        self.stdout.write(self.style.SUCCESS('Extracción de Dataset Sintético'))
        self.stdout.write('='*60)
        self.stdout.write('')

        # Obtener todos los pacientes sintéticos
        patients = Patient.objects.filter(identity_document__startswith='SYNTH-')

        if not patients.exists():
            self.stdout.write(self.style.ERROR('No hay pacientes sintéticos'))
            return

        self.stdout.write(f'Pacientes sintéticos encontrados: {patients.count()}')
        self.stdout.write('')

        # Extraer features de cada paciente
        extracted_count = 0
        error_count = 0

        for patient in patients:
            try:
                # Extraer features
                features = DiabetesDataExtractor.extract_patient_features(str(patient.id))

                # Convertir a array
                features_array = DiabetesDataExtractor.features_to_array(features)

                # Determinar outcome basado en características
                # Si glucosa > 126 o IMC > 30 y antecedentes familiares
                has_diabetes = (
                    features['glucose'] > 126 or
                    (features['bmi'] > 30 and features['diabetes_pedigree_function'] > 0.7)
                )
                outcome = 1 if has_diabetes else 0

                # Guardar en dataset
                DiabetesDataset.objects.create(
                    pregnancies=features['pregnancies'],
                    glucose=features['glucose'],
                    blood_pressure=features['blood_pressure'],
                    skin_thickness=features['skin_thickness'],
                    insulin=features['insulin'],
                    bmi=features['bmi'],
                    diabetes_pedigree_function=features['diabetes_pedigree_function'],
                    age=features['age'],
                    outcome=outcome,
                    source='synthetic',
                    patient_id=patient.id
                )

                extracted_count += 1

                if extracted_count % 10 == 0:
                    self.stdout.write(f'  Procesados {extracted_count} pacientes...')

            except Exception as e:
                self.stdout.write(self.style.WARNING(
                    f'Error con paciente {patient.identity_document}: {str(e)}'
                ))
                error_count += 1

        self.stdout.write('')
        self.stdout.write('='*60)
        self.stdout.write(self.style.SUCCESS('Extracción completada'))
        self.stdout.write('='*60)
        self.stdout.write(f'Total extraídos: {extracted_count}')
        self.stdout.write(f'Errores: {error_count}')

        # Estadísticas del dataset
        total_synthetic = DiabetesDataset.objects.filter(source='synthetic').count()
        with_diabetes = DiabetesDataset.objects.filter(source='synthetic', outcome=1).count()

        self.stdout.write('')
        self.stdout.write('Estadísticas del dataset sintético:')
        self.stdout.write(f'  Total registros: {total_synthetic}')
        self.stdout.write(f'  Con diabetes: {with_diabetes} ({with_diabetes/total_synthetic*100:.1f}%)')
        self.stdout.write(f'  Sin diabetes: {total_synthetic - with_diabetes}')
