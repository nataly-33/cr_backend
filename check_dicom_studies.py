"""
Script para verificar estudios DICOM en la base de datos.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.dicom.models import DicomStudy
from apps.core.models import Tenant

# Obtener todos los estudios
all_studies = DicomStudy.objects.all()
print(f"\n=== Total de estudios DICOM en la BD: {all_studies.count()} ===\n")

for study in all_studies:
    print(f"ID: {study.id}")
    print(f"Tenant: {study.tenant.name if study.tenant else 'Sin tenant'}")
    print(f"Study UID: {study.study_instance_uid}")
    print(f"Descripción: {study.study_description}")
    print(f"Modalidad: {study.modality}")
    print(f"Paciente: {study.patient.get_full_name() if study.patient else 'Sin paciente'}")
    print(f"Series: {study.series_count}")
    print(f"Instancias: {study.instances_count}")
    print("-" * 70)

# Verificar tenants
print("\n=== Tenants en la BD ===")
for tenant in Tenant.objects.all():
    print(f"ID: {tenant.id} - Nombre: {tenant.name}")
    studies_count = DicomStudy.objects.filter(tenant=tenant).count()
    print(f"  Estudios DICOM: {studies_count}")
