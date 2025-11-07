"""
═══════════════════════════════════════════════════════════════════════════════
MEGA SEEDER - Script completo para crear TODOS los datos de prueba del sistema
═══════════════════════════════════════════════════════════════════════════════

Este script crea:
1. Superusuario ASU (Admin Super Usuario)
2. Planes de suscripción (Basic, Professional, Enterprise)
3. Tenants de prueba (2 hospitales/clínicas)
4. Roles y permisos por tenant
5. Usuarios por tenant (Admin TI, Doctores, Pacientes)
6. Pacientes con datos realistas
7. Historias clínicas COMPLETAS (con alergias, medicaciones, etc.)
8. Formularios clínicos (Triaje, Consultas, Recetas, Órdenes de Lab)
9. Documentos clínicos (PDFs, reportes, resultados)
10. Plantillas de reportes

Uso:
    python scripts/seed_data.py
"""

import os
import sys
import django
from pathlib import Path
from decimal import Decimal

# Setup Django
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

import pandas as pd
import numpy as np
from faker import Faker
from datetime import datetime, timedelta
from django.utils import timezone
from django.utils.text import slugify
import random

from apps.core.models import Tenant, set_current_tenant
from apps.accounts.models import User, Role, Permission
from apps.accounts.constants import SystemRoles
from apps.patients.models import Patient
from apps.clinical_records.models import ClinicalRecord, ClinicalForm
from apps.documents.models import ClinicalDocument
from apps.tenants.models import SubscriptionPlan
from apps.reports.models import ReportTemplate

fake = Faker('es_ES')
Faker.seed(42)
np.random.seed(42)
random.seed(42)


# ============================================================================
# DATOS MÉDICOS REALISTAS PARA HISTORIAS CLÍNICAS
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
    'Sulfonamidas',
    'Huevos',
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
    'Enfermedad de Crohn',
    'Colitis ulcerosa',
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
    {'name': 'Amoxicilina', 'dose': '500mg', 'frequency': 'Cada 8h', 'via': 'Oral'},
    {'name': 'Ibuprofeno', 'dose': '400mg', 'frequency': 'Cada 8h', 'via': 'Oral'},
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
    'Ginecología',
    'Urología',
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


# ============================================================================
# PASO 1: CREAR SUPERUSUARIO ASU
# ============================================================================

def create_superuser():
    """
    Crea el superusuario ASU (Admin Super Usuario) que puede ver todos los tenants.
    Este usuario NO pertenece a ningún tenant específico.
    """
    print("\n" + "="*80)
    print("[1/10] Creando Super Usuario (ASU)...")
    print("="*80)

    superuser_email = 'superadmin@clinidocs.com'

    # Verificar si ya existe
    if User.objects.filter(email=superuser_email).exists():
        print(f"  ⏭️  Superusuario ya existe: {superuser_email}")
        return User.objects.get(email=superuser_email)

    # Crear superusuario sin tenant
    superuser = User.objects.create_superuser(
        email=superuser_email,
        password='SuperAdmin123!',
        first_name='Super',
        last_name='Administrador',
    )

    # No asignar tenant ni rol (es superusuario global)
    superuser.is_staff = True
    superuser.is_superuser = True
    superuser.email_verified = True
    superuser.save()

    print(f"  ✅ Superusuario creado: {superuser.email}")
    print(f"     Password: SuperAdmin123!")
    print(f"     Este usuario puede acceder a TODOS los tenants")

    return superuser


# ============================================================================
# PASO 2: CREAR PLANES DE SUSCRIPCIÓN
# ============================================================================

def create_subscription_plans():
    """Crear los 3 planes de suscripción públicos"""
    print("\n" + "="*80)
    print("[2/10] Creando Planes de Suscripción...")
    print("="*80)

    plans_data = [
        {
            'name': 'Básico',
            'slug': 'basic',
            'plan_type': 'basic',
            'description': 'Plan básico ideal para clínicas pequeñas. Incluye funcionalidades esenciales.',
            'monthly_price': Decimal('1.00'),
            'annual_price': Decimal('10.00'),
            'max_users': 10,
            'max_patients': 500,
            'storage_gb': 50,
            'features': [
                '10 usuarios',
                '500 pacientes',
                '50 GB almacenamiento',
                'Historias clínicas digitales',
                'Gestión de documentos',
                'Reportes básicos',
                'Soporte por email'
            ],
            'is_active': True,
            'display_order': 1
        },
        {
            'name': 'Profesional',
            'slug': 'professional',
            'plan_type': 'professional',
            'description': 'Plan profesional para clínicas medianas con funcionalidades avanzadas.',
            'monthly_price': Decimal('19.00'),
            'annual_price': Decimal('190.00'),
            'max_users': 50,
            'max_patients': 2000,
            'storage_gb': 200,
            'features': [
                '50 usuarios',
                '2,000 pacientes',
                '200 GB almacenamiento',
                'Todas las funciones del Basic',
                'Reportes avanzados',
                'Dashboard analítico',
                'Firma digital',
                'API access',
                'Soporte prioritario'
            ],
            'is_active': True,
            'display_order': 2
        },
        {
            'name': 'Empresarial',
            'slug': 'enterprise',
            'plan_type': 'enterprise',
            'description': 'Plan empresarial para hospitales grandes con soporte dedicado.',
            'monthly_price': Decimal('49.00'),
            'annual_price': Decimal('490.00'),
            'max_users': 200,
            'max_patients': 10000,
            'storage_gb': 1000,
            'features': [
                '200 usuarios',
                '10,000 pacientes',
                '1 TB almacenamiento',
                'Todas las funciones del Professional',
                'Backup automático diario',
                'Multi-sucursales',
                'Integración HL7/DICOM',
                'OCR y análisis con IA',
                'Auditoría avanzada',
                'SLA 99.9%',
                'Soporte 24/7',
                'Onboarding personalizado'
            ],
            'is_active': True,
            'display_order': 3
        }
    ]

    created_count = 0
    for plan_data in plans_data:
        plan, created = SubscriptionPlan.objects.get_or_create(
            slug=plan_data['slug'],
            defaults=plan_data
        )

        if created:
            created_count += 1
            print(f"  ✅ Plan creado: {plan.name} (${plan.monthly_price}/mes)")

    print(f"\n  Total planes creados: {created_count}/3")


# ============================================================================
# PASO 3: CREAR TENANTS
# ============================================================================

def create_tenants():
    """Crea 2 tenants de prueba"""
    print("\n" + "="*80)
    print("[3/10] Creando Tenants...")
    print("="*80)

    tenants_data = [
        {
            'name': 'Hospital General Santa Cruz',
            'subdomain': 'hospital-santacruz',
            'email': 'admin@hospital-santacruz.com',
            'phone': '+591 3 123456',
            'address': 'Av. San Martín 123',
            'subscription_plan': 'pro',
            'subscription_status': 'active',
            'subscription_start': timezone.now(),
            'subscription_end': timezone.now() + timedelta(days=365),
            'max_users': 50,
            'max_storage_gb': 200,
        },
        {
            'name': 'Clínica Médica La Paz',
            'subdomain': 'clinica-lapaz',
            'email': 'admin@clinica-lapaz.com',
            'phone': '+591 2 987654',
            'address': 'Calle Comercio 456',
            'subscription_plan': 'basic',
            'subscription_status': 'trial',
            'subscription_start': timezone.now(),
            'subscription_end': timezone.now() + timedelta(days=30),
            'max_users': 10,
            'max_storage_gb': 50,
        }
    ]

    tenants = []
    for data in tenants_data:
        tenant, created = Tenant.objects.get_or_create(
            subdomain=data['subdomain'],
            defaults={
                **data,
                'slug': slugify(data['name'])
            }
        )
        if created:
            print(f"  ✅ Tenant creado: {tenant.name}")
        else:
            print(f"  ⏭️  Tenant ya existe: {tenant.name}")
        tenants.append(tenant)

    return tenants


# ============================================================================
# PASO 4: CREAR PERMISOS Y ROLES POR TENANT
# ============================================================================

def create_permissions_and_roles(tenant):
    """
    Crea permisos y roles para un tenant según RBAC definido.

    Roles del sistema:
    - Administrador TI: Gestión completa del tenant
    - Doctor: CRUD completo de historias clínicas y documentos
    - Paciente: Solo lectura de SU propia historia clínica
    """
    print(f"\n  🔐 Creando permisos y roles para {tenant.name}...")

    set_current_tenant(tenant)

    # Definir recursos y acciones
    resources = ['patient', 'clinical_record', 'clinical_form', 'document', 'user', 'role', 'report', 'audit', 'notification', 'dashboard']
    actions = ['create', 'read', 'update', 'delete', 'export', 'sign', 'manage', 'view', 'view_global']
    permissions = []
    permissions_dict = {}

    # Crear TODOS los permisos posibles
    for resource in resources:
        for action in actions:
            # No todos los recursos tienen todas las acciones
            # Excluir combinaciones inválidas
            if resource == 'audit' and action in ['create', 'update', 'delete']:
                continue
            if resource == 'audit' and action in ['sign', 'manage']:
                continue
            if action == 'sign' and resource != 'document':
                continue
            if resource == 'notification' and action == 'sign':
                continue
            if resource == 'notification' and action == 'export':
                continue
            if resource == 'dashboard' and action in ['create', 'update', 'delete', 'sign', 'export', 'manage']:
                continue
            perm_code = f'{resource}.{action}'
            perm, created = Permission.objects.get_or_create(
                tenant=tenant,
                code=perm_code,
                defaults={
                    'name': f'{action.title()} {resource}',
                    'description': f'Permite {action} en {resource}',
                    'resource': resource,
                    'action': action
                }
            )
            permissions.append(perm)
            permissions_dict[perm_code] = perm

    print(f"    ✅ {len(permissions)} permisos creados")

    # ========================================================================
    # DEFINIR ROLES SEGÚN ESPECIFICACIÓN
    # ========================================================================

    roles_config = {
        SystemRoles.ADMIN_TI: {
            'description': 'Administrador del tenant con acceso completo a todo',
            'is_system_role': True,
            'permissions': permissions  # TODOS los permisos
        },
        'Doctor': {
            'description': 'Doctor con acceso CRUD completo a historias clínicas y documentos',
            'is_system_role': False,
            'permissions': [
                # Pacientes: lectura y actualización
                permissions_dict.get('patient.read'),
                permissions_dict.get('patient.update'),
                # Historias clínicas: CRUD completo
                permissions_dict.get('clinical_record.create'),
                permissions_dict.get('clinical_record.read'),
                permissions_dict.get('clinical_record.update'),
                permissions_dict.get('clinical_record.delete'),
                permissions_dict.get('clinical_record.export'),
                # Formularios clínicos: CRUD completo
                permissions_dict.get('clinical_form.create'),
                permissions_dict.get('clinical_form.read'),
                permissions_dict.get('clinical_form.update'),
                permissions_dict.get('clinical_form.delete'),
                # Documentos: CRUD completo + firma
                permissions_dict.get('document.create'),
                permissions_dict.get('document.read'),
                permissions_dict.get('document.update'),
                permissions_dict.get('document.delete'),
                permissions_dict.get('document.sign'),
                permissions_dict.get('document.export'),
                # Reportes: lectura y creación
                permissions_dict.get('report.read'),
                permissions_dict.get('report.create'),
                permissions_dict.get('report.export'),
                # Notificaciones: lectura, actualización, creación
                permissions_dict.get('notification.read'),
                permissions_dict.get('notification.update'),
                permissions_dict.get('notification.create'),
                # Dashboard: lectura
                permissions_dict.get('dashboard.view'),
            ]
        },
        'Paciente': {
            'description': 'Paciente con acceso solo a SU propia historia clínica (solo lectura)',
            'is_system_role': False,
            'permissions': [
                # Solo lectura de su historia clínica
                permissions_dict.get('clinical_record.read'),
                permissions_dict.get('document.read'),
                # Notificaciones: solo lectura
                permissions_dict.get('notification.read'),
            ]
        }
    }

    roles = {}
    for role_name, role_config in roles_config.items():
        role, created = Role.objects.get_or_create(
            tenant=tenant,
            name=role_name,
            defaults={
                'description': role_config['description'],
                'is_system_role': role_config['is_system_role']
            }
        )

        # Filtrar permisos None
        role_permissions = [p for p in role_config['permissions'] if p is not None]
        role.permissions.set(role_permissions)
        roles[role_name] = role

        print(f"    ✅ Rol creado: {role_name} ({len(role_permissions)} permisos)")

    return roles


# ============================================================================
# PASO 5: CREAR USUARIOS POR TENANT
# ============================================================================

def create_users(tenant, roles):
    """
    Crea usuarios de prueba para un tenant.

    Usuarios por tenant:
    - 1 Administrador TI (gestión completa del tenant)
    - 2 Doctores (CRUD de historias clínicas)
    - 2 Pacientes (solo ven su historia clínica)
    """
    print(f"\n  👥 Creando usuarios para {tenant.name}...")

    set_current_tenant(tenant)

    users_data = [
        {
            'email': f'admin@{tenant.subdomain}.com',
            'first_name': 'Juan',
            'last_name': 'Pérez',
            'role': roles[SystemRoles.ADMIN_TI],
            'professional_id': 'ADM001',
            'is_staff': True,
            'description': 'Administrador TI del tenant'
        },
        {
            'email': f'doctor1@{tenant.subdomain}.com',
            'first_name': 'María',
            'last_name': 'González',
            'role': roles['Doctor'],
            'professional_id': 'DOC001',
            'specialty': 'Cardiología',
            'description': 'Doctora - Cardiología'
        },
        {
            'email': f'doctor2@{tenant.subdomain}.com',
            'first_name': 'Carlos',
            'last_name': 'Rodríguez',
            'role': roles['Doctor'],
            'professional_id': 'DOC002',
            'specialty': 'Pediatría',
            'description': 'Doctor - Pediatría'
        },
        {
            'email': f'paciente1@{tenant.subdomain}.com',
            'first_name': 'Pedro',
            'last_name': 'García',
            'role': roles['Paciente'],
            'description': 'Paciente de prueba 1'
        },
        {
            'email': f'paciente2@{tenant.subdomain}.com',
            'first_name': 'Laura',
            'last_name': 'Fernández',
            'role': roles['Paciente'],
            'description': 'Paciente de prueba 2'
        },
    ]

    users = []
    for data in users_data:
        user, created = User.objects.get_or_create(
            email=data['email'],
            defaults={
                'tenant': tenant,
                'first_name': data['first_name'],
                'last_name': data['last_name'],
                'role': data['role'],
                'professional_id': data.get('professional_id', ''),
                'specialty': data.get('specialty', ''),
                'is_staff': data.get('is_staff', False),
                'is_active': True,
                'email_verified': True,
            }
        )

        if created:
            user.set_password('Password123!')
            user.save()
            print(f"    ✅ {data['description']}: {user.email} | Rol: {user.role.name}")

        users.append(user)

    return users


# ============================================================================
# PASO 6: CREAR PACIENTES CON DATOS REALISTAS
# ============================================================================

def create_patients(tenant, count=50):
    """Crea pacientes de prueba usando Pandas"""
    print(f"\n  🏥 Creando {count} pacientes para {tenant.name}...")

    set_current_tenant(tenant)

    # Generar datos con Pandas
    data = {
        'first_name': [fake.first_name() for _ in range(count)],
        'last_name': [fake.last_name() for _ in range(count)],
        'identity_document': [fake.random_number(digits=8) for _ in range(count)],
        'identity_document_type': np.random.choice(['CI', 'Pasaporte', 'DNI'], count),
        'date_of_birth': [fake.date_of_birth(minimum_age=18, maximum_age=90) for _ in range(count)],
        'gender': np.random.choice(['M', 'F'], count),
        'phone': [fake.phone_number() for _ in range(count)],
        'email': [fake.email() for _ in range(count)],
        'address': [fake.address() for _ in range(count)],
        'city': [fake.city() for _ in range(count)],
    }

    df = pd.DataFrame(data)

    patients = []
    for _, row in df.iterrows():
        patient, created = Patient.objects.get_or_create(
            tenant=tenant,
            identity_document=str(row['identity_document']),
            defaults={
                'identity_document_type': row['identity_document_type'],
                'first_name': row['first_name'],
                'last_name': row['last_name'],
                'date_of_birth': row['date_of_birth'],
                'gender': row['gender'],
                'phone': row['phone'],
                'email': row['email'],
                'address': row['address'],
                'city': row['city'],
            }
        )
        patients.append(patient)

    print(f"    ✅ {len(patients)} pacientes creados")
    return patients


# ============================================================================
# PASO 7: CREAR HISTORIAS CLÍNICAS COMPLETAS
# ============================================================================

def create_clinical_records(tenant, patients):
    """
    Crea historias clínicas COMPLETAS para los pacientes con:
    - Tipo de sangre
    - Alergias (0-3)
    - Condiciones crónicas (0-2)
    - Medicaciones actuales (0-4)
    """
    print(f"\n  📋 Creando historias clínicas COMPLETAS para {tenant.name}...")

    set_current_tenant(tenant)

    records = []
    for i, patient in enumerate(patients):
        # Generar alergias (0-3)
        num_allergies = np.random.choice([0, 0, 0, 1, 1, 2, 3])
        allergies = random.sample(ALLERGIES, num_allergies) if num_allergies > 0 else []
        
        # Generar condiciones crónicas (0-2)
        num_conditions = np.random.choice([0, 0, 0, 1, 1, 2])
        chronic_conditions = random.sample(CHRONIC_CONDITIONS, num_conditions) if num_conditions > 0 else []
        
        # Generar medicaciones actuales (0-4)
        num_medications = np.random.choice([0, 0, 1, 1, 2, 2, 3])
        medications = random.sample(MEDICATIONS, num_medications) if num_medications > 0 else []
        
        record, created = ClinicalRecord.objects.get_or_create(
            tenant=tenant,
            patient=patient,
            defaults={
                'record_number': f'HC-{timezone.now().year}-{str(i+1).zfill(6)}',
                'status': 'active',
                'blood_type': random.choice(BLOOD_TYPES),
                'allergies': allergies,
                'chronic_conditions': chronic_conditions,
                'medications': medications,
            }
        )
        
        if not created:
            # Actualizar con datos completos si ya existía
            record.blood_type = random.choice(BLOOD_TYPES)
            record.allergies = allergies
            record.chronic_conditions = chronic_conditions
            record.medications = medications
            record.save()
        
        records.append(record)

    print(f"    ✅ {len(records)} historias clínicas creadas con datos completos")
    return records


# ============================================================================
# PASO 8: CREAR FORMULARIOS CLÍNICOS (Triaje, Consultas, Recetas, etc.)
# ============================================================================

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
                    'description': random.choice(COMMON_DIAGNOSES),
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
    selected_meds = random.sample(MEDICATIONS, random.randint(1, 3))

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
        'diagnosis': random.choice(COMMON_DIAGNOSES),
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
        'diagnosis': random.choice(COMMON_DIAGNOSES),
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


def create_clinical_forms(tenant, clinical_records, doctors):
    """Crear formularios clínicos para las historias clínicas"""
    print(f"\n  📝 Creando formularios clínicos para {tenant.name}...")

    set_current_tenant(tenant)

    forms_created = 0

    # Crear formularios para cada historia clínica
    for record in clinical_records[:20]:  # Limitamos a las primeras 20 historias
        doctor = random.choice(doctors)

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

    print(f"    ✅ {forms_created} formularios clínicos creados")
    return forms_created


# ============================================================================
# PASO 9: CREAR DOCUMENTOS CLÍNICOS COMPLETOS
# ============================================================================

def create_clinical_documents(tenant, clinical_records, doctors):
    """
    Crear documentos clínicos completos (consultas, laboratorios, recetas, etc.)
    con contenido estructurado y metadatos
    """
    print(f"\n  📄 Creando documentos clínicos para {tenant.name}...")

    set_current_tenant(tenant)

    documents_created = 0

    # Crear documentos para cada historia clínica
    for record in clinical_records[:15]:  # Limitamos a las primeras 15 historias
        doctor = random.choice(doctors)
        specialty = random.choice(SPECIALTIES)
        
        # Número de documentos por historia: 2-5
        num_docs = random.randint(2, 5)

        for _ in range(num_docs):
            days_ago = random.randint(1, 365)  # Últimos 12 meses
            document_date = timezone.now() - timedelta(days=days_ago)
            
            # Tipo de documento (50% consultas, 25% labs, 25% otros)
            rand = random.random()
            
            if rand < 0.5:
                # Consulta médica
                doc_type = 'consultation'
                diagnosis = random.choice(COMMON_DIAGNOSES)
                
                content = {
                    'chief_complaint': random.choice([
                        'Dolor abdominal',
                        'Cefalea intensa',
                        'Tos y fiebre',
                        'Control de rutina',
                        'Dolor articular',
                    ]),
                    'history_present_illness': fake.text(max_nb_chars=300),
                    'vital_signs': {
                        'blood_pressure': f'{random.randint(100, 140)}/{random.randint(60, 90)}',
                        'heart_rate': random.randint(60, 100),
                        'temperature': round(random.uniform(36.0, 37.5), 1),
                        'respiratory_rate': random.randint(12, 20),
                        'oxygen_saturation': random.randint(95, 100),
                    },
                    'physical_examination': fake.text(max_nb_chars=300),
                    'diagnosis': diagnosis,
                    'treatment_plan': random.choice([
                        'Continuar con medicación actual. Control en 1 mes.',
                        'Prescribir tratamiento sintomático. Reposo relativo.',
                        'Solicitar exámenes complementarios.',
                        'Referir a especialidad.',
                    ]),
                }
                title = f'Consulta Médica - {diagnosis}'
                
            elif rand < 0.75:
                # Resultado de laboratorio
                doc_type = 'lab_result'
                
                content = {
                    'test_name': random.choice([
                        'Hemograma Completo',
                        'Perfil Lipídico',
                        'Glucosa en Ayunas',
                        'Función Renal',
                    ]),
                    'test_date': document_date.strftime('%Y-%m-%d'),
                    'results': {
                        'Hemoglobina': {'value': '14.5', 'unit': 'g/dL', 'reference': '12-16'},
                        'Leucocitos': {'value': '7500', 'unit': '/mm³', 'reference': '4000-11000'},
                        'Glucosa': {'value': '95', 'unit': 'mg/dL', 'reference': '70-100'},
                    },
                    'interpretation': 'Resultados dentro de parámetros normales',
                }
                title = f'Resultados de Laboratorio - {content["test_name"]}'
                
            else:
                # Receta médica
                doc_type = 'prescription'
                
                selected_meds = random.sample(MEDICATIONS, random.randint(1, 3))
                content = {
                    'diagnosis': random.choice(COMMON_DIAGNOSES),
                    'medications': selected_meds,
                    'instructions': 'Tomar según indicaciones. No suspender sin consultar.',
                    'duration': f'{random.choice([7, 10, 14, 30])} días',
                }
                title = 'Receta Médica'

            try:
                ClinicalDocument.objects.create(
                    tenant=tenant,
                    clinical_record=record,
                    document_type=doc_type,
                    title=title,
                    description=fake.text(max_nb_chars=150),
                    document_date=document_date,
                    specialty=specialty,
                    doctor_name=f'Dr./Dra. {doctor.get_full_name()}',
                    doctor_license=doctor.professional_id or f'MED-{random.randint(10000, 99999)}',
                    content=content,
                    tags=[specialty.lower().replace(' ', '_'), doc_type, 'completed'],
                    created_by=doctor,
                )
                documents_created += 1
            except Exception as e:
                print(f"  ❌ Error creando documento: {e}")
                continue

    print(f"    ✅ {documents_created} documentos clínicos creados")
    return documents_created


# ============================================================================
# PASO 10: CREAR PLANTILLAS DE REPORTES
# ============================================================================

def create_report_templates(tenant):
    """Crea plantillas de reportes por defecto para el tenant"""
    print(f"\n  📊 Creando plantillas de reportes para {tenant.name}...")

    templates = [
        {
            'name': 'Documentos por Tipo',
            'description': 'Reporte estadístico de documentos agrupados por tipo',
            'report_type': 'documents_by_type',
            'category': 'Documentos',
            'output_formats': ['pdf', 'excel'],
            'is_public': True,
            'allowed_roles': ['Administrador TI', 'Doctor'],
        },
        {
            'name': 'Resumen de Pacientes',
            'description': 'Estadísticas generales de pacientes',
            'report_type': 'patients_summary',
            'category': 'Pacientes',
            'output_formats': ['pdf', 'excel'],
            'is_public': True,
            'allowed_roles': ['Administrador TI', 'Doctor'],
        },
        {
            'name': 'Registro de Actividad',
            'description': 'Log de actividades del sistema',
            'report_type': 'activity_log',
            'category': 'Auditoría',
            'output_formats': ['excel', 'csv'],
            'is_public': False,
            'allowed_roles': ['Administrador TI'],
        },
        {
            'name': 'Estadísticas de Uso',
            'description': 'Métricas de uso del sistema',
            'report_type': 'usage_statistics',
            'category': 'Estadísticas',
            'output_formats': ['excel', 'pdf'],
            'is_public': False,
            'allowed_roles': ['Administrador TI'],
        },
    ]

    created_count = 0
    for template_data in templates:
        template, created = ReportTemplate.objects.get_or_create(
            tenant=tenant,
            name=template_data['name'],
            defaults=template_data
        )

        if created:
            created_count += 1

    print(f"    ✅ {created_count} plantillas de reportes creadas")


# ============================================================================
# PASO 10: RESUMEN Y CREDENCIALES
# ============================================================================

def show_credentials(tenants):
    """Mostrar credenciales de acceso"""
    print("\n" + "="*80)
    print("[10/10] CREDENCIALES DE ACCESO")
    print("="*80)

    print("\n🌟 SUPERUSUARIO (ASU - Acceso a todos los tenants):")
    print(f"   Email: superadmin@clinidocs.com")
    print(f"   Password: SuperAdmin123!")
    print(f"   Puede ver información de TODOS los tenants")

    for tenant in tenants:
        print(f"\n🏥 {tenant.name.upper()}:")
        print(f"   URL: http://{tenant.subdomain}.localhost:8000")
        print(f"   Administrador TI: admin@{tenant.subdomain}.com")
        print(f"   Doctor: doctor1@{tenant.subdomain}.com")
        print(f"   Paciente: paciente1@{tenant.subdomain}.com")
        print(f"   Password (todos): Password123!")

    print("\n📝 Sistema de Permisos RBAC:")
    print(f"  • {SystemRoles.ADMIN_TI}: Gestión completa del tenant")
    print("  • Doctor: CRUD completo de historias clínicas")
    print("  • Paciente: Solo lectura de SU historia clínica")
    print()


def show_summary():
    """Mostrar resumen final de datos creados"""
    print("\n" + "="*80)
    print("📊 RESUMEN FINAL")
    print("="*80)

    set_current_tenant(None)  # Limpiar contexto para ver todos

    stats = {
        'Tenants': Tenant.objects.count(),
        'Usuarios totales': User.objects.count(),
        'Roles totales': Role.objects.count(),
        'Permisos totales': Permission.objects.count(),
        'Pacientes totales': Patient.objects.count(),
        'Historias clínicas': ClinicalRecord.objects.count(),
        'Formularios clínicos': ClinicalForm.objects.count(),
        'Documentos clínicos': ClinicalDocument.objects.count(),
        'Planes de suscripción': SubscriptionPlan.objects.count(),
        'Plantillas de reportes': ReportTemplate.objects.count(),
    }

    for key, value in stats.items():
        print(f"  • {key}: {value}")

    print("\n" + "="*80)
    print("💡 Flujo del Sistema:")
    print("="*80)
    print("  1. CLINICAL_RECORD (Historia Clínica)")
    print("     └─ Creada para cada paciente")
    print("     └─ Contiene: alergias, condiciones crónicas, medicaciones")
    print("")
    print("  2. CLINICAL_FORM (Formulario Clínico)")
    print("     └─ Asociado a una historia clínica")
    print("     └─ Tipos: Triaje, Consulta, Receta, Orden de Lab")
    print("     └─ Llenado por doctores/personal médico")
    print("")
    print("  3. CLINICAL_DOCUMENT (Documento Clínico)")
    print("     └─ También asociado a una historia clínica")
    print("     └─ Tipos: Consulta, Resultado Lab, Receta, Reporte")
    print("     └─ Puede incluir archivos (PDFs, imágenes)")
    print("\n" + "="*80)


# ============================================================================
# MAIN - EJECUTAR TODO EL SEEDER
# ============================================================================

def main():
    """Función principal del seeder"""
    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*20 + "MEGA SEEDER - TODOS LOS DATOS DE PRUEBA" + " "*19 + "║")
    print("╚" + "="*78 + "╝")
    print("\n")

    try:
        # 1. Crear superusuario ASU (Admin Super Usuario)
        superuser = create_superuser()

        # 2. Crear planes de suscripción
        create_subscription_plans()

        # 3. Crear tenants
        tenants = create_tenants()

        # 4-10. Para cada tenant, crear permisos, roles, usuarios, pacientes, etc.
        for idx, tenant in enumerate(tenants, 1):
            print("\n" + "="*80)
            print(f"[{idx+3}/11] Configurando: {tenant.name}")
            print("="*80)

            # 4. Permisos y roles
            roles = create_permissions_and_roles(tenant)

            # 5. Usuarios
            users = create_users(tenant, roles)
            
            # Obtener doctores para crear formularios y documentos
            doctors = [u for u in users if u.role and u.role.name in ['Doctor', SystemRoles.ADMIN_TI]]
            if not doctors:
                doctors = [users[0]]  # Usar el primer usuario como fallback

            # 6. Pacientes
            patients_count = 50 if tenant.subscription_plan == 'pro' else 20
            patients = create_patients(tenant, count=patients_count)

            # 7. Historias clínicas COMPLETAS (con alergias, medicaciones, etc.)
            records = create_clinical_records(tenant, patients)

            # 8. Formularios clínicos (Triaje, Consultas, Recetas, Órdenes de Lab)
            create_clinical_forms(tenant, records, doctors)

            # 9. Documentos clínicos (con contenido estructurado)
            create_clinical_documents(tenant, records, doctors)

            # 10. Plantillas de reportes
            create_report_templates(tenant)

        # 11. Mostrar credenciales y resumen
        show_credentials(tenants)
        show_summary()

        print("\n✅ SEEDER COMPLETADO EXITOSAMENTE\n")

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        print("\n⚠️  El seeder falló. Revisa los errores arriba.")


if __name__ == '__main__':
    main()
