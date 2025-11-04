import os
import sys
import django
from pathlib import Path

# Setup Django
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

import pandas as pd
import numpy as np
from faker import Faker
from datetime import datetime, timedelta
from django.utils import timezone
from django.utils.text import slugify

from apps.core.models import Tenant, set_current_tenant
from apps.accounts.models import User, Role, Permission
from apps.patients.models import Patient
from apps.clinical_records.models import ClinicalRecord

fake = Faker('es_ES')
Faker.seed(42)
np.random.seed(42)


def create_superuser():
    """
    Crea el superusuario ASU (Admin Super Usuario) que puede ver todos los tenants.
    Este usuario NO pertenece a ningún tenant específico.
    """
    print("[+] Creando Super Usuario (ASU)...")
    
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


def create_tenants():
    """Crea 2 tenants de prueba"""
    print("[+] Creando tenants...")
    
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


def create_permissions_and_roles(tenant):
    """
    Crea permisos y roles para un tenant según RBAC definido.
    
    Roles del sistema:
    - Administrador TI: Gestión completa del tenant (usuarios, roles, pacientes, historias, etc.)
    - Doctor: CRUD completo de historias clínicas y documentos
    - Paciente: Solo lectura de SU propia historia clínica
    - Enfermera: Lectura y actualización (sin crear/eliminar)
    """
    print(f"  🔐 Creando permisos y roles para {tenant.name}...")
    
    set_current_tenant(tenant)
    
    # Definir recursos y acciones
    resources = ['patient', 'clinical_record', 'document', 'user', 'role', 'report', 'audit', 'notification']
    actions = ['create', 'read', 'update', 'delete', 'export', 'sign', 'manage']
    
    permissions = []
    permissions_dict = {}
    
    # Crear TODOS los permisos posibles
    for resource in resources:
        for action in actions:
            # No todos los recursos tienen todas las acciones
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
        'Administrador TI': {
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
            ]
        },
        'Paciente': {
            'description': 'Paciente con acceso solo a SU propia historia clínica (solo lectura)',
            'is_system_role': False,
            'permissions': [
                # Solo lectura de su historia clínica
                # La validación de "solo la suya" se hace en el ViewSet con has_object_permission
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


def create_users(tenant, roles):
    """
    Crea usuarios de prueba para un tenant.
    
    Usuarios por tenant:
    - 1 Administrador TI (gestión completa del tenant)
    - 2 Doctores (CRUD de historias clínicas)
    - 1 Enfermera (lectura y actualización)
    - 1 Administrativo (gestión de pacientes)
    - 2 Pacientes (solo ven su historia clínica)
    """
    print(f"  👥 Creando usuarios para {tenant.name}...")
    
    set_current_tenant(tenant)
    
    users_data = [
        {
            'email': f'admin@{tenant.subdomain}.com',
            'first_name': 'Juan',
            'last_name': 'Pérez',
            'role': roles['Administrador TI'],
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


def create_patients(tenant, count=50):
    """Crea pacientes de prueba usando Pandas"""
    print(f"  🏥 Creando {count} pacientes para {tenant.name}...")
    
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


def create_clinical_records(tenant, patients):
    """Crea historias clínicas para los pacientes"""
    print(f"  📋 Creando historias clínicas para {tenant.name}...")
    
    set_current_tenant(tenant)
    
    records = []
    for i, patient in enumerate(patients):
        record, created = ClinicalRecord.objects.get_or_create(
            tenant=tenant,
            patient=patient,
            defaults={
                'record_number': f'HC-2024-{str(i+1).zfill(6)}',
                'status': 'active',
                'blood_type': np.random.choice(['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']),
                'allergies': [],
                'chronic_conditions': [],
                'medications': [],
            }
        )
        records.append(record)
    
    print(f"    ✅ {len(records)} historias clínicas creadas")
    return records

def create_sample_documents(tenant, clinical_records):
    """Crea documentos de ejemplo para las historias clínicas"""
    print(f"  📄 Creando documentos de ejemplo para {tenant.name}...")
    
    set_current_tenant(tenant)
    
    from apps.documents.models import ClinicalDocument
    from datetime import datetime, timedelta
    
    document_types = [
        'consultation', 'lab_result', 'imaging_report', 
        'prescription', 'progress_note'
    ]
    
    specialties = ['Cardiología', 'Pediatría', 'Medicina General', 'Neurología']
    
    documents_created = 0
    
    # Crear 2-3 documentos por historia clínica (sample)
    for record in clinical_records[:10]:  # Solo las primeras 10 historias
        num_docs = np.random.randint(2, 4)
        
        for i in range(num_docs):
            doc_type = np.random.choice(document_types)
            specialty = np.random.choice(specialties)
            
            ClinicalDocument.objects.create(
                tenant=tenant,
                clinical_record=record,
                document_type=doc_type,
                title=f"{doc_type.replace('_', ' ').title()} - {fake.catch_phrase()}",
                description=fake.text(max_nb_chars=200),
                document_date=timezone.now() - timedelta(days=np.random.randint(1, 365)),
                specialty=specialty,
                doctor_name=fake.name(),
                doctor_license=f"MED-{fake.random_number(digits=6)}",
                content={
                    'notes': fake.text(max_nb_chars=500),
                    'diagnosis': fake.sentence()
                },
                tags=[specialty.lower(), doc_type],
                created_by=tenant.users.first()
            )
            documents_created += 1
    
    print(f"    ✅ {documents_created} documentos creados")
    return documents_created

def main():
    """Función principal del seeder"""
    print("\n" + "="*60)
    print("🌱 INICIANDO SEEDER DE DATOS DE PRUEBA")
    print("="*60 + "\n")
    
    # 0. Crear superusuario ASU (Admin Super Usuario)
    superuser = create_superuser()
    
    # 1. Crear tenants
    tenants = create_tenants()
    
    # 2. Para cada tenant, crear permisos, roles, usuarios y pacientes
    for tenant in tenants:
        print(f"\n📦 Configurando: {tenant.name}")
        print("-" * 60)
        
        # Permisos y roles
        roles = create_permissions_and_roles(tenant)
        
        # Usuarios
        users = create_users(tenant, roles)
        
        # Pacientes
        patients_count = 50 if tenant.subscription_plan == 'pro' else 20
        patients = create_patients(tenant, count=patients_count)
        
        # Historias clínicas
        records = create_clinical_records(tenant, patients)
        docs_count = create_sample_documents(tenant, records)

    print("\n" + "="*60)
    print("✅ SEEDER COMPLETADO EXITOSAMENTE")
    print("="*60)
    # Mostrar totales globales: limpiar el tenant actual para que los managers
    # basados en tenant no filtren por el último tenant usado en el seeder.
    set_current_tenant(None)
    print("\n📊 Resumen:")
    print(f"  • Tenants: {len(tenants)}")
    print(f"  • Usuarios totales: {User.objects.count()}")
    print(f"  • Pacientes totales: {Patient.objects.count()}")
    print(f"  • Historias clínicas: {ClinicalRecord.objects.count()}")
    
    print("\n🔑 Credenciales de acceso:")
    
    print("\n  🌟 SUPERUSUARIO (ASU - Acceso a todos los tenants):")
    print(f"    • Email: superadmin@clinidocs.com")
    print(f"    • Password: SuperAdmin123!")
    print(f"    • Puede ver información de TODOS los tenants")
    
    for tenant in tenants:
        print(f"\n  {tenant.name}:")
        print(f"    • URL: http://{tenant.subdomain}.localhost:8000")
        print(f"    • Administrador TI: admin@{tenant.subdomain}.com")
        print(f"    • Doctor: doctor1@{tenant.subdomain}.com")
        print(f"    • Paciente: paciente1@{tenant.subdomain}.com")
        print(f"    • Password (todos): Password123!")
    
    print("\n📝 Sistema de Permisos RBAC:")
    print("  • Administrador TI: Gestión completa del tenant")
    print("  • Doctor: CRUD completo de historias clínicas")
    print("  • Paciente: Solo lectura de SU historia clínica")
    print()



if __name__ == '__main__':
    main()