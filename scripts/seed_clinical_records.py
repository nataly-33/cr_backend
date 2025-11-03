"""
Seeder para crear historias clínicas completas con datos realistas
Genera consultas, diagnósticos, tratamientos, exámenes, etc.
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
from apps.patients.models import Patient
from apps.clinical_records.models import ClinicalRecord
from apps.documents.models import ClinicalDocument
from apps.accounts.models import User

fake = Faker('es_ES')
Faker.seed(42)
random.seed(42)

# ============================================================================
# DATOS MÉDICOS REALISTAS
# ============================================================================

BLOOD_TYPES = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']

ALLERGIES = [
    'Penicilina',
    'Polen',
    'Ácaros del polvo',
    'Látex',
    'Mariscos',
    'Frutos secos',
    'Aspirina',
    'Ibuprofeno',
    'Ácido acetilsalicílico',
    'Contraste yodado',
]

CHRONIC_CONDITIONS = [
    'Hipertensión arterial',
    'Diabetes mellitus tipo 2',
    'Diabetes mellitus tipo 1',
    'Asma bronquial',
    'EPOC (Enfermedad Pulmonar Obstructiva Crónica)',
    'Artritis reumatoide',
    'Hipotiroidismo',
    'Hipertiroidismo',
    'Insuficiencia renal crónica',
    'Enfermedad cardíaca coronaria',
    'Arritmia cardíaca',
    'Osteoporosis',
    'Anemia crónica',
]

MEDICATIONS = [
    {'name': 'Losartán', 'dose': '50mg', 'frequency': 'Cada 24h', 'via': 'Oral'},
    {'name': 'Metformina', 'dose': '850mg', 'frequency': 'Cada 12h', 'via': 'Oral'},
    {'name': 'Atorvastatina', 'dose': '20mg', 'frequency': 'Cada 24h', 'via': 'Oral'},
    {'name': 'Omeprazol', 'dose': '20mg', 'frequency': 'Cada 24h', 'via': 'Oral'},
    {'name': 'Levotiroxina', 'dose': '75mcg', 'frequency': 'Cada 24h', 'via': 'Oral'},
    {'name': 'Salbutamol', 'dose': '100mcg', 'frequency': 'PRN', 'via': 'Inhalada'},
    {'name': 'Insulina NPH', 'dose': '10UI', 'frequency': 'Cada 12h', 'via': 'Subcutánea'},
    {'name': 'Paracetamol', 'dose': '500mg', 'frequency': 'Cada 8h PRN', 'via': 'Oral'},
]

SPECIALTIES = [
    'Medicina General',
    'Cardiología',
    'Pediatría',
    'Neurología',
    'Dermatología',
    'Gastroenterología',
    'Endocrinología',
    'Neumología',
    'Traumatología',
    'Psiquiatría',
]

CONSULTATION_TYPES = [
    {'type': 'consultation', 'title': 'Consulta Médica General'},
    {'type': 'consultation', 'title': 'Consulta de Seguimiento'},
    {'type': 'consultation', 'title': 'Consulta por Emergencia'},
    {'type': 'lab_result', 'title': 'Resultados de Laboratorio'},
    {'type': 'imaging_report', 'title': 'Informe de Radiografía'},
    {'type': 'imaging_report', 'title': 'Informe de Tomografía'},
    {'type': 'imaging_report', 'title': 'Informe de Ecografía'},
    {'type': 'prescription', 'title': 'Receta Médica'},
    {'type': 'progress_note', 'title': 'Nota de Evolución'},
    {'type': 'progress_note', 'title': 'Nota de Ingreso Hospitalario'},
]

COMMON_DIAGNOSES = [
    'Hipertensión arterial esencial',
    'Diabetes mellitus tipo 2',
    'Infección respiratoria aguda',
    'Gastroenteritis aguda',
    'Cefalea tensional',
    'Lumbalgia mecánica',
    'Dermatitis atópica',
    'Ansiedad generalizada',
    'Hipotiroidismo',
    'Artrosis de rodilla',
    'Conjuntivitis aguda',
    'Faringitis viral',
    'Bronquitis aguda',
    'Otitis media aguda',
    'Control prenatal',
]

LAB_TESTS = [
    {
        'name': 'Hemograma Completo',
        'results': {
            'Hemoglobina': {'value': '14.5', 'unit': 'g/dL', 'reference': '12-16'},
            'Leucocitos': {'value': '7500', 'unit': '/mm³', 'reference': '4000-11000'},
            'Plaquetas': {'value': '250000', 'unit': '/mm³', 'reference': '150000-450000'},
            'Hematocrito': {'value': '42', 'unit': '%', 'reference': '37-47'},
        }
    },
    {
        'name': 'Perfil Lipídico',
        'results': {
            'Colesterol Total': {'value': '180', 'unit': 'mg/dL', 'reference': '<200'},
            'HDL': {'value': '50', 'unit': 'mg/dL', 'reference': '>40'},
            'LDL': {'value': '110', 'unit': 'mg/dL', 'reference': '<130'},
            'Triglicéridos': {'value': '120', 'unit': 'mg/dL', 'reference': '<150'},
        }
    },
    {
        'name': 'Glucosa en Ayunas',
        'results': {
            'Glucosa': {'value': '95', 'unit': 'mg/dL', 'reference': '70-100'},
        }
    },
    {
        'name': 'Función Renal',
        'results': {
            'Creatinina': {'value': '0.9', 'unit': 'mg/dL', 'reference': '0.6-1.2'},
            'Urea': {'value': '35', 'unit': 'mg/dL', 'reference': '15-40'},
        }
    },
]

VITAL_SIGNS_TEMPLATES = [
    {'bp_systolic': 120, 'bp_diastolic': 80, 'heart_rate': 72, 'temperature': 36.5, 'respiratory_rate': 16, 'oxygen_saturation': 98},
    {'bp_systolic': 130, 'bp_diastolic': 85, 'heart_rate': 78, 'temperature': 36.7, 'respiratory_rate': 18, 'oxygen_saturation': 97},
    {'bp_systolic': 110, 'bp_diastolic': 70, 'heart_rate': 65, 'temperature': 36.3, 'respiratory_rate': 14, 'oxygen_saturation': 99},
    {'bp_systolic': 140, 'bp_diastolic': 90, 'heart_rate': 82, 'temperature': 37.2, 'respiratory_rate': 20, 'oxygen_saturation': 96},
]


# ============================================================================
# FUNCIONES GENERADORAS
# ============================================================================

def generate_clinical_record_data(patient):
    """Genera datos completos para una historia clínica"""
    
    # Número de alergias (0-3)
    num_allergies = random.choice([0, 0, 0, 1, 1, 2, 3])
    allergies = random.sample(ALLERGIES, num_allergies) if num_allergies > 0 else []
    
    # Número de condiciones crónicas (0-2)
    num_conditions = random.choice([0, 0, 0, 1, 1, 2])
    chronic_conditions = random.sample(CHRONIC_CONDITIONS, num_conditions) if num_conditions > 0 else []
    
    # Medicamentos actuales (0-4)
    num_medications = random.choice([0, 0, 1, 1, 2, 2, 3])
    medications = random.sample(MEDICATIONS, num_medications) if num_medications > 0 else []
    
    return {
        'blood_type': random.choice(BLOOD_TYPES),
        'allergies': allergies,
        'chronic_conditions': chronic_conditions,
        'medications': medications,
        'status': 'active',
    }


def generate_consultation_document(clinical_record, doctor, days_ago=0):
    """Genera un documento de consulta médica completo"""
    
    specialty = random.choice(SPECIALTIES)
    consultation_type = random.choice(CONSULTATION_TYPES)
    diagnosis = random.choice(COMMON_DIAGNOSES)
    vital_signs = random.choice(VITAL_SIGNS_TEMPLATES)
    
    # Fecha de la consulta
    document_date = timezone.now() - timedelta(days=days_ago)
    
    # Motivo de consulta
    chief_complaints = [
        'Dolor abdominal de 2 días de evolución',
        'Cefalea intensa matutina',
        'Tos y fiebre desde hace 3 días',
        'Control de rutina',
        'Dolor en rodilla derecha al caminar',
        'Mareos y visión borrosa',
        'Dificultad para respirar',
        'Dolor torácico opresivo',
    ]
    
    # Historia de enfermedad actual
    hpi_templates = [
        f'Paciente refiere {random.choice(chief_complaints).lower()}, sin antecedentes de trauma. '
        f'Niega otros síntomas asociados. Examen físico: dentro de límites normales.',
        
        f'Paciente acude por control de su patología crónica. Refiere adherencia al tratamiento. '
        f'Sin nuevos síntomas. Signos vitales estables.',
        
        f'Cuadro clínico de {random.randint(1, 7)} días de evolución caracterizado por '
        f'síntomas compatibles con {diagnosis.lower()}. Examen físico revela hallazgos concordantes.',
    ]
    
    # Plan de tratamiento
    treatment_plans = [
        'Continuar con medicación actual. Control en 1 mes.',
        'Se prescribe tratamiento sintomático. Reposo relativo. Control en 7 días.',
        'Solicitar exámenes de laboratorio. Valorar ajuste de dosis según resultados.',
        'Referir a especialidad. Continuar tratamiento actual.',
    ]
    
    content = {
        'chief_complaint': random.choice(chief_complaints),
        'history_present_illness': random.choice(hpi_templates),
        'vital_signs': vital_signs,
        'physical_examination': fake.text(max_nb_chars=300),
        'diagnosis': diagnosis,
        'treatment_plan': random.choice(treatment_plans),
        'additional_notes': fake.text(max_nb_chars=150) if random.random() > 0.5 else '',
    }
    
    return {
        'tenant': clinical_record.tenant,
        'clinical_record': clinical_record,
        'document_type': consultation_type['type'],
        'title': consultation_type['title'],
        'description': f'{specialty} - {diagnosis}',
        'document_date': document_date,
        'specialty': specialty,
        'doctor_name': f'Dr./Dra. {doctor.get_full_name()}',
        'doctor_license': doctor.professional_id or f'MED-{random.randint(10000, 99999)}',
        'content': content,
        'tags': [specialty.lower().replace(' ', '_'), consultation_type['type'], 'completed'],
        'created_by': doctor,
    }


def generate_lab_result_document(clinical_record, doctor, days_ago=0):
    """Genera un documento de resultados de laboratorio"""
    
    lab_test = random.choice(LAB_TESTS)
    document_date = timezone.now() - timedelta(days=days_ago)
    
    content = {
        'test_name': lab_test['name'],
        'test_date': document_date.strftime('%Y-%m-%d'),
        'results': lab_test['results'],
        'interpretation': 'Resultados dentro de parámetros normales' if random.random() > 0.3 
                         else 'Se observan valores fuera del rango de referencia',
        'lab_name': fake.company(),
        'lab_license': f'LAB-{random.randint(1000, 9999)}',
    }
    
    return {
        'tenant': clinical_record.tenant,
        'clinical_record': clinical_record,
        'document_type': 'lab_result',
        'title': f'Resultados de {lab_test["name"]}',
        'description': f'Examen de laboratorio - {lab_test["name"]}',
        'document_date': document_date,
        'specialty': 'Laboratorio Clínico',
        'doctor_name': f'Dr./Dra. {doctor.get_full_name()}',
        'doctor_license': doctor.professional_id or f'MED-{random.randint(10000, 99999)}',
        'content': content,
        'tags': ['laboratory', 'lab_result', 'completed'],
        'created_by': doctor,
    }


def generate_prescription_document(clinical_record, doctor, days_ago=0):
    """Genera una receta médica"""
    
    document_date = timezone.now() - timedelta(days=days_ago)
    num_medications = random.randint(1, 4)
    prescribed_meds = random.sample(MEDICATIONS, num_medications)
    
    content = {
        'diagnosis': random.choice(COMMON_DIAGNOSES),
        'medications': prescribed_meds,
        'instructions': 'Tomar según indicaciones. No suspender sin consultar.',
        'duration': f'{random.choice([7, 10, 14, 30])} días',
        'next_visit': (document_date + timedelta(days=random.choice([7, 14, 30]))).strftime('%Y-%m-%d'),
    }
    
    return {
        'tenant': clinical_record.tenant,
        'clinical_record': clinical_record,
        'document_type': 'prescription',
        'title': 'Receta Médica',
        'description': f'Prescripción de {num_medications} medicamento(s)',
        'document_date': document_date,
        'specialty': random.choice(SPECIALTIES),
        'doctor_name': f'Dr./Dra. {doctor.get_full_name()}',
        'doctor_license': doctor.professional_id or f'MED-{random.randint(10000, 99999)}',
        'content': content,
        'tags': ['prescription', 'medication', 'active'],
        'created_by': doctor,
    }


# ============================================================================
# FUNCIONES PRINCIPALES
# ============================================================================

def seed_clinical_records_for_tenant(tenant):
    """Crear historias clínicas completas para un tenant"""
    print(f"\n{'='*60}")
    print(f"🏥 Generando historias clínicas para: {tenant.name}")
    print(f"{'='*60}\n")
    
    set_current_tenant(tenant)
    
    # Obtener pacientes y doctores
    patients = list(Patient.objects.filter(tenant=tenant))
    doctors = list(User.objects.filter(
        tenant=tenant,
        role__name='Doctor'
    ))
    
    if not doctors:
        print("  ⚠️  No hay doctores disponibles. Usando usuario admin.")
        doctors = [User.objects.filter(tenant=tenant, is_staff=True).first()]
    
    if not patients:
        print("  ⚠️  No hay pacientes disponibles. Saltando...")
        return
    
    print(f"  📊 Pacientes encontrados: {len(patients)}")
    print(f"  👨‍⚕️ Doctores disponibles: {len(doctors)}")
    
    records_created = 0
    documents_created = 0
    
    # Crear historias clínicas para todos los pacientes
    for i, patient in enumerate(patients, 1):
        try:
            # Generar datos de la historia clínica
            record_data = generate_clinical_record_data(patient)
            
            # Crear o actualizar historia clínica
            record, created = ClinicalRecord.objects.get_or_create(
                tenant=tenant,
                patient=patient,
                defaults={
                    'record_number': f'HC-{timezone.now().year}-{str(i).zfill(6)}',
                    **record_data
                }
            )
            
            if not created:
                # Actualizar historia existente con datos más completos
                for key, value in record_data.items():
                    setattr(record, key, value)
                record.save()
            
            records_created += 1
            
            # Generar documentos para esta historia clínica
            # Número de consultas: 1-5 por paciente
            num_consultations = random.randint(1, 5)
            
            for j in range(num_consultations):
                doctor = random.choice(doctors)
                days_ago = random.randint(1, 365)  # Últimos 12 meses
                
                # Tipo de documento (60% consultas, 20% labs, 20% recetas)
                rand = random.random()
                
                if rand < 0.6:
                    # Consulta médica
                    doc_data = generate_consultation_document(record, doctor, days_ago)
                elif rand < 0.8:
                    # Resultado de laboratorio
                    doc_data = generate_lab_result_document(record, doctor, days_ago)
                else:
                    # Receta médica
                    doc_data = generate_prescription_document(record, doctor, days_ago)
                
                # Crear documento
                ClinicalDocument.objects.create(**doc_data)
                documents_created += 1
            
            # Mostrar progreso cada 10 pacientes
            if i % 10 == 0:
                print(f"  ⏳ Procesados {i}/{len(patients)} pacientes...")
        
        except Exception as e:
            print(f"  ❌ Error con paciente {patient.get_full_name()}: {str(e)}")
            continue
    
    print(f"\n  ✅ Historias clínicas creadas/actualizadas: {records_created}")
    print(f"  ✅ Documentos clínicos generados: {documents_created}")
    print(f"  📈 Promedio: {documents_created/records_created:.1f} documentos por historia")


def main():
    """Función principal"""
    print("\n" + "="*60)
    print("🌱 SEEDER DE HISTORIAS CLÍNICAS COMPLETAS")
    print("="*60)
    
    # Obtener todos los tenants
    tenants = Tenant.objects.all()
    
    if not tenants.exists():
        print("\n❌ No hay tenants disponibles.")
        print("Ejecuta primero: python run_seeder.py")
        return
    
    print(f"\n📋 Tenants encontrados: {tenants.count()}")
    
    for tenant in tenants:
        seed_clinical_records_for_tenant(tenant)
    
    # Resumen final
    set_current_tenant(None)
    
    print("\n" + "="*60)
    print("✅ SEEDER COMPLETADO EXITOSAMENTE")
    print("="*60)
    print("\n📊 Resumen Global:")
    print(f"  • Historias clínicas totales: {ClinicalRecord.objects.count()}")
    print(f"  • Documentos clínicos totales: {ClinicalDocument.objects.count()}")
    print(f"  • Pacientes con historia: {Patient.objects.filter(clinicalrecord__isnull=False).distinct().count()}")
    
    print("\n💡 Ahora puedes probar:")
    print("  • Módulo de Reportes (generar reportes de historias clínicas)")
    print("  • Módulo de Documentos (ver/editar documentos)")
    print("  • Módulo de Pacientes (ver historias clínicas completas)")
    print()


if __name__ == '__main__':
    main()
