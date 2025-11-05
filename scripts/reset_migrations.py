"""
Script para BORRAR todas las migraciones y recrearlas desde cero.

IMPORTANTE: Solo ejecutar en desarrollo, NUNCA en producción.
"""
import os
import shutil
from pathlib import Path

# Directorio base del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent

# Apps Django locales que tienen migraciones
APPS = [
    'apps.core',
    'apps.accounts',
    'apps.tenants',
    'apps.patients',
    'apps.clinical_records',
    'apps.documents',
    'apps.audit',
    'apps.reports',
    'apps.backup',
    'apps.notifications',
]


def delete_migrations():
    """Eliminar todas las carpetas migrations/ excepto __init__.py"""
    print("\n" + "="*80)
    print("ELIMINANDO TODAS LAS MIGRACIONES")
    print("="*80 + "\n")

    total_deleted = 0

    for app_path in APPS:
        # Convertir 'apps.core' a 'apps/core'
        app_dir = BASE_DIR / app_path.replace('.', os.sep)
        migrations_dir = app_dir / 'migrations'

        if migrations_dir.exists():
            print(f"[+] {app_path}/migrations/")

            # Listar todos los archivos
            files = list(migrations_dir.glob('*.py'))

            for file in files:
                # NO borrar __init__.py
                if file.name == '__init__.py':
                    print(f"   [SKIP] Manteniendo: {file.name}")
                    continue

                # Borrar archivo de migración
                file.unlink()
                print(f"   [DEL] Eliminado: {file.name}")
                total_deleted += 1

            # Borrar archivos .pyc en __pycache__
            pycache_dir = migrations_dir / '__pycache__'
            if pycache_dir.exists():
                shutil.rmtree(pycache_dir)
                print(f"   [DEL] Eliminado: __pycache__/")

    print(f"\n{'='*80}")
    print(f"[OK] Total de archivos de migracion eliminados: {total_deleted}")
    print("="*80 + "\n")


def show_next_steps():
    """Mostrar los siguientes pasos"""
    print("="*80)
    print("SIGUIENTES PASOS")
    print("="*80 + "\n")

    print("Ahora debes RECREAR las migraciones y aplicarlas:\n")
    print("1. CREAR NUEVAS MIGRACIONES:")
    print("   python manage.py makemigrations")
    print()
    print("2. APLICAR MIGRACIONES A LA BD:")
    print("   python manage.py migrate")
    print()
    print("3. CREAR DATOS DE PRUEBA:")
    print("   python scripts/seed_data.py")
    print()
    print("4. VERIFICAR CONEXIÓN A BD:")
    print("   python manage.py dbshell")
    print("   # Dentro de PostgreSQL:")
    print("   \\dt  # Listar tablas")
    print("   \\q   # Salir")
    print()
    print("="*80 + "\n")


def main():
    """Función principal"""
    print("\n")
    print("=" * 80)
    print(" " * 25 + "RESET DE MIGRACIONES")
    print("=" * 80)
    print("\n")

    print("ADVERTENCIA: Este script eliminara TODAS las migraciones existentes.")
    print("Solo debes ejecutar esto en desarrollo, NUNCA en produccion.\n")

    response = input("Estas seguro que quieres continuar? (escribe 'SI' para confirmar): ")

    if response.strip().upper() != 'SI':
        print("\nOperacion cancelada")
        return

    print("\nConfirmado. Iniciando...\n")

    try:
        # Eliminar migraciones
        delete_migrations()

        # Mostrar siguientes pasos
        show_next_steps()

        print("[OK] RESET DE MIGRACIONES COMPLETADO\n")

    except Exception as e:
        print(f"\n[ERROR] ERROR: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
