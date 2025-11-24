# Ejemplo Completo: Subir y Ver una Tomografía

## 🎯 **Objetivo**

Demostrar el flujo completo para:
1. Subir una tomografía de tórax
2. Aplicar mejora de imagen con CLAHE
3. Extraer texto del informe con OCR
4. Visualizar la imagen en el visor

---

## 📋 **Requisitos Previos**

- ✅ Paciente con historia clínica activa
- ✅ Usuario con sesión iniciada
- ✅ Archivo de tomografía (PDF, JPG, PNG o DICOM)
- ✅ AWS S3 configurado
- ✅ (Opcional) AWS Textract para OCR

---

## 🚀 **Opción 1: Desde el Frontend (Recomendado)**

### **Paso 1: Navegar a la Página de Carga**

1. Abre el navegador en `http://localhost:5173`
2. Inicia sesión con tu usuario
3. Ve a **"Documentos"** en el menú lateral
4. Click en **"Subir Documento"** (botón azul con ícono de upload)

**URL**: `http://localhost:5173/documents/upload`

---

### **Paso 2: Completar el Formulario**

Llena los siguientes campos:

| Campo | Valor de Ejemplo | Requerido |
|-------|------------------|-----------|
| **Historia Clínica** | Selecciona el paciente | ✅ Sí |
| **Tipo de Documento** | "Informe de Imagen" | ✅ Sí |
| **Título** | "Tomografía de Tórax sin Contraste" | ✅ Sí |
| **Descripción** | "Estudio de tórax para evaluación pulmonar" | ❌ No |
| **Fecha del Documento** | 2025-11-19 | ❌ No (usa fecha actual) |
| **Especialidad** | "Radiología" | ❌ No |
| **Nombre del Médico** | "Dr. Carlos Ramírez" | ❌ No |
| **Matrícula del Médico** | "R-12345" | ❌ No |

---

### **Paso 3: Arrastrar el Archivo**

Puedes:

**A) Arrastrar y soltar**:
- Arrastra el archivo desde tu explorador de archivos
- Suéltalo en la zona de dropzone (aparece resaltada)

**B) Click para seleccionar**:
- Click en el área de dropzone
- Selecciona el archivo en el diálogo

**Archivos aceptados**:
- 📄 PDF (`.pdf`)
- 🖼️ Imágenes: PNG, JPG, JPEG, GIF
- 📝 Word: DOC, DOCX
- 🩻 DICOM: `.dcm` (usar API directa)

**Tamaño máximo**: 50 MB

---

### **Paso 4: Configurar OCR (Opcional)**

Si el archivo es una imagen escaneada o PDF con texto:

✅ **Activar checkbox**: "Procesar OCR automáticamente"

Esto hará que AWS Textract extraiga el texto del informe.

---

### **Paso 5: Subir el Documento**

Click en **"Subir Documento"**

**Lo que sucede:**

```
1. ⏳ Validando archivo...
2. ⏳ Subiendo a S3... (barra de progreso)
3. ⏳ Creando registro en base de datos...
4. ✅ Documento subido exitosamente!
```

**Redirección automática** a `/documents/:id`

---

### **Paso 6: Ver el Documento**

Ahora estás en el **Visor de Documentos**:

**Información mostrada:**

```
┌─────────────────────────────────────────────────────────┐
│ Tomografía de Tórax sin Contraste                      │
│                                                         │
│ 📋 Tipo: Informe de Imagen                            │
│ 📅 Fecha: 19/11/2025 10:30 AM                         │
│ 🏥 Especialidad: Radiología                            │
│ 👨‍⚕️ Médico: Dr. Carlos Ramírez (R-12345)               │
│                                                         │
│ ┌─────────┬──────────┬──────────┐                      │
│ │ Visor   │   OCR    │ Mejorada │ (Pestañas)          │
│ └─────────┴──────────┴──────────┘                      │
│                                                         │
│  [Imagen de la tomografía]                             │
│                                                         │
│  Controles:                                            │
│  [🔍 Zoom In] [🔍 Zoom Out]                           │
│  [⬅️ Anterior] Página 1 de 1 [➡️ Siguiente]            │
│                                                         │
│  Acciones:                                             │
│  [⬇️ Descargar] [🖨️ Imprimir] [🗑️ Eliminar]          │
└─────────────────────────────────────────────────────────┘
```

---

### **Paso 7: Mejorar la Imagen con CLAHE**

Si la imagen tiene bajo contraste:

1. Click en pestaña **"✨ Mejorada"**

2. Aparecerán controles:

```
┌─────────────────────────────────────────────┐
│ Mejorar Imagen con CLAHE                   │
│                                             │
│ ☑️ Usar preset por modalidad (CT)          │
│                                             │
│ Clip Limit: [━━━━━●━━━━] 2.0              │
│ Tile Grid Size: [━━━━━●━━━━] 8            │
│                                             │
│ [✨ Mejorar Imagen]                        │
└─────────────────────────────────────────────┘
```

3. Click **"Mejorar Imagen"**

4. Espera unos segundos (se procesa en el backend)

5. **Resultado**: Comparación lado a lado

```
┌──────────────────┬──────────────────┐
│   Original       │    Mejorada      │
│                  │                  │
│  [Imagen con     │  [Imagen con     │
│   bajo contraste]│   alto contraste]│
│                  │                  │
└──────────────────┴──────────────────┘
        ← Arrastra para comparar →
```

---

### **Paso 8: Ver Texto Extraído por OCR**

Si activaste OCR al subir:

1. Click en pestaña **"🔍 OCR"**

2. **Si está procesando**:

```
⏳ Procesando OCR...
Estado: Procesando (Asíncrono)
Job ID: abc123...
```

3. **Cuando termina**:

```
┌─────────────────────────────────────────────┐
│ Texto Extraído por OCR                     │
│                                             │
│ ✅ Estado: Completado                      │
│ 📊 Confianza: 94.5%                        │
│                                             │
│ ════════════════════════════════════════    │
│                                             │
│ INFORME DE TOMOGRAFÍA COMPUTARIZADA         │
│ DE TÓRAX                                    │
│                                             │
│ Paciente: Juan Pérez García                │
│ Edad: 45 años                               │
│ Fecha: 19/11/2025                           │
│                                             │
│ TÉCNICA:                                    │
│ Se realizó estudio tomográfico axial de     │
│ tórax sin administración de contraste...    │
│                                             │
│ HALLAZGOS:                                  │
│ Parénquima pulmonar sin lesiones focales... │
│                                             │
│ [Copiar Texto]                              │
└─────────────────────────────────────────────┘
```

---

## 🔌 **Opción 2: Usando la API REST**

### **Paso 1: Obtener Token de Autenticación**

```bash
# Login
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "doctor@clinidocs.com",
    "password": "tu_password"
  }'
```

**Respuesta:**

```json
{
  "access": "eyJhbGciOiJIUzI1NiIs...",
  "refresh": "eyJhbGciOiJIUzI1NiIs...",
  "user": {
    "id": "uuid",
    "email": "doctor@clinidocs.com"
  }
}
```

Guarda el `access` token.

---

### **Paso 2: Subir la Tomografía**

```bash
curl -X POST http://localhost:8000/api/documents/ \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  -F "clinical_record=<clinical_record_uuid>" \
  -F "document_type=imaging_report" \
  -F "title=Tomografía de Tórax sin Contraste" \
  -F "description=Estudio de tórax para evaluación pulmonar" \
  -F "specialty=Radiología" \
  -F "doctor_name=Dr. Carlos Ramírez" \
  -F "doctor_license=R-12345" \
  -F "document_date=2025-11-19T10:30:00Z" \
  -F "file=@/ruta/a/tomografia.jpg"
```

**Respuesta:**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "clinical_record": "uuid",
  "document_type": "imaging_report",
  "document_type_display": "Informe de Imagen",
  "title": "Tomografía de Tórax sin Contraste",
  "description": "Estudio de tórax para evaluación pulmonar",
  "file_path": "documents/tenant-id/550e8400-e29b-41d4-a716-446655440000.jpg",
  "file_name": "tomografia.jpg",
  "file_size": 2457600,
  "mime_type": "image/jpeg",
  "specialty": "Radiología",
  "doctor_name": "Dr. Carlos Ramírez",
  "doctor_license": "R-12345",
  "document_date": "2025-11-19T10:30:00Z",
  "ocr_processed": false,
  "ocr_status": "pending",
  "enhanced_image_path": "",
  "is_signed": false,
  "created_at": "2025-11-19T10:35:00Z"
}
```

---

### **Paso 3: Obtener URL para Visualizar**

```bash
curl -X GET http://localhost:8000/api/documents/550e8400-e29b-41d4-a716-446655440000/view/ \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

**Respuesta:**

```json
{
  "url": "https://s3.amazonaws.com/clinidocs-documents/documents/tenant-id/550e8400.jpg?AWSAccessKeyId=...&Signature=...&Expires=1700409600",
  "expires_at": "2025-11-19T11:35:00Z",
  "file_name": "tomografia.jpg"
}
```

Usa esta URL en tu aplicación para mostrar la imagen (válida por 1 hora).

---

### **Paso 4: Mejorar Imagen con CLAHE**

```bash
curl -X POST http://localhost:8000/api/documents/550e8400-e29b-41d4-a716-446655440000/enhance/ \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  -H "Content-Type: application/json" \
  -d '{
    "modality": "CT",
    "use_preset": true
  }'
```

**Respuesta:**

```json
{
  "success": true,
  "message": "Imagen mejorada exitosamente",
  "original_url": "https://s3.../original.jpg",
  "enhanced_url": "https://s3.../enhanced.jpg",
  "metrics": {
    "mse": 245.8,
    "psnr": 34.2,
    "ssim": 0.92
  },
  "method": "CLAHE",
  "parameters": {
    "clip_limit": 2.0,
    "tile_grid_size": [8, 8]
  }
}
```

---

### **Paso 5: Procesar OCR**

```bash
curl -X POST http://localhost:8000/api/documents/550e8400-e29b-41d4-a716-446655440000/ocr/ \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

**Respuesta (inicia procesamiento asíncrono):**

```json
{
  "success": true,
  "message": "Procesamiento OCR iniciado",
  "job_id": "abc123-def456-ghi789",
  "status": "async_processing"
}
```

**Consultar estado:**

```bash
curl -X GET http://localhost:8000/api/documents/550e8400-e29b-41d4-a716-446655440000/ \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

Cuando `ocr_status === 'completed'`:

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "ocr_processed": true,
  "ocr_status": "completed",
  "ocr_confidence": 94.5,
  "ocr_text": "INFORME DE TOMOGRAFÍA COMPUTARIZADA DE TÓRAX\n\nPaciente: Juan Pérez García...",
  ...
}
```

---

## 🩻 **Opción 3: Subir Imagen DICOM (Especializado)**

Para archivos `.dcm` con metadatos DICOM completos:

```bash
curl -X POST http://localhost:8000/api/documents/images/ \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  -F "clinical_record=<clinical_record_uuid>" \
  -F "image_type=ct_scan" \
  -F "title=TC Tórax - Serie Completa" \
  -F "study_date=2025-11-19T10:30:00Z" \
  -F "modality=CT" \
  -F "body_part=Tórax" \
  -F "file=@/ruta/a/ct_slice_001.dcm"
```

**Respuesta:**

```json
{
  "id": "uuid",
  "clinical_record": "uuid",
  "image_type": "ct_scan",
  "image_type_display": "Tomografía",
  "title": "TC Tórax - Serie Completa",
  "study_date": "2025-11-19T10:30:00Z",
  "modality": "CT",
  "body_part": "Tórax",
  "file_path": "medical-images/tenant-id/uuid.dcm",
  "file_name": "ct_slice_001.dcm",
  "file_size": 5242880,
  "dicom_metadata": {
    "PatientID": "12345",
    "StudyInstanceUID": "1.2.840.113619.2.55.3...",
    "SeriesInstanceUID": "1.2.840.113619.2.55.3...",
    "SliceThickness": "5.0",
    "KVP": "120",
    "SliceLocation": "0.0",
    "ImagePositionPatient": ["0.0", "0.0", "0.0"],
    "PixelSpacing": ["0.625", "0.625"],
    "Rows": 512,
    "Columns": 512
  },
  "enhancement_applied": false,
  "enhanced_image_path": null,
  "created_at": "2025-11-19T10:35:00Z"
}
```

**Mejorar imagen DICOM:**

```bash
curl -X POST http://localhost:8000/api/documents/images/<image_id>/enhance/ \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

---

## 📊 **Consultar Imágenes de un Paciente**

### **Todas las imágenes**

```bash
GET /api/documents/?clinical_record=<uuid>&document_type=imaging_report
```

### **Solo tomografías**

```bash
GET /api/documents/images/?clinical_record=<uuid>&image_type=ct_scan
```

### **Filtrar por parte del cuerpo**

```bash
GET /api/documents/images/?clinical_record=<uuid>&body_part=Tórax
```

### **Ordenar por fecha**

```bash
GET /api/documents/images/?clinical_record=<uuid>&ordering=-study_date
```

---

## 🎯 **Resumen del Flujo Completo**

```
1. Usuario sube tomografía desde frontend
   ↓
2. Archivo se guarda en AWS S3
   ↓
3. Se crea registro en base de datos
   ↓
4. (Opcional) AWS Textract extrae texto
   ↓
5. Usuario ve imagen en el visor
   ↓
6. (Opcional) Aplica mejora CLAHE
   ↓
7. Compara original vs mejorada
   ↓
8. Lee texto extraído por OCR
   ↓
9. Descarga o imprime según necesidad
```

---

## ✅ **Verificación**

Para confirmar que todo funciona:

```bash
# 1. Verificar que el documento existe
GET /api/documents/<id>/

# 2. Verificar que el archivo está en S3
aws s3 ls s3://clinidocs-documents/documents/<tenant_id>/

# 3. Verificar OCR (si fue procesado)
GET /api/documents/<id>/
# Revisar: ocr_status === 'completed'

# 4. Verificar mejora (si fue aplicada)
GET /api/documents/<id>/
# Revisar: enhanced_image_path !== ''
```

---

¡Listo! Ahora puedes subir, mejorar y visualizar tomografías en tu sistema CliniDocs 🎉
