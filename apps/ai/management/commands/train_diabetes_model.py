"""
Management command para entrenar el modelo de predicción de diabetes
"""
from django.core.management.base import BaseCommand
from apps.ai.services.diabetes_model_trainer import DiabetesModelTrainer


class Command(BaseCommand):
    help = 'Entrena un modelo de predicción de diabetes usando Decision Tree'

    def add_arguments(self, parser):
        parser.add_argument(
            '--model-version',
            type=str,
            help='Versión del modelo (ej: 1.0). Si no se especifica, se genera automáticamente',
        )
        parser.add_argument(
            '--test-size',
            type=float,
            default=0.2,
            help='Proporción de datos para test (0.0 - 1.0). Default: 0.2',
        )
        parser.add_argument(
            '--max-depth',
            type=int,
            default=5,
            help='Profundidad máxima del árbol. Default: 5',
        )
        parser.add_argument(
            '--min-samples-split',
            type=int,
            default=20,
            help='Mínimo de muestras para dividir un nodo. Default: 20',
        )
        parser.add_argument(
            '--min-samples-leaf',
            type=int,
            default=10,
            help='Mínimo de muestras en una hoja. Default: 10',
        )

    def handle(self, *args, **options):
        self.stdout.write('='*60)
        self.stdout.write(self.style.SUCCESS('Entrenamiento de Modelo de Predicción de Diabetes'))
        self.stdout.write('='*60)
        self.stdout.write('')

        # Construir hiperparámetros
        hyperparameters = {
            'max_depth': options['max_depth'],
            'min_samples_split': options['min_samples_split'],
            'min_samples_leaf': options['min_samples_leaf'],
            'random_state': 42,
            'criterion': 'gini',
        }

        self.stdout.write('Configuración:')
        self.stdout.write(f"  Versión: {options.get('model_version') or 'auto'}")
        self.stdout.write(f"  Test size: {options['test_size']}")
        self.stdout.write(f"  Max depth: {hyperparameters['max_depth']}")
        self.stdout.write(f"  Min samples split: {hyperparameters['min_samples_split']}")
        self.stdout.write(f"  Min samples leaf: {hyperparameters['min_samples_leaf']}")
        self.stdout.write('')

        try:
            # Entrenar modelo
            model_db, metrics = DiabetesModelTrainer.train_model(
                version=options.get('model_version'),
                hyperparameters=hyperparameters,
                test_size=options['test_size'],
                user=None  # TODO: Obtener user del contexto si es necesario
            )

            # Mostrar resumen final
            self.stdout.write('')
            self.stdout.write('='*60)
            self.stdout.write(self.style.SUCCESS('Entrenamiento completado exitosamente'))
            self.stdout.write('='*60)
            self.stdout.write('')
            self.stdout.write(f"Modelo ID: {model_db.id}")
            self.stdout.write(f"Versión: {model_db.version}")
            self.stdout.write(f"Accuracy: {model_db.accuracy:.4f} ({model_db.accuracy*100:.2f}%)")
            self.stdout.write(f"Precision: {model_db.precision:.4f}")
            self.stdout.write(f"Recall: {model_db.recall:.4f}")
            self.stdout.write(f"F1-Score: {model_db.f1_score:.4f}")
            self.stdout.write('')

            # Interpretación de métricas
            self.stdout.write('Interpretación:')
            if model_db.accuracy >= 0.75:
                self.stdout.write(self.style.SUCCESS(f"  Accuracy: Excelente (>= 75%)"))
            elif model_db.accuracy >= 0.65:
                self.stdout.write(self.style.WARNING(f"  Accuracy: Buena (>= 65%)"))
            else:
                self.stdout.write(self.style.ERROR(f"  Accuracy: Necesita mejorar (< 65%)"))

            if model_db.recall >= 0.70:
                self.stdout.write(self.style.SUCCESS(f"  Recall: Buena detección de diabéticos (>= 70%)"))
            else:
                self.stdout.write(self.style.WARNING(f"  Recall: Podría perder casos de diabetes (< 70%)"))

            if model_db.precision >= 0.70:
                self.stdout.write(self.style.SUCCESS(f"  Precision: Bajo número de falsos positivos (>= 70%)"))
            else:
                self.stdout.write(self.style.WARNING(f"  Precision: Muchos falsos positivos (< 70%)"))

        except Exception as e:
            self.stdout.write('')
            self.stdout.write(self.style.ERROR(f'Error durante el entrenamiento: {str(e)}'))
            import traceback
            traceback.print_exc()
            return

        self.stdout.write('')
        self.stdout.write('Modelo listo para realizar predicciones')
