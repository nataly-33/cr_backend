import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.core.models import Tenant
from apps.reports.models import ReportTemplate

def seed_report_templates():
    """Crea plantillas de reportes por defecto"""
    
    tenants = Tenant.objects.all()
    
    templates = [
        {
            'name': 'Documentos por Tipo',
            'description': 'Reporte estadístico de documentos agrupados por tipo',
            'report_type': 'documents_by_type',
            'default_format': 'pdf',
        },
        {
            'name': 'Resumen de Pacientes',
            'description': 'Estadísticas generales de pacientes',
            'report_type': 'patients_summary',
            'default_format': 'pdf',
        },
        {
            'name': 'Registro de Actividad',
            'description': 'Log de actividades del sistema',
            'report_type': 'activity_log',
            'default_format': 'excel',
        },
        {
            'name': 'Estadísticas de Uso',
            'description': 'Métricas de uso del sistema',
            'report_type': 'usage_statistics',
            'default_format': 'excel',
        },
    ]
    
    for tenant in tenants:
        print(f"\n🏥 Creando templates de reportes para {tenant.name}...")
        
        for template_data in templates:
            template, created = ReportTemplate.objects.get_or_create(
                tenant=tenant,
                report_type=template_data['report_type'],
                defaults=template_data
            )
            
            if created:
                print(f"  ✅ {template.name}")
            else:
                print(f"  ⏭️  {template.name} (ya existe)")

if __name__ == '__main__':
    print("🌱 Seeding plantillas de reportes...")
    seed_report_templates()
    print("\n✅ Seed completado!")