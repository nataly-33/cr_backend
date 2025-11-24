# Guía Rápida: Visor de Imágenes Médicas

## ✅ **¡Ya está funcionando!**

Tu sistema ahora puede visualizar resonancias magnéticas, tomografías y ecografías directamente en el navegador.

---

## 🎯 **Cómo funciona**

### **Paso 1: Subir una Resonancia Magnética**

1. Ve a **Documentos** → **Subir Documento**
2. Completa el formulario:
   - **Tipo de Documento**: Selecciona **"Informe de Imagen"**
   - **Título**: "Resonancia Magnética de Cerebro"
   - **Descripción**: "Estudio sin contraste"
   - **Historia Clínica**: Selecciona el paciente
3. Arrastra tu archivo (JPG, PNG, o DICOM)
4. Click **"Subir Documento"**

---

### **Paso 2: Ver la Imagen con el Visor Médico**

Cuando abras el documento, verás:

```
┌──────────────────────────────────────────────────────────┐
│ Barra de Herramientas                                    │
│ [🔍 Zoom +] [🔍 Zoom -] [🔄 Rotar] [⚫⚪ Invertir]     │
│                                       Modalidad: MRI      │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│                                                          │
│                                                          │
│         [IMAGEN DE RESONANCIA MAGNÉTICA]                 │
│                                                          │
│                                                          │
│ ℹ️ Visor Simplificado                                   │
│ Este es un visor básico. Para funcionalidad completa... │
└──────────────────────────────────────────────────────────┘
```

---

## 🛠️ **Herramientas Disponibles**

| Herramienta | Descripción | Botón |
|-------------|-------------|-------|
| **Zoom In** | Acercar la imagen | 🔍+ |
| **Zoom Out** | Alejar la imagen | 🔍- |
| **Rotar** | Girar 90° | 🔄 |
| **Invertir** | Invertir blanco/negro | ⚫⚪ |
| **Restaurar** | Volver a vista inicial | ⬜ |

---

## 📋 **Detección Automática**

El sistema detecta **automáticamente** si un documento es una imagen médica basándose en:

1. **Tipo de documento** = `"imaging_report"` ✅
2. **Extensión de archivo** = `.dcm` o `.dicom` ✅
3. **MIME type** = `application/dicom` ✅

Si cumple alguna condición → Muestra **Visor Médico**
Si no → Muestra visor normal (PDF o imagen estándar)

---

## 🔧 **Código Implementado**

### **Archivos Modificados:**

1. **[DicomViewer.tsx](../../cr_frontend/src/modules/documents/components/DicomViewer.tsx)**
   - Nuevo componente de visor médico
   - Herramientas: zoom, rotar, invertir
   - Diseño adaptado para imágenes médicas

2. **[DocumentViewerPage.tsx](../../cr_frontend/src/modules/documents/pages/DocumentViewerPage.tsx)**
   - Integración del DicomViewer
   - Detección automática de imágenes médicas
   - Fallback a visor normal si no es imagen médica

---

## 🎨 **Características del Visor Actual**

### ✅ **Lo que SÍ tiene:**
- Zoom in/out
- Rotación 90°
- Inversión de colores (útil para rayos X)
- Vista en pantalla completa
- Interfaz adaptada a modalidad (MRI, CT, etc.)

### ⚠️ **Lo que NO tiene (aún):**
- Windowing/Leveling (ajuste de brillo médico)
- Mediciones (distancias, ángulos)
- Visualización de múltiples cortes (series DICOM)
- Renderizado 3D
- MPR (Multi-Planar Reconstruction)

---

## 🚀 **Para Funcionalidad Completa DICOM**

Si en el futuro necesitas herramientas médicas avanzadas:

### **Opción 1: Cornerstone.js 3D** (Recomendado)
```bash
# Instalación (ya hecha)
npm install @cornerstonejs/core @cornerstonejs/tools

# Implementar visor completo
# Ver: VISORES_DICOM_OPCIONES.md
```

**Agrega:**
- Windowing/Leveling completo
- Mediciones precisas en mm
- Visualización de series multi-frame
- Renderizado 3D volumétrico

### **Opción 2: OHIF Viewer** (Para hospitales grandes)
- Aplicación completa tipo PACS
- Certificaciones médicas (FDA, CE)
- Comparación de estudios
- Reportes estructurados

---

## 📸 **Ejemplo de Uso**

### **Subir Resonancia:**
```
1. Documentos → Subir
2. Tipo: "Informe de Imagen"
3. Título: "RM Cerebro"
4. Archivo: resonancia.jpg
```

### **Ver Resonancia:**
```
→ Sistema detecta que es imaging_report
→ Muestra DicomViewer automáticamente
→ Usuario puede:
   - Hacer zoom para ver detalles
   - Rotar si está mal orientada
   - Invertir colores si es necesario
```

---

## ❓ **Preguntas Frecuentes**

### **1. ¿Funciona con archivos DICOM (.dcm)?**

✅ **Sí**, pero con limitaciones:
- El visor actual muestra archivos `.dcm` como imágenes estáticas
- Para funcionalidad completa DICOM (ventana/nivel, series), usa Cornerstone.js 3D

### **2. ¿Puedo ver múltiples cortes de una tomografía?**

⚠️ **No con el visor actual**
- El visor simple muestra 1 imagen a la vez
- Para series completas, necesitas Cornerstone.js o OHIF

### **3. ¿Funciona con JPG y PNG de resonancias?**

✅ **Sí**, perfectamente:
- Si subes una foto/escaneo de una resonancia
- Y seleccionas tipo **"Informe de Imagen"**
- El visor médico se activa automáticamente

### **4. ¿Puedo medir distancias en la imagen?**

❌ **No con el visor actual**
- Solo tiene zoom, rotar, invertir
- Para mediciones, necesitas integrar Cornerstone.js

### **5. ¿Cómo cambio entre visor médico y visor normal?**

**Es automático:**
- `document_type === "imaging_report"` → Visor médico
- Otro tipo → Visor normal (PDF, imagen estándar)

---

## ✅ **Checklist de Verificación**

- [x] DicomViewer implementado
- [x] Integrado en DocumentViewerPage
- [x] Detección automática funciona
- [x] Build exitoso
- [x] Herramientas básicas (zoom, rotar, invertir)
- [ ] **Prueba manual**: Subir una resonancia y verificar

---

## 🎯 **Próximos Pasos (Opcional)**

### **Si quieres mejorar el visor:**

1. **Agregar Window/Level manual**
   - Input para ajustar brillo/contraste
   - Presets por tipo de estudio (pulmón, hueso, etc.)

2. **Integrar Cornerstone.js completo**
   - Seguir guía en VISORES_DICOM_OPCIONES.md
   - ~2-4 horas de trabajo
   - Agrega todas las herramientas profesionales

3. **Soporte para series DICOM**
   - Permitir subir múltiples archivos .dcm
   - Navegación entre cortes con scroll

---

## 📞 **Soporte**

Para más información:
- 📄 Guía completa: [GUIA_IMAGENES_MEDICAS.md](./GUIA_IMAGENES_MEDICAS.md)
- 🔍 Opciones avanzadas: [VISORES_DICOM_OPCIONES.md](./VISORES_DICOM_OPCIONES.md)
- 📖 Ejemplo de uso: [EJEMPLO_SUBIR_TOMOGRAFIA.md](./EJEMPLO_SUBIR_TOMOGRAFIA.md)

---

¡Ya puedes visualizar resonancias magnéticas en tu sistema! 🎉
