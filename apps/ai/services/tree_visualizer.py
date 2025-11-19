"""
Servicio para visualizar el árbol de decisión y extraer reglas interpretables
"""
import os
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from sklearn.tree import plot_tree, export_text
from django.conf import settings
from apps.ai.services.diabetes_model_trainer import DiabetesModelTrainer


class TreeVisualizer:
    """Visualiza y exporta reglas del árbol de decisión"""

    FEATURE_NAMES = [
        'Embarazos',
        'Glucosa',
        'Presión Arterial',
        'Grosor Piel',
        'Insulina',
        'IMC',
        'Función Pedigree',
        'Edad'
    ]

    CLASS_NAMES = ['Sin Riesgo', 'Con Riesgo']

    @staticmethod
    def visualize_tree(save_path=None):
        """
        Genera imagen PNG del árbol de decisión

        Args:
            save_path: Ruta donde guardar la imagen. Si es None, usa ruta por defecto

        Returns:
            str: Ruta donde se guardó la imagen
        """
        # Cargar modelo activo
        model, model_db = DiabetesModelTrainer.load_active_model()

        # Definir ruta de guardado
        if save_path is None:
            media_root = settings.MEDIA_ROOT
            models_dir = os.path.join(media_root, 'models')
            os.makedirs(models_dir, exist_ok=True)
            save_path = os.path.join(models_dir, f'tree_visualization_{model_db.version}.png')

        # Crear figura con tamaño adecuado
        plt.figure(figsize=(25, 15))

        # Plotear árbol
        plot_tree(
            model,
            feature_names=TreeVisualizer.FEATURE_NAMES,
            class_names=TreeVisualizer.CLASS_NAMES,
            filled=True,
            rounded=True,
            fontsize=10,
            proportion=True,
            precision=2
        )

        plt.title(f'Árbol de Decisión - Predicción de Diabetes\nVersión: {model_db.version} | Accuracy: {model_db.accuracy:.2%}',
                  fontsize=16, pad=20)

        # Guardar imagen
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()

        return save_path

    @staticmethod
    def get_tree_rules():
        """
        Exporta reglas del árbol en formato texto interpretable

        Returns:
            dict: Contiene reglas en texto y estructura interpretable
        """
        # Cargar modelo activo
        model, model_db = DiabetesModelTrainer.load_active_model()

        # Exportar reglas en texto
        tree_rules_text = export_text(
            model,
            feature_names=TreeVisualizer.FEATURE_NAMES,
            decimals=2
        )

        # Extraer reglas interpretables
        interpretable_rules = TreeVisualizer._extract_interpretable_rules(model)

        return {
            'model_version': model_db.version,
            'accuracy': model_db.accuracy,
            'tree_depth': model.get_depth(),
            'n_leaves': model.get_n_leaves(),
            'rules_text': tree_rules_text,
            'interpretable_rules': interpretable_rules
        }

    @staticmethod
    def _extract_interpretable_rules(model):
        """
        Extrae reglas interpretables del árbol de decisión

        Args:
            model: Modelo de árbol de decisión entrenado

        Returns:
            list: Lista de reglas interpretables
        """
        tree = model.tree_
        feature_names = TreeVisualizer.FEATURE_NAMES

        def recurse(node, depth, path_conditions):
            """Función recursiva para extraer caminos del árbol"""
            if tree.feature[node] != -2:  # No es hoja
                feature = feature_names[tree.feature[node]]
                threshold = tree.threshold[node]

                # Rama izquierda (<=)
                left_conditions = path_conditions + [f"{feature} ≤ {threshold:.1f}"]
                recurse(tree.children_left[node], depth + 1, left_conditions)

                # Rama derecha (>)
                right_conditions = path_conditions + [f"{feature} > {threshold:.1f}"]
                recurse(tree.children_right[node], depth + 1, right_conditions)
            else:
                # Es una hoja - extraer predicción
                class_idx = tree.value[node].argmax()
                samples = int(tree.n_node_samples[node])
                confidence = tree.value[node][0][class_idx] / samples

                rule = {
                    'conditions': path_conditions,
                    'prediction': TreeVisualizer.CLASS_NAMES[class_idx],
                    'samples': samples,
                    'confidence': float(confidence),
                    'depth': depth
                }
                rules.append(rule)

        rules = []
        recurse(0, 0, [])

        # Ordenar por confianza descendente
        rules.sort(key=lambda x: x['confidence'], reverse=True)

        # Tomar las 10 reglas más importantes
        return rules[:10]

    @staticmethod
    def get_feature_importance_chart():
        """
        Genera gráfico de importancia de características

        Returns:
            str: Ruta donde se guardó la imagen
        """
        # Cargar modelo activo
        model, model_db = DiabetesModelTrainer.load_active_model()

        # Obtener importancias
        importances = model.feature_importances_

        # Crear gráfico
        plt.figure(figsize=(10, 6))
        indices = importances.argsort()[::-1]

        plt.bar(range(len(importances)), importances[indices])
        plt.xticks(range(len(importances)),
                   [TreeVisualizer.FEATURE_NAMES[i] for i in indices],
                   rotation=45, ha='right')
        plt.xlabel('Características')
        plt.ylabel('Importancia')
        plt.title(f'Importancia de Características - Modelo v{model_db.version}')
        plt.tight_layout()

        # Guardar
        media_root = settings.MEDIA_ROOT
        models_dir = os.path.join(media_root, 'models')
        os.makedirs(models_dir, exist_ok=True)
        save_path = os.path.join(models_dir, f'feature_importance_{model_db.version}.png')

        plt.savefig(save_path, dpi=100, bbox_inches='tight')
        plt.close()

        return save_path
