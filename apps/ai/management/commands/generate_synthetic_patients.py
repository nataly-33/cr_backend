"""
Management command para generar pacientes sintéticos con datos clínicos completos
para entrenar el modelo de predicción de diabetes
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import random
from decimal import Decimal

from apps.patients.models import Patient
from apps.clinical_records.models import ClinicalRecord, ClinicalForm
from apps.core.models import Tenant
from apps.accounts.models import User


class Command(BaseCommand):
    help = 'Genera pacientes sintéticos con datos clínicos completos para entrenamiento del modelo'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=100,
            help='Número de pacientes a generar (default: 100)',
        )
        parser.add_argument(
            '--with-diabetes',
            type=float,
            default=0.30,
            help='Proporción de pacientes con diabetes (default: 0.30 = 30%%)',
        )
        parser.add_argument(
            '--tenant-id',
            type=str,
            help='ID del tenant (si no se especifica, usa el primero disponible)',
        )
        parser.add_argument(
            '--clean',
            action='store_true',
            help='Eliminar pacientes sintéticos existentes antes de generar nuevos',
        )

    def handle(self, *args, **options):
        count = options['count']
        diabetes_ratio = options['with_diabetes']
        tenant_id = options['tenant_id']
        clean = options['clean']

        self.stdout.write('='*60)
        self.stdout.write(self.style.SUCCESS('Generación de Pacientes Sintéticos'))
        self.stdout.write('='*60)
        self.stdout.write('')

        # Obtener tenant
        if tenant_id:
            tenant = Tenant.objects.get(id=tenant_id)
        else:
            tenant = Tenant.objects.first()
            if not tenant:
                self.stdout.write(self.style.ERROR('No hay tenants disponibles'))
                return

        # Limpiar pacientes sintéticos existentes si se solicita
        if clean:
            deleted_patients = Patient.objects.filter(
                tenant=tenant,
                identity_document__startswith='SYNTH-'
            ).delete()
            self.stdout.write(self.style.WARNING(f'Eliminados {deleted_patients[0]} pacientes sintéticos existentes'))
            self.stdout.write('')

        # Obtener un usuario del sistema para filled_by
        system_user = User.objects.filter(tenant=tenant, is_active=True).first()
        if not system_user:
            self.stdout.write(self.style.ERROR('No hay usuarios activos en el tenant'))
            return

        self.stdout.write(f'Tenant: {tenant.name}')
        self.stdout.write(f'Usuario sistema: {system_user.email}')
        self.stdout.write(f'Pacientes a generar: {count}')
        self.stdout.write(f'Con diabetes: {int(count * diabetes_ratio)} ({diabetes_ratio*100:.0f}%)')
        self.stdout.write('')

        generated_count = 0
        diabetes_count = 0

        for i in range(count):
            try:
                # Decidir si tendrá diabetes
                has_diabetes = random.random() < diabetes_ratio

                # Generar paciente
                patient, has_diabetes_actual = self._generate_patient(tenant, system_user, has_diabetes, i)
                generated_count += 1
                if has_diabetes_actual:
                    diabetes_count += 1

                if (i + 1) % 20 == 0:
                    self.stdout.write(f'  Generados {i + 1} pacientes...')

            except Exception as e:
                self.stdout.write(self.style.WARNING(f'Error generando paciente {i+1}: {str(e)}'))
                continue

        self.stdout.write('')
        self.stdout.write('='*60)
        self.stdout.write(self.style.SUCCESS('Generación completada'))
        self.stdout.write('='*60)
        self.stdout.write(f'Total generados: {generated_count}')
        if generated_count > 0:
            self.stdout.write(f'Con diabetes: {diabetes_count} ({diabetes_count/generated_count*100:.1f}%)')
            self.stdout.write(f'Sin diabetes: {generated_count - diabetes_count}')
        else:
            self.stdout.write('No se generó ningún paciente')

    def _generate_patient(self, tenant, system_user, should_have_diabetes, index):
        """
        Genera un paciente sintético con datos clínicos

        Returns:
            tuple: (patient, has_diabetes)
        """
        # Género aleatorio
        gender = random.choice(['M', 'F'])

        # Edad: distribución realista (más casos en 40-70 años)
        age = int(random.gauss(55, 15))
        age = max(18, min(90, age))  # entre 18 y 90 años

        # Fecha de nacimiento
        today = timezone.now().date()
        date_of_birth = today - timedelta(days=age*365)

        # Crear paciente
        patient = Patient.objects.create(
            tenant=tenant,
            identity_document=f'SYNTH-{index:05d}',
            first_name=f'Paciente',
            last_name=f'Sintético {index:03d}',
            date_of_birth=date_of_birth,
            gender=gender,
            phone=f'555-{random.randint(1000, 9999)}',
            email=f'paciente{index}@synthetic.test'
        )

        # Crear historia clínica
        clinical_record = ClinicalRecord.objects.create(
            patient=patient,
            tenant=tenant,
            record_number=f'HC-SYNTH-{index:05d}',
            status='active'
        )

        # Generar datos según perfil de diabetes
        if should_have_diabetes:
            features = self._generate_diabetic_profile(age, gender)
        else:
            features = self._generate_healthy_profile(age, gender)

        # Crear formulario de triaje
        self._create_triage(clinical_record, features, system_user)

        # Crear órdenes de laboratorio
        self._create_lab_orders(clinical_record, features, system_user)

        # Agregar historial familiar si es relevante
        if features.get('diabetes_pedigree_function', 0) > 0.5:
            clinical_record.family_history = self._generate_family_history(
                features['diabetes_pedigree_function']
            )
            clinical_record.save()

        return patient, should_have_diabetes

    def _generate_diabetic_profile(self, age, gender):
        """Genera perfil típico de paciente con riesgo de diabetes"""
        features = {}

        # IMC elevado (obesidad es factor de riesgo)
        weight_kg = random.gauss(85, 15)  # Peso elevado
        height_cm = random.gauss(165, 10)
        features['weight'] = max(50, weight_kg)
        features['height'] = max(140, min(200, height_cm))

        # Glucosa elevada
        features['glucose'] = random.gauss(140, 20)  # Por encima de 126 mg/dL
        features['glucose'] = max(100, min(300, features['glucose']))

        # Presión arterial elevada
        features['blood_pressure_systolic'] = random.gauss(140, 15)
        features['blood_pressure_diastolic'] = random.gauss(90, 10)

        # Insulina (si está alta indica resistencia)
        features['insulin'] = random.gauss(150, 50)
        features['insulin'] = max(0, features['insulin'])

        # Grosor de piel
        features['skin_thickness'] = random.gauss(30, 5)

        # Embarazos (si es mujer)
        if gender == 'F':
            features['pregnancies'] = random.randint(0, 5)

        # Historial familiar fuerte
        features['diabetes_pedigree_function'] = random.gauss(0.7, 0.2)
        features['diabetes_pedigree_function'] = max(0.2, min(2.5, features['diabetes_pedigree_function']))

        return features

    def _generate_healthy_profile(self, age, gender):
        """Genera perfil típico de paciente saludable"""
        features = {}

        # IMC normal
        weight_kg = random.gauss(70, 10)
        height_cm = random.gauss(170, 10)
        features['weight'] = max(50, weight_kg)
        features['height'] = max(140, min(200, height_cm))

        # Glucosa normal
        features['glucose'] = random.gauss(95, 10)  # Por debajo de 100 mg/dL
        features['glucose'] = max(70, min(125, features['glucose']))

        # Presión arterial normal
        features['blood_pressure_systolic'] = random.gauss(120, 10)
        features['blood_pressure_diastolic'] = random.gauss(75, 5)

        # Insulina normal
        features['insulin'] = random.gauss(80, 30)
        features['insulin'] = max(0, features['insulin'])

        # Grosor de piel normal
        features['skin_thickness'] = random.gauss(20, 5)

        # Embarazos (si es mujer)
        if gender == 'F':
            features['pregnancies'] = random.randint(0, 3)

        # Historial familiar débil o nulo
        features['diabetes_pedigree_function'] = random.gauss(0.3, 0.15)
        features['diabetes_pedigree_function'] = max(0.0, min(1.0, features['diabetes_pedigree_function']))

        return features

    def _create_triage(self, clinical_record, features, system_user):
        """Crea formulario de triaje con signos vitales"""
        triage_data = {
            'weight': round(features['weight'], 1),
            'height': round(features['height'], 1),
            'blood_pressure_systolic': round(features['blood_pressure_systolic']),
            'blood_pressure_diastolic': round(features['blood_pressure_diastolic']),
            'heart_rate': random.randint(60, 100),
            'temperature': round(random.gauss(36.5, 0.3), 1),
            'chief_complaint': 'Control de salud',
            'vital_signs_notes': 'Signos vitales estables'
        }

        ClinicalForm.objects.create(
            clinical_record=clinical_record,
            tenant=clinical_record.tenant,
            form_type='triage',
            form_data=triage_data,
            form_date=timezone.now(),
            filled_by=system_user
        )

    def _create_lab_orders(self, clinical_record, features, system_user):
        """Crea órdenes de laboratorio"""
        # Orden de glucosa
        glucose_data = {
            'test_name': 'Glucosa en ayunas',
            'test_type': 'chemistry',
            'result': f"{round(features['glucose'], 1)} mg/dL",
            'reference_range': '70-100 mg/dL',
            'notes': 'Ayuno de 8 horas'
        }

        ClinicalForm.objects.create(
            clinical_record=clinical_record,
            tenant=clinical_record.tenant,
            form_type='lab_order',
            form_data=glucose_data,
            form_date=timezone.now(),
            filled_by=system_user
        )

        # Orden de insulina
        insulin_data = {
            'test_name': 'Insulina sérica',
            'test_type': 'chemistry',
            'result': f"{round(features['insulin'], 1)} µU/mL",
            'reference_range': '2.6-24.9 µU/mL',
            'notes': ''
        }

        ClinicalForm.objects.create(
            clinical_record=clinical_record,
            tenant=clinical_record.tenant,
            form_type='lab_order',
            form_data=insulin_data,
            form_date=timezone.now(),
            filled_by=system_user
        )

    def _generate_family_history(self, pedigree_score):
        """Genera texto de historial familiar basado en score"""
        if pedigree_score > 0.8:
            templates = [
                "Madre con diabetes tipo 2. Abuela materna con diabetes.",
                "Padre y tío paterno con diabetes tipo 2.",
                "Ambos padres con diabetes. Hermano diagnosticado a los 45 años.",
            ]
        elif pedigree_score > 0.5:
            templates = [
                "Madre con diabetes tipo 2 diagnosticada a los 50 años.",
                "Padre con diabetes tipo 2.",
                "Abuela materna con diabetes.",
            ]
        else:
            templates = [
                "Tío abuelo con diabetes.",
                "Abuela paterna con diabetes diagnosticada a los 70 años.",
                "Sin antecedentes familiares directos de diabetes.",
            ]

        return random.choice(templates)
