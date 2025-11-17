# 🗺️ ROADMAP DEFINITIVO - CLINIDOCS
## Plan de Trabajo para 3 Personas en Paralelo

**Tiempo total:** 4 días
**Equipo:**
- 👨‍💻 **Luis** - Desarrollador Móvil
- 🤖 **Trevor** - ML/Random Forest + IA
- ☁️ **Nataly** - AWS/Deploy + OCR + Integración

**Objetivo:** Completar funcionalidades al 100% (básico y funcional). Testing después.

---

## 👨‍💻 LUIS - DESARROLLADOR MÓVIL

**Objetivo:** App móvil funcional con lo MÁS IMPORTANTE Y LLAMATIVO

### ⚡ PRIORIDAD CRÍTICA (Días 1-2)

#### ✅ Tarea 1: Arreglar Login y Persistencia (4h)
**Archivo:** `cr_movil/lib/features/auth/`

**Qué hacer:**
1. **Arreglar SplashPage** - Verificar token al iniciar
   ```dart
   // lib/features/auth/presentation/pages/splash_page.dart
   - Verificar si hay token guardado
   - Si hay token válido → navegar a Home
   - Si token expirado → intentar refresh
   - Si no hay token → navegar a Login
   ```

2. **Implementar GoRouter** - Navegación profesional
   ```dart
   // lib/config/routes/app_routes.dart
   - Configurar GoRouter con todas las rutas
   - Deep linking básico
   - Guards para rutas protegidas
   ```

3. **Biometría (opcional pero llamativo)** - Login con huella
   ```dart
   // Usar local_auth (ya instalado)
   - Checkbox "Usar huella digital"
   - Guardar preferencia en FlutterSecureStorage
   - Login rápido con biometría
   ```

**Resultado:** Login fluido, app recuerda sesión, biometría funciona.

---

#### ✅ Tarea 2: Módulo Pacientes BÁSICO (6h)
**Archivo:** `cr_movil/lib/features/patients/`

**Qué hacer:**
1. **Cache Offline SIMPLE** (3h)
   ```dart
   // lib/features/patients/data/datasources/patient_local_datasource.dart
   - Configurar Hive box para Patient
   - Guardar lista cuando hay internet
   - Mostrar cache si no hay internet
   - Indicador visual "Modo Offline"
   ```

2. **Paginación Infinita** (2h)
   ```dart
   // lib/features/patients/presentation/pages/patients_list_page.dart
   - ScrollController listener
   - Cargar más al llegar al 80% del scroll
   - Indicador de carga abajo
   ```

3. **Pull to Refresh** (1h)
   ```dart
   - RefreshIndicator en lista
   - Actualizar cache
   ```

**Resultado:** Lista de pacientes con scroll infinito, funciona offline.

---

### ⭐ FUNCIONALIDAD LLAMATIVA (Día 3)

#### ✅ Tarea 3: Captura de Cámara + Upload (8h)
**Archivos:** `cr_movil/lib/features/camera/`, `cr_movil/lib/features/documents/`

**Qué hacer:**
1. **Módulo Camera** (5h)
   ```dart
   // lib/features/camera/presentation/pages/camera_page.dart

   Funcionalidades BÁSICAS:
   - ✅ Inicializar cámara
   - ✅ Botón de captura (grande y central)
   - ✅ Flash on/off
   - ✅ Preview de foto capturada
   - ✅ Galería de 3-5 fotos capturadas
   - ✅ Botón "Listo" para confirmar
   - ❌ NO necesitas multi-cámara
   - ❌ NO necesitas zoom avanzado
   ```

2. **Upload a Backend** (3h)
   ```dart
   // lib/features/documents/data/datasources/document_remote_datasource.dart

   - Multipart request con Dio
   - FormData con List<File>
   - Progress indicator (%)
   - Asociar a paciente específico
   - Tipo de documento (recetar, lab, rayos X, etc.)
   ```

**Resultado:** Capturar fotos de documentos médicos y subirlos. MUY LLAMATIVO.

---

### 🔔 FUNCIONALIDAD IMPORTANTE (Día 4)

#### ✅ Tarea 4: Historias Clínicas VISUALIZACIÓN (6h)
**Archivo:** `cr_movil/lib/features/clinical_records/`

**Qué hacer - SOLO VISUALIZACIÓN:**
1. **Domain + Data Layer** (2h)
   ```dart
   // Entities
   - ClinicalRecordEntity (básico: alergias, condiciones, tipo sangre)
   - ❌ NO necesitas signos vitales complejos

   // DataSource
   - Solo RemoteDataSource (sin cache por ahora)
   - GetClinicalRecordByPatient
   ```

2. **UI Simple** (4h)
   ```dart
   // ClinicalRecordDetailPage

   Mostrar:
   - ✅ Tipo de sangre (destacado)
   - ✅ Alergias (en rojo si hay)
   - ✅ Condiciones crónicas (lista)
   - ✅ Medicaciones actuales (lista)
   - ✅ Últimos formularios (lista simple)
   - ❌ NO necesitas gráficos complejos
   - ❌ NO necesitas timeline avanzado
   ```

**Resultado:** Ver historia clínica del paciente desde el detalle.

---

#### ✅ Tarea 5: Push Notifications BÁSICAS (2h)
**Archivo:** `cr_movil/lib/core/services/notification_service.dart`

**Qué hacer - MÍNIMO FUNCIONAL:**
```dart
1. Descomentar firebase_core y firebase_messaging en pubspec.yaml
2. Descargar google-services.json (Nataly te da el archivo)
3. Configurar android/app/build.gradle
4. Servicio básico:
   - Inicializar FCM
   - Obtener token
   - Enviar token a backend: POST /api/notifications/register-device/
   - Mostrar notificación local cuando llega mensaje
   - ❌ NO necesitas navegación avanzada
   - ❌ NO necesitas categorías de notificaciones
```

**Resultado:** App recibe notificaciones push básicas.

---

### 📋 CHECKLIST LUIS (Móvil)

**Día 1:**
- [ ] Arreglar SplashPage y persistencia de sesión (2h)
- [ ] Implementar GoRouter (2h)
- [ ] Biometría básica (1h)
- [ ] Cache offline para pacientes (3h)

**Día 2:**
- [ ] Paginación infinita (2h)
- [ ] Pull to refresh (1h)
- [ ] Iniciar módulo camera (5h)

**Día 3:**
- [ ] Completar camera + preview (3h)
- [ ] Upload de documentos (3h)
- [ ] Testing de captura (2h)

**Día 4:**
- [ ] Módulo clinical_records (visualización) (6h)
- [ ] Push notifications básicas (2h)

**Total estimado:** 32 horas (4 días x 8h)

---

## 🤖 TREVOR - ML / RANDOM FOREST

**Objetivo:** Modelo de predicción funcionando + ayuda en mejora de imágenes

### ⚡ PRIORIDAD 1: Random Forest (Días 1-2)

#### ✅ Tarea 1: Preparar Datos y Entrenar Modelo (8h)
**Ubicación:** `cr_backend/apps/ml/` (crear carpeta)

**Estructura:**
```
cr_backend/apps/ml/
├── __init__.py
├── models.py           # Modelo Django para guardar predicciones
├── serializers.py
├── views.py            # Endpoint de predicción
├── urls.py
├── train.py            # Script de entrenamiento
├── predict.py          # Lógica de predicción
└── models/             # Carpeta para .pkl files
    └── risk_predictor.pkl
```

**Paso a paso:**

1. **Preparar Features** (3h)
   ```python
   # apps/ml/train.py
   from apps.patients.models import Patient
   from apps.clinical_records.models import ClinicalRecord
   import pandas as pd
   import numpy as np

   def prepare_training_data():
       """
       Extraer features de pacientes y sus historias clínicas
       """
       patients = Patient.objects.all()

       data = []
       for p in patients:
           record = p.clinical_record
           if not record:
               continue

           features = {
               'age': p.age,  # Calcular edad desde birth_date
               'gender': 1 if p.gender == 'M' else 0,
               'has_allergies': 1 if record.allergies else 0,
               'num_chronic_conditions': len(record.chronic_conditions or []),
               'num_medications': len(record.current_medications or []),
               'blood_type_risk': get_blood_type_risk(record.blood_type),
               # Agregar más features relevantes
           }

           # Label: Nivel de riesgo (0=bajo, 1=medio, 2=alto)
           # Puedes calcularlo basado en condiciones crónicas, edad, etc.
           label = calculate_risk_level(p, record)

           data.append({**features, 'risk_level': label})

       return pd.DataFrame(data)

   def calculate_risk_level(patient, record):
       """Calcular nivel de riesgo basado en reglas"""
       score = 0
       if patient.age > 60:
           score += 2
       if record.chronic_conditions and len(record.chronic_conditions) > 2:
           score += 2
       if record.allergies and len(record.allergies) > 3:
           score += 1

       if score >= 4:
           return 2  # Alto
       elif score >= 2:
           return 1  # Medio
       else:
           return 0  # Bajo
   ```

2. **Entrenar Modelo** (2h)
   ```python
   # apps/ml/train.py (continuación)
   from sklearn.ensemble import RandomForestClassifier
   from sklearn.model_selection import train_test_split
   from sklearn.metrics import classification_report
   import joblib

   def train_model():
       # Preparar datos
       df = prepare_training_data()

       # Separar features y labels
       X = df.drop('risk_level', axis=1)
       y = df['risk_level']

       # Split train/test
       X_train, X_test, y_train, y_test = train_test_split(
           X, y, test_size=0.2, random_state=42
       )

       # Entrenar Random Forest
       model = RandomForestClassifier(
           n_estimators=100,
           max_depth=10,
           random_state=42
       )
       model.fit(X_train, y_train)

       # Evaluar
       score = model.score(X_test, y_test)
       print(f"Accuracy: {score}")

       y_pred = model.predict(X_test)
       print(classification_report(y_test, y_pred))

       # Guardar modelo
       joblib.dump(model, 'apps/ml/models/risk_predictor.pkl')

       return model

   if __name__ == '__main__':
       train_model()
   ```

3. **Ejecutar Entrenamiento** (1h)
   ```bash
   # Instalar dependencias
   pip install scikit-learn==1.3.0 joblib==1.3.0

   # Agregar a requirements.txt
   echo "scikit-learn==1.3.0" >> requirements.txt
   echo "joblib==1.3.0" >> requirements.txt

   # Ejecutar entrenamiento
   python apps/ml/train.py
   ```

4. **Testing Manual** (2h)
   - Verificar que el modelo se guardó en `apps/ml/models/risk_predictor.pkl`
   - Probar predicciones con datos de prueba
   - Ajustar hiperparámetros si es necesario

**Resultado:** Modelo entrenado y guardado.

---

#### ✅ Tarea 2: Crear API de Predicción (6h)
**Ubicación:** `cr_backend/apps/ml/`

**Paso a paso:**

1. **Modelo Django** (1h)
   ```python
   # apps/ml/models.py
   from django.db import models
   from apps.core.models import TenantAwareModel
   from apps.patients.models import Patient

   class RiskPrediction(TenantAwareModel):
       patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
       risk_level = models.IntegerField(choices=[
           (0, 'Bajo'),
           (1, 'Medio'),
           (2, 'Alto')
       ])
       confidence = models.FloatField()
       features_used = models.JSONField()
       predicted_at = models.DateTimeField(auto_now_add=True)

       class Meta:
           ordering = ['-predicted_at']
   ```

2. **Serializer** (1h)
   ```python
   # apps/ml/serializers.py
   from rest_framework import serializers
   from .models import RiskPrediction

   class RiskPredictionSerializer(serializers.ModelSerializer):
       risk_level_display = serializers.CharField(source='get_risk_level_display', read_only=True)
       patient_name = serializers.CharField(source='patient.full_name', read_only=True)

       class Meta:
           model = RiskPrediction
           fields = ['id', 'patient', 'patient_name', 'risk_level',
                    'risk_level_display', 'confidence', 'features_used',
                    'predicted_at']
   ```

3. **Lógica de Predicción** (2h)
   ```python
   # apps/ml/predict.py
   import joblib
   import numpy as np
   from apps.patients.models import Patient

   class RiskPredictor:
       def __init__(self):
           self.model = joblib.load('apps/ml/models/risk_predictor.pkl')

       def extract_features(self, patient):
           """Extraer features del paciente"""
           record = patient.clinical_record

           return {
               'age': patient.age,
               'gender': 1 if patient.gender == 'M' else 0,
               'has_allergies': 1 if record and record.allergies else 0,
               'num_chronic_conditions': len(record.chronic_conditions or []) if record else 0,
               'num_medications': len(record.current_medications or []) if record else 0,
               'blood_type_risk': self.get_blood_type_risk(record.blood_type if record else None),
           }

       def predict(self, patient_id):
           """Predecir riesgo de un paciente"""
           patient = Patient.objects.get(id=patient_id)
           features = self.extract_features(patient)

           # Convertir a array
           X = np.array([[
               features['age'],
               features['gender'],
               features['has_allergies'],
               features['num_chronic_conditions'],
               features['num_medications'],
               features['blood_type_risk'],
           ]])

           # Predicción
           risk_level = self.model.predict(X)[0]
           confidence = self.model.predict_proba(X).max()

           return {
               'risk_level': int(risk_level),
               'confidence': float(confidence),
               'features_used': features
           }

       @staticmethod
       def get_blood_type_risk(blood_type):
           """Asignar nivel de riesgo por tipo de sangre"""
           risk_map = {
               'O-': 0, 'O+': 1, 'A-': 2, 'A+': 3,
               'B-': 2, 'B+': 3, 'AB-': 4, 'AB+': 5
           }
           return risk_map.get(blood_type, 2)
   ```

4. **ViewSet** (2h)
   ```python
   # apps/ml/views.py
   from rest_framework import viewsets, status
   from rest_framework.decorators import action
   from rest_framework.response import Response
   from rest_framework.permissions import IsAuthenticated
   from .models import RiskPrediction
   from .serializers import RiskPredictionSerializer
   from .predict import RiskPredictor

   class RiskPredictionViewSet(viewsets.ModelViewSet):
       queryset = RiskPrediction.objects.all()
       serializer_class = RiskPredictionSerializer
       permission_classes = [IsAuthenticated]

       @action(detail=False, methods=['post'], url_path='predict')
       def predict_risk(self, request):
           """
           POST /api/ml/predict/
           Body: { "patient_id": "uuid" }
           """
           patient_id = request.data.get('patient_id')

           if not patient_id:
               return Response(
                   {'error': 'patient_id es requerido'},
                   status=status.HTTP_400_BAD_REQUEST
               )

           try:
               predictor = RiskPredictor()
               result = predictor.predict(patient_id)

               # Guardar predicción
               prediction = RiskPrediction.objects.create(
                   patient_id=patient_id,
                   risk_level=result['risk_level'],
                   confidence=result['confidence'],
                   features_used=result['features_used']
               )

               serializer = self.get_serializer(prediction)
               return Response(serializer.data)

           except Exception as e:
               return Response(
                   {'error': str(e)},
                   status=status.HTTP_500_INTERNAL_SERVER_ERROR
               )
   ```

5. **URLs** (30min)
   ```python
   # apps/ml/urls.py
   from rest_framework.routers import DefaultRouter
   from .views import RiskPredictionViewSet

   router = DefaultRouter()
   router.register(r'ml', RiskPredictionViewSet, basename='ml')

   urlpatterns = router.urls
   ```

   ```python
   # config/urls.py (agregar)
   path('api/', include('apps.ml.urls')),
   ```

**Resultado:** Endpoint funcional para predicciones.

---

### 🎨 OPCIÓN 2: Ayudar con Mejora de Imágenes (Día 3-4)

Si terminas Random Forest antes, puedes ayudar a Nataly con:

#### ✅ Tarea 3: Implementar Real-ESRGAN (opcional)

**Solo si tienes tiempo:**
```python
# apps/documents/ai_services.py (agregar)
from realesrgan import RealESRGAN

class ImageEnhancementService:
    # ... (CLAHE ya lo hace Nataly)

    def enhance_with_esrgan(self, image_path):
        """Mejorar resolución con Real-ESRGAN"""
        model = RealESRGAN('RealESRGAN_x4plus')
        sr_image = model.predict(image_path)

        output_path = image_path.replace('.png', '_esrgan.png')
        sr_image.save(output_path)
        return output_path
```

**Instalación:**
```bash
pip install realesrgan
# Descargar weights (pesado ~60MB)
```

**Nota:** Esto es OPCIONAL. Solo si Random Forest está 100% completo.

---

### 📋 CHECKLIST TREVOR (ML)

**Día 1:**
- [ ] Crear estructura de apps/ml/ (30min)
- [ ] Preparar features de entrenamiento (3h)
- [ ] Entrenar modelo Random Forest (2h)
- [ ] Instalar scikit-learn y dependencias (30min)
- [ ] Testing manual del modelo (2h)

**Día 2:**
- [ ] Modelo Django RiskPrediction (1h)
- [ ] Serializer (1h)
- [ ] Lógica de predicción (2h)
- [ ] ViewSet y endpoint (2h)
- [ ] URLs y registro (30min)
- [ ] Testing de API (1.5h)

**Día 3-4:**
- [ ] Documentar cómo usar la API (1h)
- [ ] Crear 10 predicciones de prueba (1h)
- [ ] Ajustar modelo si accuracy < 70% (2h)
- [ ] (Opcional) Real-ESRGAN si hay tiempo (4h)
- [ ] (Opcional) Frontend básico para mostrar predicciones (2h)

**Total estimado:** 24 horas (3 días x 8h)

---

## ☁️ NATALY - AWS / DEPLOY / INTEGRACIÓN

**Objetivo:** OCR funcionando, S3 verificado, mejora de imágenes, arreglar bugs

### ⚡ PRIORIDAD 1: OCR con AWS Textract (Día 1)

#### ✅ Tarea 1: Configurar AWS y Activar OCR (6h)

**Paso a paso:**

1. **Setup AWS IAM** (1h)
   ```bash
   # En AWS Console:
   1. Ir a IAM → Users → Create User
   2. Nombre: clinidocs-textract-user
   3. Attach policies:
      - AmazonTextractFullAccess
      - AmazonS3FullAccess (si S3 no está configurado)
   4. Create Access Key
   5. Copiar Access Key ID y Secret Access Key
   ```

2. **Configurar Variables de Entorno** (30min)
   ```bash
   # cr_backend/.env

   # AWS Credentials
   AWS_ACCESS_KEY_ID=AKIA...
   AWS_SECRET_ACCESS_KEY=...
   AWS_STORAGE_BUCKET_NAME=clinidocs-files-2025
   AWS_S3_REGION_NAME=us-east-1

   # OCR
   ENABLE_OCR=True
   TEXTRACT_REGION=us-east-1
   ```

3. **Verificar S3** (1h)
   ```python
   # En Django shell:
   python manage.py shell

   >>> from apps.documents.storage import S3Storage
   >>> storage = S3Storage()
   >>> storage.use_s3
   True  # Debe ser True

   # Probar subida
   >>> from django.core.files.base import ContentFile
   >>> storage.save('test.txt', ContentFile(b'test'))
   'test.txt'  # Si funciona, S3 está OK
   ```

4. **Activar Procesamiento Automático** (2h)
   ```python
   # apps/documents/views.py
   from rest_framework import viewsets, status
   from .tasks import process_document_ocr  # Importar tarea Celery

   class ClinicalDocumentViewSet(viewsets.ModelViewSet):
       # ...

       def create(self, request, *args, **kwargs):
           """Override create para trigger OCR automático"""
           response = super().create(request, *args, **kwargs)

           if response.status_code == 201:
               document_id = response.data['id']
               document_type = response.data['document_type']

               # Solo procesar PDFs e imágenes
               if document_type in ['pdf', 'image']:
                   # Lanzar tarea Celery asíncrona
                   process_document_ocr.delay(document_id)

           return response
   ```

5. **Crear Tarea Celery** (1.5h)
   ```python
   # apps/documents/tasks.py (crear archivo)
   from celery import shared_task
   from .models import ClinicalDocument
   from .services import OCRService
   import logging

   logger = logging.getLogger(__name__)

   @shared_task(bind=True, max_retries=3)
   def process_document_ocr(self, document_id):
       """Procesar OCR de un documento"""
       try:
           document = ClinicalDocument.objects.get(id=document_id)

           # Verificar que tenga archivo
           if not document.file_path:
               logger.warning(f"Document {document_id} no tiene archivo")
               return

           # Marcar como procesando
           document.ocr_status = 'processing'
           document.save()

           # Ejecutar OCR
           ocr_service = OCRService()

           if document.file_path.endswith('.pdf'):
               # PDF: usar método asíncrono
               job_id = ocr_service.extract_text_async(
                   bucket=settings.AWS_STORAGE_BUCKET_NAME,
                   file_path=document.file_path
               )
               document.ocr_job_id = job_id
               document.ocr_status = 'async_processing'
           else:
               # Imagen: procesamiento directo
               result = ocr_service.extract_text_from_s3(
                   bucket=settings.AWS_STORAGE_BUCKET_NAME,
                   file_path=document.file_path
               )
               document.ocr_text = result['text']
               document.ocr_confidence = result['confidence']
               document.ocr_status = 'completed'

           document.save()
           logger.info(f"OCR completado para documento {document_id}")

       except Exception as e:
           logger.error(f"Error en OCR: {str(e)}")
           document.ocr_status = 'failed'
           document.save()
           raise self.retry(exc=e, countdown=60)
   ```

6. **Testing** (30min)
   ```bash
   # Subir documento de prueba
   curl -X POST http://localhost:8000/api/documents/ \
     -H "Authorization: Bearer <token>" \
     -F "file=@receta_medica.pdf" \
     -F "document_type=prescription" \
     -F "patient=<patient_id>"

   # Verificar en logs de Celery
   # Debe aparecer: "OCR completado para documento..."

   # Consultar documento
   curl http://localhost:8000/api/documents/<doc_id>/
   # Debe tener ocr_text, ocr_confidence
   ```

**Resultado:** OCR procesando automáticamente todos los PDFs e imágenes.

---

#### ✅ Tarea 2: Frontend para Visualizar OCR (2h)

**Ubicación:** `cr_frontend/src/modules/documents/pages/DocumentViewerPage.tsx`

**Qué hacer:**
```typescript
// Agregar Tab "Texto Extraído" en DocumentViewerPage

// 1. Verificar si tiene OCR
{document.ocr_processed && (
  <Tab label="Texto Extraído">
    <Box sx={{ p: 3 }}>
      {/* Indicador de confianza */}
      <Box sx={{ mb: 2 }}>
        <Typography variant="subtitle2">
          Confianza del OCR: {(document.ocr_confidence * 100).toFixed(1)}%
        </Typography>
        <LinearProgress
          variant="determinate"
          value={document.ocr_confidence * 100}
          color={document.ocr_confidence > 0.8 ? 'success' : 'warning'}
        />
      </Box>

      {/* Texto extraído */}
      <Paper sx={{ p: 2, bgcolor: '#f5f5f5' }}>
        <Typography
          variant="body2"
          component="pre"
          sx={{ whiteSpace: 'pre-wrap', fontFamily: 'monospace' }}
        >
          {document.ocr_text}
        </Typography>
      </Paper>

      {/* Botón copiar */}
      <Button
        startIcon={<ContentCopyIcon />}
        onClick={() => navigator.clipboard.writeText(document.ocr_text)}
        sx={{ mt: 2 }}
      >
        Copiar Texto
      </Button>
    </Box>
  </Tab>
)}
```

**Resultado:** Ver texto extraído en el visor de documentos.

---

### 🎨 PRIORIDAD 2: Mejora de Imágenes con IA (Día 2)

#### ✅ Tarea 3: Implementar CLAHE (6h)

**Paso a paso:**

1. **Instalar Dependencias** (30min)
   ```bash
   pip install opencv-python==4.8.1.78
   pip install Pillow==10.1.0

   # Agregar a requirements.txt
   echo "opencv-python==4.8.1.78" >> requirements.txt
   echo "Pillow==10.1.0" >> requirements.txt
   ```

2. **Crear Servicio de Mejora** (3h)
   ```python
   # apps/documents/ai_services.py (crear archivo)
   import cv2
   import numpy as np
   from PIL import Image
   import os
   import logging

   logger = logging.getLogger(__name__)

   class ImageEnhancementService:
       """Servicio para mejorar calidad de imágenes médicas"""

       def enhance_with_clahe(self, image_path):
           """
           Mejorar imagen con CLAHE + Denoise + Sharpen

           Args:
               image_path: Ruta a la imagen original

           Returns:
               Ruta a la imagen mejorada
           """
           try:
               # Leer imagen
               img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)

               if img is None:
                   raise ValueError(f"No se pudo leer imagen: {image_path}")

               # 1. CLAHE (Contrast Limited Adaptive Histogram Equalization)
               clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
               enhanced = clahe.apply(img)

               # 2. Denoise (reducir ruido)
               enhanced = cv2.fastNlMeansDenoising(enhanced, h=10)

               # 3. Sharpen (aumentar nitidez)
               kernel = np.array([[-1, -1, -1],
                                 [-1,  9, -1],
                                 [-1, -1, -1]])
               enhanced = cv2.filter2D(enhanced, -1, kernel)

               # Guardar imagen mejorada
               base, ext = os.path.splitext(image_path)
               enhanced_path = f"{base}_enhanced{ext}"
               cv2.imwrite(enhanced_path, enhanced)

               logger.info(f"Imagen mejorada: {enhanced_path}")
               return enhanced_path

           except Exception as e:
               logger.error(f"Error mejorando imagen: {str(e)}")
               raise

       def enhance_color_image(self, image_path):
           """Mejorar imagen a color (para documentos)"""
           try:
               img = cv2.imread(image_path)

               # Convertir a LAB
               lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
               l, a, b = cv2.split(lab)

               # CLAHE en canal L
               clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
               l = clahe.apply(l)

               # Merge y convertir a BGR
               lab = cv2.merge([l, a, b])
               enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

               # Guardar
               base, ext = os.path.splitext(image_path)
               enhanced_path = f"{base}_enhanced{ext}"
               cv2.imwrite(enhanced_path, enhanced)

               return enhanced_path

           except Exception as e:
               logger.error(f"Error mejorando imagen color: {str(e)}")
               raise
   ```

3. **Crear Tarea Celery** (1.5h)
   ```python
   # apps/documents/tasks.py (agregar)
   from .ai_services import ImageEnhancementService

   @shared_task(bind=True, max_retries=3)
   def enhance_medical_image(self, image_id):
       """Mejorar calidad de una imagen médica"""
       try:
           from .models import MedicalImage

           image = MedicalImage.objects.get(id=image_id)

           # Marcar como procesando
           image.enhancement_status = 'processing'
           image.save()

           # Aplicar CLAHE
           service = ImageEnhancementService()
           enhanced_path = service.enhance_with_clahe(image.original_file.path)

           # Guardar ruta mejorada
           image.enhanced_file = enhanced_path
           image.enhancement_applied = True
           image.enhancement_method = 'clahe'
           image.enhancement_params = {
               'clipLimit': 2.0,
               'tileGridSize': (8, 8),
               'denoise_h': 10
           }
           image.enhancement_status = 'completed'
           image.save()

           logger.info(f"Imagen {image_id} mejorada exitosamente")

       except Exception as e:
           logger.error(f"Error mejorando imagen: {str(e)}")
           image.enhancement_status = 'failed'
           image.save()
           raise self.retry(exc=e, countdown=60)
   ```

4. **Endpoint Manual de Mejora** (1h)
   ```python
   # apps/documents/views.py (agregar)
   from rest_framework.decorators import action
   from .tasks import enhance_medical_image

   class MedicalImageViewSet(viewsets.ModelViewSet):
       # ...

       @action(detail=True, methods=['post'], url_path='enhance')
       def enhance_image(self, request, pk=None):
           """
           POST /api/medical-images/{id}/enhance/
           Trigger manual de mejora de imagen
           """
           image = self.get_object()

           if image.enhancement_applied:
               return Response({
                   'message': 'Imagen ya está mejorada',
                   'enhanced_url': image.enhanced_url
               })

           # Lanzar tarea asíncrona
           enhance_medical_image.delay(image.id)

           return Response({
               'message': 'Procesamiento iniciado',
               'status': 'processing'
           }, status=status.HTTP_202_ACCEPTED)
   ```

**Resultado:** Imágenes médicas se mejoran con CLAHE.

---

#### ✅ Tarea 4: Frontend Comparador (2h)

**Ubicación:** `cr_frontend/src/modules/documents/components/ImageComparisonViewer.tsx`

**Crear componente:**
```typescript
import React, { useState } from 'react';
import { Box, Grid, Typography, Slider, Button } from '@mui/material';

interface ImageComparisonViewerProps {
  originalUrl: string;
  enhancedUrl: string;
}

export const ImageComparisonViewer: React.FC<ImageComparisonViewerProps> = ({
  originalUrl,
  enhancedUrl
}) => {
  const [zoom, setZoom] = useState(1);

  return (
    <Box>
      {/* Controles */}
      <Box sx={{ mb: 2, display: 'flex', gap: 2, alignItems: 'center' }}>
        <Typography>Zoom:</Typography>
        <Slider
          value={zoom}
          onChange={(_, value) => setZoom(value as number)}
          min={0.5}
          max={3}
          step={0.1}
          sx={{ width: 200 }}
        />
        <Typography>{(zoom * 100).toFixed(0)}%</Typography>
      </Box>

      {/* Comparación lado a lado */}
      <Grid container spacing={2}>
        <Grid item xs={6}>
          <Typography variant="h6" gutterBottom>
            Original
          </Typography>
          <Box
            sx={{
              border: '1px solid #ccc',
              overflow: 'auto',
              height: 500
            }}
          >
            <img
              src={originalUrl}
              alt="Original"
              style={{
                transform: `scale(${zoom})`,
                transformOrigin: 'top left',
                transition: 'transform 0.2s'
              }}
            />
          </Box>
        </Grid>

        <Grid item xs={6}>
          <Typography variant="h6" gutterBottom>
            Mejorada con IA
          </Typography>
          <Box
            sx={{
              border: '1px solid #ccc',
              overflow: 'auto',
              height: 500
            }}
          >
            <img
              src={enhancedUrl}
              alt="Mejorada"
              style={{
                transform: `scale(${zoom})`,
                transformOrigin: 'top left',
                transition: 'transform 0.2s'
              }}
            />
          </Box>
        </Grid>
      </Grid>

      {/* Botones de descarga */}
      <Box sx={{ mt: 2, display: 'flex', gap: 2 }}>
        <Button href={originalUrl} download variant="outlined">
          Descargar Original
        </Button>
        <Button href={enhancedUrl} download variant="contained">
          Descargar Mejorada
        </Button>
      </Box>
    </Box>
  );
};
```

**Usar en DocumentViewerPage:**
```typescript
{document.type === 'medical_image' && document.enhanced_url && (
  <ImageComparisonViewer
    originalUrl={document.file_url}
    enhancedUrl={document.enhanced_url}
  />
)}
```

**Resultado:** Comparador visual de imágenes originales vs mejoradas.

---

### 🔧 PRIORIDAD 3: Arreglar Bugs e Incoherencias (Día 3-4)

#### ✅ Tarea 5: Auditoría de Código (4h)

**Qué revisar:**

1. **Backend - Inconsistencias** (2h)
   ```bash
   # Buscar TODOs y FIXMEs
   grep -r "TODO" cr_backend/apps/
   grep -r "FIXME" cr_backend/apps/

   # Verificar imports no usados
   flake8 cr_backend/apps/ --select=F401

   # Verificar variables no usadas
   flake8 cr_backend/apps/ --select=F841
   ```

   **Problemas comunes a buscar:**
   - Endpoints sin permisos
   - Queries N+1 (falta select_related o prefetch_related)
   - Archivos sin cerrar
   - Conexiones de DB sin cerrar
   - Serializers sin validación

2. **Frontend - Inconsistencias** (2h)
   ```bash
   # Linting
   cd cr_frontend
   npm run lint

   # Buscar console.log olvidados
   grep -r "console.log" src/

   # Buscar errores de TypeScript
   npm run type-check
   ```

   **Problemas comunes:**
   - Componentes sin tipos
   - Estados no inicializados
   - Promesas sin .catch()
   - Memory leaks (useEffect sin cleanup)

---

#### ✅ Tarea 6: Verificar Integraciones (4h)

**Checklist:**

1. **S3 Upload/Download** (1h)
   - Subir documento PDF
   - Subir imagen PNG/JPG
   - Verificar que aparece en S3
   - Descargar y verificar integridad

2. **Stripe Checkout** (1h)
   - Crear sesión de checkout
   - Completar pago en test mode
   - Verificar webhook recibido
   - Verificar pago registrado en DB

3. **Notificaciones** (1h)
   - Enviar notificación in-app
   - Verificar que aparece en frontend
   - Probar marcar como leída
   - Probar envío de email (si SendGrid configurado)

4. **Celery Tasks** (1h)
   - Verificar que worker está corriendo
   - Verificar que beat está programando tareas
   - Ejecutar backup manual
   - Verificar logs

---

### 📋 CHECKLIST NATALY (AWS/Deploy)

**Día 1: OCR**
- [ ] Crear IAM user en AWS (1h)
- [ ] Configurar variables de entorno (30min)
- [ ] Verificar S3 funcionando (1h)
- [ ] Activar procesamiento automático OCR (2h)
- [ ] Crear tarea Celery para OCR (1.5h)
- [ ] Testing con PDFs reales (1h)
- [ ] Frontend tab de texto extraído (1h)

**Día 2: Mejora de Imágenes**
- [ ] Instalar opencv-python (30min)
- [ ] Crear ImageEnhancementService con CLAHE (3h)
- [ ] Tarea Celery para mejora (1.5h)
- [ ] Endpoint manual de mejora (1h)
- [ ] Frontend ImageComparisonViewer (2h)

**Día 3: Auditoría**
- [ ] Buscar TODOs y FIXMEs (1h)
- [ ] Arreglar imports no usados (1h)
- [ ] Verificar queries N+1 (2h)
- [ ] Linting frontend (2h)
- [ ] Arreglar errores TypeScript (2h)

**Día 4: Verificación Final**
- [ ] Testing S3 (1h)
- [ ] Testing Stripe (1h)
- [ ] Testing Notificaciones (1h)
- [ ] Testing Celery (1h)
- [ ] Documentar credenciales AWS (1h)
- [ ] Crear archivo google-services.json para Luis (30min)
- [ ] Ayudar a Trevor si necesita (2.5h)

**Total estimado:** 32 horas (4 días x 8h)

---

## 🎯 COORDINACIÓN ENTRE LOS 3

### Reuniones Diarias (Stand-up)

**Cuándo:** Inicio del día (15 min)

**Qué compartir:**
- ¿Qué hice ayer?
- ¿Qué voy a hacer hoy?
- ¿Tengo algún blocker?

### Dependencias Críticas

1. **Luis depende de Nataly:**
   - Día 4: Necesita `google-services.json` para push notifications
   - Coordinar antes del mediodía del Día 3

2. **Trevor puede ayudar a Nataly:**
   - Si termina Random Forest en Día 2
   - Puede implementar Real-ESRGAN mientras Nataly hace CLAHE

3. **Todos necesitan:**
   - Backend corriendo en localhost:8000
   - Credenciales de prueba funcionando
   - Base de datos con datos del seeder

---

## 📊 RESUMEN DE PROGRESO ESPERADO

### Fin del Día 1
- Luis: Login funcional, persistencia OK ✅
- Trevor: Modelo Random Forest entrenado ✅
- Nataly: OCR procesando automáticamente ✅

### Fin del Día 2
- Luis: Pacientes offline, paginación, cámara iniciada ✅
- Trevor: API de predicción funcionando ✅
- Nataly: CLAHE mejorando imágenes ✅

### Fin del Día 3
- Luis: Cámara completa, upload funcionando ✅
- Trevor: Documentación + testing ML ✅
- Nataly: Bugs arreglados, código limpio ✅

### Fin del Día 4
- Luis: Historias clínicas + push notifications ✅
- Trevor: (Opcional) Real-ESRGAN o frontend ML ✅
- Nataly: Todo verificado, integraciones OK ✅

---

## 🚀 RESULTADO FINAL

### Móvil (Luis)
- ✅ Login con persistencia y biometría
- ✅ Lista de pacientes con cache offline
- ✅ Captura de cámara para documentos
- ✅ Ver historia clínica básica
- ✅ Push notifications básicas

### IA (Trevor)
- ✅ Random Forest prediciendo nivel de riesgo
- ✅ API de predicción funcionando
- ✅ 10+ predicciones de prueba
- ✅ (Opcional) Real-ESRGAN

### AWS/Integración (Nataly)
- ✅ OCR procesando todos los documentos
- ✅ CLAHE mejorando imágenes médicas
- ✅ S3 verificado y funcionando
- ✅ Frontend mostrando OCR y comparación
- ✅ Código sin bugs críticos
- ✅ Todas las integraciones verificadas

---

## 🎓 NOTAS FINALES

### Lo que NO se hace (porque no es crítico ahora):
- ❌ Tests automatizados (se hacen después)
- ❌ DICOM completo (básico es suficiente)
- ❌ Sincronización offline compleja en móvil
- ❌ Notificaciones push avanzadas
- ❌ Deployment a producción (se hace después)

### Lo que SÍ es crítico:
- ✅ Funcionalidades básicas pero COMPLETAS
- ✅ Todo funcionando end-to-end
- ✅ Sin errores críticos
- ✅ Datos de prueba realistas

---

**¡Con este plan y 3 personas trabajando en paralelo, completan todas las funcionalidades críticas en 4 días!**
