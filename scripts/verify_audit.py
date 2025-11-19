#!/usr/bin/env python
"""
Script para verificar que el sistema de auditoría está funcionando
Ejecutar: python scripts/verify_audit.py
"""

import os
import sys
import json
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')

import django
django.setup()

from apps.audit.models import AuditLog
from apps.audit.detailed_audit import DetailedAuditService
from apps.accounts.models import User

print("\n" + "="*80)
print("VERIFICACIÓN DEL SISTEMA DE AUDITORÍA")
print("="*80 + "\n")

# 1. Verificar que el servicio inicia
print("1. VERIFICANDO SERVICIO DE AUDITORÍA")
print("-" * 80)
try:
    service = DetailedAuditService()
    print("   ✓ DetailedAuditService inicializado correctamente")
    print(f"   ✓ CloudWatch enabled: {service.cloudwatch_enabled}")
    print()
except Exception as e:
    print(f"   ❌ Error: {e}\n")
    sys.exit(1)

# 2. Contar logs existentes
print("2. CONTANDO LOGS EXISTENTES")
print("-" * 80)
try:
    total = AuditLog.objects.count()
    today = AuditLog.objects.filter(
        timestamp__date=datetime.now().date()
    ).count()
    
    print(f"   Total de logs: {total}")
    print(f"   Logs de hoy: {today}")
    
    if total > 0:
        last_log = AuditLog.objects.order_by('-timestamp').first()
        print(f"   Último log: {last_log.timestamp}")
        print(f"      - Acción: {last_log.action_type}")
        print(f"      - Usuario: {last_log.user_email}")
        print(f"      - Recurso: {last_log.resource_type}/{last_log.resource_id}")
    print()
except Exception as e:
    print(f"   ❌ Error: {e}\n")

# 3. Crear un log de prueba
print("3. CREANDO LOG DE PRUEBA")
print("-" * 80)
try:
    user = User.objects.filter(is_staff=True).first() or User.objects.first()
    
    if not user:
        print("   ⚠️  No hay usuarios en la BD, saltando prueba\n")
    else:
        test_log = service.log_crud_action(
            user=user,
            action_type='TEST',
            resource_type='audit_verification',
            resource_id=None,
            resource_name='Test Log',
            changes={'test': {'before': None, 'after': 'success'}},
            severity='INFO',
        )
        
        print(f"   ✓ Log de prueba creado: {test_log.id}")
        print(f"   ✓ Usuario: {test_log.user_email}")
        print(f"   ✓ Acción: {test_log.action_type}")
        print(f"   ✓ Cambios: {test_log.changes}")
        print()
except Exception as e:
    print(f"   ❌ Error: {e}\n")

# 4. Verificar integridad de logs
print("4. VERIFICANDO INTEGRIDAD DE LOGS")
print("-" * 80)
try:
    recent_logs = AuditLog.objects.order_by('-timestamp')[:5]
    
    if recent_logs:
        valid = 0
        invalid = 0
        
        for log in recent_logs:
            if log.verify_integrity():
                valid += 1
            else:
                invalid += 1
        
        print(f"   ✓ Logs válidos: {valid}")
        if invalid > 0:
            print(f"   ⚠️  Logs manipulados: {invalid}")
        print()
    else:
        print("   ⚠️  No hay logs para verificar\n")
except Exception as e:
    print(f"   ❌ Error: {e}\n")

# 5. Verificar formato de datos
print("5. VERIFICANDO FORMATO DE DATOS")
print("-" * 80)
try:
    last_log = AuditLog.objects.order_by('-timestamp').first()
    
    if last_log:
        print("   Estructura del último log:")
        print(f"      id: {last_log.id}")
        print(f"      user_email: {last_log.user_email}")
        print(f"      user_name: {last_log.user_name}")
        print(f"      action_type: {last_log.action_type}")
        print(f"      resource_type: {last_log.resource_type}")
        print(f"      resource_id: {last_log.resource_id}")
        print(f"      ip_address: {last_log.ip_address}")
        print(f"      user_agent: {last_log.user_agent[:50]}...")
        print(f"      changes: {json.dumps(last_log.changes, indent=6)}")
        print(f"      metadata: {json.dumps(last_log.metadata, indent=6)}")
        print(f"      timestamp: {last_log.timestamp}")
        print(f"      log_hash: {last_log.log_hash}")
        print()
except Exception as e:
    print(f"   ❌ Error: {e}\n")

# 6. Estadísticas
print("6. ESTADÍSTICAS DE AUDITORÍA")
print("-" * 80)
try:
    from django.db.models import Count
    
    # Por acción
    by_action = AuditLog.objects.values('action_type').annotate(
        count=Count('id')
    ).order_by('-count')
    
    print("   Por tipo de acción:")
    for item in by_action[:5]:
        print(f"      {item['action_type']}: {item['count']}")
    
    # Por recurso
    by_resource = AuditLog.objects.values('resource_type').annotate(
        count=Count('id')
    ).order_by('-count')
    
    print("\n   Por tipo de recurso:")
    for item in by_resource[:5]:
        print(f"      {item['resource_type']}: {item['count']}")
    
    # Por usuario
    by_user = AuditLog.objects.values('user_email').annotate(
        count=Count('id')
    ).order_by('-count')
    
    print("\n   Por usuario:")
    for item in by_user[:5]:
        print(f"      {item['user_email']}: {item['count']}")
    
    print()
except Exception as e:
    print(f"   ❌ Error: {e}\n")

# 7. Métodos disponibles
print("7. MÉTODOS DISPONIBLES DEL SERVICIO")
print("-" * 80)
try:
    methods = [
        'log_crud_action',
        'log_error',
        'extract_changes',
        'get_client_info',
        'get_audit_trail',
        'get_user_actions',
        'verify_log_integrity',
        'export_audit_logs',
    ]
    
    print("   Métodos disponibles:")
    for method in methods:
        if hasattr(service, method):
            print(f"      ✓ {method}")
        else:
            print(f"      ❌ {method}")
    print()
except Exception as e:
    print(f"   ❌ Error: {e}\n")

# 8. Ejemplo de exportación
print("8. EJEMPLO DE EXPORTACIÓN")
print("-" * 80)
try:
    json_export = service.export_audit_logs(limit=2, format_type='json')
    data = json.loads(json_export)
    
    print(f"   ✓ Exportación JSON lista")
    print(f"   ✓ Registros: {len(data)}")
    
    if data:
        print("\n   Ejemplo de primer registro:")
        first = data[0]
        for key, value in list(first.items())[:5]:
            print(f"      {key}: {value}")
    print()
except Exception as e:
    print(f"   ❌ Error: {e}\n")

# Resumen final
print("="*80)
print("✓ VERIFICACIÓN COMPLETADA")
print("="*80 + "\n")

print("Próximos pasos:")
print("1. Integrar AuditMixin en ViewSets (ver EJEMPLOS_INTEGRACION.md)")
print("2. Hacer git push")
print("3. En EC2: git pull && sudo systemctl restart gunicorn")
print("4. Hacer una acción en la app y verificar logs")
print("5. Ver CloudWatch: /clinidocs-audit")
print()
