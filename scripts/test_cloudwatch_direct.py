#!/usr/bin/env python
"""
Script para PROBAR CloudWatch directamente
Ejecutar: python scripts/test_cloudwatch_direct.py
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
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

print("\n" + "="*80)
print("TEST DIRECTO DE CLOUDWATCH")
print("="*80 + "\n")

# Verificar configuración
print("1. CONFIGURACIÓN ACTUAL")
print("-" * 80)
print(f"   DJANGO_SETTINGS_MODULE: {os.environ.get('DJANGO_SETTINGS_MODULE')}")
print(f"   USE_CLOUDWATCH: {getattr(settings, 'USE_CLOUDWATCH', False)}")
print(f"   AWS_REGION: {getattr(settings, 'AWS_REGION', 'NO DEFINIDO')}")
print(f"   AWS_CLOUDWATCH_LOG_GROUP: {getattr(settings, 'AWS_CLOUDWATCH_LOG_GROUP', 'NO DEFINIDO')}")
print()

# Verificar credenciales
print("2. VERIFICANDO CREDENCIALES AWS")
print("-" * 80)

access_key = os.environ.get('AWS_ACCESS_KEY_ID', 'NO DEFINIDA')
secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY', 'NO DEFINIDA')

print(f"   AWS_ACCESS_KEY_ID: {access_key[:10]}..." if access_key != 'NO DEFINIDA' else "   AWS_ACCESS_KEY_ID: NO DEFINIDA")
print(f"   AWS_SECRET_ACCESS_KEY: {secret_key[:10]}..." if secret_key != 'NO DEFINIDA' else "   AWS_SECRET_ACCESS_KEY: NO DEFINIDA")
print()

# Conectar a CloudWatch
print("3. CONECTANDO A CLOUDWATCH")
print("-" * 80)

try:
    client = boto3.client(
        'logs',
        region_name=getattr(settings, 'AWS_REGION', 'us-east-1')
    )
    print("   ✓ Cliente boto3 creado exitosamente")
    print()
except Exception as e:
    print(f"   ❌ Error: {e}")
    sys.exit(1)

# Describir log groups
print("4. VERIFICANDO LOG GROUPS")
print("-" * 80)

try:
    response = client.describe_log_groups()
    log_groups = response.get('logGroups', [])
    print(f"   Total log groups: {len(log_groups)}")
    
    if log_groups:
        print("\n   Log groups disponibles:")
        for lg in log_groups[-10:]:  # Últimos 10
            print(f"      - {lg['logGroupName']}")
    print()
except ClientError as e:
    print(f"   ❌ Error ClientError: {e}")
    print()
except Exception as e:
    print(f"   ❌ Error: {type(e).__name__}: {e}")
    print()

# Crear o verificar log group
log_group = getattr(settings, 'AWS_CLOUDWATCH_LOG_GROUP', '/clinidocs-audit')
log_stream = f"audit-{datetime.now().strftime('%Y-%m-%d')}"

print(f"5. VERIFICANDO LOG GROUP: {log_group}")
print("-" * 80)

try:
    # Crear el log group si no existe
    try:
        client.create_log_group(logGroupName=log_group)
        print(f"   ✓ Log group creado: {log_group}")
    except client.exceptions.ResourceAlreadyExistsException:
        print(f"   ✓ Log group ya existe: {log_group}")
    
    print()
except ClientError as e:
    error_code = e.response['Error']['Code']
    if error_code == 'AccessDenied':
        print(f"   ❌ ACCESO DENEGADO - El usuario IAM no tiene permiso para crear log groups")
        print(f"      Necesita: logs:CreateLogGroup")
    else:
        print(f"   ❌ ClientError ({error_code}): {e}")
    print()
    sys.exit(1)
except Exception as e:
    print(f"   ❌ Error: {type(e).__name__}: {e}")
    print()
    sys.exit(1)

# Crear o verificar log stream
print(f"6. VERIFICANDO LOG STREAM: {log_stream}")
print("-" * 80)

try:
    # Crear el stream si no existe
    try:
        client.create_log_stream(
            logGroupName=log_group,
            logStreamName=log_stream
        )
        print(f"   ✓ Log stream creado: {log_stream}")
    except client.exceptions.ResourceAlreadyExistsException:
        print(f"   ✓ Log stream ya existe: {log_stream}")
    
    print()
except ClientError as e:
    error_code = e.response['Error']['Code']
    if error_code == 'AccessDenied':
        print(f"   ❌ ACCESO DENEGADO - El usuario IAM no tiene permiso para crear streams")
        print(f"      Necesita: logs:CreateLogStream")
    else:
        print(f"   ❌ ClientError ({error_code}): {e}")
    print()
    sys.exit(1)

# Enviar un evento de prueba
print("7. ENVIANDO EVENTO DE PRUEBA")
print("-" * 80)

test_message = {
    'test': True,
    'timestamp': datetime.now().isoformat(),
    'message': 'Test de CloudWatch - Verificar que esto aparece en CloudWatch'
}

try:
    response = client.put_log_events(
        logGroupName=log_group,
        logStreamName=log_stream,
        logEvents=[
            {
                'timestamp': int(datetime.now().timestamp() * 1000),
                'message': json.dumps(test_message)
            }
        ]
    )
    print(f"   ✓ Evento enviado exitosamente")
    print(f"   Sequence token: {response.get('nextSequenceToken', 'N/A')}")
    print()
except ClientError as e:
    error_code = e.response['Error']['Code']
    if error_code == 'AccessDenied':
        print(f"   ❌ ACCESO DENEGADO - El usuario IAM no tiene permiso para enviar eventos")
        print(f"      Necesita: logs:PutLogEvents")
    else:
        print(f"   ❌ ClientError ({error_code}): {e}")
    print()
    sys.exit(1)
except Exception as e:
    print(f"   ❌ Error: {type(e).__name__}: {e}")
    print()
    sys.exit(1)

# Leer los eventos
print("8. LEYENDO EVENTOS")
print("-" * 80)

try:
    response = client.get_log_events(
        logGroupName=log_group,
        logStreamName=log_stream,
        startFromHead=False,
        limit=5
    )
    
    events = response.get('events', [])
    if events:
        print(f"   ✓ Se encontraron {len(events)} eventos:")
        for event in events[-3:]:
            ts = datetime.fromtimestamp(event['timestamp']/1000)
            print(f"      [{ts.strftime('%H:%M:%S')}] {event['message'][:80]}")
    else:
        print(f"   ⚠️  No hay eventos en el stream")
    print()
except Exception as e:
    print(f"   ❌ Error: {type(e).__name__}: {e}")
    print()

print("="*80)
print("✓ TEST COMPLETADO EXITOSAMENTE")
print("="*80 + "\n")
