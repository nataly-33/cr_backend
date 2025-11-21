"""
Script para verificar que la configuración de OpenAI funciona correctamente
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
django.setup()

from django.conf import settings
from apps.reports_ai.nlp_service import NLPParserService

print("=" * 60)
print("✓ Verificación de Configuración OpenAI")
print("=" * 60)

# 1. Verificar API Key
api_key = getattr(settings, 'OPENAI_API_KEY', None)
openai_model = getattr(settings, 'OPENAI_MODEL', None)

if api_key:
    key_display = api_key[:20] + "..." + api_key[-10:] if len(api_key) > 30 else api_key
    print(f"OPENAI_API_KEY configurada: {key_display}")
else:
    print("OPENAI_API_KEY no configurada")
    exit(1)

print(f"OPENAI_MODEL: {openai_model}")

# 2. Verificar que el servicio se puede importar e inicializar
try:
    parser = NLPParserService(ai_provider='openai')
    print(f"Parser inicializado con proveedor: {parser.ai_provider}")
    print(f"Cliente disponible: {parser.client is not None}")
    
    # 3. Probar un query simple
    print("\n Prueba de Parseo:")
    result = parser.parse_query("Dame 5 pacientes de agosto", "es")
    
    if result.get('sql'):
        print(f" SQL Generado: {result['sql'][:100]}...")
        print(f"Confianza: {result.get('confidence', 0):.2f}")
        print(f"Proveedor usado: {result.get('provider', 'desconocido')}")
    else:
        print(f"Sin SQL generado: {result.get('error', 'Error desconocido')}")
    
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

print("=" * 60)
