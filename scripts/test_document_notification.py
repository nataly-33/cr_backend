#!/usr/bin/env python
"""
Script para probar notificación usando evento de documento.

Uso:
    python scripts/test_document_notification.py
"""
import os
import sys
import django
import uuid

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

# Cargar variables de entorno desde .env
from dotenv import load_dotenv
load_dotenv()

from django.db import transaction
from apps.accounts.models import User
from apps.patients.models import Patient
from apps.notifications.orchestrator import NotificationOrchestrator

def send_test():
    print("=" * 80)
    print("📱 ENVIANDO NOTIFICACIÓN DE DOCUMENTO DE PRUEBA")
    print("=" * 80)
    
    # Obtener usuario admin y doctor
    admin_user = User.objects.get(email='admin@clinica-lapaz.com')
    doctor_user = User.objects.filter(
        role__name__icontains='Doctor',
        tenant=admin_user.tenant
    ).first()
    
    if not doctor_user:
        print("\n❌ No hay doctores en el sistema")
        return
    
    # Obtener un paciente
    patient = Patient.objects.filter(tenant=admin_user.tenant).first()
    
    if not patient:
        print("\n❌ No hay pacientes en el sistema")
        return
    
    print(f"\n✅ Admin: {admin_user.full_name}")
    print(f"   Token FCM: {admin_user.fcm_token[:50] if admin_user.fcm_token else 'None'}...")
    print(f"\n✅ Doctor: {doctor_user.full_name}")
    print(f"\n✅ Paciente: {patient.first_name} {patient.last_name}")
    
    if not admin_user.fcm_token:
        print("\n❌ Usuario admin no tiene token FCM")
        return
    
    # Crear orquestador
    orchestrator = NotificationOrchestrator(admin_user.tenant)
    
    # Simular evento de documento creado
    print("\n📤 Enviando notificación de documento...")
    
    # Ejecutar dentro de una transacción para que on_commit funcione
    with transaction.atomic():
        result = orchestrator.process_event(
            event_type='document.uploaded',
            event_id=f'test_{uuid.uuid4()}',
            actor_id=str(doctor_user.id),  # Convertir UUID a string
            data={
                'document_id': str(uuid.uuid4()),
                'document_name': 'Documento de Prueba.pdf',
                'document_type': 'test',
                'patient_id': str(patient.id),  # Convertir UUID a string
                'patient_name': f'{patient.first_name} {patient.last_name}',
                'doctor_id': str(doctor_user.id),  # Convertir UUID a string
                'doctor_name': doctor_user.full_name,
                'uploaded_by': doctor_user.full_name,
            },
            channels=['push', 'in_app']
        )
    
    print(f"\n✅ Resultado:")
    print(f"   Success: {result['success']}")
    print(f"   Notificaciones creadas: {result['notifications_created']}")
    print(f"   Notificaciones omitidas: {result['notifications_skipped']}")
    
    if result['errors']:
        print(f"   Errores: {result['errors']}")
    
    print("\n   Verifica tu celular en los próximos segundos.")
    print("   También verifica los logs de Celery Worker para ver el envío.")
    print("=" * 80)

if __name__ == '__main__':
    send_test()
