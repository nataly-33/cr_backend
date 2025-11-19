#!/usr/bin/env python
"""
Script para diagnosticar el problema de logs en CloudWatch
Verifica:
1. Si CloudWatch está habilitado en settings
2. Si hay credenciales AWS válidas
3. Si se pueden conectar a CloudWatch
4. Si hay logs pendientes en BD
5. Si hay errores al enviar a CloudWatch
"""

import os
import sys
import json
import django
from datetime import datetime, timedelta
from pathlib import Path

# Setup Django
sys.path.insert(0, str(Path(__file__).parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
django.setup()

from django.conf import settings
from apps.audit.models import AuditLog
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

print("\n" + "="*70)
print("DIAGNÓSTICO DE CLOUDWATCH - CLINIC RECORDS")
print("="*70 + "\n")

# 1. Verificar configuración
print("1. VERIFICANDO CONFIGURACIÓN EN SETTINGS")
print("-" * 70)
print(f"   USE_CLOUDWATCH: {getattr(settings, 'USE_CLOUDWATCH', 'NO DEFINIDO')}")
print(f"   AWS_CLOUDWATCH_LOG_GROUP: {getattr(settings, 'AWS_CLOUDWATCH_LOG_GROUP', 'NO DEFINIDO')}")
print(f"   AWS_REGION: {getattr(settings, 'AWS_REGION', 'NO DEFINIDO')}")

if not getattr(settings, 'USE_CLOUDWATCH', False):
    print("\n   ⚠️  PROBLEMA: CloudWatch está DESHABILITADO en settings!")
    print("   Verifica que USE_CLOUDWATCH=True en tu .env\n")
else:
    print("   ✓ CloudWatch está HABILITADO\n")

# 2. Verificar credenciales AWS
print("2. VERIFICANDO CREDENCIALES AWS")
print("-" * 70)
try:
    # Intentar conectar a CloudWatch
    cloudwatch_client = boto3.client(
        'logs',
        region_name=getattr(settings, 'AWS_REGION', 'us-east-1')
    )
    
    # Hacer una llamada simple para verificar credenciales
    cloudwatch_client.describe_log_groups(limit=1)
    print("   ✓ Credenciales AWS válidas")
    print(f"   ✓ Conectado a CloudWatch en región: {getattr(settings, 'AWS_REGION', 'us-east-1')}\n")
    
except NoCredentialsError:
    print("   ❌ ERROR: No se encontraron credenciales AWS")
    print("   Verifica que AWS_ACCESS_KEY_ID y AWS_SECRET_ACCESS_KEY estén configuradas\n")
except ClientError as e:
    print(f"   ❌ ERROR: {e}\n")
except Exception as e:
    print(f"   ❌ ERROR: {type(e).__name__}: {e}\n")

# 3. Verificar Log Group
print("3. VERIFICANDO LOG GROUP EN CLOUDWATCH")
print("-" * 70)
try:
    log_group = getattr(settings, 'AWS_CLOUDWATCH_LOG_GROUP', '/clinidocs-audit')
    print(f"   Buscando log group: {log_group}")
    
    response = cloudwatch_client.describe_log_groups()
    log_groups = [lg['logGroupName'] for lg in response.get('logGroups', [])]
    
    if log_group in log_groups:
        print(f"   ✓ Log group EXISTS: {log_group}\n")
    else:
        print(f"   ⚠️  Log group NO EXISTE: {log_group}")
        print(f"   Grupos disponibles: {log_groups}\n")
        
except Exception as e:
    print(f"   ❌ ERROR al verificar log group: {e}\n")

# 4. Verificar Log Streams
print("4. VERIFICANDO LOG STREAMS")
print("-" * 70)
try:
    log_group = getattr(settings, 'AWS_CLOUDWATCH_LOG_GROUP', '/clinidocs-audit')
    
    response = cloudwatch_client.describe_log_streams(logGroupName=log_group)
    streams = response.get('logStreams', [])
    
    if streams:
        print(f"   ✓ Se encontraron {len(streams)} log streams:\n")
        for stream in streams[-5:]:  # Mostrar últimos 5
            last_event = stream.get('lastEventTimestamp', 'N/A')
            if last_event != 'N/A':
                last_event = datetime.fromtimestamp(last_event/1000).strftime('%Y-%m-%d %H:%M:%S')
            print(f"      - {stream['logStreamName']}")
            print(f"        Último evento: {last_event}")
            print(f"        Eventos: {stream.get('storedBytes', 0)} bytes\n")
    else:
        print(f"   ⚠️  No hay log streams en {log_group}\n")
        
except Exception as e:
    print(f"   ❌ ERROR al verificar streams: {e}\n")

# 5. Contar logs en Base de Datos
print("5. VERIFICANDO LOGS EN BASE DE DATOS")
print("-" * 70)
try:
    total_logs = AuditLog.objects.count()
    today_logs = AuditLog.objects.filter(
        timestamp__date=datetime.now().date()
    ).count()
    
    last_log = AuditLog.objects.order_by('-timestamp').first()
    
    print(f"   Total de logs: {total_logs}")
    print(f"   Logs de hoy: {today_logs}")
    
    if last_log:
        print(f"   Último log: {last_log.timestamp}")
        print(f"      - Acción: {last_log.action_type}")
        print(f"      - Usuario: {last_log.user_email}")
        print(f"      - Recurso: {last_log.resource_type}")
    else:
        print("   ⚠️  No hay logs en la BD\n")
    
except Exception as e:
    print(f"   ❌ ERROR al verificar logs BD: {e}\n")

# 6. Obtener eventos recientes de CloudWatch
print("6. VERIFICANDO EVENTOS RECIENTES EN CLOUDWATCH")
print("-" * 70)
try:
    log_group = getattr(settings, 'AWS_CLOUDWATCH_LOG_GROUP', '/clinidocs-audit')
    log_stream = f"audit-{datetime.now().strftime('%Y-%m-%d')}"
    
    print(f"   Buscando eventos en: {log_stream}\n")
    
    response = cloudwatch_client.get_log_events(
        logGroupName=log_group,
        logStreamName=log_stream,
        startFromHead=False,
        limit=10
    )
    
    events = response.get('events', [])
    if events:
        print(f"   ✓ Se encontraron {len(events)} eventos:\n")
        for event in events[-5:]:
            timestamp = datetime.fromtimestamp(event['timestamp']/1000).strftime('%Y-%m-%d %H:%M:%S')
            print(f"      [{timestamp}] {event['message'][:100]}...")
    else:
        print(f"   ❌ No hay eventos en el log stream de hoy: {log_stream}\n")
        
        # Buscar en streams anteriores
        response = cloudwatch_client.describe_log_streams(
            logGroupName=log_group,
            orderBy='LastEventTime',
            descending=True,
            limit=5
        )
        
        if response.get('logStreams'):
            print("   Últimos log streams con eventos:")
            for stream in response['logStreams'][:3]:
                print(f"      - {stream['logStreamName']}")
        
        print()
        
except Exception as e:
    print(f"   ❌ ERROR al obtener eventos: {e}\n")

# 7. Intentar enviar un log de prueba
print("7. INTENTANDO ENVIAR LOG DE PRUEBA")
print("-" * 70)
try:
    if getattr(settings, 'USE_CLOUDWATCH', False):
        from apps.audit.services import AuditLogService
        from apps.accounts.models import User
        
        service = AuditLogService()
        
        # Crear usuario de prueba o usar el primero
        user = User.objects.filter(is_staff=True).first()
        if not user:
            user = User.objects.first()
        
        if user:
            audit_log = service.log_action(
                user=user,
                action_type='TEST',
                resource_type='diagnostic',
                resource_id=None,
                ip_address='127.0.0.1',
                request_method='TEST',
                request_path='/test',
                response_status=200,
            )
            
            print(f"   ✓ Log de prueba creado: {audit_log.id}")
            print(f"   ✓ Intentando enviar a CloudWatch...\n")
            
            # Esperar un momento y verificar
            import time
            time.sleep(2)
            
            response = cloudwatch_client.get_log_events(
                logGroupName=getattr(settings, 'AWS_CLOUDWATCH_LOG_GROUP', '/clinidocs-audit'),
                logStreamName=f"audit-{datetime.now().strftime('%Y-%m-%d')}",
                startFromHead=False,
                limit=1
            )
            
            if response.get('events'):
                print("   ✓ Log recibido en CloudWatch!\n")
            else:
                print("   ❌ Log NO fue recibido en CloudWatch\n")
        else:
            print("   ⚠️  No hay usuarios en la BD para hacer prueba\n")
    
except Exception as e:
    print(f"   ❌ ERROR: {type(e).__name__}: {e}\n")

# 8. Resumen y recomendaciones
print("8. RESUMEN Y RECOMENDACIONES")
print("-" * 70)

issues = []

if not getattr(settings, 'USE_CLOUDWATCH', False):
    issues.append("❌ CloudWatch está deshabilitado (USE_CLOUDWATCH=False)")

if not getattr(settings, 'AWS_REGION', ''):
    issues.append("❌ AWS_REGION no está configurada")

if issues:
    print("\nProblemas encontrados:")
    for issue in issues:
        print(f"   {issue}")
    
    print("\nSoluciones:")
    print("   1. Verifica que en tu .env (producción) tengas:")
    print("      USE_CLOUDWATCH=True")
    print("      AWS_REGION=us-east-1")
    print("      AWS_ACCESS_KEY_ID=<tu_key>")
    print("      AWS_SECRET_ACCESS_KEY=<tu_secret>")
    print("      AWS_CLOUDWATCH_LOG_GROUP=/clinidocs-audit")
    print("\n   2. Si está en AWS EC2, verifica que el rol IAM tiene permisos:")
    print("      - logs:CreateLogGroup")
    print("      - logs:CreateLogStream")
    print("      - logs:PutLogEvents")
    print("      - logs:DescribeLogStreams")
    print("      - logs:DescribeLogGroups")
else:
    print("\n   ✓ Configuración parece estar bien")
    print("   ✓ Revisa si hay errores en los logs de la aplicación")

print("\n" + "="*70 + "\n")
