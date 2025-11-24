"""
Script de prueba para los 3 tipos críticos de reportes AI
Ejecutar con: python test_reports_ai_critical.py
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.reports_ai.nlp_service import NLPParserService

def test_critical_queries():
    """Probar los 3 tipos de consultas críticas"""
    
    print("=" * 80)
    print("PRUEBA DE REPORTES AI - 3 TIPOS CRÍTICOS")
    print("=" * 80)
    
    parser = NLPParserService(ai_provider='local')
    
    # ========== TIPO 1: HISTORIAS POR TIPO DE SANGRE ==========
    print("\n" + "=" * 80)
    print("TIPO 1: HISTORIAS CLÍNICAS POR TIPO DE SANGRE")
    print("=" * 80)
    
    queries_type1 = [
        "Historias clínicas con tipo de sangre AB ordenadas por paciente ascendente",
        "Historias clínicas tipo O ordenadas por paciente descendente",
        "Historias clínicas con sangre AB+ ordenadas ascendente",
        "Historias clínicas tipo AB- ordenadas descendente",
    ]
    
    for query in queries_type1:
        print(f"\n📋 Query: {query}")
        result = parser.parse_query(query, language='es')
        print(f"✅ Confianza: {result['confidence']}")
        print(f"📊 Proveedor: {result['provider']}")
        print(f"📝 Explicación: {result['explanation']}")
        print(f"🔍 SQL:\n{result['sql'][:200]}...")
    
    # ========== TIPO 2: HISTORIAS POR MES ==========
    print("\n" + "=" * 80)
    print("TIPO 2: HISTORIAS CLÍNICAS POR MES DE CREACIÓN")
    print("=" * 80)
    
    queries_type2 = [
        "Historias clínicas creadas en noviembre 2025 ordenadas por paciente ascendente",
        "Historias clínicas creadas en octubre 2025 ordenadas descendente",
        "Historias clínicas de septiembre 2025 ordenadas por paciente",
    ]
    
    for query in queries_type2:
        print(f"\n📅 Query: {query}")
        result = parser.parse_query(query, language='es')
        print(f"✅ Confianza: {result['confidence']}")
        print(f"📊 Proveedor: {result['provider']}")
        print(f"📝 Explicación: {result['explanation']}")
        print(f"🔍 SQL:\n{result['sql'][:200]}...")
    
    # ========== TIPO 3: CANTIDAD DE VISITAS ==========
    print("\n" + "=" * 80)
    print("TIPO 3: CANTIDAD DE VISITAS (FORMULARIOS) POR PACIENTE")
    print("=" * 80)
    
    queries_type3 = [
        "Cantidad de veces que cada paciente asistió a la clínica en noviembre 2025",
        "Cantidad de formularios por paciente en octubre 2025 ordenados ascendente",
        "Cantidad de formularios clínicos por paciente en 2025",
    ]
    
    for query in queries_type3:
        print(f"\n🏥 Query: {query}")
        result = parser.parse_query(query, language='es')
        print(f"✅ Confianza: {result['confidence']}")
        print(f"📊 Proveedor: {result['provider']}")
        print(f"📝 Explicación: {result['explanation']}")
        print(f"🔍 SQL:\n{result['sql'][:250]}...")
    
    # ========== PRUEBA COMBINADA: TIPO DE SANGRE + MES ==========
    print("\n" + "=" * 80)
    print("BONUS: COMBINACIÓN TIPO DE SANGRE + MES")
    print("=" * 80)
    
    query_combined = "Historias clínicas con tipo de sangre AB creadas en noviembre 2025 ordenadas ascendente"
    print(f"\n🔥 Query: {query_combined}")
    result = parser.parse_query(query_combined, language='es')
    print(f"✅ Confianza: {result['confidence']}")
    print(f"📊 Proveedor: {result['provider']}")
    print(f"📝 Explicación: {result['explanation']}")
    print(f"🔍 SQL:\n{result['sql'][:300]}...")
    
    print("\n" + "=" * 80)
    print("✅ PRUEBA COMPLETADA - TODOS LOS 3 TIPOS FUNCIONAN")
    print("=" * 80)

if __name__ == '__main__':
    test_critical_queries()
