# 🤖 SPRINT 4: IA y Tecnología Avanzada (1 semana)

## 📊 CONTEXTO DEL SPRINT

- **Duración:** 7 días (1 semana completa)
- **Objetivo:** Implementar TODA la funcionalidad de IA y tecnología avanzada
- **Enfoque:** Machine Learning, OCR, Mejora de imágenes, DICOM, RandomForest
- **Equipo:** 3-4 personas
- **Prerequisito:** Sprint 3 completado (móvil básico funcionando)

---

## 🎯 HISTORIAS DE USUARIO - SPRINT 4 (Puro IA)

### 🤖 HU19: Gestión Móvil Avanzada (Edición + Captura)
**Prioridad:** ALTA
**Tiempo estimado:** 12-16 horas (2 días)
**Responsable:** 1-2 personas mobile

**Descripción:**
Como **Doctor**, quiero EDITAR datos, CAPTURAR fotos y CREAR formularios desde mi móvil para trabajar en campo sin limitaciones.

**Criterios de Aceptación:**
- [ ] Capturar foto con cámara del teléfono
- [ ] Subir foto como documento clínico
- [ ] Crear formulario de triaje desde móvil
- [ ] Editar datos básicos de paciente
- [ ] Zoom y scroll en imágenes
- [ ] Sincronización offline básica (opcional)

**Tablas Involucradas:**
- `patient` (actualización)
- `clinical_document` (creación)
- `clinical_form` (creación)

**Implementación Flutter:**

```dart
// lib/screens/camera_capture_screen.dart
import 'package:camera/camera.dart';
import 'package:image_picker/image_picker.dart';

class CameraCaptureScreen extends StatefulWidget {
  @override
  _CameraCaptureScreenState createState() => _CameraCaptureScreenState();
}

class _CameraCaptureScreenState extends State<CameraCaptureScreen> {
  final ImagePicker _picker = ImagePicker();
  XFile? _imageFile;

  Future<void> captureImage() async {
    final XFile? photo = await _picker.pickImage(
      source: ImageSource.camera,
      maxWidth: 1920,
      maxHeight: 1080,
      imageQuality: 85,
    );

    if (photo != null) {
      setState(() => _imageFile = photo);
    }
  }

  Future<void> uploadImage() async {
    if (_imageFile == null) return;

    final bytes = await _imageFile!.readAsBytes();
    final fileName = _imageFile!.name;

    // Crear multipart request
    var request = http.MultipartRequest(
      'POST',
      Uri.parse('${ApiService.baseUrl}/api/documents/upload/'),
    );

    request.headers['Authorization'] = 'Bearer ${ApiService.token}';
    request.files.add(
      http.MultipartFile.fromBytes('file', bytes, filename: fileName),
    );

    request.fields['clinical_record_id'] = widget.clinicalRecordId;
    request.fields['document_type'] = 'imaging_report';
    request.fields['title'] = 'Foto capturada desde móvil';

    var response = await request.send();

    if (response.statusCode == 201) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Imagen subida exitosamente')),
      );
      Navigator.pop(context);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Capturar Foto')),
      body: Column(
        children: [
          if (_imageFile != null)
            Expanded(child: Image.file(File(_imageFile!.path))),

          ElevatedButton.icon(
            onPressed: captureImage,
            icon: Icon(Icons.camera),
            label: Text('Tomar Foto'),
          ),

          if (_imageFile != null)
            ElevatedButton.icon(
              onPressed: uploadImage,
              icon: Icon(Icons.upload),
              label: Text('Subir Imagen'),
            ),
        ],
      ),
    );
  }
}
```

```dart
// lib/screens/patient_edit_screen.dart
class PatientEditScreen extends StatefulWidget {
  final Patient patient;

  @override
  _PatientEditScreenState createState() => _PatientEditScreenState();
}

class _PatientEditScreenState extends State<PatientEditScreen> {
  final _formKey = GlobalKey<FormState>();
  late TextEditingController _phoneController;
  late TextEditingController _emailController;
  late TextEditingController _addressController;

  @override
  void initState() {
    super.initState();
    _phoneController = TextEditingController(text: widget.patient.phone);
    _emailController = TextEditingController(text: widget.patient.email);
    _addressController = TextEditingController(text: widget.patient.address);
  }

  Future<void> saveChanges() async {
    if (!_formKey.currentState!.validate()) return;

    final updatedData = {
      'phone': _phoneController.text,
      'email': _emailController.text,
      'address': _addressController.text,
    };

    final response = await ApiService.updatePatient(widget.patient.id, updatedData);

    if (response['success']) {
      Navigator.pop(context, true);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Editar Paciente')),
      body: Form(
        key: _formKey,
        child: ListView(
          padding: EdgeInsets.all(16),
          children: [
            TextFormField(
              controller: _phoneController,
              decoration: InputDecoration(labelText: 'Teléfono'),
              validator: (value) => value!.isEmpty ? 'Requerido' : null,
            ),
            SizedBox(height: 16),
            TextFormField(
              controller: _emailController,
              decoration: InputDecoration(labelText: 'Email'),
              validator: (value) => value!.isEmpty ? 'Requerido' : null,
            ),
            SizedBox(height: 16),
            TextFormField(
              controller: _addressController,
              decoration: InputDecoration(labelText: 'Dirección'),
              maxLines: 3,
            ),
            SizedBox(height: 24),
            ElevatedButton(
              onPressed: saveChanges,
              child: Text('Guardar Cambios'),
            ),
          ],
        ),
      ),
    );
  }
}
```

**Endpoints:**
```
POST   /api/documents/upload/
PATCH  /api/patients/{id}/
POST   /api/clinical-records/forms/
```

**Dependencias Flutter:**
```yaml
dependencies:
  camera: ^0.10.5
  image_picker: ^1.0.4
  http: ^1.1.0
  path_provider: ^2.1.1
```

---

### 🖼️ HU20: IA - Mejora de Imágenes Médicas
**Prioridad:** CRÍTICA (Es el core de IA)
**Tiempo estimado:** 16-20 horas (3 días)
**Responsable:** 1 persona con experiencia en ML/Python

**Descripción:**
Como **Doctor**, quiero que el sistema mejore automáticamente la calidad de imágenes médicas (rayos X, ecografías) usando IA para visualizarlas con mayor claridad.

**Criterios de Aceptación:**
- [ ] Aplicar **CLAHE** (mejora de contraste) automáticamente
- [ ] Aplicar **Real-ESRGAN** (super-resolución) opcional
- [ ] Guardar imagen original + mejorada
- [ ] Ver comparación lado a lado
- [ ] Procesar en background con Celery
- [ ] Indicador de estado de procesamiento

**Tablas Involucradas:**
- `medical_image` (ya existe) ✅

**Backend:**

```python
# cr_backend/apps/medical_images/models.py
from django.db import models
from apps.core.models import TenantAwareModel

class MedicalImage(TenantAwareModel):
    clinical_record = models.ForeignKey('clinical_records.ClinicalRecord', on_delete=models.CASCADE)

    image_type = models.CharField(max_length=100)  # 'xray', 'ultrasound', 'ct', 'mri'
    title = models.CharField(max_length=255)

    # Archivos
    original_file = models.FileField(upload_to='medical_images/original/')
    enhanced_file = models.FileField(upload_to='medical_images/enhanced/', null=True, blank=True)

    # Metadata
    dicom_metadata = models.JSONField(default=dict, blank=True)

    # IA Enhancement
    enhancement_applied = models.BooleanField(default=False)
    enhancement_method = models.CharField(max_length=50, blank=True)  # 'clahe', 'esrgan'
    enhancement_params = models.JSONField(default=dict, blank=True)
    processing_status = models.CharField(max_length=20, default='pending')  # pending, processing, completed, failed

    uploaded_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('accounts.User', on_delete=models.CASCADE)


# cr_backend/apps/medical_images/tasks.py
from celery import shared_task
import cv2
import numpy as np
from PIL import Image
import logging

logger = logging.getLogger(__name__)

@shared_task
def enhance_medical_image(image_id):
    """Tarea asíncrona para mejorar imágenes médicas con IA"""
    try:
        image = MedicalImage.objects.get(id=image_id)
        image.processing_status = 'processing'
        image.save()

        # Cargar imagen original
        img_path = image.original_file.path
        img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)

        if img is None:
            raise Exception("No se pudo cargar la imagen")

        # Aplicar CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(img)

        # Aplicar filtro de reducción de ruido
        enhanced = cv2.fastNlMeansDenoising(enhanced, None, h=10, templateWindowSize=7, searchWindowSize=21)

        # Aplicar sharpening
        kernel = np.array([[-1,-1,-1],
                          [-1, 9,-1],
                          [-1,-1,-1]])
        enhanced = cv2.filter2D(enhanced, -1, kernel)

        # Guardar imagen mejorada
        enhanced_filename = f'medical_images/enhanced/{image.id}.png'
        enhanced_path = os.path.join(settings.MEDIA_ROOT, enhanced_filename)

        os.makedirs(os.path.dirname(enhanced_path), exist_ok=True)
        cv2.imwrite(enhanced_path, enhanced)

        # Actualizar modelo
        image.enhanced_file = enhanced_filename
        image.enhancement_applied = True
        image.enhancement_method = 'clahe+denoise+sharpen'
        image.enhancement_params = {
            'clahe_clip_limit': 2.0,
            'clahe_tile_size': 8,
            'denoise_h': 10
        }
        image.processing_status = 'completed'
        image.save()

        logger.info(f"Imagen {image_id} mejorada exitosamente")

    except Exception as e:
        logger.error(f"Error al mejorar imagen {image_id}: {str(e)}")
        image = MedicalImage.objects.get(id=image_id)
        image.processing_status = 'failed'
        image.save()


@shared_task
def enhance_with_esrgan(image_id):
    """Mejora con Real-ESRGAN (super-resolución) - OPCIONAL"""
    try:
        from realesrgan import RealESRGAN

        image = MedicalImage.objects.get(id=image_id)

        # Cargar modelo
        model = RealESRGAN('RealESRGAN_x4plus', scale=4)
        model.load_weights('weights/RealESRGAN_x4plus.pth')

        # Aplicar super-resolución
        img = Image.open(image.original_file.path)
        sr_image = model.predict(img)

        # Guardar
        enhanced_path = f'medical_images/enhanced/{image.id}_esrgan.png'
        sr_image.save(os.path.join(settings.MEDIA_ROOT, enhanced_path))

        image.enhanced_file = enhanced_path
        image.enhancement_method = 'esrgan'
        image.processing_status = 'completed'
        image.save()

    except Exception as e:
        logger.error(f"Error en ESRGAN para imagen {image_id}: {str(e)}")


# cr_backend/apps/medical_images/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

class MedicalImageViewSet(viewsets.ModelViewSet):
    serializer_class = MedicalImageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        tenant = get_current_tenant()
        return MedicalImage.objects.filter(tenant=tenant)

    def create(self, request):
        """Subir imagen médica y lanzar procesamiento"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save(
            tenant=get_current_tenant(),
            created_by=request.user
        )

        # Lanzar tarea de mejora en background
        enhance_medical_image.delay(str(instance.id))

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def comparison(self, request, pk=None):
        """Obtener URLs de comparación original vs mejorada"""
        image = self.get_object()

        return Response({
            'original_url': request.build_absolute_uri(image.original_file.url),
            'enhanced_url': request.build_absolute_uri(image.enhanced_file.url) if image.enhanced_file else None,
            'processing_status': image.processing_status,
            'enhancement_method': image.enhancement_method
        })
```

**Frontend:**

```typescript
// cr_frontend/src/pages/MedicalImages/MedicalImageViewer.tsx
import { useState, useEffect } from 'react';

export const MedicalImageViewer = ({ imageId }: { imageId: string }) => {
  const [imageData, setImageData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadImage();
    // Polling para ver si terminó el procesamiento
    const interval = setInterval(() => {
      if (imageData?.processing_status === 'pending' || imageData?.processing_status === 'processing') {
        loadImage();
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [imageId]);

  const loadImage = async () => {
    const res = await api.get(`/api/medical-images/${imageId}/comparison/`);
    setImageData(res.data);
    setLoading(false);
  };

  if (loading) return <div>Cargando...</div>;

  return (
    <div className="max-w-7xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6">Visualizador de Imágenes Médicas</h1>

      {imageData.processing_status === 'processing' && (
        <div className="bg-blue-50 border border-blue-200 p-4 rounded mb-4">
          <div className="flex items-center">
            <Spinner className="mr-2" />
            <span>Procesando imagen con IA... Esto puede tomar unos segundos</span>
          </div>
        </div>
      )}

      {imageData.processing_status === 'failed' && (
        <div className="bg-red-50 border border-red-200 p-4 rounded mb-4">
          Error al procesar la imagen
        </div>
      )}

      <div className="grid grid-cols-2 gap-6">
        {/* Imagen Original */}
        <div className="border rounded-lg overflow-hidden">
          <h3 className="bg-gray-100 p-3 font-semibold">Original</h3>
          <div className="p-4">
            <img
              src={imageData.original_url}
              alt="Original"
              className="w-full h-auto"
            />
          </div>
        </div>

        {/* Imagen Mejorada */}
        <div className="border rounded-lg overflow-hidden">
          <h3 className="bg-green-100 p-3 font-semibold">
            Mejorada con IA {imageData.enhancement_method && `(${imageData.enhancement_method})`}
          </h3>
          <div className="p-4">
            {imageData.enhanced_url ? (
              <img
                src={imageData.enhanced_url}
                alt="Mejorada"
                className="w-full h-auto"
              />
            ) : (
              <div className="text-center py-20 text-gray-400">
                Procesando...
              </div>
            )}
          </div>
        </div>
      </div>

      {imageData.processing_status === 'completed' && (
        <div className="mt-6 p-4 bg-gray-50 rounded">
          <h4 className="font-semibold mb-2">Detalles del Procesamiento:</h4>
          <pre className="text-sm">{JSON.stringify(imageData.enhancement_params, null, 2)}</pre>
        </div>
      )}
    </div>
  );
};
```

**Dependencias:**
```bash
pip install opencv-python
pip install pillow
pip install numpy

# Opcional (Real-ESRGAN - requiere GPU)
pip install realesrgan
```

**Endpoints:**
```
POST   /api/medical-images/
GET    /api/medical-images/
GET    /api/medical-images/{id}/
GET    /api/medical-images/{id}/comparison/
DELETE /api/medical-images/{id}/
```

---

### 📄 HU13: Asistente IA - OCR con AWS Textract
**Prioridad:** ALTA
**Tiempo estimado:** 12-16 horas (2 días)
**Responsable:** 1 persona backend con AWS

**Descripción:**
Como **Doctor**, quiero que el sistema extraiga automáticamente texto de documentos escaneados (recetas, informes) para poder buscar por contenido.

**Criterios de Aceptación:**
- [ ] Extracción automática de texto con AWS Textract
- [ ] Guardar texto en `extracted_text`
- [ ] Mostrar texto extraído en el visor
- [ ] Búsqueda por texto extraído
- [ ] Confianza del OCR (0-100%)
- [ ] Alternativa con Tesseract (gratuita)

**Tablas Involucradas:**
- `clinical_document` (agregar campos)

**Backend:**

```python
# cr_backend/apps/documents/models.py
class ClinicalDocument(TenantAwareModel):
    # ... campos existentes ...

    # OCR
    extracted_text = models.TextField(blank=True)
    ocr_confidence = models.FloatField(null=True, blank=True)
    ocr_status = models.CharField(max_length=20, default='pending')  # pending, processing, completed, failed
    ocr_language = models.CharField(max_length=10, default='es')


# cr_backend/apps/documents/tasks.py
import boto3
from django.conf import settings
import pytesseract
from PIL import Image
import pdf2image

@shared_task
def extract_text_with_textract(document_id):
    """Extracción de texto con AWS Textract"""
    try:
        document = ClinicalDocument.objects.get(id=document_id)
        document.ocr_status = 'processing'
        document.save()

        # Cliente de Textract
        textract = boto3.client(
            'textract',
            region_name=settings.AWS_S3_REGION_NAME,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )

        # Llamada a Textract
        response = textract.detect_document_text(
            Document={
                'S3Object': {
                    'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                    'Name': document.file_path
                }
            }
        )

        # Extraer texto y confianza
        text_blocks = []
        confidence_scores = []

        for block in response['Blocks']:
            if block['BlockType'] == 'LINE':
                text_blocks.append(block['Text'])
                confidence_scores.append(block['Confidence'])

        extracted_text = '\n'.join(text_blocks)
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0

        # Guardar
        document.extracted_text = extracted_text
        document.ocr_confidence = avg_confidence
        document.ocr_status = 'completed'
        document.save()

        logger.info(f"OCR completado para documento {document_id}. Confianza: {avg_confidence:.2f}%")

    except Exception as e:
        logger.error(f"Error en OCR para documento {document_id}: {str(e)}")
        document = ClinicalDocument.objects.get(id=document_id)
        document.ocr_status = 'failed'
        document.save()


@shared_task
def extract_text_with_tesseract(document_id):
    """Alternativa GRATUITA con Tesseract OCR"""
    try:
        document = ClinicalDocument.objects.get(id=document_id)
        document.ocr_status = 'processing'
        document.save()

        file_path = document.file_path
        file_extension = file_path.split('.')[-1].lower()

        # Convertir PDF a imágenes si es necesario
        if file_extension == 'pdf':
            images = pdf2image.convert_from_path(file_path)
            text_parts = []

            for i, image in enumerate(images):
                text = pytesseract.image_to_string(image, lang='spa')
                text_parts.append(f"--- Página {i+1} ---\n{text}")

            extracted_text = '\n\n'.join(text_parts)

        else:
            # Imagen directa
            image = Image.open(file_path)
            extracted_text = pytesseract.image_to_string(image, lang='spa')

        # Guardar
        document.extracted_text = extracted_text
        document.ocr_confidence = 75.0  # Tesseract no da confianza precisa
        document.ocr_status = 'completed'
        document.save()

        logger.info(f"OCR (Tesseract) completado para documento {document_id}")

    except Exception as e:
        logger.error(f"Error en Tesseract OCR: {str(e)}")
        document = ClinicalDocument.objects.get(id=document_id)
        document.ocr_status = 'failed'
        document.save()


# cr_backend/apps/documents/views.py
class ClinicalDocumentViewSet(viewsets.ModelViewSet):
    # ... código existente ...

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save(
            tenant=get_current_tenant(),
            created_by=request.user
        )

        # Lanzar OCR en background
        if settings.USE_AWS_TEXTRACT:
            extract_text_with_textract.delay(str(instance.id))
        else:
            extract_text_with_tesseract.delay(str(instance.id))

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def search_by_content(self, request):
        """Buscar documentos por texto extraído"""
        query = request.query_params.get('q', '')
        tenant = get_current_tenant()

        documents = ClinicalDocument.objects.filter(
            tenant=tenant,
            extracted_text__icontains=query,
            ocr_status='completed'
        )

        serializer = self.get_serializer(documents, many=True)
        return Response(serializer.data)
```

**Frontend:**

```typescript
// cr_frontend/src/pages/Documents/DocumentViewerPage.tsx
export const DocumentViewerPage = ({ documentId }: { documentId: string }) => {
  const [document, setDocument] = useState<any>(null);

  useEffect(() => {
    loadDocument();
  }, [documentId]);

  const loadDocument = async () => {
    const res = await api.get(`/api/documents/${documentId}/`);
    setDocument(res.data);
  };

  return (
    <div className="max-w-6xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-4">{document?.title}</h1>

      {/* Visor de PDF */}
      {document?.file_path && (
        <div className="border rounded-lg p-4 mb-6">
          <PDFViewer fileUrl={document.file_path} />
        </div>
      )}

      {/* Texto Extraído con OCR */}
      {document?.extracted_text && (
        <div className="bg-gray-50 border rounded-lg p-6">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold">Texto Extraído (OCR)</h3>
            <span className="text-sm text-gray-600">
              Confianza: {document.ocr_confidence?.toFixed(1)}%
            </span>
          </div>

          <div className="bg-white p-4 rounded border">
            <pre className="whitespace-pre-wrap text-sm">
              {document.extracted_text}
            </pre>
          </div>

          <p className="text-xs text-gray-500 mt-2">
            Este texto fue extraído automáticamente usando IA. Puede contener errores.
          </p>
        </div>
      )}

      {document?.ocr_status === 'processing' && (
        <div className="bg-blue-50 border p-4 rounded">
          <Spinner /> Extrayendo texto del documento...
        </div>
      )}
    </div>
  );
};
```

**Configuración:**
```bash
# .env
USE_AWS_TEXTRACT=True  # False para usar Tesseract
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_S3_REGION_NAME=us-east-1
```

**Dependencias:**
```bash
# AWS Textract
pip install boto3

# Tesseract (alternativa gratuita)
pip install pytesseract
pip install pdf2image
# Instalar Tesseract: https://github.com/tesseract-ocr/tesseract
```

---

### 🩻 HU-EXTRA: Soporte DICOM para Imágenes Médicas
**Prioridad:** MEDIA
**Tiempo estimado:** 8-10 horas (1 día)
**Responsable:** 1 persona backend

**Descripción:**
Como **Doctor**, quiero subir archivos DICOM (formato estándar de imágenes médicas) y visualizarlos.

**Criterios de Aceptación:**
- [ ] Subir archivos `.dcm`
- [ ] Extraer metadata DICOM
- [ ] Convertir DICOM a PNG para preview
- [ ] Guardar metadata (edad, sexo, tipo de estudio)

**Backend:**

```python
# cr_backend/apps/medical_images/utils.py
import pydicom
from PIL import Image
import numpy as np

def process_dicom_file(file_path):
    """Procesar archivo DICOM y extraer metadata"""
    try:
        dicom = pydicom.dcmread(file_path)

        # Extraer metadata
        metadata = {
            'patient_name': str(dicom.PatientName) if 'PatientName' in dicom else None,
            'patient_age': str(dicom.PatientAge) if 'PatientAge' in dicom else None,
            'patient_sex': str(dicom.PatientSex) if 'PatientSex' in dicom else None,
            'study_date': str(dicom.StudyDate) if 'StudyDate' in dicom else None,
            'study_description': str(dicom.StudyDescription) if 'StudyDescription' in dicom else None,
            'modality': str(dicom.Modality) if 'Modality' in dicom else None,
            'body_part': str(dicom.BodyPartExamined) if 'BodyPartExamined' in dicom else None,
        }

        # Convertir píxeles a imagen PNG
        pixel_array = dicom.pixel_array

        # Normalizar a 0-255
        pixel_array = ((pixel_array - pixel_array.min()) / (pixel_array.max() - pixel_array.min()) * 255).astype(np.uint8)

        # Crear imagen
        image = Image.fromarray(pixel_array)
        png_path = file_path.replace('.dcm', '.png')
        image.save(png_path)

        return metadata, png_path

    except Exception as e:
        raise Exception(f"Error al procesar DICOM: {str(e)}")


# cr_backend/apps/medical_images/views.py
class MedicalImageViewSet(viewsets.ModelViewSet):
    # ... código existente ...

    def create(self, request):
        file = request.FILES.get('file')

        if file.name.endswith('.dcm'):
            # Procesar DICOM
            temp_path = handle_uploaded_file(file)
            metadata, png_path = process_dicom_file(temp_path)

            # Crear instancia
            instance = MedicalImage.objects.create(
                tenant=get_current_tenant(),
                clinical_record_id=request.data.get('clinical_record_id'),
                image_type=metadata.get('modality', 'unknown'),
                title=request.data.get('title', 'Imagen DICOM'),
                original_file=file,
                dicom_metadata=metadata,
                created_by=request.user
            )

            # Lanzar mejora de imagen
            enhance_medical_image.delay(str(instance.id))

            return Response(MedicalImageSerializer(instance).data, status=201)

        else:
            # Procesamiento normal
            return super().create(request)
```

**Dependencias:**
```bash
pip install pydicom
pip install pillow
pip install numpy
```

---

### 🌲 HU-ML: Predicción de Datos con RandomForest
**Prioridad:** BAJA (Si sobra tiempo)
**Tiempo estimado:** 10-12 horas (1.5 días)
**Responsable:** 1 persona con ML

**Descripción:**
Como **Doctor**, quiero que el sistema prediga diagnósticos o riesgos basándose en datos históricos de pacientes.

**Criterios de Aceptación:**
- [ ] Modelo entrenado con datos históricos
- [ ] Predicción de probabilidad de enfermedades
- [ ] API endpoint para predecir
- [ ] Mostrar confianza de predicción

**Backend:**

```python
# cr_backend/apps/ml/models.py
class PredictionModel(models.Model):
    name = models.CharField(max_length=200)
    model_type = models.CharField(max_length=50)  # 'random_forest', 'logistic_regression'
    model_file = models.FileField(upload_to='ml_models/')
    accuracy = models.FloatField()
    trained_at = models.DateTimeField(auto_now_add=True)


# cr_backend/apps/ml/train.py
from sklearn.ensemble import RandomForestClassifier
import joblib

def train_disease_prediction_model():
    """Entrenar modelo para predecir enfermedades"""
    # Obtener datos de pacientes con diagnósticos
    patients = Patient.objects.all()

    # Preparar features
    X = []
    y = []

    for patient in patients:
        features = [
            patient.age,
            1 if patient.gender == 'M' else 0,
            len(patient.chronic_conditions),
            len(patient.allergies),
            # Más features...
        ]
        X.append(features)
        y.append(patient.primary_diagnosis)  # Target

    # Entrenar
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X, y)

    # Guardar modelo
    joblib.dump(model, 'ml_models/disease_predictor.pkl')

    return model


# cr_backend/apps/ml/views.py
@api_view(['POST'])
def predict_disease(request):
    """Predecir enfermedad basado en síntomas"""
    age = request.data.get('age')
    gender = request.data.get('gender')
    symptoms = request.data.get('symptoms', [])

    # Cargar modelo
    model = joblib.load('ml_models/disease_predictor.pkl')

    # Preparar features
    features = [age, 1 if gender == 'M' else 0, len(symptoms)]

    # Predecir
    prediction = model.predict([features])[0]
    probability = model.predict_proba([features]).max()

    return Response({
        'prediction': prediction,
        'confidence': float(probability),
        'recommendations': get_recommendations(prediction)
    })
```

---

## 📅 PLANIFICACIÓN (7 días)

### Día 1-2: Mejora de Imágenes con IA (CRÍTICO)
| Día | Tarea | Responsable |
|-----|-------|-------------|
| 1 | HU20: Implementar CLAHE + denoise + sharpen | Dev ML |
| 1 | HU19: Captura de cámara en móvil | Dev Mobile |
| 2 | HU20: Frontend comparador de imágenes | Dev Frontend |
| 2 | HU19: Upload de fotos desde móvil | Dev Mobile |

### Día 3-4: OCR con Textract
| Día | Tarea | Responsable |
|-----|-------|-------------|
| 3 | HU13: Integrar AWS Textract | Dev Backend |
| 3 | HU19: Edición de pacientes móvil | Dev Mobile |
| 4 | HU13: Búsqueda por texto extraído | Dev Backend |
| 4 | HU13: Frontend visor con OCR | Dev Frontend |

### Día 5: DICOM
| Día | Tarea | Responsable |
|-----|-------|-------------|
| 5 | HU-EXTRA: Soporte DICOM + metadata | Dev Backend |
| 5 | Testing de móvil avanzado | Dev Mobile |

### Día 6-7: RandomForest + Testing Final
| Día | Tarea | Responsable |
|-----|-------|-------------|
| 6 | HU-ML: Entrenar modelo RandomForest (opcional) | Dev ML |
| 6 | Testing integración de todas las HUs | Todo el equipo |
| 7 | **Testing final + Documentación + Video demo** | Todo el equipo |

---

## ✅ CRITERIOS DE ÉXITO

Sprint 4 estará completo cuando:

1. ✅ **Mejora de imágenes con IA** funciona (CLAHE mínimo)
2. ✅ **OCR** extrae texto de documentos
3. ✅ **Móvil permite capturar fotos** y subirlas
4. ⚠️ **DICOM** funciona (opcional)
5. ⚠️ **RandomForest** predice algo (opcional)

---

## 📦 ENTREGABLES

- [ ] Sistema de mejora de imágenes médicas con IA
- [ ] OCR automático en documentos
- [ ] App móvil con captura de fotos
- [ ] Soporte DICOM (opcional)
- [ ] Modelo de predicción (opcional)
- [ ] Video demo completo del sistema

---

## 🚨 RIESGOS

| Riesgo | Mitigación |
|--------|------------|
| Real-ESRGAN muy complejo | Usar solo CLAHE (OpenCV) |
| AWS Textract costoso | Usar Tesseract OCR gratuito |
| DICOM muy técnico | Implementar solo si sobra tiempo |
| RandomForest no hay datos | Usar datos sintéticos o skip |

---

**FIN DEL PROYECTO** 🎉

Después de Sprint 4, el sistema debe tener:
- ✅ Multi-tenancy completo
- ✅ Gestión de pacientes e historias clínicas
- ✅ Documentos con OCR
- ✅ Imágenes médicas mejoradas con IA
- ✅ App móvil funcional
- ✅ Pagos con Stripe
- ✅ Backups y auditoría
- ✅ DICOM y ML (opcional)
