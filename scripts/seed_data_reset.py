"""
Script para LIMPIAR COMPLETAMENTE la base de datos.

IMPORTANTE: Este script SOLO borra datos. NO crea nada.
Para crear datos de prueba, ejecuta seed_data.py después de este script.
"""
import os
import sys
import django
from pathlib import Path

# Setup Django
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.core.models import Tenant
from apps.accounts.models import User, Role, Permission, UserPreferences
from apps.patients.models import Patient
from apps.clinical_records.models import ClinicalRecord
from apps.documents.models import ClinicalDocument
from apps.tenants.models import TenantRegistration, SubscriptionPlan
from apps.notifications.models import Notification
from apps.audit.models import AuditLog


def confirm_reset():
    """Pedir confirmación antes de borrar todo"""
    print("\n" + "="*80)
    print("⚠️  ADVERTENCIA: ELIMINACIÓN TOTAL DE DATOS")
    print("="*80)
    print("\nEste script va a BORRAR PERMANENTEMENTE:")
    print("  • Todos los tenants")
    print("  • Todos los usuarios")
    print("  • Todos los roles y permisos")
    print("  • Todos los pacientes")
    print("  • Todas las historias clínicas")
    print("  • Todos los documentos")
    print("  • Todos los registros de activación")
    print("  • Todos los planes de suscripción")
    print("  • Todas las notificaciones")
    print("  • Todos los logs de auditoría")
    print("\n⚠️  TODOS LOS DATOS ACTUALES SE PERDERÁN PERMANENTEMENTE")
    print("\n💡 Después de este script, ejecuta: python scripts/seed_data.py")
    print("="*80 + "\n")

    response = input("¿Estás seguro que quieres continuar? (escribe 'SI' para confirmar): ")

    if response.strip().upper() != 'SI':
        print("\n❌ Operación cancelada")
        return False

    print("\n✅ Confirmado. Iniciando limpieza...\n")
    return True


def delete_all_data():
    """
    Eliminar todos los datos de todas las tablas.

    IMPORTANTE: El orden es crucial para respetar las foreign keys.
    """
    print("="*80)
    print("ELIMINANDO TODOS LOS DATOS")
    print("="*80 + "\n")

    # Orden de eliminación para respetar foreign keys
    models_to_delete = [
        # 1. Datos dependientes
        (AuditLog, "Logs de auditoría"),
        (Notification, "Notificaciones"),
        (UserPreferences, "Preferencias de usuario"),
        (ClinicalDocument, "Documentos clínicos"),
        (ClinicalRecord, "Historias clínicas"),
        (Patient, "Pacientes"),

        # 2. Usuarios y roles
        (User, "Usuarios"),
        (Role, "Roles"),
        (Permission, "Permisos"),

        # 3. Tenants y registros
        (TenantRegistration, "Registros de activación"),
        (Tenant, "Tenants"),

        # 4. Planes
        (SubscriptionPlan, "Planes de suscripción"),
    ]

    total_deleted = 0
    errors = []

    for model, name in models_to_delete:
        try:
            count = model.objects.count()
            if count > 0:
                # Usar _base_manager para evitar problemas con tenants
                if hasattr(model, '_base_manager'):
                    model._base_manager.all().delete()
                else:
                    model.objects.all().delete()

                print(f"  ✅ {name}: {count} registros eliminados")
                total_deleted += count
            else:
                print(f"  ⏭️  {name}: Ya estaba vacío")
        except Exception as e:
            error_msg = f"  ❌ Error eliminando {name}: {str(e)}"
            print(error_msg)
            errors.append(error_msg)

    print(f"\n{'='*80}")
    print(f"Total de registros eliminados: {total_deleted}")

    if errors:
        print(f"\n⚠️  Se encontraron {len(errors)} errores:")
        for error in errors:
            print(error)
    else:
        print("✅ Todos los datos fueron eliminados exitosamente")

    print("="*80 + "\n")


def verify_database_empty():
    """Verificar que la base de datos quedó limpia"""
    print("="*80)
    print("VERIFICANDO QUE LA BASE DE DATOS QUEDÓ VACÍA")
    print("="*80 + "\n")

    models_to_check = [
        (Tenant, "Tenants"),
        (User, "Usuarios"),
        (Role, "Roles"),
        (Permission, "Permisos"),
        (Patient, "Pacientes"),
        (ClinicalRecord, "Historias clínicas"),
        (ClinicalDocument, "Documentos"),
        (TenantRegistration, "Registros de activación"),
        (SubscriptionPlan, "Planes de suscripción"),
    ]

    all_empty = True
    for model, name in models_to_check:
        try:
            if hasattr(model, '_base_manager'):
                count = model._base_manager.count()
            else:
                count = model.objects.count()

            if count == 0:
                print(f"  ✅ {name}: 0 registros (vacío)")
            else:
                print(f"  ⚠️  {name}: {count} registros (DEBERÍA ESTAR VACÍO)")
                all_empty = False
        except Exception as e:
            print(f"  ❌ Error verificando {name}: {str(e)}")
            all_empty = False

    print(f"\n{'='*80}")
    if all_empty:
        print("✅ BASE DE DATOS COMPLETAMENTE VACÍA")
    else:
        print("⚠️  ADVERTENCIA: Algunos datos no se eliminaron correctamente")
        print("   Considera ejecutar este script nuevamente")
    print("="*80 + "\n")

    return all_empty


def show_next_steps():
    """Mostrar próximos pasos"""
    print("="*80)
    print("PRÓXIMOS PASOS")
    print("="*80 + "\n")

    print("La base de datos está vacía. Para crear datos de prueba:\n")
    print("  1. CREAR DATOS DE PRUEBA:")
    print("     python scripts/seed_data.py")
    print()
    print("  2. INICIAR EL SERVIDOR:")
    print("     python manage.py runserver")
    print()
    print("  3. VERIFICAR DATOS CREADOS:")
    print("     python scripts/diagnose_activation.py --list")
    print()

    print("="*80 + "\n")


def main():
    """Función principal"""
    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*25 + "RESET DE BASE DE DATOS" + " "*30 + "║")
    print("╚" + "="*78 + "╝")
    print("\n")

    # Pedir confirmación
    if not confirm_reset():
        return

    try:
        # 1. Eliminar todos los datos
        delete_all_data()

        # 2. Verificar que quedó vacío
        is_empty = verify_database_empty()

        # 3. Mostrar próximos pasos
        show_next_steps()

        if is_empty:
            print("✅ RESET COMPLETADO EXITOSAMENTE\n")
        else:
            print("⚠️  RESET COMPLETADO CON ADVERTENCIAS\n")

    except Exception as e:
        print(f"\n❌ ERROR CRÍTICO: {str(e)}")
        import traceback
        traceback.print_exc()
        print("\n⚠️  El reset falló. La base de datos puede estar en estado inconsistente.")
        print("    Considera ejecutar el script nuevamente o revisar los errores arriba.")


if __name__ == '__main__':
    main()
