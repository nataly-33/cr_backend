"""
Seeder para crear formularios clínicos de ejemplo
Incluye: Triaje, Consultas, Notas de evolución, Recetas, etc.
"""
import os
import sys
import django
from pathlib import Path

# Setup Django
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

import random
from datetime import datetime, timedelta
from django.utils import timezone
from faker import Faker

from apps.core.models import Tenant, set_current_tenant
from apps.clinical_records.models import ClinicalRecord, ClinicalForm
from apps.accounts.models import User

fake = Faker('es_ES')
Faker.seed(42)
random.seed(42)


def create_triage_form(clinical_record, doctor):
    """Crear formulario de triaje"""
    form_data = {
        # Signos vitales
        'vital_signs': {
            'temperature': round(random.uniform(36.0, 37.5), 1),
            'blood_pressure_systolic': random.randint(100, 140),
            'blood_pressure_diastolic': random.randint(60, 90),
            'heart_rate': random.randint(60, 100),
            'respiratory_rate': random.randint(12, 20),
            'oxygen_saturation': random.randint(95, 100),
            'weight': round(random.uniform(50, 90), 1),
            'height': round(random.uniform(150, 180), 0),
        },
        # Motivo de consulta
        'chief_complaint': random.choice([
            'Dolor de cabeza',
            'Fiebre',
            'Dolor abdominal',
            'Tos y dolor de garganta',
            'Dolor en el pecho',
            'Mareos',
            'Control de rutina',
        ]),
        # Evaluación inicial
        'initial_assessment': random.choice([
            'Paciente alerta y orientado, signos vitales estables',
            'Paciente con dolor moderado, hemodinámicamente estable',
            'Paciente con fiebre, en observación',
            'Paciente estable, consulta de control',
        ]),
        # Nivel de urgencia
        'triage_level': random.choice([
            {'level': 1, 'name': 'Resucitación', 'color': 'red'},
            {'level': 2, 'name': 'Emergencia', 'color': 'orange'},
            {'level': 3, 'name': 'Urgente', 'color': 'yellow'},
            {'level': 4, 'name': 'Semi-urgente', 'color': 'green'},
            {'level': 5, 'name': 'No urgente', 'color': 'blue'},
        ]),
    }

    return ClinicalForm.objects.create(
        tenant=clinical_record.tenant,
        clinical_record=clinical_record,
        form_type='triage',
        form_data=form_data,
        filled_by=doctor,
        form_date=timezone.now() - timedelta(days=random.randint(0, 30))
    )


def create_consultation_form(clinical_record, doctor):
    """Crear formulario de consulta médica"""
    form_data = {
        'subjective': {
            'chief_complaint': random.choice([
                'Dolor abdominal de 2 días de evolución',
                'Fiebre y malestar general desde hace 3 días',
                'Cefalea intensa y náuseas',
                'Tos productiva con expectoración amarillenta',
            ]),
            'history_present_illness': fake.text(max_nb_chars=200),
            'review_of_systems': {
                'constitutional': random.choice(['Normal', 'Fiebre', 'Pérdida de peso']),
                'cardiovascular': random.choice(['Normal', 'Palpitaciones', 'Dolor torácico']),
                'respiratory': random.choice(['Normal', 'Tos', 'Disnea']),
                'gastrointestinal': random.choice(['Normal', 'Náuseas', 'Vómito']),
            }
        },
        'objective': {
            'physical_exam': {
                'general': 'Paciente alerta, orientado, cooperador',
                'head_eyes_ears_nose_throat': random.choice(['Normal', 'Faringe eritematosa']),
                'cardiovascular': 'Ruidos cardíacos rítmicos, sin soplos',
                'respiratory': random.choice(['Murmullo vesicular normal', 'Estertores crepitantes']),
                'abdomen': random.choice(['Suave, depresible, no doloroso', 'Doloroso a la palpación']),
                'extremities': 'Sin edema, pulsos presentes',
            }
        },
        'assessment': {
            'diagnoses': [
                {
                    'code': f'J{random.randint(10, 99)}.{random.randint(0, 9)}',
                    'description': random.choice([
                        'Infección respiratoria aguda',
                        'Gastroenteritis aguda',
                        'Cefalea tensional',
                        'Hipertensión arterial',
                        'Diabetes mellitus tipo 2',
                    ]),
                    'type': random.choice(['principal', 'secundario']),
                }
            ],
            'differential_diagnosis': fake.text(max_nb_chars=100),
        },
        'plan': {
            'medications': [
                {
                    'name': random.choice(['Paracetamol', 'Ibuprofeno', 'Amoxicilina', 'Omeprazol']),
                    'dose': random.choice(['500mg', '1g', '250mg', '20mg']),
                    'frequency': random.choice(['cada 8 horas', 'cada 12 horas', 'cada 24 horas']),
                    'duration': f'{random.randint(3, 10)} días',
                }
            ],
            'lab_orders': random.choice([
                ['Hemograma completo', 'Glucemia'],
                ['Perfil lipídico', 'Creatinina'],
                [],
            ]),
            'follow_up': random.choice([
                'Control en 7 días',
                'Control en 15 días',
                'Control en 1 mes',
                'SOS si persisten síntomas',
            ]),
        }
    }

    return ClinicalForm.objects.create(
        tenant=clinical_record.tenant,
        clinical_record=clinical_record,
        form_type='consultation',
        form_data=form_data,
        filled_by=doctor,
        form_date=timezone.now() - timedelta(days=random.randint(0, 30))
    )


def create_prescription_form(clinical_record, doctor):
    """Crear receta médica"""
    medications = [
        {'name': 'Amoxicilina', 'dose': '500mg', 'frequency': 'cada 8 horas'},
        {'name': 'Ibuprofeno', 'dose': '400mg', 'frequency': 'cada 8 horas'},
        {'name': 'Paracetamol', 'dose': '1g', 'frequency': 'cada 8 horas'},
        {'name': 'Omeprazol', 'dose': '20mg', 'frequency': 'cada 24 horas'},
        {'name': 'Loratadina', 'dose': '10mg', 'frequency': 'cada 24 horas'},
    ]

    selected_meds = random.sample(medications, random.randint(1, 3))

    form_data = {
        'medications': [
            {
                **med,
                'duration': f'{random.randint(3, 14)} días',
                'instructions': random.choice([
                    'Tomar con alimentos',
                    'Tomar en ayunas',
                    'Tomar antes de dormir',
                    'Tomar después de las comidas',
                ]),
                'quantity': random.randint(10, 30),
            }
            for med in selected_meds
        ],
        'diagnosis': random.choice([
            'Infección respiratoria aguda',
            'Gastritis aguda',
            'Cefalea tensional',
            'Faringitis aguda',
        ]),
        'notes': 'Acudir a emergencias si presenta: fiebre alta, dificultad respiratoria o dolor intenso.',
    }

    return ClinicalForm.objects.create(
        tenant=clinical_record.tenant,
        clinical_record=clinical_record,
        form_type='prescription',
        form_data=form_data,
        filled_by=doctor,
        form_date=timezone.now() - timedelta(days=random.randint(0, 30))
    )


def create_lab_order_form(clinical_record, doctor):
    """Crear orden de laboratorio"""
    lab_tests = [
        'Hemograma completo',
        'Glucemia en ayunas',
        'Perfil lipídico',
        'Creatinina',
        'Ácido úrico',
        'Transaminasas (TGO, TGP)',
        'Orina completa',
        'Coprocultivo',
        'TSH',
        'T4 libre',
    ]

    form_data = {
        'tests': random.sample(lab_tests, random.randint(2, 5)),
        'diagnosis': random.choice([
            'Control de rutina',
            'Hipertensión arterial',
            'Diabetes mellitus',
            'Sospecha de infección',
        ]),
        'urgency': random.choice(['routine', 'urgent', 'stat']),
        'fasting_required': random.choice([True, False]),
        'notes': fake.text(max_nb_chars=100),
    }

    return ClinicalForm.objects.create(
        tenant=clinical_record.tenant,
        clinical_record=clinical_record,
        form_type='lab_order',
        form_data=form_data,
        filled_by=doctor,
        form_date=timezone.now() - timedelta(days=random.randint(0, 30))
    )


def seed_forms_for_tenant(tenant):
    """Crear formularios clínicos para un tenant"""
    print(f"\n🏥 Creando formularios clínicos para {tenant.name}...")

    set_current_tenant(tenant)

    # Obtener doctores y registros clínicos
    doctors = User.objects.filter(
        tenant=tenant,
        role__name__in=['Doctor', 'Administrador']
    )

    if not doctors.exists():
        print("  ⚠️  No hay doctores disponibles")
        return

    clinical_records = ClinicalRecord.objects.filter(tenant=tenant)

    if not clinical_records.exists():
        print("  ⚠️  No hay historias clínicas disponibles")
        return

    forms_created = 0

    # Crear formularios para cada historia clínica
    for record in clinical_records[:10]:  # Limitamos a 10 para no saturar
        doctor = random.choice(doctors)

        # Crear diferentes tipos de formularios
        try:
            # Triaje (1 por historia)
            create_triage_form(record, doctor)
            forms_created += 1

            # Consulta médica (1-2 por historia)
            for _ in range(random.randint(1, 2)):
                create_consultation_form(record, doctor)
                forms_created += 1

            # Receta médica (0-1 por historia)
            if random.random() > 0.3:
                create_prescription_form(record, doctor)
                forms_created += 1

            # Orden de laboratorio (0-1 por historia)
            if random.random() > 0.5:
                create_lab_order_form(record, doctor)
                forms_created += 1

        except Exception as e:
            print(f"  ❌ Error creando formularios para {record.record_number}: {e}")
            continue

    print(f"  ✅ {forms_created} formularios clínicos creados")


def main():
    """Función principal"""
    print("=" * 60)
    print("🌱 INICIANDO SEEDER DE FORMULARIOS CLÍNICOS")
    print("=" * 60)

    tenants = Tenant.objects.filter(deleted_at__isnull=True)

    for tenant in tenants:
        seed_forms_for_tenant(tenant)

    print("\n" + "=" * 60)
    print("✅ SEEDER DE FORMULARIOS CLÍNICOS COMPLETADO")
    print("=" * 60)


if __name__ == '__main__':
    main()
