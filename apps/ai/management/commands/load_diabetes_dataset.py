"""
Management command para cargar el dataset Pima Indians a la base de datos
"""
import csv
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from apps.ai.models import DiabetesDataset


class Command(BaseCommand):
    help = 'Carga el dataset Pima Indians de diabetes a la base de datos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Elimina todos los datos existentes antes de cargar',
        )

    def handle(self, *args, **options):
        # Ruta al archivo CSV
        csv_path = os.path.join(
            settings.BASE_DIR,
            'apps', 'ai', 'data', 'diabetes_pima.csv'
        )

        # Verificar que el archivo existe
        if not os.path.exists(csv_path):
            self.stdout.write(self.style.ERROR(f'Archivo no encontrado: {csv_path}'))
            return

        # Limpiar datos existentes si se especifica
        if options['clear']:
            deleted_count = DiabetesDataset.objects.filter(source='pima').delete()[0]
            self.stdout.write(self.style.WARNING(f'Eliminados {deleted_count} registros existentes'))

        # Cargar datos desde CSV
        loaded_count = 0
        skipped_count = 0

        self.stdout.write('Cargando dataset Pima Indians...')

        with open(csv_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)

            for row in reader:
                try:
                    # Crear registro en la base de datos
                    DiabetesDataset.objects.create(
                        source='pima',
                        pregnancies=int(row['Pregnancies']),
                        glucose=float(row['Glucose']),
                        blood_pressure=float(row['BloodPressure']),
                        skin_thickness=float(row['SkinThickness']),
                        insulin=float(row['Insulin']),
                        bmi=float(row['BMI']),
                        diabetes_pedigree_function=float(row['DiabetesPedigreeFunction']),
                        age=int(row['Age']),
                        outcome=bool(int(row['Outcome'])),
                        is_training_data=True  # Todos son datos de entrenamiento inicialmente
                    )
                    loaded_count += 1

                    if loaded_count % 100 == 0:
                        self.stdout.write(f'  Cargados {loaded_count} registros...')

                except Exception as e:
                    skipped_count += 1
                    self.stdout.write(
                        self.style.WARNING(f'Error en fila {loaded_count + skipped_count}: {str(e)}')
                    )

        # Resumen
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Carga completada exitosamente'))
        self.stdout.write(f'  Registros cargados: {loaded_count}')
        self.stdout.write(f'  Registros omitidos: {skipped_count}')

        # Estadísticas del dataset
        total = DiabetesDataset.objects.filter(source='pima').count()
        with_diabetes = DiabetesDataset.objects.filter(source='pima', outcome=True).count()
        without_diabetes = total - with_diabetes

        self.stdout.write('')
        self.stdout.write('Estadísticas del dataset:')
        self.stdout.write(f'  Total: {total}')
        self.stdout.write(f'  Con diabetes: {with_diabetes} ({with_diabetes/total*100:.1f}%)')
        self.stdout.write(f'  Sin diabetes: {without_diabetes} ({without_diabetes/total*100:.1f}%)')
