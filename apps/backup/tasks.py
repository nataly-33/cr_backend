from celery import shared_task
from datetime import datetime, timedelta
from django.utils import timezone
from .services import BackupService
from .models import BackupJob
from apps.core.models import Tenant


@shared_task(bind=True, name='apps.backup.tasks.crear_backup_automatico')
def crear_backup_automatico(self):
    """
    Tarea de Celery para crear backups automáticos de todos los tenants activos.
    Se ejecuta diariamente a las 2:00 AM (configurado en config/celery.py).
    """
    service = BackupService()
    resultados = {
        'exitosos': 0,
        'fallidos': 0,
        'errores': []
    }

    try:
        # Backup del sistema completo
        print(f"[{datetime.now()}] Iniciando backup automático del sistema...")

        try:
            job = service.create_backup(tenant=None, includes_files=True)
            resultados['exitosos'] += 1
            print(f"✓ Backup del sistema creado exitosamente: {job.storage_location}")
        except Exception as e:
            resultados['fallidos'] += 1
            resultados['errores'].append({
                'tenant': 'Sistema',
                'error': str(e)
            })
            print(f"✗ Error en backup del sistema: {str(e)}")

        # Backup de cada tenant activo
        tenants_activos = Tenant.objects.filter(subscription_status='active')

        for tenant in tenants_activos:
            try:
                print(f"[{datetime.now()}] Creando backup para tenant: {tenant.name}...")
                job = service.create_backup(tenant=tenant, includes_files=True)
                resultados['exitosos'] += 1
                print(f"✓ Backup creado exitosamente: {job.storage_location}")
            except Exception as e:
                resultados['fallidos'] += 1
                resultados['errores'].append({
                    'tenant': tenant.name,
                    'error': str(e)
                })
                print(f"✗ Error en backup de {tenant.name}: {str(e)}")

        print(f"\n[{datetime.now()}] Proceso de backup completado:")
        print(f"  - Backups exitosos: {resultados['exitosos']}")
        print(f"  - Backups fallidos: {resultados['fallidos']}")

        if resultados['errores']:
            print("\nErrores encontrados:")
            for error in resultados['errores']:
                print(f"  - {error['tenant']}: {error['error']}")

        return resultados

    except Exception as e:
        print(f"✗ Error crítico en tarea de backup: {str(e)}")
        raise


@shared_task(bind=True, name='apps.backup.tasks.crear_backup_tenant')
def crear_backup_tenant(self, tenant_id, includes_files=True):
    """
    Tarea de Celery para crear un backup de un tenant específico.

    Args:
        tenant_id: ID del tenant
        includes_files: Si incluir archivos o solo base de datos

    Returns:
        dict con información del backup creado
    """
    service = BackupService()

    try:
        tenant = Tenant.objects.get(id=tenant_id)
        print(f"[{datetime.now()}] Creando backup para tenant: {tenant.name}...")

        job = service.create_backup(tenant=tenant, includes_files=includes_files)

        print(f"✓ Backup creado exitosamente: {job.storage_location}")

        return {
            'success': True,
            'job_id': str(job.id),
            'tenant': tenant.name,
            'size_bytes': job.backup_size_bytes,
            'storage_location': job.storage_location,
        }

    except Tenant.DoesNotExist:
        error_msg = f"Tenant con ID {tenant_id} no encontrado"
        print(f"✗ {error_msg}")
        return {'success': False, 'error': error_msg}

    except Exception as e:
        error_msg = str(e)
        print(f"✗ Error al crear backup: {error_msg}")
        return {'success': False, 'error': error_msg}


@shared_task(bind=True, name='apps.backup.tasks.limpiar_backups_vencidos')
def limpiar_backups_vencidos(self):
    """
    Tarea de Celery para eliminar backups que han excedido su período de retención.
    Se ejecuta semanalmente los domingos a las 3:00 AM.
    """
    import os

    try:
        print(f"[{datetime.now()}] Iniciando limpieza de backups vencidos...")

        # Obtener backups vencidos
        hoy = timezone.now().date()
        backups_vencidos = BackupJob.objects.filter(
            retention_until__lt=hoy,
            status='completed'
        )

        eliminados = 0
        errores = []

        for backup in backups_vencidos:
            try:
                # Eliminar archivo físico
                if backup.storage_location and os.path.exists(backup.storage_location):
                    os.remove(backup.storage_location)
                    print(f"✓ Archivo eliminado: {backup.storage_location}")

                # Marcar como eliminado en BD
                backup.status = 'deleted'
                backup.save()

                eliminados += 1

            except Exception as e:
                errores.append({
                    'backup_id': str(backup.id),
                    'error': str(e)
                })
                print(f"✗ Error al eliminar backup {backup.id}: {str(e)}")

        resultado = {
            'eliminados': eliminados,
            'errores': len(errores),
            'detalles_errores': errores
        }

        print(f"\n[{datetime.now()}] Limpieza completada:")
        print(f"  - Backups eliminados: {eliminados}")
        print(f"  - Errores: {len(errores)}")

        return resultado

    except Exception as e:
        error_msg = f"Error crítico en limpieza de backups: {str(e)}"
        print(f"✗ {error_msg}")
        raise


@shared_task(bind=True, name='apps.backup.tasks.restaurar_backup')
def restaurar_backup(self, job_id):
    """
    Tarea de Celery para restaurar un backup.

    Args:
        job_id: ID del BackupJob a restaurar

    Returns:
        dict con resultado de la restauración
    """
    service = BackupService()

    try:
        print(f"[{datetime.now()}] Iniciando restauración de backup {job_id}...")

        result = service.restore_backup(job_id)

        print(f"✓ Backup restaurado exitosamente")

        return {
            'success': True,
            'job_id': job_id,
            'message': 'Backup restaurado correctamente'
        }

    except Exception as e:
        error_msg = str(e)
        print(f"✗ Error al restaurar backup: {error_msg}")
        return {'success': False, 'error': error_msg}
