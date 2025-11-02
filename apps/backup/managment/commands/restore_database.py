from django.core.management.base import BaseCommand
from apps.backup.services import BackupService


class Command(BaseCommand):
    help = 'Restaurar backup de la base de datos'
    
    def add_arguments(self, parser):
        parser.add_argument(
            'job_id',
            type=str,
            help='ID del backup job a restaurar'
        )
    
    def handle(self, *args, **options):
        service = BackupService()
        job_id = options['job_id']
        
        self.stdout.write(f"Restaurando backup {job_id}...")
        self.stdout.write(self.style.WARNING("ADVERTENCIA: Esto sobrescribirá los datos actuales."))
        
        confirm = input("¿Continuar? (yes/no): ")
        
        if confirm.lower() == 'yes':
            try:
                service.restore_backup(job_id)
                self.stdout.write(self.style.SUCCESS("✓ Backup restaurado exitosamente"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error: {str(e)}"))
        else:
            self.stdout.write("Operación cancelada")