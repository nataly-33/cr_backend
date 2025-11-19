"""
Management command para agregar datos clínicos a pacientes existentes
sin formularios de triaje o laboratorio completos
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import random

from apps.patients.models import Patient
from apps.clinical_records.models import ClinicalRecord, ClinicalForm
from apps.accounts.models import User


class Command(BaseCommand):
    help = 'Agrega datos clínicos (triaje, labs) a pacientes existentes que no los tienen'

    def add_arguments(self, parser):
        parser.add_argument(
            '--patient-id',
            type=str,
            help='ID de un paciente específico (opcional)',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Procesar todos los pacientes sin datos completos',
        )
        parser.add_argument(
            '--tenant-id',
            type=str,
            help='ID del tenant (si no se especifica, usa el primero disponible)',
        )

    def handle(self, *args, **options):
        patient_id = options.get('patient_id')
        process_all = options.get('all')
        tenant_id = options.get('tenant_id')

        self.stdout.write('='*60)
        self.stdout.write(self.style.SUCCESS('Agregar Datos Clínicos a Pacientes'))
        self.stdout.write('='*60)
        self.stdout.write('')

        # Obtener pacientes a procesar
        if patient_id:
            patients = Patient.objects.filter(id=patient_id)
            if not patients.exists():
                self.stdout.write(self.style.ERROR(f'Paciente {patient_id} no encontrado'))
                return
        elif process_all:
            # Filtrar por tenant si se especificó
            if tenant_id:
                patients = Patient.objects.filter(tenant_id=tenant_id)
            else:
                patients = Patient.objects.all()

            # Excluir pacientes sintéticos
            patients = patients.exclude(identity_document__startswith='SYNTH-')

            self.stdout.write(f'Pacientes encontrados: {patients.count()}')
        else:
            self.stdout.write(self.style.ERROR('Debes especificar --patient-id o --all'))
            return

        # Obtener usuario del sistema
        first_patient = patients.first()
        system_user = User.objects.filter(
            tenant=first_patient.tenant,
            is_active=True
        ).first()

        if not system_user:
            self.stdout.write(self.style.ERROR('No hay usuarios activos en el tenant'))
            return

        self.stdout.write(f'Usuario sistema: {system_user.email}')
        self.stdout.write('')

        processed = 0
        skipped = 0
        errors = 0

        for patient in patients:
            try:
                # Verificar si ya tiene datos completos
                clinical_record = ClinicalRecord.objects.filter(
                    patient=patient,
                    status='active'
                ).first()

                if not clinical_record:
                    # Crear historia clínica si no existe
                    clinical_record = ClinicalRecord.objects.create(
                        patient=patient,
                        tenant=patient.tenant,
                        record_number=f'HC-{patient.identity_document}',
                        status='active'
                    )
                    self.stdout.write(f'  Historia clínica creada para {patient.identity_document}')

                # Verificar qué le falta
                has_triage = ClinicalForm.objects.filter(
                    clinical_record=clinical_record,
                    form_type='triage'
                ).exists()

                has_glucose = ClinicalForm.objects.filter(
                    clinical_record=clinical_record,
                    form_type='lab_order',
                    form_data__test_name__icontains='glucosa'
                ).exists()

                has_insulin = ClinicalForm.objects.filter(
                    clinical_record=clinical_record,
                    form_type='lab_order',
                    form_data__test_name__icontains='insulina'
                ).exists()

                needs_data = not (has_triage and has_glucose and has_insulin)

                if not needs_data:
                    skipped += 1
                    continue

                # Generar datos clínicos realistas
                age = patient.get_age()
                gender = patient.gender

                # Perfil aleatorio con tendencia saludable
                if random.random() < 0.2:  # 20% con riesgo
                    profile = self._generate_risk_profile(age, gender)
                else:  # 80% saludable
                    profile = self._generate_healthy_profile(age, gender)

                # Crear triaje si no existe
                if not has_triage:
                    self._create_triage(clinical_record, profile, system_user)

                # Crear orden de glucosa si no existe
                if not has_glucose:
                    self._create_glucose_order(clinical_record, profile, system_user)

                # Crear orden de insulina si no existe
                if not has_insulin:
                    self._create_insulin_order(clinical_record, profile, system_user)

                # Agregar historial familiar a algunos pacientes
                if not clinical_record.family_history and random.random() < 0.3:
                    clinical_record.family_history = self._generate_family_history()
                    clinical_record.save()

                processed += 1
                self.stdout.write(self.style.SUCCESS(
                    f'OK {patient.first_name} {patient.last_name} ({patient.identity_document})'
                ))

            except Exception as e:
                errors += 1
                self.stdout.write(self.style.ERROR(
                    f'ERROR con {patient.identity_document}: {str(e)}'
                ))

        self.stdout.write('')
        self.stdout.write('='*60)
        self.stdout.write(self.style.SUCCESS('Proceso completado'))
        self.stdout.write('='*60)
        self.stdout.write(f'Procesados: {processed}')
        self.stdout.write(f'Omitidos (ya tenían datos): {skipped}')
        self.stdout.write(f'Errores: {errors}')

    def _generate_healthy_profile(self, age, gender):
        """Genera perfil saludable"""
        return {
            'weight': random.gauss(70, 12),
            'height': random.gauss(170, 10),
            'blood_pressure_systolic': random.gauss(120, 10),
            'blood_pressure_diastolic': random.gauss(75, 8),
            'glucose': random.gauss(95, 8),
            'insulin': random.gauss(85, 25),
        }

    def _generate_risk_profile(self, age, gender):
        """Genera perfil con factores de riesgo"""
        return {
            'weight': random.gauss(85, 15),
            'height': random.gauss(165, 10),
            'blood_pressure_systolic': random.gauss(135, 12),
            'blood_pressure_diastolic': random.gauss(85, 10),
            'glucose': random.gauss(125, 20),
            'insulin': random.gauss(140, 40),
        }

    def _create_triage(self, clinical_record, profile, system_user):
        """Crea formulario de triaje"""
        triage_data = {
            'weight': round(max(40, profile['weight']), 1),
            'height': round(max(140, min(200, profile['height'])), 1),
            'blood_pressure_systolic': round(profile['blood_pressure_systolic']),
            'blood_pressure_diastolic': round(profile['blood_pressure_diastolic']),
            'heart_rate': random.randint(60, 100),
            'temperature': round(random.gauss(36.5, 0.3), 1),
            'chief_complaint': 'Consulta general',
            'vital_signs_notes': 'Signos vitales registrados'
        }

        ClinicalForm.objects.create(
            clinical_record=clinical_record,
            tenant=clinical_record.tenant,
            form_type='triage',
            form_data=triage_data,
            form_date=timezone.now(),
            filled_by=system_user
        )

    def _create_glucose_order(self, clinical_record, profile, system_user):
        """Crea orden de glucosa"""
        glucose_value = max(70, min(300, profile['glucose']))

        glucose_data = {
            'test_name': 'Glucosa en ayunas',
            'test_type': 'chemistry',
            'result': f"{round(glucose_value, 1)} mg/dL",
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

    def _create_insulin_order(self, clinical_record, profile, system_user):
        """Crea orden de insulina"""
        insulin_value = max(0, profile['insulin'])

        insulin_data = {
            'test_name': 'Insulina sérica',
            'test_type': 'chemistry',
            'result': f"{round(insulin_value, 1)} µU/mL",
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

    def _generate_family_history(self):
        """Genera historial familiar aleatorio"""
        templates = [
            "Sin antecedentes familiares de diabetes",
            "Tío paterno con diabetes tipo 2",
            "Abuela materna con diabetes diagnosticada a los 65 años",
            "Madre con diabetes tipo 2 diagnosticada a los 55 años",
            "Padre con diabetes tipo 2",
            "Hermano con prediabetes",
        ]
        return random.choice(templates)
