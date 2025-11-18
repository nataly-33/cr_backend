"""
Script para probar la exportación a Excel
"""
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.reports.dynamic_reports_service import DynamicReportBuilder
from apps.core.models import Tenant


def test_excel_export():
    """Test exportación a Excel"""
    print("\n" + "="*80)
    print("TESTING EXCEL EXPORT")
    print("="*80)
    
    tenant = Tenant.objects.first()
    if not tenant:
        print("❌ No tenant found")
        return
    
    builder = DynamicReportBuilder(tenant)
    
    # Generar reporte de usuarios
    result = builder.build_query(
        model_name='user',
        fields=['email', 'first_name', 'last_name', 'specialty', 'tenant_name'],
        order_by='-created_at',
        limit=10
    )
    
    print(f"\n✅ Query ejecutado: {result['total_records']} records")
    print(f"✅ Campos: {result['fields']}")
    
    # Exportar a Excel
    try:
        excel_content = builder.export_report(
            report_data=result,
            format_type='excel',
            title='Reporte de Usuarios',
            metadata={'generated_by': 'Test Script', 'date': '2024-11-18'}
        )
        
        # Guardar archivo de prueba
        output_path = 'test_report.xlsx'
        with open(output_path, 'wb') as f:
            f.write(excel_content)
        
        print(f"\n✅ Excel generado exitosamente!")
        print(f"✅ Archivo guardado: {output_path}")
        print(f"✅ Tamaño: {len(excel_content)} bytes")
        
    except Exception as e:
        print(f"\n❌ ERROR al generar Excel: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*80)


if __name__ == '__main__':
    test_excel_export()
