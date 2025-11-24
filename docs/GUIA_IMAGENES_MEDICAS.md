# Guía: Sistema de Imágenes Médicas (Tomografías, Ecografías, Resonancias)

## 📋 **Resumen del Sistema**

Tu sistema CliniDocs **YA SOPORTA** almacenamiento, visualización y procesamiento de imágenes médicas incluyendo:

✅ **Tomografías (CT Scan)**
✅ **Resonancias Magnéticas (MRI)**
✅ **Ecografías (Ultrasound)**
✅ Rayos X
✅ Mamografías
✅ PET Scan

---

## 🏗️ **Arquitectura del Sistema**

### **1. Dos Modelos Complementarios**

#### **A) ClinicalDocument** (Para informes de imagen)
**Ubicación**: `apps/documents/models.py:9-258`

Almacena el **informe médico** de la imagen:

```python
DOCUMENT_TYPE_CHOICES = [
    ('imaging_report', 'Informe de Imagen'),  # ← Tipo para imágenes médicas
    # ... otros tipos
]
```

**Características:**
- 📄 Informe PDF/Word del médico radiólogo
- 🔍 OCR automático con **AWS Textract**
- 🖼️ Mejora de imágenes con **algoritmo CLAHE**
- 🔒 Firma digital y bloqueo de documentos
- 📊 Verificación de integridad (SHA-256)
- 💾 Almacenamiento en **AWS S3**

#### **B) MedicalImage** (Para las imágenes DICOM/PNG/JPG)
**Ubicación**: `apps/documents/models.py:260-380`

Almacena las **imágenes médicas** en sí:

```python
IMAGE_TYPE_CHOICES = [
    ('xray', 'Rayos X'),
    ('ct_scan', 'Tomografía'),         # ← Tomografías
    ('mri', 'Resonancia Magnética'),   # ← Resonancias
    ('ultrasound', 'Ecografía'),       # ← Ecografías
    ('mammography', 'Mamografía'),
    ('pet_scan', 'PET Scan'),
]
```

**Características:**
- 🩻 Metadatos DICOM completos (`dicom_metadata` JSON)
- 🎯 Modalidad DICOM (CR, CT, MR, US, etc.)
- 🧩 Parte del cuerpo estudiada
- 🤖 Mejora con IA: **Real-ESRGAN + CLAHE**
- 🔗 Vinculado a `ClinicalDocument` y `ClinicalRecord`

---

## 🚀 **Flujo Completo de Uso**

### **Paso 1: Subir una Tomografía desde el Frontend**

#### **Opción A: Como Documento (Informe PDF + Imagen)**

1. **Navega a**: `/documents/upload`

2. **Completa el formulario**:
   - **Historia Clínica**: Selecciona el paciente
   - **Tipo de Documento**: `Informe de Imagen`
   - **Título**: "Tomografía de Tórax"
   - **Descripción**: "Estudio sin contraste"
   - **Especialidad**: "Radiología"
   - **Nombre del Médico**: "Dr. Juan Pérez"

3. **Arrastra el archivo**:
   - Formatos soportados: **PDF, PNG, JPG, JPEG, GIF**
   - Tamaño máximo: **50 MB**
   - Auto-OCR: ✅ Activar para extraer texto

4. **Click en "Subir Documento"**

**Lo que sucede en el backend:**

```python
# 1. Archivo se sube a S3
file_path = f"documents/{tenant_id}/{uuid}.pdf"
s3_client.upload_fileobj(file, bucket, file_path)

# 2. Se crea el documento
document = ClinicalDocument.objects.create(
    clinical_record=clinical_record,
    document_type='imaging_report',
    title="Tomografía de Tórax",
    file_path=file_path,
    file_name="tomografia_torax.pdf",
    mime_type="application/pdf"
)

# 3. Si es imagen, se aplica CLAHE automáticamente
if mime_type.startswith('image/'):
    enhanced_path = enhance_image_with_clahe(file_path)
    document.enhanced_image_path = enhanced_path

# 4. Si OCR está activado, se procesa con AWS Textract
if process_ocr:
    textract_client.start_document_text_detection(...)
    document.ocr_status = 'async_processing'
```

#### **Opción B: Como Imagen Médica DICOM (Especializada)**

**Endpoint API**: `POST /api/medical-images/`

```bash
curl -X POST http://localhost:8000/api/medical-images/ \
  -H "Authorization: Bearer <token>" \
  -F "file=@tomografia.dcm" \
  -F "clinical_record=<clinical_record_id>" \
  -F "image_type=ct_scan" \
  -F "title=Tomografía de Tórax con Contraste" \
  -F "study_date=2025-11-19T10:00:00Z" \
  -F "modality=CT" \
  -F "body_part=Tórax"
```

**Respuesta:**

```json
{
  "id": "uuid",
  "clinical_record": "uuid",
  "image_type": "ct_scan",
  "title": "Tomografía de Tórax con Contraste",
  "study_date": "2025-11-19T10:00:00Z",
  "modality": "CT",
  "body_part": "Tórax",
  "file_path": "medical-images/tenant/uuid.dcm",
  "file_name": "tomografia.dcm",
  "dicom_metadata": {
    "PatientID": "12345",
    "StudyInstanceUID": "1.2.840...",
    "SeriesInstanceUID": "1.2.840...",
    "SliceThickness": "5.0",
    "KVP": "120",
    ...
  },
  "enhancement_applied": false,
  "enhanced_image_path": ""
}
```

---

### **Paso 2: Ver la Imagen Médica**

1. **Navega a**: `/documents` → Busca el documento

2. **Click en el documento** → Te lleva a `/documents/:id`

3. **Visualización según tipo**:

   - **PDF**: Visor PDF integrado con zoom, navegación de páginas
   - **Imágenes**: Visor de imágenes con controles de zoom

4. **Pestañas disponibles**:

   - **📄 Visor**: Muestra el archivo original
   - **🔍 OCR**: Muestra texto extraído (si fue procesado)
   - **✨ Mejorada**: Muestra imagen mejorada con CLAHE

**Controles del visor:**

```typescript
// Zoom
<Button onClick={handleZoomIn}><ZoomIn /></Button>
<Button onClick={handleZoomOut}><ZoomOut /></Button>

// Navegación (PDF)
<Button onClick={handlePreviousPage}><ChevronLeft /></Button>
<span>Página {pageNumber} de {numPages}</span>
<Button onClick={handleNextPage}><ChevronRight /></Button>

// Acciones
<Button onClick={handleDownload}><Download /> Descargar</Button>
<Button onClick={handlePrint}><Printer /> Imprimir</Button>
```

---

### **Paso 3: Mejorar Imagen con IA (CLAHE)**

**¿Qué es CLAHE?**
Contrast Limited Adaptive Histogram Equalization - Mejora el contraste local de imágenes médicas.

**Desde el Frontend:**

1. En `/documents/:id`, click en pestaña **"✨ Mejorada"**

2. **Configuración de mejora**:
   - **Usar preset por modalidad**: ✅ Automático según tipo de estudio
   - **Clip Limit**: 2.0 (ajusta contraste)
   - **Tile Grid Size**: 8 (tamaño de región local)

3. Click **"Mejorar Imagen"**

**Backend procesa:**

```python
from apps.documents.services.image_enhancement_service import ImageEnhancementService

# Aplicar CLAHE
enhanced_path = ImageEnhancementService.enhance_with_clahe(
    image_path=document.file_path,
    clip_limit=2.0,
    tile_grid_size=(8, 8),
    modality='CT'  # Presets optimizados por modalidad
)

document.enhanced_image_path = enhanced_path
document.save()
```

**Presets por modalidad:**

| Modalidad | Clip Limit | Tile Grid | Uso |
|-----------|-----------|-----------|-----|
| **CT** | 2.0 | 8x8 | Tomografías |
| **MRI** | 2.5 | 8x8 | Resonancias |
| **US** | 3.0 | 4x4 | Ecografías (más contraste) |
| **CR** | 2.0 | 8x8 | Rayos X |

---

### **Paso 4: Extraer Texto con OCR (AWS Textract)**

**Para informes escaneados o imágenes con texto:**

1. **Al subir documento**: Activar checkbox "Procesar OCR automáticamente"

   O bien:

2. **En el visor**: Click en **"🔍 Procesar OCR"**

**El sistema procesa:**

```python
# 1. Iniciar trabajo asíncrono en AWS Textract
response = textract_client.start_document_text_detection(
    DocumentLocation={
        'S3Object': {
            'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
            'Name': document.file_path
        }
    }
)

# 2. Guardar Job ID
document.ocr_job_id = response['JobId']
document.ocr_status = 'async_processing'
document.save()

# 3. Webhook recibe resultado cuando termine
# (o polling cada 30 segundos desde frontend)

# 4. Almacenar texto extraído
document.ocr_text = extracted_text
document.ocr_confidence = 94.5  # Confianza promedio
document.ocr_status = 'completed'
document.save()
```

**Ver resultado OCR:**

En la pestaña **"🔍 OCR"** del visor:

```
Confianza: 94.5%
Estado: Completado

=== TEXTO EXTRAÍDO ===

INFORME DE TOMOGRAFÍA COMPUTARIZADA DE TÓRAX

Paciente: Juan Pérez García
Fecha: 19/11/2025

TÉCNICA:
Se realizó estudio tomográfico de tórax sin
administración de contraste endovenoso...

HALLAZGOS:
Parénquima pulmonar sin lesiones focales...
```

---

## 🔍 **Casos de Uso Específicos**

### **Caso 1: Subir Ecografía (Ultrasound)**

```bash
# Via API
POST /api/documents/
Content-Type: multipart/form-data

{
  "clinical_record": "uuid-del-paciente",
  "document_type": "imaging_report",
  "title": "Ecografía Abdominal",
  "specialty": "Radiología",
  "file": <archivo.jpg>
}
```

**Frontend**: Mismo flujo en `/documents/upload`, solo cambiar título y especialidad.

### **Caso 2: Subir Resonancia Magnética (MRI)**

```bash
POST /api/medical-images/
Content-Type: multipart/form-data

{
  "clinical_record": "uuid",
  "image_type": "mri",
  "title": "RM de Cerebro",
  "modality": "MR",
  "body_part": "Cerebro",
  "file": <resonancia.dcm>
}
```

### **Caso 3: Comparar Imagen Original vs Mejorada**

En el frontend, la pestaña **"✨ Mejorada"** muestra ambas imágenes:

```typescript
// Componente React Compare Image
<ReactCompareImage
  leftImage={originalImageUrl}
  rightImage={enhancedImageUrl}
  sliderLineColor="#3b82f6"
/>
```

---

## 📊 **Consultar Imágenes de un Paciente**

### **Método 1: Desde el Detalle del Paciente**

1. Navega a `/patients/:id`
2. Sección **"Documentos Clínicos"**
3. Filtrar por tipo: `Informe de Imagen`

### **Método 2: API REST**

```bash
# Listar todos los documentos de imagen de un paciente
GET /api/documents/?clinical_record=<clinical_record_id>&document_type=imaging_report

# Respuesta
{
  "count": 3,
  "results": [
    {
      "id": "uuid-1",
      "title": "Tomografía de Tórax",
      "document_type": "imaging_report",
      "document_date": "2025-11-19T10:00:00Z",
      "file_url": "https://s3.../tomografia.pdf",
      "ocr_processed": true,
      "enhanced_image_path": "s3://bucket/enhanced/uuid.png"
    },
    ...
  ]
}
```

### **Método 3: Imágenes DICOM del Paciente**

```bash
GET /api/medical-images/?clinical_record=<clinical_record_id>&image_type=ct_scan

# Filtrar por modalidad
GET /api/medical-images/?clinical_record=<clinical_record_id>&modality=CT

# Filtrar por parte del cuerpo
GET /api/medical-images/?clinical_record=<clinical_record_id>&body_part=Tórax
```

---

## 🔧 **Configuración de AWS (Requerida)**

Para que funcione OCR y almacenamiento, necesitas configurar:

### **1. AWS S3 (Almacenamiento)**

```python
# settings.py
AWS_ACCESS_KEY_ID = 'AKIA...'
AWS_SECRET_ACCESS_KEY = 'secret...'
AWS_STORAGE_BUCKET_NAME = 'clinidocs-documents'
AWS_S3_REGION_NAME = 'us-east-1'
```

### **2. AWS Textract (OCR)**

```python
# settings.py
AWS_TEXTRACT_ENABLED = True
```

**Permisos IAM necesarios:**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject"
      ],
      "Resource": "arn:aws:s3:::clinidocs-documents/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "textract:StartDocumentTextDetection",
        "textract:GetDocumentTextDetection"
      ],
      "Resource": "*"
    }
  ]
}
```

---

## 🎯 **Mejores Prácticas**

### **1. Nombrar Imágenes Claramente**

✅ **Bueno**: "Tomografía de Tórax con Contraste - 19/11/2025"
❌ **Malo**: "IMG_20251119.jpg"

### **2. Completar Metadatos**

Siempre llenar:
- Especialidad: "Radiología"
- Médico que interpreta
- Fecha del estudio (no fecha de carga)
- Descripción breve de hallazgos

### **3. Usar OCR para Informes Escaneados**

Si subes un PDF escaneado, activa OCR para permitir búsqueda de texto.

### **4. Mejorar Imágenes Antes de Mostrar al Médico**

Para tomografías de baja calidad, aplicar CLAHE mejora la visualización.

### **5. Vincular Imagen con Informe**

```python
# Crear informe
document = ClinicalDocument.objects.create(
    document_type='imaging_report',
    title='Informe TC Tórax',
    ...
)

# Crear imagen DICOM asociada
medical_image = MedicalImage.objects.create(
    document=document,  # ← Vincular
    image_type='ct_scan',
    ...
)
```

---

## ❓ **Preguntas Frecuentes**

### **1. ¿Puedo subir archivos DICOM?**

✅ **Sí**, usa el modelo `MedicalImage` con `image_type='ct_scan'` o `'mri'`.

El sistema extracta metadatos DICOM automáticamente si el archivo es .dcm.

### **2. ¿Cuál es el tamaño máximo?**

**50 MB** por archivo (configurable en `DocumentUploadPage.tsx:79`).

Para archivos más grandes (series DICOM completas), considera:
- Aumentar límite en frontend y backend
- Usar compresión
- Subir cada corte por separado

### **3. ¿Soporta series de imágenes (múltiples cortes)?**

Actualmente no hay un modelo para "Serie DICOM". Opciones:

**A) Subir cada corte como `MedicalImage`** separado:

```python
for i, slice_file in enumerate(ct_slices):
    MedicalImage.objects.create(
        title=f'TC Tórax - Corte {i+1}',
        image_type='ct_scan',
        file_path=f'slices/ct_{i}.dcm',
        ...
    )
```

**B) Crear modelo `DicomSeries`** (requiere desarrollo):

```python
class DicomSeries(TenantAwareModel):
    clinical_record = models.ForeignKey(ClinicalRecord, ...)
    series_uid = models.CharField(max_length=255)
    images = models.ManyToManyField(MedicalImage)
```

### **4. ¿Cómo descargar una imagen?**

**Desde el visor**: Click en botón **"Descargar"**

**Via API**:
```bash
GET /api/documents/<id>/download/
# Retorna URL pre-firmada de S3
```

### **5. ¿Se puede imprimir?**

✅ **Sí**, el visor tiene botón **"Imprimir"** que abre diálogo del navegador.

---

## 🚨 **Troubleshooting**

### **Error: "No se pudo cargar el archivo para previsualización"**

**Causa**: Archivo no existe en S3 o URL expiró.

**Solución**:
```bash
# Verificar en S3
aws s3 ls s3://clinidocs-documents/documents/<tenant_id>/

# Regenerar URL
GET /api/documents/<id>/view/
```

### **Error: "OCR falló"**

**Causa**: Imagen de muy baja calidad o formato no soportado.

**Solución**:
1. Mejorar imagen con CLAHE primero
2. Verificar que AWS Textract soporte el formato
3. Revisar logs de AWS:
   ```bash
   aws textract get-document-text-detection --job-id <job_id>
   ```

### **Error: "Archivo demasiado grande"**

**Causa**: Límite de 50 MB.

**Solución**: Aumentar límite en:
```typescript
// DocumentUploadPage.tsx
maxSize: 100 * 1024 * 1024, // 100MB
```

```python
# settings.py
DATA_UPLOAD_MAX_MEMORY_SIZE = 104857600  # 100MB
```

---

## ✅ **Resumen**

Tu sistema **YA ESTÁ LISTO** para:

- ✅ Subir tomografías, ecografías, resonancias
- ✅ Almacenar en AWS S3
- ✅ Visualizar imágenes y PDFs
- ✅ Mejorar imágenes con CLAHE
- ✅ Extraer texto con OCR (AWS Textract)
- ✅ Descargar e imprimir
- ✅ Firmar digitalmente informes
- ✅ Auditar accesos

**No necesitas desarrollar nada nuevo** - solo usar las funcionalidades existentes! 🎉

---

## 📞 **Soporte**

Para más información, consulta:
- 📄 Código del modelo: [apps/documents/models.py](../apps/documents/models.py)
- 🖥️ Frontend de carga: [cr_frontend/src/modules/documents/pages/DocumentUploadPage.tsx](../../cr_frontend/src/modules/documents/pages/DocumentUploadPage.tsx)
- 👁️ Frontend de visualización: [cr_frontend/src/modules/documents/pages/DocumentViewerPage.tsx](../../cr_frontend/src/modules/documents/pages/DocumentViewerPage.tsx)
