#!/usr/bin/env python
"""
TEST COMPLETO DE AUDITORÍA - Verifica que TODO funciona:
1. Logs se crean en PostgreSQL
2. Logs se envían a CloudWatch

Ejecutar: python scripts/test_audit_complete.py
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Setup Django
sys.path.insert(0, str(Path(__file__).parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')

import django
django.setup()

from django.conf import settings
from apps.audit.services import AuditLogService
from apps.audit.models import AuditLog
from django.contrib.auth import get_user_model
import boto3

User = get_user_model()

print("\n" + "="*80)
print("TEST COMPLETO DE AUDITORÍA")
print("="*80 + "\n")

# 1. Verificar configuración
print("1. VERIFICANDO CONFIGURACIÓN")
print("-" * 80)
print(f"   USE_CLOUDWATCH: {getattr(settings, 'USE_CLOUDWATCH', False)}")
print(f"   AWS_REGION: {getattr(settings, 'AWS_REGION', 'NO DEFINIDO')}")
print(f"   AWS_CLOUDWATCH_LOG_GROUP: {getattr(settings, 'AWS_CLOUDWATCH_LOG_GROUP', 'NO DEFINIDO')}")
print()

# 2. Obtener usuario de prueba
print("2. OBTENIENDO USUARIO DE PRUEBA")
print("-" * 80)
try:
    user = User.objects.filter(is_active=True).first()
    if not user:
        print("   ❌ No hay usuarios activos en la BD")
        sys.exit(1)
    print(f"   ✓ Usuario encontrado: {user.email}")
    print()
except Exception as e:
    print(f"   ❌ Error: {e}")
    sys.exit(1)

# 3. Crear un log de prueba
print("3. CREANDO LOG DE AUDITORÍA EN POSTGRESQL")
print("-" * 80)
try:
    service = AuditLogService(tenant=user.tenant if hasattr(user, 'tenant') else None)
    
    log = service.log_action(
        user=user,
        action_type='CREATE',
        resource_type='document',
        resource_id=None,
        resource_name='Test Document from Script',
        ip_address='192.168.1.1',
        user_agent='test_script',
        request_method='POST',
        request_path='/api/documents/',
        request_body={'name': 'Test Document', 'content': 'This is a test'},
        response_status=201,
    )
    
    print(f"   ✓ Log creado con ID: {log.id}")
    print(f"   Timestamp: {log.timestamp}")
    print()
except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 4. Verificar que el log está en PostgreSQL
print("4. VERIFICANDO LOG EN POSTGRESQL")
print("-" * 80)
try:
    count = AuditLog.objects.count()
    recent_logs = AuditLog.objects.order_by('-timestamp')[:5]
    
    print(f"   Total logs en BD: {count}")
    print(f"   Últimos 5 logs:")
    for recent_log in recent_logs:
        print(f"      - {recent_log.timestamp.isoformat()[:19]} | {recent_log.action_type} {recent_log.resource_type} | {recent_log.user_email}")
    print()
except Exception as e:
    print(f"   ❌ Error: {e}")
    sys.exit(1)

# 5. Verificar CloudWatch
print("5. VERIFICANDO CLOUDWATCH")
print("-" * 80)
try:
    client = boto3.client(
        'logs',
        region_name=getattr(settings, 'AWS_REGION', 'us-east-1')
    )
    
    log_group = getattr(settings, 'AWS_CLOUDWATCH_LOG_GROUP', '/clinidocs-audit')
    log_stream = f"audit-{datetime.now().strftime('%Y-%m-%d')}"
    
    # Obtener eventos del stream
    try:
        response = client.get_log_events(
            logGroupName=log_group,
            logStreamName=log_stream,
            startFromHead=False,
            limit=10
        )
        
        events = response.get('events', [])
        print(f"   Log Group: {log_group}")
        print(f"   Log Stream: {log_stream}")
        print(f"   Eventos en CloudWatch: {len(events)}")
        
        if events:
            print(f"   Últimos 3 eventos en CloudWatch:")
            for event in events[-3:]:
                ts = datetime.fromtimestamp(event['timestamp']/1000)
                msg = event['message'][:100]
                print(f"      - {ts.isoformat()[:19]} | {msg}...")
        else:
            print(f"   ⚠️  No hay eventos en CloudWatch")
        print()
    except client.exceptions.ResourceNotFoundException as e:
        print(f"   ⚠️  Log stream no existe: {e}")
        print()
    except Exception as e:
        print(f"   ❌ Error accessing CloudWatch: {e}")
        print()
        
except Exception as e:
    print(f"   ❌ Error conectando a CloudWatch: {e}")
    print()

print("="*80)
print("TEST COMPLETADO")
print("="*80 + "\n")

print("PRÓXIMOS PASOS:")
print("-" * 80)
print("1. Si viste logs en CloudWatch → ✓ Sistema funcionando correctamente")
print("2. Si NO viste logs en CloudWatch pero sí en PostgreSQL → Revisar CloudWatch integration")
print("3. Reinicia Gunicorn en EC2 y prueba creando un documento desde la API")
print()
