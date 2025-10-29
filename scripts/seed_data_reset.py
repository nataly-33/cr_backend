import os
import sys
from pathlib import Path

# Setup Django environment
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

import argparse
from django.conf import settings
from django.core.management import call_command
from django.apps import apps


def print_model_counts():
    """Print a count summary for all models before flush."""
    models = apps.get_models()
    print("\nResumen de registros por modelo antes del reset:")
    for m in sorted(models, key=lambda x: (x._meta.app_label, x.__name__)):
        try:
            cnt = m.objects.count()
        except Exception:
            cnt = 'N/A'
        print(f"  - {m._meta.app_label}.{m.__name__}: {cnt}")


def confirm_proceed(force: bool) -> bool:
    if force:
        return True

    # If running in a non-debug environment, require explicit --force
    if not settings.DEBUG:
        print("WARNING: DEBUG is False in settings. This operation is destructive and targets a non-debug environment.")
        print("If you really want to proceed, re-run with --force flag.")
        return False

    # Ask for explicit confirmation
    print("\nADVERTENCIA: Esto borrará TODOS los datos de la base de datos (flush).")
    resp = input('Escribe YES para confirmar: ').strip()
    return resp == 'YES'


def main():
    parser = argparse.ArgumentParser(description='Resetear (vaciar) la base de datos (django flush).')
    parser.add_argument('--yes', '-y', action='store_true', help='Omitir confirmación interactiva (equivalente a --force si DEBUG True)')
    parser.add_argument('--force', action='store_true', help='Forzar incluso si DEBUG=False (peligroso)')
    args = parser.parse_args()

    should_continue = False
    if args.yes:
        should_continue = True
    else:
        should_continue = confirm_proceed(force=args.force)

    if not should_continue:
        print('Operación cancelada.')
        return

    # Show counts before flushing
    try:
        print_model_counts()
    except Exception:
        # If we cannot list counts, continue with the flush but warn
        print('No se pudieron obtener los conteos de modelos. Procediendo de todos modos.')

    # Run Django flush (this will remove all data but keep migrations)
    print('\nEjecutando flush de la base de datos...')
    try:
        call_command('flush', '--no-input')
        print('✅ Flush completado. La base de datos está limpia (sin datos).')
    except Exception as e:
        print('ERROR: Falló la operación de flush:')
        print(str(e))


if __name__ == '__main__':
    main()
