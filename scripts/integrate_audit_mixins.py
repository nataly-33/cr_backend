#!/usr/bin/env python
"""
Script para integrar AuditMixin en todos los ViewSets
Ejecutar: python scripts/integrate_audit_mixins.py

Este script:
1. Busca todos los ViewSets en las apps
2. Verifica que no estén ya integrados
3. Agrega AuditMixin automáticamente
4. Crea backups de los archivos originales
"""

import os
import sys
import re
from pathlib import Path
from datetime import datetime

APPS_TO_INTEGRATE = [
    'apps/patients',
    'apps/documents',
    'apps/clinical_records',
    'apps/reports',
    'apps/accounts',
    'apps/notifications',
    'apps/payments',
    'apps/audit',
]

VIEWSET_PATTERN = re.compile(
    r'class\s+(\w+)\s*\(\s*(?:viewsets\.|.*?)ModelViewSet',
    re.MULTILINE
)

AUDIT_IMPORT = "from apps.audit.mixins import AuditMixin"

def backup_file(filepath):
    """Crea un backup del archivo"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f"{filepath}.backup_{timestamp}"
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"   ✓ Backup creado: {backup_path}")
    return backup_path

def integrate_audit_mixin(filepath):
    """Integra AuditMixin en los ViewSets del archivo"""
    
    print(f"\n📄 {filepath}")
    print("-" * 70)
    
    if not os.path.exists(filepath):
        print(f"   ⚠️  Archivo no existe, saltando")
        return False
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Verificar si ya está integrado
    if 'AuditMixin' in content:
        print(f"   ✓ Ya tiene AuditMixin, saltando")
        return False
    
    original_content = content
    modified = False
    
    # Encontrar todos los ViewSets
    viewsets = VIEWSET_PATTERN.findall(content)
    
    if not viewsets:
        print(f"   ⚠️  No se encontraron ViewSets")
        return False
    
    print(f"   Encontrados {len(viewsets)} ViewSet(s): {', '.join(viewsets)}")
    
    # Agregar import si no existe
    if AUDIT_IMPORT not in content:
        # Encontrar la última línea de imports
        lines = content.split('\n')
        last_import_line = 0
        
        for i, line in enumerate(lines):
            if line.startswith('from ') or line.startswith('import '):
                last_import_line = i
        
        # Insertar el nuevo import después del último import existente
        if last_import_line > 0:
            lines.insert(last_import_line + 1, AUDIT_IMPORT)
            content = '\n'.join(lines)
            modified = True
            print(f"   ✓ Import agregado")
    
    # Reemplazar la definición de cada ViewSet
    for viewset_name in viewsets:
        # Patrón para encontrar la clase
        pattern = rf'class\s+{viewset_name}\s*\(\s*(.*?)ModelViewSet'
        
        def replacer(match):
            base_classes = match.group(1).strip()
            
            # Si ya tiene AuditMixin, no cambiar
            if 'AuditMixin' in base_classes:
                return match.group(0)
            
            # Si no tiene padres además de ModelViewSet, agregar AuditMixin
            if not base_classes or base_classes == '':
                return f'class {viewset_name}(AuditMixin, viewsets.ModelViewSet'
            else:
                return f'class {viewset_name}(AuditMixin, {base_classes}ModelViewSet'
        
        new_content = re.sub(pattern, replacer, content)
        
        if new_content != content:
            content = new_content
            modified = True
            print(f"   ✓ {viewset_name} actualizado")
    
    # Si se modificó, guardar con backup
    if modified:
        backup_file(filepath)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"   ✓ Archivo actualizado")
        return True
    else:
        print(f"   ⚠️  Sin cambios")
        return False

def main():
    print("\n" + "="*70)
    print("INTEGRACIÓN AUTOMÁTICA DE AUDITORIA")
    print("="*70 + "\n")
    
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    total_files = 0
    modified_files = 0
    
    for app_path in APPS_TO_INTEGRATE:
        views_file = Path(app_path) / 'views.py'
        
        if views_file.exists():
            total_files += 1
            if integrate_audit_mixin(str(views_file)):
                modified_files += 1
        else:
            print(f"\n📄 {views_file}")
            print("-" * 70)
            print(f"   ⚠️  Archivo no encontrado")
    
    # Resumen
    print("\n" + "="*70)
    print("RESUMEN")
    print("="*70)
    print(f"Archivos procesados: {total_files}")
    print(f"Archivos modificados: {modified_files}")
    
    if modified_files > 0:
        print("\n✓ Integración completada exitosamente")
        print("\nSiguientes pasos:")
        print("1. Revisar los cambios: git diff")
        print("2. Probar: python manage.py runserver")
        print("3. Hacer git add/commit")
        print("4. Push: git push origin branch")
    else:
        print("\n✓ No hay cambios que hacer (ya integrado)")
    
    print()

if __name__ == '__main__':
    main()
