# -*- coding: utf-8 -*-
import sys
import os
from django.core.management.base import BaseCommand

# Fix encoding for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

class Command(BaseCommand):
    help = 'Ejecuta el seeder de datos de prueba'

    def handle(self, *args, **options):
        # Import and run the seed_data script
        script_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'scripts')
        sys.path.insert(0, script_dir)

        # Import the seed_data module
        from scripts import seed_data

        # Run the main function
        seed_data.main()
