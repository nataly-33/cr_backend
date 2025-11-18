"""
Script para probar los reportes dinámicos con JOINs
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
import json


def test_clinical_record_report():
    """Test clinical record report with patient info"""
    print("\n" + "="*80)
    print("TESTING CLINICAL RECORD REPORT WITH PATIENT INFO")
    print("="*80)
    
    tenant = Tenant.objects.first()
    if not tenant:
        print("❌ No tenant found")
        return
    
    builder = DynamicReportBuilder(tenant)
    
    # Build query with all fields
    result = builder.build_query(
        model_name='clinical_record',
        fields=None,  # Get all fields
        order_by='-created_at',
        limit=5
    )
    
    print(f"\n✅ Total records: {result['total_records']}")
    print(f"✅ Fields returned: {len(result['fields'])}")
    print(f"✅ Fields: {', '.join(result['fields'])}")
    
    if result['data']:
        print("\n📋 First record:")
        first_record = result['data'][0]
        for key, value in first_record.items():
            print(f"  - {key}: {value}")
    
    return result


def test_clinical_form_report():
    """Test clinical form report with patient and clinical record info"""
    print("\n" + "="*80)
    print("TESTING CLINICAL FORM REPORT WITH PATIENT & RECORD INFO")
    print("="*80)
    
    tenant = Tenant.objects.first()
    if not tenant:
        print("❌ No tenant found")
        return
    
    builder = DynamicReportBuilder(tenant)
    
    result = builder.build_query(
        model_name='clinical_form',
        fields=None,
        order_by='-created_at',
        limit=5
    )
    
    print(f"\n✅ Total records: {result['total_records']}")
    print(f"✅ Fields returned: {len(result['fields'])}")
    print(f"✅ Fields: {', '.join(result['fields'])}")
    
    if result['data']:
        print("\n📋 First record:")
        first_record = result['data'][0]
        for key, value in first_record.items():
            print(f"  - {key}: {value}")
    
    return result


def test_document_report():
    """Test document report with patient and clinical record info"""
    print("\n" + "="*80)
    print("TESTING DOCUMENT REPORT WITH PATIENT & RECORD INFO")
    print("="*80)
    
    tenant = Tenant.objects.first()
    if not tenant:
        print("❌ No tenant found")
        return
    
    builder = DynamicReportBuilder(tenant)
    
    result = builder.build_query(
        model_name='document',
        fields=None,
        order_by='-created_at',
        limit=5
    )
    
    print(f"\n✅ Total records: {result['total_records']}")
    print(f"✅ Fields returned: {len(result['fields'])}")
    print(f"✅ Fields: {', '.join(result['fields'])}")
    
    if result['data']:
        print("\n📋 First record:")
        first_record = result['data'][0]
        for key, value in first_record.items():
            print(f"  - {key}: {value}")
    
    return result


def test_user_report():
    """Test user report with tenant info"""
    print("\n" + "="*80)
    print("TESTING USER REPORT WITH TENANT INFO")
    print("="*80)
    
    tenant = Tenant.objects.first()
    if not tenant:
        print("❌ No tenant found")
        return
    
    builder = DynamicReportBuilder(tenant)
    
    result = builder.build_query(
        model_name='user',
        fields=None,
        order_by='-created_at',
        limit=5
    )
    
    print(f"\n✅ Total records: {result['total_records']}")
    print(f"✅ Fields returned: {len(result['fields'])}")
    print(f"✅ Fields: {', '.join(result['fields'])}")
    
    if result['data']:
        print("\n📋 First record:")
        first_record = result['data'][0]
        for key, value in first_record.items():
            print(f"  - {key}: {value}")
    
    return result


def test_all():
    """Run all tests"""
    print("\n🚀 STARTING DYNAMIC REPORTS WITH JOINS TESTS")
    print("="*80)
    
    try:
        test_clinical_record_report()
        test_clinical_form_report()
        test_document_report()
        test_user_report()
        
        print("\n" + "="*80)
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY!")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    test_all()
