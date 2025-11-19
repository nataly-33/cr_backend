"""
Servicio para entrenar el modelo de predicción de diabetes
usando scikit-learn (Decision Tree Classifier)
"""
import os
import joblib
from datetime import datetime
from typing import Dict, Tuple
import numpy as np
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix
)
from django.conf import settings
from apps.ai.models import DiabetesDataset, DiabetesPredictionModel


class DiabetesModelTrainer:
    """Entrenador del modelo de predicción de diabetes"""

    # Hiperparámetros por defecto para el Decision Tree
    DEFAULT_HYPERPARAMETERS = {
        'max_depth': 5,
        'min_samples_split': 20,
        'min_samples_leaf': 10,
        'random_state': 42,
        'criterion': 'gini',  # o 'entropy'
    }

    # Nombres de las features en orden
    FEATURE_NAMES = [
        'pregnancies',
        'glucose',
        'blood_pressure',
        'skin_thickness',
        'insulin',
        'bmi',
        'diabetes_pedigree_function',
        'age'
    ]

    @staticmethod
    def train_model(
        version: str = None,
        hyperparameters: Dict = None,
        test_size: float = 0.2,
        user=None
    ) -> Tuple[DiabetesPredictionModel, Dict]:
        """
        Entrena un nuevo modelo de predicción de diabetes

        Args:
            version: Versión del modelo (ej: "1.0")
            hyperparameters: Hiperparámetros personalizados
            test_size: Proporción de datos para test (0.0 - 1.0)
            user: Usuario que entrena el modelo

        Returns:
            Tuple (modelo_db, métricas_dict)
        """
        # Generar versión automática si no se especifica
        if not version:
            version = DiabetesModelTrainer._generate_version()

        # Usar hiperparámetros por defecto si no se especifican
        if not hyperparameters:
            hyperparameters = DiabetesModelTrainer.DEFAULT_HYPERPARAMETERS.copy()

        # Paso 1: Cargar datos desde la base de datos
        print("Cargando dataset desde base de datos...")
        X, y = DiabetesModelTrainer._load_dataset_from_db()

        print(f"  Total registros: {len(X)}")
        print(f"  Features: {len(X[0])}")
        print(f"  Casos positivos (diabetes): {sum(y)}")
        print(f"  Casos negativos: {len(y) - sum(y)}")

        # Paso 2: Dividir en train/test
        print(f"\nDividiendo dataset (test_size={test_size})...")
        X_train, X_test, y_train, y_test = train_test_split(
            X, y,
            test_size=test_size,
            random_state=42,
            stratify=y  # Mantiene proporción de clases
        )

        print(f"  Train: {len(X_train)} registros")
        print(f"  Test: {len(X_test)} registros")

        # Paso 3: Entrenar modelo
        print("\nEntrenando Decision Tree Classifier...")
        model = DecisionTreeClassifier(**hyperparameters)
        model.fit(X_train, y_train)

        print("  Modelo entrenado exitosamente")

        # Paso 4: Evaluar en conjunto de test
        print("\nEvaluando modelo...")
        y_pred = model.predict(X_test)

        # Calcular métricas
        metrics = {
            'accuracy': accuracy_score(y_test, y_pred),
            'precision': precision_score(y_test, y_pred, zero_division=0),
            'recall': recall_score(y_test, y_pred, zero_division=0),
            'f1_score': f1_score(y_test, y_pred, zero_division=0),
            'confusion_matrix': confusion_matrix(y_test, y_pred).tolist(),
            'training_samples': len(X_train),
            'test_samples': len(X_test),
        }

        print(f"  Accuracy:  {metrics['accuracy']:.4f}")
        print(f"  Precision: {metrics['precision']:.4f}")
        print(f"  Recall:    {metrics['recall']:.4f}")
        print(f"  F1-Score:  {metrics['f1_score']:.4f}")

        # Matriz de confusión
        tn, fp, fn, tp = np.array(metrics['confusion_matrix']).ravel()
        print(f"\n  Matriz de Confusión:")
        print(f"    TN: {tn}  FP: {fp}")
        print(f"    FN: {fn}  TP: {tp}")

        # Paso 5: Guardar modelo en archivo
        print("\nGuardando modelo...")
        model_path = DiabetesModelTrainer._save_model_file(model, version)
        print(f"  Modelo guardado en: {model_path}")

        # Paso 6: Guardar información en base de datos
        print("\nRegistrando en base de datos...")

        # Desactivar otros modelos activos
        DiabetesPredictionModel.objects.filter(is_active=True).update(is_active=False)

        # Crear nuevo registro
        model_db = DiabetesPredictionModel.objects.create(
            version=version,
            model_file=model_path,
            algorithm='DecisionTreeClassifier',
            accuracy=metrics['accuracy'],
            precision=metrics['precision'],
            recall=metrics['recall'],
            f1_score=metrics['f1_score'],
            training_samples=metrics['training_samples'],
            test_samples=metrics['test_samples'],
            features_used=DiabetesModelTrainer.FEATURE_NAMES,
            hyperparameters=hyperparameters,
            confusion_matrix=metrics['confusion_matrix'],
            is_active=True,
            trained_by=user,
            notes=f"Modelo entrenado automáticamente el {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )

        print(f"  Modelo registrado con ID: {model_db.id}")
        print(f"  Versión: {version}")

        return model_db, metrics

    @staticmethod
    def _load_dataset_from_db() -> Tuple[np.ndarray, np.ndarray]:
        """
        Carga el dataset desde la base de datos

        Returns:
            Tuple (X, y) donde X son las features y y es el target
        """
        # Obtener todos los registros marcados como training_data
        records = DiabetesDataset.objects.filter(is_training_data=True).values(
            'pregnancies',
            'glucose',
            'blood_pressure',
            'skin_thickness',
            'insulin',
            'bmi',
            'diabetes_pedigree_function',
            'age',
            'outcome'
        )

        if not records:
            raise ValueError("No hay datos de entrenamiento en la base de datos")

        # Convertir a arrays numpy
        X = []
        y = []

        for record in records:
            X.append([
                record['pregnancies'],
                record['glucose'],
                record['blood_pressure'],
                record['skin_thickness'],
                record['insulin'],
                record['bmi'],
                record['diabetes_pedigree_function'],
                record['age'],
            ])
            y.append(1 if record['outcome'] else 0)

        return np.array(X), np.array(y)

    @staticmethod
    def _save_model_file(model, version: str) -> str:
        """
        Guarda el modelo entrenado en archivo .pkl

        Returns:
            Ruta relativa al archivo guardado
        """
        # Crear directorio para modelos si no existe
        models_dir = os.path.join(settings.MEDIA_ROOT, 'models', 'diabetes')
        os.makedirs(models_dir, exist_ok=True)

        # Nombre del archivo
        filename = f"diabetes_model_v{version}.pkl"
        file_path = os.path.join(models_dir, filename)

        # Guardar modelo con joblib
        joblib.dump(model, file_path)

        # Retornar ruta relativa
        relative_path = os.path.join('models', 'diabetes', filename)
        return relative_path

    @staticmethod
    def _generate_version() -> str:
        """
        Genera un número de versión automático

        Returns:
            String de versión (ej: "1.0", "1.1", "2.0")
        """
        # Obtener última versión
        last_model = DiabetesPredictionModel.objects.order_by('-created_at').first()

        if not last_model:
            return "1.0"

        # Parsear última versión
        try:
            parts = last_model.version.split('.')
            major = int(parts[0])
            minor = int(parts[1]) if len(parts) > 1 else 0

            # Incrementar versión menor
            minor += 1
            return f"{major}.{minor}"
        except:
            # Si no se puede parsear, usar timestamp
            return datetime.now().strftime("%Y%m%d.%H%M")

    @staticmethod
    def load_active_model():
        """
        Carga el modelo activo desde archivo

        Returns:
            Tupla (modelo_sklearn, modelo_db)
        """
        # Obtener modelo activo de la base de datos
        model_db = DiabetesPredictionModel.objects.filter(is_active=True).first()

        if not model_db:
            raise ValueError("No hay ningún modelo activo en el sistema")

        # Cargar archivo .pkl
        file_path = os.path.join(settings.MEDIA_ROOT, model_db.model_file)

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Archivo del modelo no encontrado: {file_path}")

        model = joblib.load(file_path)

        return model, model_db

    @staticmethod
    def get_feature_importance(model) -> Dict[str, float]:
        """
        Obtiene la importancia de cada feature

        Args:
            model: Modelo sklearn entrenado

        Returns:
            Dict con nombre de feature y su importancia
        """
        if not hasattr(model, 'feature_importances_'):
            return {}

        importance = model.feature_importances_
        return dict(zip(DiabetesModelTrainer.FEATURE_NAMES, importance.tolist()))
