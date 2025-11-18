"""
═══════════════════════════════════════════════════════════════════════════════
MEGA SEEDER MEJORADO - 500+ datos por tenant con datos realistas de Bolivia
═══════════════════════════════════════════════════════════════════════════════

Este script crea:
✅ 1 Superusuario ASU
✅ 4 Planes de suscripción (variando por almacenamiento)
✅ 2 Tenants (hospitales bolivianos)
✅ 2 Administradores TI por tenant
✅ 5 Doctores por tenant (especialidades variadas)
✅ 500 Pacientes por tenant con datos realistas de Bolivia
✅ 500 Historias clínicas por tenant
✅ 1-3 Formularios clínicos por paciente (consultas, recetas, órdenes lab)
✅ 1-3 Documentos clínicos por paciente
✅ Fechas realistas: 01/01/2023 - 18/11/2025
✅ Roles y permisos completos
✅ Estadísticas finales detalladas

Uso:
    python scripts/seed_data_mega.py
"""
import os
import sys
import django
import random
import numpy as np
import pandas as pd
from pathlib import Path
from decimal import Decimal
from datetime import datetime, timedelta, date

# Setup Django
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from faker import Faker
from django.utils import timezone
from django.utils.text import slugify

from apps.core.models import Tenant, set_current_tenant
from apps.accounts.models import User, Role, Permission
from apps.accounts.constants import SystemRoles
from apps.patients.models import Patient
from apps.clinical_records.models import ClinicalRecord, ClinicalForm
from apps.documents.models import ClinicalDocument
from apps.tenants.models import SubscriptionPlan
from apps.reports.models import ReportTemplate

# Configurar Faker para Bolivia
fake = Faker(['es_ES', 'es_MX'])
Faker.seed(42)
np.random.seed(42)
random.seed(42)


# ============================================================================
# DATOS REALISTAS PARA BOLIVIA
# ============================================================================

# Ciudades principales de Bolivia
BOLIVIAN_CITIES = [
    'La Paz', 'El Alto', 'Santa Cruz de la Sierra', 'Cochabamba',
    'Oruro', 'Sucre', 'Tarija', 'Potosí', 'Trinidad', 'Cobija'
]

# Nombres comunes bolivianos
BOLIVIAN_FIRST_NAMES_M = [
    'Juan', 'Carlos', 'José', 'Luis', 'Miguel', 'Pedro', 'Jorge', 'Fernando',
    'Diego', 'Andrés', 'Ricardo', 'Roberto', 'Daniel', 'Francisco', 'Manuel'
]

BOLIVIAN_FIRST_NAMES_F = [
    'María', 'Ana', 'Carmen', 'Rosa', 'Laura', 'Patricia', 'Isabel', 'Elena',
    'Sofía', 'Gabriela', 'Lucía', 'Valentina', 'Andrea', 'Daniela', 'Paola'
]

BOLIVIAN_LAST_NAMES = [
    'García', 'González', 'Rodríguez', 'Fernández', 'López', 'Martínez',
    'Sánchez', 'Pérez', 'Gómez', 'Martín', 'Jiménez', 'Ruiz', 'Hernández',
    'Díaz', 'Moreno', 'Álvarez', 'Romero', 'Torres', 'Ramírez', 'Flores'
]

# Tipos de sangre
BLOOD_TYPES = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']

# Alergias comunes
ALLERGIES = [
    'Penicilina', 'Polen', 'Ácaros del polvo', 'Látex', 'Mariscos',
    'Frutos secos', 'Aspirina', 'Ibuprofeno', 'Sulfonamidas', 'Huevos',
    'Leche', 'Contraste yodado', 'Picadura de abeja'
]

# Condiciones crónicas
CHRONIC_CONDITIONS = [
    'Hipertensión arterial', 'Diabetes mellitus tipo 2', 'Diabetes mellitus tipo 1',
    'Asma bronquial', 'EPOC', 'Artritis reumatoide', 'Hipotiroidismo',
    'Hipertiroidismo', 'Insuficiencia renal crónica', 'Enfermedad cardíaca coronaria',
    'Arritmia cardíaca', 'Osteoporosis', 'Anemia crónica', 'Epilepsia',
    'Enfermedad de Crohn', 'Colitis ulcerosa', 'Migraña crónica'
]

# Medicamentos comunes
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

# Especialidades médicas
SPECIALTIES = [
    'Medicina General', 'Cardiología', 'Pediatría', 'Ginecología',
    'Traumatología', 'Neurología', 'Dermatología', 'Gastroenterología',
    'Endocrinología', 'Neumología', 'Psiquiatría', 'Urología'
]

# Diagnósticos comunes
COMMON_DIAGNOSES = [
    'Hipertensión arterial esencial', 'Diabetes mellitus tipo 2',
    'Infección respiratoria aguda', 'Gastroenteritis aguda',
    'Cefalea tensional', 'Lumbalgia mecánica', 'Dermatitis atópica',
    'Ansiedad generalizada', 'Hipotiroidismo', 'Artrosis de rodilla',
    'Conjuntivitis aguda', 'Faringitis viral', 'Bronquitis aguda',
    'Otitis media aguda', 'Control prenatal', 'Dengue', 'Chagas'
]

# Rango de fechas: 01/01/2023 - 18/11/2025
START_DATE = datetime(2023, 1, 1)
END_DATE = datetime(2025, 11, 18)


def random_date_between(start_date, end_date):
    """Genera una fecha aleatoria entre dos fechas"""
    time_between = end_date - start_date
    days_between = time_between.days
    random_days = random.randint(0, days_between)
    return start_date + timedelta(days=random_days)


def random_datetime_between(start_date, end_date):
    """Genera un datetime aleatorio entre dos fechas"""
    date_result = random_date_between(start_date, end_date)
    hour = random.randint(8, 18)  # Horario laboral
    minute = random.choice([0, 15, 30, 45])
    return datetime.combine(date_result, datetime.min.time()).replace(
        hour=hour, minute=minute, tzinfo=timezone.get_current_timezone()
    )


# ============================================================================
# PASO 1: CREAR SUPERUSUARIO ASU
# ============================================================================

def create_superuser():
    """Crea el superusuario ASU"""
    print("\n" + "="*80)
    print("[1/11] Creando Super Usuario (ASU)...")
    print("="*80)

    superuser_email = 'superadmin@clinidocs.com'

    if User.objects.filter(email=superuser_email).exists():
        print(f"  ⚠️  Superusuario ya existe: {superuser_email}")
        return User.objects.get(email=superuser_email)

    superuser = User.objects.create_superuser(
        email=superuser_email,
        password='Password123!',
        first_name='Super',
        last_name='Administrador',
    )

    superuser.is_staff = True
    superuser.is_superuser = True
    superuser.email_verified = True
    superuser.save()

    print(f"  ✅ Superusuario creado: {superuser.email}")
    print(f"     Password: Password123!")

    return superuser


# ============================================================================
# PASO 2: CREAR PLANES DE SUSCRIPCIÓN (4 planes variando por almacenamiento)
# ============================================================================

def create_subscription_plans():
    """Crear 4 planes de suscripción variando por almacenamiento"""
    print("\n" + "="*80)
    print("[2/11] Creando Planes de Suscripción...")
    print("="*80)

    plans_data = [
        {
            'name': 'Básico',
            'slug': 'basic',
            'plan_type': 'basic',
            'description': 'Plan básico para clínicas pequeñas',
            'monthly_price': Decimal('99.00'),
            'annual_price': Decimal('990.00'),
            'max_users': 999,  # Ilimitado (validación suave)
            'max_patients': 999999,
            'storage_gb': 50,
            'features': [
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
            'description': 'Plan profesional con más almacenamiento',
            'monthly_price': Decimal('199.00'),
            'annual_price': Decimal('1990.00'),
            'max_users': 999,
            'max_patients': 999999,
            'storage_gb': 200,
            'features': [
                '200 GB almacenamiento',
                'Todas las funciones del Básico',
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
            'description': 'Plan empresarial con gran almacenamiento',
            'monthly_price': Decimal('399.00'),
            'annual_price': Decimal('3990.00'),
            'max_users': 999,
            'max_patients': 999999,
            'storage_gb': 500,
            'features': [
                '500 GB almacenamiento',
                'Todas las funciones del Profesional',
                'Backup automático diario',
                'Multi-sucursales',
                'Integración HL7/DICOM',
                'OCR y análisis con IA',
                'Auditoría avanzada',
                'Soporte 24/7'
            ],
            'is_active': True,
            'display_order': 3
        },
        {
            'name': 'Premium',
            'slug': 'premium',
            'plan_type': 'premium',
            'description': 'Plan premium con almacenamiento máximo',
            'monthly_price': Decimal('699.00'),
            'annual_price': Decimal('6990.00'),
            'max_users': 999,
            'max_patients': 999999,
            'storage_gb': 1000,
            'features': [
                '1 TB almacenamiento',
                'Todas las funciones del Empresarial',
                'Almacenamiento ilimitado',
                'Servidor dedicado',
                'SLA 99.9%',
                'Onboarding personalizado',
                'Consultor dedicado'
            ],
            'is_active': True,
            'display_order': 4
        }
    ]

    created_count = 0
    for plan_data in plans_data:
        plan, created = SubscriptionPlan.objects.get_or_create(
            slug=plan_data['slug'],
            defaults=plan_data
        )
        if created:
            print(f"  ✅ Plan creado: {plan.name} - {plan.storage_gb}GB - ${plan.monthly_price}/mes")
            created_count += 1
        else:
            print(f"  ⚠️  Plan ya existe: {plan.name}")

    print(f"\n  Total planes creados: {created_count}/4")
    return SubscriptionPlan.objects.all()


# ============================================================================
# PASO 3: CREAR TENANTS (2 hospitales bolivianos)
# ============================================================================

def create_tenants():
    """Crea 2 tenants de hospitales bolivianos"""
    print("\n" + "="*80)
    print("[3/11] Creando Tenants...")
    print("="*80)

    tenants_data = [
        {
            'name': 'Hospital General Santa Cruz',
            'slug': 'hospital-santacruz',
            'subdomain': 'hospital-santacruz',
            'email': 'admin@hospital-santacruz.com',
            'phone': '+591 3 123456',
            'address': 'Av. San Martín 123',
            'subscription_plan': 'professional',
            'subscription_status': 'active',
            'subscription_start': timezone.now() - timedelta(days=365),
            'subscription_end': timezone.now() + timedelta(days=365),
            'max_users': 999,
            'max_storage_gb': 200,
        },
        {
            'name': 'Clínica Médica La Paz',
            'slug': 'clinica-lapaz',
            'subdomain': 'clinica-lapaz',
            'email': 'admin@clinica-lapaz.com',
            'phone': '+591 2 987654',
            'address': 'Calle Comercio 456',
            'subscription_plan': 'basic',
            'subscription_status': 'active',
            'subscription_start': timezone.now() - timedelta(days=180),
            'subscription_end': timezone.now() + timedelta(days=180),
            'max_users': 999,
            'max_storage_gb': 50,
        }
    ]

    tenants = []
    for data in tenants_data:
        # Usar slug como clave de búsqueda (es único)
        tenant, created = Tenant.objects.get_or_create(
            slug=data['slug'],
            defaults=data
        )
        if created:
            print(f"  ✅ Tenant creado: {tenant.name}")
            print(f"     Subdomain: {tenant.subdomain}")
            print(f"     Plan: {tenant.subscription_plan} ({tenant.max_storage_gb}GB)")
        else:
            print(f"  ⚠️  Tenant ya existe: {tenant.name}")
        tenants.append(tenant)

    return tenants


# ============================================================================
# PASO 4: CREAR PERMISOS Y ROLES
# ============================================================================

def create_permissions_and_roles(tenant):
    """Crea permisos y roles para un tenant"""
    print(f"\n  🔐 Creando permisos y roles para {tenant.name}...")

    set_current_tenant(tenant)

    resources = ['patient', 'clinical_record', 'clinical_form', 'document', 'user', 'role', 'report', 'audit', 'notification', 'dashboard', 'payment', 'invoice']
    actions = ['create', 'read', 'update', 'delete', 'export', 'sign', 'manage', 'view', 'view_global', 'refund', 'download']
    
    permissions = []
    permissions_dict = {}

    for resource in resources:
        for action in actions:
            # Filtrar combinaciones inválidas
            if resource == 'dashboard' and action not in ['view']:
                continue
            if resource == 'audit' and action not in ['read', 'view', 'view_global', 'export']:
                continue
            if resource == 'notification' and action not in ['create', 'read', 'update']:
                continue
            if resource == 'payment' and action not in ['create', 'read', 'refund']:
                continue
            if resource == 'invoice' and action not in ['read', 'download', 'view']:
                continue
            
            # Generar código único: resource.action
            permission_code = f'{resource}.{action}'
            
            perm, created = Permission.objects.get_or_create(
                tenant=tenant,
                code=permission_code,
                defaults={
                    'name': f'{action.title()} {resource}',
                    'resource': resource,
                    'action': action,
                    'description': f'Permite {action} en {resource}'
                }
            )
            permissions.append(perm)
            permissions_dict[permission_code] = perm

    print(f"    ✅ {len(permissions)} permisos creados")

    # Roles
    roles_config = {
        SystemRoles.ADMIN_TI: {
            'description': 'Administrador del tenant con acceso completo',
            'is_system_role': True,
            'permissions': permissions
        },
        'Doctor': {
            'description': 'Doctor con acceso CRUD completo',
            'is_system_role': False,
            'permissions': [p for p in permissions if p.resource in ['patient', 'clinical_record', 'clinical_form', 'document', 'report', 'notification', 'dashboard']]
        },
        'Paciente': {
            'description': 'Paciente con acceso solo a su historia',
            'is_system_role': False,
            'permissions': [p for p in permissions if p.action == 'read' and p.resource in ['clinical_record', 'document', 'notification']]
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
        if created:
            role.permissions.set(role_config['permissions'])
        roles[role_name] = role

    print(f"    ✅ {len(roles)} roles creados")
    return roles


# ============================================================================
# PASO 5: CREAR USUARIOS (2 Admins TI + 5 Doctores por tenant)
# ============================================================================

def create_users(tenant, roles):
    """Crea 2 Admins TI y 5 Doctores por tenant"""
    print(f"\n  👥 Creando usuarios para {tenant.name}...")

    set_current_tenant(tenant)

    users_data = []
    
    # 2 Administradores TI
    for i in range(1, 3):
        users_data.append({
            'email': f'admin{i}@{tenant.subdomain}.com',
            'first_name': random.choice(BOLIVIAN_FIRST_NAMES_M if i % 2 == 0 else BOLIVIAN_FIRST_NAMES_F),
            'last_name': f"{random.choice(BOLIVIAN_LAST_NAMES)} {random.choice(BOLIVIAN_LAST_NAMES)}",
            'role': roles[SystemRoles.ADMIN_TI],
            'professional_id': f'ADM{str(i).zfill(3)}',
            'is_staff': True,
            'phone': f'+591 {random.choice([2, 3, 4])} {random.randint(2000000, 4999999)}',
            'description': f'Administrador TI #{i}'
        })

    # 5 Doctores con especialidades variadas
    specialties_sample = random.sample(SPECIALTIES, 5)
    for i, specialty in enumerate(specialties_sample, 1):
        gender = 'M' if i % 2 == 0 else 'F'
        users_data.append({
            'email': f'doctor{i}@{tenant.subdomain}.com',
            'first_name': random.choice(BOLIVIAN_FIRST_NAMES_M if gender == 'M' else BOLIVIAN_FIRST_NAMES_F),
            'last_name': f"{random.choice(BOLIVIAN_LAST_NAMES)} {random.choice(BOLIVIAN_LAST_NAMES)}",
            'role': roles['Doctor'],
            'professional_id': f'DOC{str(i).zfill(3)}',
            'specialty': specialty,
            'phone': f'+591 {random.choice([2, 3, 4])} {random.randint(2000000, 4999999)}',
            'gender': gender,
            'description': f'Doctor - {specialty}'
        })

    users = []
    for data in users_data:
        if User.objects.filter(email=data['email']).exists():
            user = User.objects.get(email=data['email'])
        else:
            user = User.objects.create_user(
                email=data['email'],
                password='Password123!',
                first_name=data['first_name'],
                last_name=data['last_name'],
                tenant=tenant,
            )
            user.professional_id = data.get('professional_id', '')
            user.specialty = data.get('specialty', '')
            user.phone = data.get('phone', '')
            user.gender = data.get('gender', '')
            user.is_staff = data.get('is_staff', False)
            user.email_verified = True
            user.role = data['role']
            user.save()

        users.append(user)

    print(f"    ✅ {len(users)} usuarios creados (2 Admins + 5 Doctores)")
    return users


# ============================================================================
# PASO 6: CREAR 500 PACIENTES POR TENANT
# ============================================================================

def create_patients(tenant, created_by_users, count=500):
    """Crea 500 pacientes con datos realistas bolivianos"""
    print(f"\n  🏥 Creando {count} pacientes para {tenant.name}...")

    set_current_tenant(tenant)

    patients = []
    for i in range(count):
        gender = random.choice(['M', 'F'])
        first_name = random.choice(BOLIVIAN_FIRST_NAMES_M if gender == 'M' else BOLIVIAN_FIRST_NAMES_F)
        last_name = f"{random.choice(BOLIVIAN_LAST_NAMES)} {random.choice(BOLIVIAN_LAST_NAMES)}"
        
        birth_date = random_date_between(
            datetime(1930, 1, 1),
            datetime(2015, 1, 1)
        )
        
        creation_date = random_datetime_between(START_DATE, END_DATE)
        
        # Contacto de emergencia
        emergency_contact = {
            'name': f"{random.choice(BOLIVIAN_FIRST_NAMES_M if gender == 'F' else BOLIVIAN_FIRST_NAMES_F)} {random.choice(BOLIVIAN_LAST_NAMES)}",
            'relationship': random.choice(['Esposo/a', 'Madre', 'Padre', 'Hijo/a', 'Hermano/a']),
            'phone': f'+591 {random.choice([6, 7])} {random.randint(70000000, 79999999)}'
        }
        
        patient = Patient(
            tenant=tenant,
            identity_document_type='CI',
            identity_document=str(random.randint(1000000, 15000000)),
            first_name=first_name,
            last_name=last_name,
            date_of_birth=birth_date,
            gender=gender,
            phone=f'+591 {random.choice([6, 7])} {random.randint(70000000, 79999999)}',
            email=f"{first_name.lower()}.{last_name.split()[0].lower()}@example.com" if random.random() > 0.3 else '',
            address=f"{random.choice(['Av.', 'Calle', 'Jr.'])} {fake.street_name()} #{random.randint(100, 999)}",
            city=random.choice(BOLIVIAN_CITIES),
            emergency_contact=emergency_contact,
            created_by=random.choice(created_by_users),
            created_at=creation_date,
            updated_at=creation_date
        )
        patient.save()
        patients.append(patient)

        if (i + 1) % 100 == 0:
            print(f"    ⏳ {i + 1}/{count} pacientes creados...")

    print(f"    ✅ {len(patients)} pacientes creados")
    return patients


# ============================================================================
# PASO 7: CREAR 500 HISTORIAS CLÍNICAS
# ============================================================================

def create_clinical_records(tenant, patients, doctors):
    """Crea historia clínica para cada paciente"""
    print(f"\n  📋 Creando historias clínicas para {tenant.name}...")

    set_current_tenant(tenant)

    records = []
    for i, patient in enumerate(patients):
        # Fecha: misma que la creación del paciente
        creation_date = patient.created_at
        
        # Alergias (0-3)
        num_allergies = random.choices([0, 1, 2, 3], weights=[30, 40, 20, 10])[0]
        allergies_list = []
        if num_allergies > 0:
            selected_allergies = random.sample(ALLERGIES, num_allergies)
            for allergy in selected_allergies:
                allergies_list.append({
                    'allergen': allergy,
                    'severity': random.choice(['leve', 'moderada', 'severa']),
                    'reaction': random.choice(['Rash cutáneo', 'Dificultad respiratoria', 'Edema', 'Anafilaxia'])
                })
        
        # Condiciones crónicas (0-2)
        num_conditions = random.choices([0, 1, 2], weights=[50, 35, 15])[0]
        chronic_conditions_list = random.sample(CHRONIC_CONDITIONS, num_conditions) if num_conditions > 0 else []
        
        # Medicamentos actuales (0-4)
        num_meds = random.choices([0, 1, 2, 3, 4], weights=[40, 30, 15, 10, 5])[0]
        medications_list = random.sample(MEDICATIONS, num_meds) if num_meds > 0 else []
        
        record = ClinicalRecord(
            tenant=tenant,
            patient=patient,
            status='active',
            blood_type=random.choice(BLOOD_TYPES),
            allergies=allergies_list,
            chronic_conditions=chronic_conditions_list,
            medications=medications_list,
            family_history=fake.text(max_nb_chars=150) if random.random() > 0.5 else '',
            social_history=f"No fuma. {'Consume alcohol ocasionalmente' if random.random() > 0.6 else 'No consume alcohol'}. {random.choice(['Actividad física regular', 'Sedentario', 'Actividad moderada'])}.",
            created_by=random.choice(doctors),
            created_at=creation_date,
            updated_at=creation_date
        )
        record.save()
        records.append(record)

        if (i + 1) % 100 == 0:
            print(f"    ⏳ {i + 1}/{len(patients)} historias clínicas creadas...")

    print(f"    ✅ {len(records)} historias clínicas creadas")
    return records


# ============================================================================
# PASO 8: CREAR FORMULARIOS CLÍNICOS (1-3 por paciente)
# ============================================================================

def create_clinical_forms(tenant, clinical_records, doctors):
    """Crea 1-3 formularios por historia clínica"""
    print(f"\n  📝 Creando formularios clínicos para {tenant.name}...")

    set_current_tenant(tenant)

    forms_created = 0
    for record in clinical_records:
        # Fecha base: después de la creación de la historia
        base_date = record.created_at
        
        # Número de formularios por paciente (1-3)
        num_forms = random.randint(1, 3)
        
        for j in range(num_forms):
            # Calcular cuántos días pueden pasar sin exceder END_DATE
            max_days_forward = (END_DATE - base_date.replace(tzinfo=None)).days
            if max_days_forward <= 0:
                # Si ya estamos en o después de END_DATE, usar la misma fecha base
                days_after = 0
            else:
                # Generar días aleatorios dentro del rango válido (1 a 90 días max)
                days_after = random.randint(1, min(90, max_days_forward))
            
            form_date = base_date + timedelta(days=days_after)
            
            # USAR TODOS LOS TIPOS DE FORMULARIO DEL BACKEND (10 tipos)
            form_type = random.choice([
                'triage', 'consultation', 'evolution', 'prescription', 
                'lab_order', 'imaging_order', 'procedure', 'discharge', 
                'referral', 'other'
            ])
            
            if form_type == 'consultation':
                form_data = {
                    'subjective': {
                        'chief_complaint': random.choice([
                            'Dolor abdominal de 2 días de evolución',
                            'Fiebre y malestar general',
                            'Cefalea intensa',
                            'Tos productiva',
                            'Control de rutina'
                        ]),
                        'history_present_illness': fake.text(max_nb_chars=150)
                    },
                    'assessment': {
                        'diagnoses': [{
                            'code': f'J{random.randint(10, 99)}.{random.randint(0, 9)}',
                            'description': random.choice(COMMON_DIAGNOSES),
                            'type': 'principal'
                        }]
                    },
                    'plan': {
                        'follow_up': random.choice(['Control en 7 días', 'Control en 15 días', 'SOS'])
                    }
                }
            elif form_type == 'prescription':
                selected_meds = random.sample(MEDICATIONS, random.randint(1, 2))
                form_data = {
                    'medications': [
                        {
                            **med,
                            'duration': f'{random.randint(5, 14)} días',
                            'quantity': random.randint(10, 30)
                        }
                        for med in selected_meds
                    ],
                    'diagnosis': random.choice(COMMON_DIAGNOSES)
                }
            elif form_type == 'lab_order':
                lab_tests = ['Hemograma', 'Glucemia', 'Perfil lipídico', 'Creatinina', 'Orina completa']
                form_data = {
                    'tests': random.sample(lab_tests, random.randint(2, 4)),
                    'urgency': random.choice(['routine', 'urgent'])
                }
            elif form_type == 'triage':
                form_data = {
                    'vital_signs': {
                        'temperature': round(random.uniform(36.0, 37.5), 1),
                        'blood_pressure_systolic': random.randint(100, 140),
                        'blood_pressure_diastolic': random.randint(60, 90),
                        'heart_rate': random.randint(60, 100)
                    },
                    'chief_complaint': random.choice(['Dolor de cabeza', 'Fiebre', 'Dolor abdominal'])
                }
            elif form_type == 'evolution':
                form_data = {
                    'evolution_note': fake.text(max_nb_chars=200),
                    'vital_signs': {
                        'temperature': round(random.uniform(36.0, 37.5), 1),
                        'blood_pressure': f'{random.randint(100, 140)}/{random.randint(60, 90)}'
                    }
                }
            elif form_type == 'imaging_order':
                form_data = {
                    'study_type': random.choice(['Radiografía de tórax', 'Ecografía abdominal', 'Tomografía']),
                    'clinical_indication': random.choice(COMMON_DIAGNOSES)
                }
            elif form_type == 'procedure':
                form_data = {
                    'procedure_name': random.choice(['Sutura', 'Curación', 'Drenaje']),
                    'description': fake.text(max_nb_chars=100)
                }
            elif form_type == 'discharge':
                form_data = {
                    'discharge_diagnosis': random.choice(COMMON_DIAGNOSES),
                    'instructions': 'Reposo relativo, continuar medicación'
                }
            elif form_type == 'referral':
                form_data = {
                    'referred_to': random.choice(SPECIALTIES),
                    'reason': random.choice(COMMON_DIAGNOSES)
                }
            else:  # other
                form_data = {
                    'notes': fake.text(max_nb_chars=150)
                }
            
            form = ClinicalForm(
                tenant=tenant,
                clinical_record=record,
                form_type=form_type,
                form_data=form_data,
                doctor_name=random.choice(doctors).get_full_name() if random.random() > 0.3 else '',
                doctor_specialty=random.choice(SPECIALTIES),
                filled_by=random.choice(doctors),
                form_date=form_date,
                created_at=form_date,
                updated_at=form_date
            )
            form.save()
            forms_created += 1

        if (clinical_records.index(record) + 1) % 100 == 0:
            print(f"    ⏳ {clinical_records.index(record) + 1}/{len(clinical_records)} procesados...")

    print(f"    ✅ {forms_created} formularios clínicos creados")
    return forms_created


# ============================================================================
# PASO 9: CREAR DOCUMENTOS CLÍNICOS (1-3 por paciente)
# ============================================================================

def create_clinical_documents(tenant, clinical_records, doctors):
    """Crea 1-3 documentos por historia clínica"""
    print(f"\n  📄 Creando documentos clínicos para {tenant.name}...")

    set_current_tenant(tenant)

    documents_created = 0
    for record in clinical_records:
        base_date = record.created_at
        
        num_docs = random.randint(1, 3)
        
        for j in range(num_docs):
            # Calcular cuántos días pueden pasar sin exceder END_DATE
            max_days_forward = (END_DATE - base_date.replace(tzinfo=None)).days
            if max_days_forward <= 7:
                # Si quedan menos de 7 días, usar fecha base + 1 día
                days_after = random.randint(1, max(1, max_days_forward))
            else:
                # Generar días aleatorios (7 a 90 días después, dentro del rango)
                days_after = random.randint(7, min(90, max_days_forward))
            
            doc_date = base_date + timedelta(days=days_after)
            
            # USAR TODOS LOS TIPOS DE DOCUMENTO DEL BACKEND (9 tipos)
            doc_type = random.choice([
                'consultation', 'lab_result', 'imaging_report', 'prescription',
                'surgical_note', 'discharge_summary', 'consent_form', 
                'progress_note', 'referral'
            ])
            
            doctor = random.choice(doctors)
            
            if doc_type == 'lab_result':
                title = f"Resultados de Laboratorio - {random.choice(['Hemograma', 'Bioquímica', 'Orina'])}"
                content = {
                    'test_type': random.choice(['Hemograma completo', 'Perfil lipídico', 'Glucemia']),
                    'results': {
                        'hemoglobin': f'{random.uniform(12, 16):.1f} g/dL',
                        'glucose': f'{random.randint(70, 120)} mg/dL',
                        'cholesterol': f'{random.randint(150, 220)} mg/dL'
                    },
                    'interpretation': 'Valores dentro de rangos normales'
                }
            elif doc_type == 'imaging_report':
                title = f"Informe de {random.choice(['Radiografía', 'Ecografía', 'Tomografía'])}"
                content = {
                    'study_type': random.choice(['Radiografía de tórax', 'Ecografía abdominal']),
                    'findings': 'Sin hallazgos patológicos significativos',
                    'conclusion': 'Estudio normal'
                }
            elif doc_type == 'prescription':
                title = f"Receta Médica - {doc_date.strftime('%d/%m/%Y')}"
                selected_meds = random.sample(MEDICATIONS, random.randint(1, 3))
                content = {
                    'medications': selected_meds,
                    'diagnosis': random.choice(COMMON_DIAGNOSES)
                }
            elif doc_type == 'surgical_note':
                title = f"Nota Quirúrgica - {random.choice(['Apendicectomía', 'Colecistectomía', 'Herniorrafia'])}"
                content = {
                    'procedure': random.choice(['Apendicectomía laparoscópica', 'Colecistectomía']),
                    'surgeon': doctor.get_full_name(),
                    'findings': 'Procedimiento sin complicaciones',
                    'complications': 'Ninguna'
                }
            elif doc_type == 'discharge_summary':
                title = f"Resumen de Alta - {doc_date.strftime('%d/%m/%Y')}"
                content = {
                    'admission_date': (doc_date - timedelta(days=random.randint(1, 7))).strftime('%Y-%m-%d'),
                    'discharge_date': doc_date.strftime('%Y-%m-%d'),
                    'discharge_diagnosis': random.choice(COMMON_DIAGNOSES),
                    'treatment_summary': 'Tratamiento médico completado satisfactoriamente',
                    'follow_up': 'Control en 15 días'
                }
            elif doc_type == 'consent_form':
                title = f"Consentimiento Informado - {random.choice(['Procedimiento', 'Cirugía', 'Tratamiento'])}"
                content = {
                    'procedure_type': random.choice(['Cirugía menor', 'Procedimiento diagnóstico']),
                    'risks_explained': True,
                    'patient_consent': True,
                    'witness_name': f"{random.choice(BOLIVIAN_FIRST_NAMES_M)} {random.choice(BOLIVIAN_LAST_NAMES)}"
                }
            elif doc_type == 'progress_note':
                title = f"Nota de Evolución - {doc_date.strftime('%d/%m/%Y')}"
                content = {
                    'subjective': 'Paciente refiere mejoría de síntomas',
                    'objective': f'TA: {random.randint(100, 140)}/{random.randint(60, 90)} mmHg, FC: {random.randint(60, 100)} lpm',
                    'assessment': 'Evolución favorable',
                    'plan': 'Continuar tratamiento actual'
                }
            elif doc_type == 'referral':
                title = f"Referencia a {random.choice(SPECIALTIES)}"
                content = {
                    'referred_to': random.choice(SPECIALTIES),
                    'reason': random.choice(COMMON_DIAGNOSES),
                    'urgency': random.choice(['Rutina', 'Urgente']),
                    'summary': fake.text(max_nb_chars=100)
                }
            else:  # consultation
                title = f"Consulta Médica - {doc_date.strftime('%d/%m/%Y')}"
                content = {
                    'diagnosis': random.choice(COMMON_DIAGNOSES),
                    'treatment': 'Tratamiento sintomático',
                    'follow_up': 'Control en 15 días'
                }
            
            document = ClinicalDocument(
                tenant=tenant,
                clinical_record=record,
                document_type=doc_type,
                title=title,
                description=f"Documento generado en consulta del {doc_date.strftime('%d/%m/%Y')}",
                document_date=doc_date,
                specialty=doctor.specialty if hasattr(doctor, 'specialty') and doctor.specialty else random.choice(SPECIALTIES),
                doctor_name=doctor.get_full_name(),
                doctor_license=doctor.professional_id if hasattr(doctor, 'professional_id') else f'MP-{random.randint(1000, 9999)}',
                content=content,
                file_name=f"{doc_type}_{record.record_number}_{j+1}.pdf",
                file_size_bytes=random.randint(50000, 500000),
                mime_type='application/pdf',
                ocr_processed=random.choice([True, False]),
                ocr_confidence=Decimal(str(random.uniform(85, 99))) if random.random() > 0.5 else None,
                is_signed=random.choice([True, False]),
                is_locked=random.choice([True, False]),
                created_by=doctor,
                created_at=doc_date,
                updated_at=doc_date
            )
            document.save()
            documents_created += 1

        if (clinical_records.index(record) + 1) % 100 == 0:
            print(f"    ⏳ {clinical_records.index(record) + 1}/{len(clinical_records)} procesados...")

    print(f"    ✅ {documents_created} documentos clínicos creados")
    return documents_created


# ============================================================================
# PASO 10: CREAR PLANTILLAS DE REPORTES
# ============================================================================

def create_report_templates(tenant):
    """Crea plantillas de reportes por defecto"""
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
# PASO 11: RESUMEN Y ESTADÍSTICAS
# ============================================================================

def show_summary():
    """Muestra resumen completo con estadísticas"""
    print("\n" + "="*80)
    print("📊 RESUMEN Y ESTADÍSTICAS FINALES")
    print("="*80)

    print("\n🔐 SUPERUSUARIO:")
    print("  Email: superadmin@clinidocs.com")
    print("  Password: Password123!")

    print("\n📦 PLANES DE SUSCRIPCIÓN:")
    plans = SubscriptionPlan.objects.all()
    for plan in plans:
        print(f"  - {plan.name}: {plan.storage_gb}GB - ${plan.monthly_price}/mes")

    print("\n🏥 TENANTS:")
    tenants = Tenant.objects.all()
    for tenant in tenants:
        print(f"\n  📍 {tenant.name} ({tenant.subdomain})")
        print(f"     Plan: {tenant.subscription_plan} ({tenant.max_storage_gb}GB)")
        
        set_current_tenant(tenant)
        
        users = User.objects.filter(tenant=tenant)
        admins = users.filter(role__name=SystemRoles.ADMIN_TI)
        doctors = users.filter(role__name='Doctor')
        patients_count = Patient.objects.filter(tenant=tenant).count()
        records_count = ClinicalRecord.objects.filter(tenant=tenant).count()
        forms_count = ClinicalForm.objects.filter(tenant=tenant).count()
        docs_count = ClinicalDocument.objects.filter(tenant=tenant).count()
        
        print(f"     👥 Usuarios:")
        print(f"        - Administradores TI: {admins.count()}")
        for admin in admins:
            print(f"          • {admin.email} (Password: Password123!)")
        print(f"        - Doctores: {doctors.count()}")
        for doctor in doctors:
            print(f"          • {doctor.email} - {doctor.specialty} (Password: Password123!)")
        
        print(f"     📋 Datos:")
        print(f"        - Pacientes: {patients_count}")
        print(f"        - Historias Clínicas: {records_count}")
        print(f"        - Formularios Clínicos: {forms_count}")
        print(f"        - Documentos Clínicos: {docs_count}")

    print("\n" + "="*80)
    print("✅ SEEDER COMPLETADO EXITOSAMENTE")
    print("="*80)
    print("\n💡 Puedes ingresar con cualquiera de los emails mostrados arriba")
    print("   Password para todos: Password123!")
    print("   Superusuario: Password123!\n")


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Ejecuta todo el seeder"""
    print("\n" + "🚀"*40)
    print("MEGA SEEDER - Iniciando creación de datos...")
    print("🚀"*40)

    start_time = datetime.now()

    # 1. Superusuario
    superuser = create_superuser()

    # 2. Planes de suscripción
    plans = create_subscription_plans()

    # 3. Tenants
    tenants = create_tenants()

    # 4-10. Procesar cada tenant
    for tenant in tenants:
        print(f"\n{'='*80}")
        print(f"🏥 PROCESANDO TENANT: {tenant.name}")
        print(f"{'='*80}")

        # 4. Permisos y roles
        roles = create_permissions_and_roles(tenant)

        # 5. Usuarios (2 Admins + 5 Doctores)
        users = create_users(tenant, roles)
        doctors = [u for u in users if u.role.name == 'Doctor']
        all_creators = [u for u in users if u.role.name in [SystemRoles.ADMIN_TI, 'Doctor']]

        # 6. 500 Pacientes
        patients = create_patients(tenant, all_creators, count=500)

        # 7. 500 Historias clínicas
        clinical_records = create_clinical_records(tenant, patients, doctors)

        # 8. Formularios clínicos (1-3 por paciente)
        create_clinical_forms(tenant, clinical_records, doctors)

        # 9. Documentos clínicos (1-3 por paciente)
        create_clinical_documents(tenant, clinical_records, doctors)

        # 10. Plantillas de reportes
        create_report_templates(tenant)

    # 11. Resumen final
    show_summary()

    end_time = datetime.now()
    duration = end_time - start_time

    print(f"\n⏱️  Tiempo total de ejecución: {duration}")
    print(f"✅ ¡Seeder completado exitosamente!\n")


if __name__ == '__main__':
    main()
