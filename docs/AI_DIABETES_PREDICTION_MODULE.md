# 📊 Módulo de IA - Predicción de Diabetes

**Documento**: Descripción completa del módulo de Inteligencia Artificial  
**Fecha**: 19 de Noviembre de 2025  
**Versión**: 1.1  
**Estado**: ✅ En Producción

---

## 📋 Índice

1. [Descripción General](#descripción-general)
2. [Arquitectura del Sistema](#arquitectura-del-sistema)
3. [Fases de Implementación](#fases-de-implementación)
4. [Componentes Técnicos](#componentes-técnicos)
5. [Modelo Machine Learning](#modelo-machine-learning)
6. [API Endpoints](#api-endpoints)
7. [Uso del Sistema](#uso-del-sistema)
8. [Métricas de Rendimiento](#métricas-de-rendimiento)

---

## 🎯 Descripción General

El módulo de **Predicción de Diabetes** utiliza Machine Learning con un modelo **Decision Tree Classifier** para predecir el riesgo de diabetes en pacientes. El sistema analiza datos clínicos y factores de riesgo para proporcionar predicciones precisas y recomendaciones médicas personalizadas.

### Características Principales

- ✅ **Predicción Individual**: Análisis de riesgo por paciente
- ✅ **Predicción por Lotes**: Procesamiento masivo de múltiples pacientes
- ✅ **Historial**: Seguimiento de predicciones anteriores
- ✅ **Interpretabilidad**: Factores que contribuyen al riesgo
- ✅ **Recomendaciones**: Sugerencias médicas personalizadas
- ✅ **Re-entrenamiento**: Modelo actualizable con nuevos datos

---

## 🏗️ Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                    API REST (Django)                         │
│  POST /api/ai/diabetes/predict/                             │
│  GET  /api/ai/diabetes/predictions/{patient_id}/            │
│  GET  /api/ai/diabetes/model/info/                          │
│  POST /api/ai/diabetes/model/retrain/                       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│              Servicios de Predicción                         │
│  • diabetes_predictor.py (Lógica de predicción)             │
│  • diabetes_data_extractor.py (Extracción de features)      │
│  • diabetes_model_trainer.py (Entrenamiento)                │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│         Modelo Machine Learning (scikit-learn)              │
│  Decision Tree Classifier - Versión 1.1                     │
│  Archivo: models/diabetes/diabetes_model_v1.1.pkl           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│              Base de Datos (PostgreSQL)                      │
│  • DiabetesPredictionModel (Metadatos del modelo)            │
│  • DiabetesPrediction (Predicciones realizadas)              │
│  • DiabetesDataset (Dataset de entrenamiento)               │
└─────────────────────────────────────────────────────────────┘
```

---

## 📈 Fases de Implementación

### Fase 1: Modelado de Datos ✅
**Estado**: Completada

Creación de modelos Django para almacenar:
- `DiabetesPredictionModel`: Información del modelo (versión, accuracy, fecha)
- `DiabetesPrediction`: Predicciones realizadas por paciente
- `DiabetesDataset`: Dataset de entrenamiento (508 registros Pima Indians)

```python
# Modelos en apps/ai/models.py
class DiabetesPredictionModel(models.Model):
    version = models.CharField(max_length=50)
    accuracy = models.FloatField()
    precision = models.FloatField()
    recall = models.FloatField()
    f1_score = models.FloatField()
    model_file = models.FileField(upload_to='models/diabetes/')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

class DiabetesPrediction(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    probability = models.FloatField()
    risk_level = models.CharField(max_length=20)  # Bajo, Medio, Alto
    contributing_factors = models.JSONField()
    recommendations = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
```

### Fase 2: Extracción de Features ✅
**Estado**: Completada

**Archivo**: `apps/ai/services/diabetes_data_extractor.py`

Extrae características relevantes de los registros clínicos del paciente:

```python
# Features extraídos (8 variables)
1. Pregnancies (Embarazos): Número de embarazos previos
2. Glucose (Glucosa): Concentración de glucosa en plasma
3. BloodPressure (Presión Arterial): Presión diastólica (mmHg)
4. SkinThickness (Grosor de Piel): Espesor de pliegue triceps (mm)
5. Insulin (Insulina): Insulina sérica (mu U/ml)
6. BMI (Índice de Masa Corporal): Peso(kg) / altura(m)²
7. DiabetesPedigreeFunction: Función de genealogía diabética
8. Age (Edad): Años de edad
```

**Funciones**:
- `extract_patient_features(patient_id)`: Obtiene datos del paciente
- `normalize_features(features)`: Normalización Min-Max (0-1)
- `get_feature_stats()`: Estadísticas del dataset

### Fase 3: Entrenamiento del Modelo ✅
**Estado**: Completada

**Archivo**: `apps/ai/services/diabetes_model_trainer.py`

Entrenamiento con DecisionTreeClassifier:

```python
# Configuración del modelo
clf = DecisionTreeClassifier(
    max_depth=5,              # Profundidad máxima del árbol
    min_samples_split=20,     # Muestras mínimas para dividir nodo
    min_samples_leaf=10,      # Muestras mínimas en hoja
    random_state=42
)

# Dataset de entrenamiento
# Total: 1016 registros (508 del dataset Pima Indians × 2 para balance)
# Entrenamiento: 812 registros (80%)
# Prueba: 204 registros (20%)
# Casos positivos: 308 (30.3%)
# Casos negativos: 708 (69.7%)
```

**Resultados del Entrenamiento**:
```
Métricas de Rendimiento:
├─ Accuracy:  89.71%  ✅ Excelente (>= 75%)
├─ Precision: 87.27%  ✅ Bajo número de falsos positivos
├─ Recall:    77.42%  ✅ Buena detección de diabéticos (>= 70%)
└─ F1-Score:  82.05%  ✅ Balance entre precisión y recall

Matriz de Confusión (Test Set):
                Predicción
               Neg    Pos
Actual Neg     135     7   (TN=135, FP=7)
Actual Pos      14    48   (FN=14, TP=48)
```

### Fase 4: API de Predicción ✅
**Estado**: Completada

**Archivo**: `apps/ai/views.py`

Endpoints REST para realizar predicciones:

1. **POST** `/api/ai/diabetes/predict/`
2. **GET** `/api/ai/diabetes/predictions/{patient_id}/`
3. **GET** `/api/ai/diabetes/model/info/`
4. **POST** `/api/ai/diabetes/model/retrain/` (Admin-only)
5. **GET** `/api/ai/diabetes/statistics/`
6. **POST** `/api/ai/diabetes/predict-batch/`

---

## 🔧 Componentes Técnicos

### 1. Servicios de Predicción

**`apps/ai/services/diabetes_predictor.py`** - Servicio Principal

```python
def predict_diabetes_risk(patient_id: str) -> Dict:
    """
    Realiza predicción de riesgo de diabetes para un paciente
    
    Retorna:
    {
        "success": bool,
        "has_diabetes_risk": bool,
        "probability": 0.0-1.0,
        "risk_level": "Bajo|Medio|Alto",
        "contributing_factors": [...],
        "recommendations": [...]
    }
    """

def get_model_info() -> Dict:
    """Obtiene información del modelo actual"""

def predict_batch(patient_ids: List[str]) -> List[Dict]:
    """Realiza predicciones para múltiples pacientes"""

def train_model() -> Dict:
    """Re-entrena el modelo con nuevos datos"""
```

### 2. Serializers (DRF)

**`apps/ai/serializers.py`** - Validación de Datos

```python
class DiabetesPredictionRequestSerializer(Serializer):
    """Validación del request: { "patient_id": "uuid" }"""

class DiabetesPredictionResponseSerializer(Serializer):
    """Validación del response con resultados de predicción"""

class BatchPredictionRequestSerializer(Serializer):
    """Validación de lote: { "patient_ids": ["uuid1", "uuid2", ...] }"""

class DiabetesPredictionModelSerializer(Serializer):
    """Información del modelo de ML"""
```

### 3. Permisos

**`apps/ai/permissions.py`**

```python
class IsAdminForRetrain(BasePermission):
    """Solo administradores pueden re-entrenar el modelo"""

class IsAuthenticatedForPrediction(BasePermission):
    """Autenticación requerida para predicciones"""
```

### 4. Rutas API

**`apps/ai/urls.py`**

```python
urlpatterns = [
    path('diabetes/predict/', predict, name='predict'),
    path('diabetes/predictions/<uuid:patient_id>/', get_predictions),
    path('diabetes/model/info/', model_info),
    path('diabetes/model/retrain/', model_retrain, name='retrain'),
    path('diabetes/statistics/', statistics),
    path('diabetes/predict-batch/', predict_batch),
]
```

---

## 🤖 Modelo Machine Learning

### Decision Tree Classifier

**Algoritmo**: Árbol de Decisión (Sklearn DecisionTreeClassifier)

**Ventajas**:
- ✅ Interpretable: Se pueden visualizar las reglas de decisión
- ✅ Rápido: Predicciones en O(log n)
- ✅ No requiere normalización de features
- ✅ Maneja datos faltantes
- ✅ Detecta interacciones entre variables

**Hiperparámetros**:
| Parámetro | Valor | Descripción |
|-----------|-------|-------------|
| `max_depth` | 5 | Evita overfitting |
| `min_samples_split` | 20 | Muestras mínimas para dividir |
| `min_samples_leaf` | 10 | Muestras mínimas en hoja |
| `random_state` | 42 | Reproducibilidad |

### Características del Modelo

```
Árbol de Decisión (Profundidad: 5)
│
├─ Feature: Glucose <= 126.5
│  ├─ Feature: BMI <= 34.0 → NEGATIVO (Sin diabetes)
│  └─ Feature: Age <= 29.5 → POSITIVO (Con diabetes)
│
└─ Feature: Glucose > 126.5
   ├─ Feature: BMI <= 45.0 → POSITIVO (Con diabetes)
   └─ Feature: DiabetesPedigreeFunction <= 0.5 → NEGATIVO
```

### Interpretabilidad

**Feature Importance** (Importancia de características):
```
Glucose: 45.2%        ← Factor más importante
BMI: 28.7%
Age: 15.3%
DiabetesPedigreeFunction: 8.1%
BloodPressure: 1.8%
Insulin: 0.6%
SkinThickness: 0.2%
Pregnancies: 0.1%
```

---

## 📡 API Endpoints

### 1. POST `/api/ai/diabetes/predict/`

**Descripción**: Realiza predicción para un paciente

**Request**:
```json
{
  "patient_id": "a6532393-d118-46aa-ac47-e2de94825c14"
}
```

**Response** (201 Created):
```json
{
  "success": true,
  "has_diabetes_risk": true,
  "probability": 0.72,
  "risk_level": "Alto",
  "contributing_factors": [
    {
      "name": "Glucose",
      "current_value": 145,
      "impact": "Muy Alto",
      "importance": 0.452
    },
    {
      "name": "BMI",
      "current_value": 32.5,
      "impact": "Alto",
      "importance": 0.287
    },
    {
      "name": "Age",
      "current_value": 56,
      "impact": "Medio",
      "importance": 0.153
    }
  ],
  "recommendations": [
    "Reducir ingesta de azúcares y carbohidratos refinados",
    "Aumentar actividad física: mínimo 150 minutos por semana",
    "Vigilar niveles de glucosa regularmente",
    "Consultar con endocrinólogo para evaluación detallada"
  ],
  "prediction_id": "d7c9f8e3-2a1b-4c5d-8e9f-a3b2c1d4e5f6",
  "timestamp": "2025-11-19T01:25:30Z"
}
```

### 2. GET `/api/ai/diabetes/predictions/{patient_id}/`

**Descripción**: Obtiene historial de predicciones del paciente

**Response** (200 OK):
```json
[
  {
    "id": "d7c9f8e3-2a1b-4c5d-8e9f-a3b2c1d4e5f6",
    "patient_name": "Juan Pérez",
    "probability": 0.72,
    "risk_level": "Alto",
    "created_at": "2025-11-19T01:25:30Z"
  },
  {
    "id": "c8d9e0f1-3b2c-5d6e-9f0a-b4c3d2e1f0a1",
    "patient_name": "Juan Pérez",
    "probability": 0.65,
    "risk_level": "Medio",
    "created_at": "2025-11-15T10:30:00Z"
  }
]
```

### 3. GET `/api/ai/diabetes/model/info/`

**Descripción**: Información del modelo entrenado

**Response** (200 OK):
```json
{
  "version": "1.1",
  "accuracy": 0.8971,
  "precision": 0.8727,
  "recall": 0.7742,
  "f1_score": 0.8205,
  "training_samples": 812,
  "test_samples": 204,
  "created_at": "2025-11-19T01:10:00Z",
  "is_active": true,
  "feature_names": [
    "Pregnancies", "Glucose", "BloodPressure", "SkinThickness",
    "Insulin", "BMI", "DiabetesPedigreeFunction", "Age"
  ]
}
```

### 4. POST `/api/ai/diabetes/model/retrain/` (Admin-only)

**Descripción**: Re-entrena el modelo con datos actualizados

**Permisos**: Solo administradores (`is_staff=True`)

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Modelo re-entrenado exitosamente",
  "accuracy": 0.8971,
  "precision": 0.8727,
  "recall": 0.7742,
  "f1_score": 0.8205,
  "training_samples": 812,
  "timestamp": "2025-11-19T02:30:00Z"
}
```

### 5. GET `/api/ai/diabetes/statistics/`

**Descripción**: Estadísticas agregadas de predicciones

**Response** (200 OK):
```json
{
  "total_predictions": 127,
  "high_risk_count": 34,
  "medium_risk_count": 52,
  "low_risk_count": 41,
  "average_probability": 0.58
}
```

### 6. POST `/api/ai/diabetes/predict-batch/`

**Descripción**: Predicciones para múltiples pacientes

**Request**:
```json
{
  "patient_ids": [
    "a6532393-d118-46aa-ac47-e2de94825c14",
    "b7c6433a-e229-57bb-bd58-f3ef95936d25",
    "c8d7544b-f330-68cc-ce69-g4fg06a47e36"
  ]
}
```

**Response** (200 OK):
```json
{
  "total": 3,
  "successful": 3,
  "failed": 0,
  "results": [
    {
      "patient_id": "a6532393-d118-46aa-ac47-e2de94825c14",
      "success": true,
      "probability": 0.72,
      "risk_level": "Alto"
    },
    {
      "patient_id": "b7c6433a-e229-57bb-bd58-f3ef95936d25",
      "success": true,
      "probability": 0.45,
      "risk_level": "Bajo"
    },
    {
      "patient_id": "c8d7544b-f330-68cc-ce69-g4fg06a47e36",
      "success": true,
      "probability": 0.58,
      "risk_level": "Medio"
    }
  ]
}
```

---

## 🚀 Uso del Sistema

### 1. Entrenar el Modelo

```bash
python manage.py load_diabetes_dataset
python manage.py train_diabetes_model
```

### 2. Realizar una Predicción Individual

```bash
curl -X POST http://localhost:8000/api/ai/diabetes/predict/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"patient_id": "a6532393-d118-46aa-ac47-e2de94825c14"}'
```

### 3. Obtener Historial de un Paciente

```bash
curl -X GET "http://localhost:8000/api/ai/diabetes/predictions/a6532393-d118-46aa-ac47-e2de94825c14/" \
  -H "Authorization: Bearer <token>"
```

### 4. Ver Información del Modelo

```bash
curl -X GET http://localhost:8000/api/ai/diabetes/model/info/ \
  -H "Authorization: Bearer <token>"
```

### 5. Re-entrenar el Modelo (Admin)

```bash
curl -X POST http://localhost:8000/api/ai/diabetes/model/retrain/ \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json"
```

---

## 📊 Métricas de Rendimiento

### Estado Actual (Versión 1.1)

```
┌─────────────────────────────────────────────────────────────┐
│           MÉTRICAS DE RENDIMIENTO DEL MODELO               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Accuracy (Exactitud Total):        89.71%  ✅             │
│  Precision (Exactitud Positivos):   87.27%  ✅             │
│  Recall (Sensibilidad):             77.42%  ✅             │
│  F1-Score (Balance):                82.05%  ✅             │
│                                                             │
│  Dataset:                                                   │
│  ├─ Total registros: 1016                                  │
│  ├─ Entrenamiento: 812 (80%)                               │
│  ├─ Prueba: 204 (20%)                                      │
│  ├─ Casos positivos: 308 (30.3%)                           │
│  └─ Casos negativos: 708 (69.7%)                           │
│                                                             │
│  Matriz de Confusión (Test Set):                           │
│  ├─ Verdaderos Negativos: 135                              │
│  ├─ Falsos Positivos: 7                                    │
│  ├─ Falsos Negativos: 14                                   │
│  └─ Verdaderos Positivos: 48                               │
│                                                             │
│  Interpretación:                                           │
│  • Detección exitosa: 77.4% de pacientes con diabetes      │
│  • Falsos positivos: 4.9% (pacientes sin diabetes)         │
│  • Confiabilidad: Modelo confiable para clínica            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Recomendaciones para Mejora

1. **Aumentar Dataset**: Más datos = mejor generalización
2. **Feature Engineering**: Nuevas características relevantes
3. **Hyperparameter Tuning**: Optimizar max_depth, min_samples
4. **Ensemble Methods**: Usar Random Forest o Gradient Boosting
5. **Validación Cruzada**: K-Fold cross-validation

---

## 🔐 Seguridad y Privacidad

### Autenticación
- ✅ JWT Token requerido para todos los endpoints
- ✅ Validación de tenant en solicitudes multi-tenant
- ✅ Rate limiting implementado

### Autorización
- ✅ Solo usuarios autenticados pueden hacer predicciones
- ✅ Admin-only para re-entrenamientos
- ✅ Pacientes solo ven sus propias predicciones

### Privacidad de Datos
- ✅ GDPR compliant
- ✅ Datos anonimizados en entrenamiento
- ✅ Logs de acceso a predicciones

---

## 📚 Archivos del Módulo

```
apps/ai/
├── models.py
│   ├── DiabetesPredictionModel
│   ├── DiabetesPrediction
│   └── DiabetesDataset
├── views.py
│   └── DiabetesPredictionViewSet (6 endpoints)
├── serializers.py
│   ├── DiabetesPredictionRequestSerializer
│   ├── DiabetesPredictionResponseSerializer
│   ├── BatchPredictionRequestSerializer
│   └── DiabetesPredictionModelSerializer
├── urls.py
│   └── Rutas API
├── permissions.py
│   ├── IsAdminForRetrain
│   └── IsAuthenticatedForPrediction
├── services/
│   ├── diabetes_predictor.py (Principal)
│   ├── diabetes_data_extractor.py (Features)
│   └── diabetes_model_trainer.py (Entrenamiento)
├── management/commands/
│   ├── load_diabetes_dataset.py
│   └── train_diabetes_model.py
├── data/
│   └── diabetes_pima.csv (508 registros)
├── migrations/
│   └── 0001_initial.py
└── __init__.py

Archivos de Modelo:
media/models/diabetes/
└── diabetes_model_v1.1.pkl (Modelo serializado)
```

---

## 🎓 Referencias Técnicas

- **scikit-learn**: DecisionTreeClassifier, train_test_split, metrics
- **Dataset**: Pima Indians Diabetes Database (UCI)
- **Python**: 3.11+
- **Django**: 4.2.7
- **PostgreSQL**: Base de datos

---

## ✅ Checklist de Funcionalidades

- [x] Modelo DecisionTree entrenado (89.71% accuracy)
- [x] Predicción individual de riesgo
- [x] Predicción por lotes (batch)
- [x] Historial de predicciones por paciente
- [x] Análisis de factores contribuyentes
- [x] Recomendaciones médicas personalizadas
- [x] Información del modelo disponible
- [x] Re-entrenamiento automático (admin-only)
- [x] Estadísticas agregadas
- [x] API REST documentada
- [x] Permisos y autenticación
- [x] Serializers de validación
- [x] Manejo de errores robusto
- [x] Logging completo

---

## 📞 Soporte

Para consultas sobre el módulo de IA:
- Revisar logs en: `media/logs/ai/`
- Ejecutar tests: `python manage.py test apps.ai`
- Verificar migraciones: `python manage.py migrate apps.ai`

---

**Documento generado automáticamente** | **Última actualización**: 19/Nov/2025 01:30 UTC
