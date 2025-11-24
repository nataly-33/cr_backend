# Guía: Sistema de Predicción de Diabetes

## 📋 **Resumen del Sistema**

El sistema de predicción de diabetes extrae automáticamente datos del historial clínico del paciente y utiliza un modelo de Machine Learning (Decision Tree) para predecir el riesgo de diabetes.

### **Features Utilizadas (8)**

1. **Age** (Edad) - Calculada desde fecha de nacimiento
2. **Pregnancies** (Embarazos) - Solo para mujeres, desde historial
3. **Glucose** (Glucosa) - Desde orden de laboratorio "Glucosa en ayunas"
4. **BloodPressure** (Presión arterial diastólica) - Desde triaje
5. **SkinThickness** (Grosor de piel) - Valor por defecto 20.0
6. **Insulin** (Insulina) - Desde orden de laboratorio "Insulina sérica"
7. **BMI** (Índice de masa corporal) - Calculado de peso/altura del triaje
8. **DiabetesPedigreeFunction** - Calculado desde family_history

### **Rendimiento del Modelo (v1.2)**

- ✅ **Accuracy: 85.98%**
- ✅ **Precision: 72.97%**
- ✅ **Recall: 84.38%**
- ✅ **Dataset: 1066 registros** (508 Pima + 558 sintéticos)

---

## 🚀 **Paso 1: Generar Datos Clínicos para tus Pacientes**

### **Comando: Agregar datos clínicos masivamente**

```bash
cd cr_backend

# Opción A: Agregar datos a TODOS los pacientes que no los tienen
python manage.py add_clinical_data_to_patients --all

# Opción B: Agregar datos a un paciente específico
python manage.py add_clinical_data_to_patients --patient-id <UUID>

# Opción C: Agregar datos a todos los pacientes de un tenant
python manage.py add_clinical_data_to_patients --all --tenant-id <UUID>
```

### **¿Qué hace este comando?**

Para cada paciente SIN datos completos:

1. ✅ Crea una historia clínica (`ClinicalRecord`) si no existe
2. ✅ Genera un formulario de **triaje** con:
   - Peso (kg)
   - Altura (cm)
   - Presión arterial sistólica/diastólica
   - Frecuencia cardíaca
   - Temperatura
3. ✅ Genera orden de **glucosa en ayunas**
4. ✅ Genera orden de **insulina sérica**
5. ✅ Agrega historial familiar al 30% de los pacientes

### **Distribución de Datos**

- 📊 **80% saludables**: Glucosa ~95 mg/dL, IMC ~25, presión normal
- 📊 **20% con riesgo**: Glucosa ~125 mg/dL, IMC ~30, presión elevada

---

## 🔍 **Paso 2: Verificar que el Paciente tiene Datos Completos**

### **Método 1: Usando la API**

```bash
GET /api/patients/<patient_id>/
```

Revisar que el paciente tenga:
- `clinical_record` activo
- Al menos 1 triaje (`form_type: triage`)
- Al menos 1 orden de glucosa (`test_name: Glucosa en ayunas`)
- Al menos 1 orden de insulina (`test_name: Insulina sérica`)

### **Método 2: Directamente en la base de datos**

```sql
-- Ver paciente con sus formularios
SELECT
    p.first_name,
    p.last_name,
    p.identity_document,
    cf.form_type,
    cf.form_data->>'test_name' as test_name
FROM patient p
JOIN clinical_record cr ON cr.patient_id = p.id
LEFT JOIN clinical_form cf ON cf.clinical_record_id = cr.id
WHERE p.id = '<patient-uuid>'
ORDER BY cf.form_date DESC;
```

---

## 🎯 **Paso 3: Realizar una Predicción**

### **Opción A: Desde el Frontend**

1. Navega al detalle del paciente: `/patients/<patient_id>`
2. Haz clic en "Ver Predicción" en la tarjeta "Análisis Predictivo de Diabetes"
3. El sistema mostrará:
   - ✅ Predicción (Positiva/Negativa)
   - ✅ Nivel de riesgo (Bajo/Moderado/Alto)
   - ✅ Confianza del modelo
   - ✅ Historial de predicciones anteriores

### **Opción B: Usando la API REST**

```bash
POST /api/ai/diabetes/predict/
Content-Type: application/json
Authorization: Bearer <token>

{
  "patient_id": "<patient-uuid>"
}
```

**Respuesta:**

```json
{
  "success": true,
  "message": "Predicción realizada exitosamente",
  "data": {
    "id": "uuid",
    "patient": "uuid",
    "prediction": 0,  // 0 = No diabetes, 1 = Diabetes
    "probability_no_diabetes": 0.75,
    "probability_diabetes": 0.25,
    "risk_level": "low",  // low, moderate, high
    "model_version": "1.2",
    "features_used": {
      "age": 45,
      "glucose": 98.5,
      "bmi": 24.3,
      "blood_pressure": 78.0,
      "insulin": 85.2,
      "diabetes_pedigree_function": 0.5,
      "pregnancies": 0,
      "skin_thickness": 20.0
    },
    "prediction_date": "2025-11-19T06:00:00Z"
  }
}
```

---

## 🧬 **Paso 4: Comprobar Impacto del Historial Familiar**

### **¿Cómo afecta el historial familiar?**

El campo `family_history` en `ClinicalRecord` se analiza automáticamente y se convierte en la feature `diabetes_pedigree_function`:

| Historial Familiar | Pedigree Score | Ejemplo |
|-------------------|----------------|---------|
| Sin antecedentes | 0.5 (neutral) | "Sin antecedentes familiares de diabetes" |
| Familiar lejano | 0.9 | "Tío abuelo con diabetes" |
| Familiar 2º grado | 0.9 | "Abuela materna con diabetes tipo 2" |
| Familiar 1er grado | 1.5 | "Madre con diabetes tipo 2" |
| Múltiples familiares | 1.5 | "Madre y abuela con diabetes" |
| Ambos padres | 2.0 | "Padre y madre con diabetes tipo 2" |

### **Prueba Manual**

```python
# 1. Editar historial familiar del paciente
from apps.clinical_records.models import ClinicalRecord

cr = ClinicalRecord.objects.get(patient_id='<uuid>')
cr.family_history = 'Madre con diabetes tipo 2 diagnosticada a los 50 años'
cr.save()

# 2. Hacer una nueva predicción (desde frontend o API)
# El pedigree_function ahora será ~1.5 en lugar de 0.5

# 3. Comparar probabilidades
# Verás que la probabilidad de diabetes aumentó
```

### **Ejemplo Real**

**SIN historial familiar:**
```
diabetes_pedigree_function: 0.5
Probabilidad diabetes: 15%
```

**CON historial fuerte (ambos padres):**
```
diabetes_pedigree_function: 2.0
Probabilidad diabetes: 35%  (+20%)
```

---

## 📊 **Paso 5: Ver Visualizaciones del Modelo**

### **Árbol de Decisión Completo**

Navega a: `/ai/decision-tree`

**Pestaña 1: Visualización del Árbol**
- Imagen completa del árbol de decisión
- Muestra todas las reglas y splits

**Pestaña 2: Reglas Interpretables**
- Top 10 reglas más importantes
- Formato legible: "Si Glucose > 127.5 y Age > 28.5 → Diabetes (95% confianza)"

**Pestaña 3: Importancia de Features**
- Gráfico de barras mostrando qué features son más importantes
- Generalmente: Glucose > BMI > Age > DiabetesPedigreeFunction

---

## 🔧 **Comandos Útiles**

### **Ver información del modelo activo**

```bash
GET /api/ai/diabetes/model/info/
```

### **Ver historial de predicciones de un paciente**

```bash
GET /api/ai/diabetes/patient/<patient_id>/
```

### **Generar más pacientes sintéticos**

```bash
python manage.py generate_synthetic_patients --count 100 --clean
python manage.py extract_synthetic_dataset
python manage.py train_diabetes_model
```

---

## ❓ **Preguntas Frecuentes**

### **1. ¿Qué pasa si el paciente no tiene todos los datos?**

El extractor usa valores por defecto seguros:
- Glucosa: 120.0 mg/dL
- Insulina: 100.0 µU/mL
- IMC: 25.0
- Presión: 80.0 mmHg
- SkinThickness: 20.0 mm
- DiabetesPedigreeFunction: 0.5

### **2. ¿Cómo agrego datos manualmente?**

Puedes crear formularios clínicos directamente desde el frontend:
1. Ve al detalle del paciente
2. Crea un nuevo triaje con peso, altura, presión
3. Crea órdenes de laboratorio con resultados de glucosa e insulina

### **3. ¿Se puede modificar el modelo?**

Sí, entrena un nuevo modelo:

```bash
python manage.py train_diabetes_model --max-depth 7 --min-samples-split 15
```

### **4. ¿Dónde están los datos?**

Todo está en PostgreSQL:
- **Pacientes**: Tabla `patient`
- **Historias clínicas**: Tabla `clinical_record`
- **Formularios**: Tabla `clinical_form` (JSON flexible)
- **Dataset ML**: Tabla `diabetes_dataset`
- **Predicciones**: Tabla `diabetes_prediction`
- **Modelo**: Archivo `models/diabetes/diabetes_model_v1.2.pkl`

---

## 🎓 **Flujo Completo de Ejemplo**

```bash
# 1. Agregar datos a todos los pacientes
python manage.py add_clinical_data_to_patients --all

# 2. Verificar que se crearon
# → 69 pacientes procesados

# 3. Hacer predicción desde frontend
# → Navegar a /patients/<id>/diabetes-prediction
# → Click en "Predecir Riesgo de Diabetes"

# 4. Ver resultado
# → Predicción: NEGATIVA
# → Riesgo: BAJO (15%)
# → Features usadas: {glucose: 95, bmi: 24.3, ...}

# 5. Modificar historial familiar
# → Editar paciente en admin o API
# → Agregar: "Madre con diabetes tipo 2"

# 6. Hacer nueva predicción
# → Riesgo aumenta a MODERADO (35%)

# 7. Ver árbol de decisión
# → Navegar a /ai/decision-tree
# → Ver reglas: "Si Glucose > 127 → Alta probabilidad"
```

---

## ✅ **Checklist de Verificación**

- [ ] Todos los pacientes tienen `clinical_record` activo
- [ ] Todos los pacientes tienen triaje con peso y altura
- [ ] Todos los pacientes tienen orden de glucosa
- [ ] Todos los pacientes tienen orden de insulina
- [ ] ~30% de pacientes tienen `family_history` completo
- [ ] El modelo v1.2 está activo (accuracy 85.98%)
- [ ] El frontend muestra la predicción correctamente
- [ ] Las visualizaciones del árbol se cargan

---

## 🚨 **Troubleshooting**

### **Error: "No se pudo extraer features del paciente"**

**Causa**: Faltan datos clínicos

**Solución**:
```bash
python manage.py add_clinical_data_to_patients --patient-id <uuid>
```

### **Error: "No hay modelo activo"**

**Causa**: El modelo no está entrenado

**Solución**:
```bash
python manage.py train_diabetes_model
```

### **Error: 404 en visualización del árbol**

**Causa**: Servidor no reiniciado

**Solución**:
```bash
# Reiniciar Django
python manage.py runserver
```

---

¡Todo listo para hacer predicciones masivas! 🎉
