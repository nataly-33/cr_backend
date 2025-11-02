from django.core.management.base import BaseCommand
from apps.backup.services import BackupService
from apps.core.models import Tenant


class Command(BaseCommand):
    help = 'Crear backup de la base de datos'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--tenant',
            type=str,
            help='Slug del tenant para backup específico'
        )
        parser.add_argument(
            '--all-tenants',
            action='store_true',
            help='Backup de todos los tenants'
        )
    
    def handle(self, *args, **options):
        service = BackupService()
        
        if options['all_tenants']:
            tenants = Tenant.objects.filter(deleted_at__isnull=True)
            for tenant in tenants:
                self.stdout.write(f"Creando backup para {tenant.name}...")
                job = service.create_backup(tenant=tenant)
                self.stdout.write(self.style.SUCCESS(f"✓ Backup completado: {job.storage_location}"))
        
        elif options['tenant']:
            try:
                tenant = Tenant.objects.get(slug=options['tenant'])
                self.stdout.write(f"Creando backup para {tenant.name}...")
                job = service.create_backup(tenant=tenant)
                self.stdout.write(self.style.SUCCESS(f"✓ Backup completado: {job.storage_location}"))
            except Tenant.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Tenant '{options['tenant']}' no encontrado"))
        
        else:
            self.stdout.write("Creando backup del sistema completo...")
            job = service.create_backup()
            self.stdout.write(self.style.SUCCESS(f"✓ Backup completado: {job.storage_location}"))