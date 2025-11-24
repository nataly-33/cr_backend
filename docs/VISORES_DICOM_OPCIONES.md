# Opciones de Visores DICOM para CliniDocs

## 🎯 **Tu Necesidad**

Quieres visualizar tomografías, resonancias y ecografías **dentro de tu sistema** sin descargar software externo. Los usuarios deben poder ver las imágenes médicas directamente en el navegador con herramientas profesionales.

---

## 🏆 **Comparativa de Opciones**

| Opción | Tipo | Costo | Dificultad | Características | Recomendación |
|--------|------|-------|------------|-----------------|---------------|
| **Cornerstone.js** | Librería Open Source | 🆓 Gratis | ⭐⭐ Media | ⭐⭐⭐⭐⭐ Excelente | 🥇 **MÁS RECOMENDADO** |
| **OHIF Viewer** | Aplicación completa | 🆓 Gratis | ⭐⭐⭐ Alta | ⭐⭐⭐⭐⭐ Excelente | 🥈 Mejor para sistemas grandes |
| **DWV (DICOM Web Viewer)** | Librería ligera | 🆓 Gratis | ⭐ Fácil | ⭐⭐⭐ Buena | 🥉 Más simple pero limitada |
| **Kheops** | SaaS Cloud | 💰 Pago | ⭐ Fácil | ⭐⭐⭐⭐ Muy buena | Solo si quieres servicio externo |
| **Orthanc + Stone Viewer** | Servidor DICOM | 🆓 Gratis | ⭐⭐⭐⭐ Muy alta | ⭐⭐⭐⭐⭐ Excelente | Para infraestructura completa |

---

## 🥇 **OPCIÓN 1: Cornerstone.js** (RECOMENDADA)

### **¿Qué es?**

Cornerstone.js es la **librería JavaScript más usada** para visualización de imágenes médicas DICOM en navegadores. Es open-source, gratuita y usada por hospitales profesionales.

### **✅ Ventajas:**

- ✅ **100% Gratis** y open-source (MIT License)
- ✅ **Integración sencilla** en React
- ✅ **Todas las herramientas profesionales** que necesitas:
  - Zoom, pan, rotación
  - Windowing/Leveling (ajuste de brillo/contraste médico)
  - Medición de distancias y ángulos
  - Anotaciones y marcadores
  - Multi-frame y series completas
  - Renderizado 3D (con Cornerstone3D)
- ✅ **Funciona con archivos S3**: Solo necesitas una URL
- ✅ **Soporta todos los formatos**: DICOM, JPG, PNG
- ✅ **Activamente mantenida**: Gran comunidad

### **❌ Desventajas:**

- Requiere instalación de dependencias NPM
- Necesitas configurar el loader de DICOM

### **📦 Instalación:**

```bash
cd cr_frontend

npm install @cornerstonejs/core
npm install @cornerstonejs/tools
npm install @cornerstonejs/dicom-image-loader
npm install dicom-parser
```

### **🔧 Implementación:**

Ya creé el componente completo: [DicomViewer.tsx](../../cr_frontend/src/modules/documents/components/DicomViewer.tsx)

**Cómo usarlo:**

```tsx
import { DicomViewer } from '@modules/documents/components/DicomViewer';

// En tu DocumentViewerPage
<DicomViewer
  dicomUrl={fileUrl}
  modality="CT"
  windowPresets={[
    { name: 'Pulmón', windowWidth: 1500, windowCenter: -600 },
    { name: 'Mediastino', windowWidth: 350, windowCenter: 50 }
  ]}
/>
```

### **🎨 Herramientas Incluidas:**

| Herramienta | Descripción | Ícono |
|-------------|-------------|-------|
| **Pan** | Mover la imagen | ✋ |
| **Zoom In/Out** | Acercar/Alejar | 🔍 |
| **Rotate** | Rotar 90° | 🔄 |
| **Invert** | Invertir colores (blanco/negro) | ⚫⚪ |
| **Window/Level** | Ajustar brillo médico | 🎚️ |
| **Length** | Medir distancias (mm) | 📏 |
| **Angle** | Medir ángulos | 📐 |
| **Magnify** | Lupa | 🔎 |

### **🏥 Presets Médicos Incluidos:**

**Para CT (Tomografía):**
- Pulmón (W:1500, L:-600) - Para ver estructuras pulmonares
- Mediastino (W:350, L:50) - Para ver corazón y vasos
- Hueso (W:2500, L:480) - Para ver fracturas
- Cerebro (W:80, L:40) - Para ver lesiones cerebrales
- Hígado (W:150, L:30) - Para ver patologías hepáticas

**Para MRI (Resonancia):**
- T1 (W:600, L:300)
- T2 (W:400, L:200)
- FLAIR (W:500, L:250)

### **💰 Costo:**

**GRATIS** - Licencia MIT

---

## 🥈 **OPCIÓN 2: OHIF Viewer** (Para Sistemas Grandes)

### **¿Qué es?**

OHIF (Open Health Imaging Foundation) es una **aplicación completa de visualización DICOM** tipo PACS (Picture Archiving and Communication System). Es lo que usan hospitales grandes.

### **✅ Ventajas:**

- ✅ **Aplicación completa** - No necesitas programar nada
- ✅ **Interfaz profesional** estilo PACS médico
- ✅ **Todas las funcionalidades avanzadas**:
  - Visualización multi-monitor
  - Comparación de estudios
  - Reportes estructurados
  - Hanging protocols (layouts automáticos)
  - MPR (Multi-Planar Reconstruction)
  - Segmentación con IA
- ✅ **Integraciones**: Google Cloud Healthcare, AWS HealthLake
- ✅ **Certificaciones médicas** (FDA, CE)

### **❌ Desventajas:**

- ⚠️ **MUY complejo de integrar** - Es una aplicación standalone
- ⚠️ Requiere **servidor DICOM** (DICOMweb)
- ⚠️ Curva de aprendizaje alta
- ⚠️ Puede ser "overkill" para tu caso

### **📦 Instalación:**

```bash
# Clonar repositorio
git clone https://github.com/OHIF/Viewers.git
cd Viewers

# Instalar y ejecutar
yarn install
yarn run dev
```

### **🔧 Integración:**

Necesitas configurar un servidor DICOMweb:

```javascript
// config/default.js
window.config = {
  servers: {
    dicomWeb: [
      {
        name: 'CliniDocs',
        wadoUriRoot: 'http://localhost:8000/api/dicom/wado',
        qidoRoot: 'http://localhost:8000/api/dicom/qido',
        wadoRoot: 'http://localhost:8000/api/dicom/wado',
      }
    ]
  }
}
```

Luego embeber en iframe:

```tsx
<iframe
  src="http://localhost:3000/viewer?StudyInstanceUID=1.2.840..."
  width="100%"
  height="800px"
/>
```

### **💰 Costo:**

**GRATIS** - Licencia MIT

**Pero necesitas:**
- Servidor DICOMweb (puede usar Orthanc - gratis)
- Mucho tiempo de configuración

---

## 🥉 **OPCIÓN 3: DWV (DICOM Web Viewer)** (Simple y Rápida)

### **¿Qué es?**

DWV es una librería JavaScript **muy liviana** para visualización DICOM básica. Ideal si solo necesitas mostrar imágenes sin herramientas avanzadas.

### **✅ Ventajas:**

- ✅ **Muy fácil de implementar** (5 minutos)
- ✅ **Ligera** (bundle pequeño)
- ✅ **Funciona sin servidor DICOM**
- ✅ Herramientas básicas incluidas

### **❌ Desventajas:**

- ❌ Funcionalidades limitadas vs Cornerstone
- ❌ UI menos moderna
- ❌ Menos herramientas de medición

### **📦 Instalación:**

```bash
npm install dwv
```

### **🔧 Implementación:**

```tsx
import dwv from 'dwv';
import { useEffect, useRef } from 'react';

export const SimpleDicomViewer = ({ fileUrl }) => {
  const containerRef = useRef(null);

  useEffect(() => {
    if (!containerRef.current) return;

    const app = new dwv.App();
    app.init({
      containerDivId: 'dwv-container',
      tools: ['Scroll', 'ZoomAndPan', 'WindowLevel', 'Draw']
    });

    // Cargar imagen
    app.loadURLs([fileUrl]);

    return () => app.reset();
  }, [fileUrl]);

  return <div id="dwv-container" ref={containerRef} />;
};
```

### **💰 Costo:**

**GRATIS** - Licencia GPL-3.0

---

## 💼 **OPCIÓN 4: Kheops (SaaS Cloud)** (Servicio Externo)

### **¿Qué es?**

Kheops es un **servicio en la nube** para almacenar y visualizar imágenes DICOM. Lo alojas en sus servidores.

### **✅ Ventajas:**

- ✅ **Sin desarrollo** - Solo subes archivos a su API
- ✅ Visor profesional incluido
- ✅ Compartir estudios fácilmente
- ✅ Almacenamiento DICOM optimizado

### **❌ Desventajas:**

- ❌ **Servicio externo** - Datos fuera de tu control
- ❌ Depende de internet
- ❌ Puede tener costos en el futuro

### **🔧 Implementación:**

```javascript
// Subir DICOM a Kheops
fetch('https://kheops.eu/api/studies', {
  method: 'POST',
  headers: { 'Authorization': 'Bearer token' },
  body: dicomFile
});

// Embedear visor
<iframe src="https://kheops.eu/view/study/123" />
```

### **💰 Costo:**

**GRATIS** por ahora - Proyecto de investigación
⚠️ Pero puedes perder acceso o empezar a cobrar

---

## 🏥 **OPCIÓN 5: Orthanc + Stone Viewer** (Infraestructura Completa)

### **¿Qué es?**

Orthanc es un **servidor DICOM completo** que actúa como mini-PACS. Stone Viewer es su visor web integrado.

### **✅ Ventajas:**

- ✅ **Solución completa** - Servidor + Visor + Base de datos
- ✅ Compatible con equipos médicos (DICOM C-STORE)
- ✅ Búsquedas DICOM avanzadas (QIDO-RS, WADO-RS)
- ✅ Stone Viewer muy potente
- ✅ Almacenamiento optimizado

### **❌ Desventajas:**

- ❌ **Requiere servidor adicional** (Docker)
- ❌ Configuración compleja
- ❌ Overhead para archivos simples

### **🔧 Instalación:**

```bash
# Docker Compose
version: '3'
services:
  orthanc:
    image: jodogne/orthanc-plugins
    ports:
      - "8042:8042"
      - "4242:4242"  # DICOM port
    volumes:
      - ./orthanc-db:/var/lib/orthanc/db
    environment:
      - ORTHANC__NAME=CliniDocs
```

### **Integración con Django:**

```python
# Subir DICOM a Orthanc
import requests

response = requests.post(
    'http://localhost:8042/instances',
    files={'file': dicom_file},
    auth=('orthanc', 'orthanc')
)

instance_id = response.json()['ID']

# Ver en Stone Viewer
viewer_url = f'http://localhost:8042/stone-webviewer/index.html?study={study_id}'
```

### **💰 Costo:**

**GRATIS** - Licencia GPL-3.0

**Pero necesitas:**
- Servidor adicional (hosting/Docker)
- Mantenimiento técnico

---

## 📊 **Comparativa Técnica**

### **Funcionalidades:**

| Característica | Cornerstone.js | OHIF | DWV | Kheops | Orthanc |
|----------------|----------------|------|-----|---------|---------|
| **Zoom/Pan** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Windowing** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Mediciones** | ✅✅ | ✅✅ | ✅ | ✅ | ✅✅ |
| **Anotaciones** | ✅ | ✅✅ | ✅ | ✅ | ✅ |
| **Multi-frame** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **3D Rendering** | ✅ (v3) | ✅ | ❌ | ✅ | ✅ |
| **MPR** | ✅ (v3) | ✅ | ❌ | ❌ | ✅ |
| **Comparación** | ⚠️ Manual | ✅ | ❌ | ✅ | ✅ |
| **Hanging Protocols** | ⚠️ Custom | ✅ | ❌ | ❌ | ✅ |

### **Integración:**

| Aspecto | Cornerstone.js | OHIF | DWV | Kheops | Orthanc |
|---------|----------------|------|-----|---------|---------|
| **Instalación NPM** | ⭐⭐⭐ Fácil | ⭐ Difícil | ⭐⭐⭐ Muy fácil | N/A | N/A |
| **Integración React** | ⭐⭐⭐ Nativa | ⭐⭐ Compleja | ⭐⭐⭐ Fácil | ⭐⭐⭐ Iframe | ⭐⭐ Iframe |
| **Configuración** | 30 min | 4-8 horas | 10 min | 15 min | 2-4 horas |
| **Requiere Backend** | ❌ | ✅ DICOMweb | ❌ | ✅ API | ✅ Servidor |
| **Bundle Size** | ~1.5 MB | ~5 MB | ~500 KB | N/A | N/A |

---

## 🎯 **Recomendación Final**

### **Para tu caso (CliniDocs):**

🥇 **USA CORNERSTONE.JS** porque:

1. ✅ **Perfecto balance** entre funcionalidad y simplicidad
2. ✅ **Integración directa** en tu React app existente
3. ✅ **No requiere servidor adicional** - Solo URLs de S3
4. ✅ **Todas las herramientas** que un médico necesita
5. ✅ **Gratis y open-source**
6. ✅ **Gran comunidad** y documentación

### **Implementación Paso a Paso:**

```bash
# 1. Instalar dependencias
npm install @cornerstonejs/core @cornerstonejs/tools
npm install @cornerstonejs/dicom-image-loader dicom-parser

# 2. Usar el componente que ya creé
# cr_frontend/src/modules/documents/components/DicomViewer.tsx

# 3. Integrarlo en DocumentViewerPage
import { DicomViewer } from '../components/DicomViewer';

// Detectar si es DICOM
const isDICOM = fileUrl?.endsWith('.dcm') ||
                document.document_type === 'imaging_report';

{isDICOM ? (
  <DicomViewer
    dicomUrl={fileUrl}
    modality={document.modality || 'CT'}
  />
) : (
  // Tu visor actual para PDF/imágenes normales
)}
```

### **Si en el futuro necesitas más:**

📈 **Actualiza a OHIF Viewer** cuando:
- Tengas cientos de estudios diarios
- Necesites comparación automática de estudios
- Quieras MPR y reconstrucciones 3D avanzadas
- Necesites certificación médica (FDA/CE)

---

## 📚 **Recursos y Documentación**

### **Cornerstone.js:**
- 🌐 Web: https://www.cornerstonejs.org/
- 📖 Docs: https://www.cornerstonejs.org/docs/
- 💻 GitHub: https://github.com/cornerstonejs/cornerstone3D
- 🎥 Tutorial: https://www.youtube.com/watch?v=xyz (buscar "Cornerstone.js tutorial")

### **OHIF Viewer:**
- 🌐 Web: https://ohif.org/
- 📖 Docs: https://v3-docs.ohif.org/
- 💻 GitHub: https://github.com/OHIF/Viewers

### **DWV:**
- 🌐 Web: https://ivmartel.github.io/dwv/
- 💻 GitHub: https://github.com/ivmartel/dwv

### **Orthanc:**
- 🌐 Web: https://www.orthanc-server.com/
- 📖 Docs: https://book.orthanc-server.com/

---

## ✅ **Próximos Pasos**

1. **Instala Cornerstone.js** (30 minutos)
2. **Prueba el DicomViewer** que creé con una tomografía de ejemplo
3. **Integra en DocumentViewerPage** para detección automática DICOM
4. **Configura presets** según tus especialidades médicas
5. ✨ **¡Listo!** - Tu sistema ya tiene visor DICOM profesional

---

¿Quieres que te ayude con la instalación e integración de Cornerstone.js? 🚀
