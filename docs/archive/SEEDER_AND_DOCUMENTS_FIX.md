# 🔧 Correcciones: Seeder Completo y Visualización de Documentos

## Fecha: 5 de Noviembre de 2025

---

## 📋 Problemas Identificados

### 1. **Seeder Incompleto** ❌

- `seed_data.py` no incluía la lógica de `seed_clinical_forms.py` y `seed_clinical_records.py`
- Las historias clínicas no tenían **alergias**, **condiciones crónicas** ni **medicaciones**
- No se creaban **formularios clínicos** (triaje, consultas, recetas, órdenes de laboratorio)
- Los documentos eran muy básicos y no tenían contenido estructurado

### 2. **Visualización de Documentos** ❌

- Los documentos generados por el seeder no tenían archivos físicos (solo contenido JSON)
- El frontend intentaba descargar archivos que no existían
- Error 404 al intentar ver documentos: `Page not found - Los índices de directorio no están permitidos`
- No se podían visualizar los documentos clínicos en el frontend

---

## ✅ Soluciones Implementadas

### 1. **Seeder Completo y Mejorado** (`seed_data.py`)

#### **Historias Clínicas Completas**

```python
def create_clinical_records(tenant, patients):
    """
    Crea historias clínicas COMPLETAS con:
    - Tipo de sangre
    - Alergias (0-3 por paciente)
    - Condiciones crónicas (0-2 por paciente)
    - Medicaciones actuales (0-4 por paciente)
    """
```

**Datos médicos realistas agregados:**

- 8 tipos de sangre: A+, A-, B+, B-, AB+, AB-, O+, O-
- 12 alergias comunes: Penicilina, Polen, Mariscos, Látex, etc.
- 15 condiciones crónicas: Hipertensión, Diabetes, Asma, EPOC, etc.
- 10 medicaciones: Losartán, Metformina, Atorvastatina, Omeprazol, etc.

#### **Formularios Clínicos** (Nuevo)

Se agregaron 4 tipos de formularios clínicos:

1. **Triaje** (`create_triage_form`)

   - Signos vitales completos (temperatura, presión, frecuencia cardíaca, etc.)
   - Motivo de consulta
   - Evaluación inicial
   - Nivel de urgencia (1-5)

2. **Consulta Médica** (`create_consultation_form`)

   - Historia de enfermedad actual
   - Revisión de sistemas
   - Examen físico
   - Diagnósticos con códigos CIE
   - Plan de tratamiento con medicamentos
   - Órdenes de laboratorio
   - Seguimiento

3. **Receta Médica** (`create_prescription_form`)

   - Lista de medicamentos con dosis, frecuencia y duración
   - Instrucciones de administración
   - Diagnóstico
   - Notas adicionales

4. **Orden de Laboratorio** (`create_lab_order_form`)
   - Lista de exámenes solicitados
   - Diagnóstico
   - Urgencia (routine/urgent/stat)
   - Requerimientos especiales (ayuno, etc.)

#### **Documentos Clínicos Mejorados**

```python
def create_clinical_documents(tenant, clinical_records, doctors):
    """
    Crear documentos clínicos completos con contenido estructurado:
    - Consultas médicas con signos vitales y diagnósticos
    - Resultados de laboratorio con valores y rangos de referencia
    - Recetas médicas detalladas
    """
```

**Tipos de documentos con contenido JSON estructurado:**

1. **Consulta Médica**

   ```json
   {
     "chief_complaint": "Dolor abdominal",
     "history_present_illness": "...",
     "vital_signs": {
       "blood_pressure": "120/80",
       "heart_rate": 72,
       "temperature": 36.5
     },
     "physical_examination": "...",
     "diagnosis": "Gastroenteritis aguda",
     "treatment_plan": "..."
   }
   ```

2. **Resultado de Laboratorio**

   ```json
   {
     "test_name": "Hemograma Completo",
     "results": {
       "Hemoglobina": {
         "value": "14.5",
         "unit": "g/dL",
         "reference": "12-16"
       }
     },
     "interpretation": "..."
   }
   ```

3. **Receta Médica**
   ```json
   {
     "diagnosis": "...",
     "medications": [
       {
         "name": "Amoxicilina",
         "dose": "500mg",
         "frequency": "cada 8h",
         "duration": "7 días"
       }
     ]
   }
   ```

---

### 2. **Visualización de Documentos en el Frontend**

#### **Cambios en el Tipo `ClinicalDocument`**

```typescript
export interface ClinicalDocument {
  // ... campos existentes
  file_path?: string; // ✅ NUEVO: Ruta del archivo en S3
  content?: Record<string, any>; // ✅ NUEVO: Contenido estructurado
}
```

#### **Nuevo Componente: `DocumentContentViewer`**

Componente React que renderiza el contenido JSON de manera profesional según el tipo de documento:

**Características:**

- ✅ **Consultas médicas**: Muestra signos vitales, diagnóstico, plan de tratamiento
- ✅ **Resultados de laboratorio**: Tabla con valores, unidades y rangos de referencia
- ✅ **Recetas médicas**: Lista de medicamentos con dosis y frecuencias
- ✅ **Genérico**: Visualización JSON estructurada para otros tipos

**Ejemplo de renderizado:**

```tsx
// Para Consultas
<DocumentContentViewer content={document.content} documentType="consultation" />

// Muestra:
// ┌─────────────────────────────────────┐
// │     Consulta Médica                 │
// ├─────────────────────────────────────┤
// │ Motivo de Consulta                  │
// │ Dolor abdominal                     │
// │                                     │
// │ Signos Vitales                      │
// │ ┌─────────┬─────────┬─────────┐   │
// │ │ PA      │ FC      │ Temp    │   │
// │ │ 120/80  │ 72 lpm  │ 36.5°C  │   │
// │ └─────────┴─────────┴─────────┘   │
// │                                     │
// │ Diagnóstico                         │
// │ 🔹 Gastroenteritis aguda            │
// └─────────────────────────────────────┘
```

#### **Lógica de Visualización Mejorada**

```tsx
// Antes ❌
if (doc.file) {
  const { url } = await documentsService.download(id!);
  setFileUrl(url);
}

// Después ✅
if (doc.file_path && doc.file_name) {
  try {
    const { url } = await documentsService.download(id!);
    setFileUrl(url);
  } catch (error) {
    console.warn("No hay archivo, mostrando contenido JSON");
  }
}
```

**Flujo de visualización:**

1. ¿Hay archivo PDF? → Mostrar con visor PDF
2. ¿Hay archivo de imagen? → Mostrar imagen
3. ¿Hay contenido JSON? → Mostrar con `DocumentContentViewer` ✨
4. No hay nada → Mensaje "Vista previa no disponible"

---

## 🔄 Flujo del Sistema (Aclarado)

### **1. CLINICAL_RECORD (Historia Clínica)**

- Se crea **UNA SOLA VEZ** por paciente
- Contiene: alergias, condiciones crónicas, medicaciones actuales
- Es el "contenedor principal"

### **2. CLINICAL_FORM (Formulario Clínico)**

- Asociado a una historia clínica
- **Múltiples formularios** por historia
- Tipos: Triaje, Consulta, Receta, Orden de Lab
- Llenados por doctores durante la atención
- Estructura: JSON flexible en `form_data`

### **3. CLINICAL_DOCUMENT (Documento Clínico)**

- También asociado a una historia clínica
- **Múltiples documentos** por historia
- Tipos: Consulta, Resultado Lab, Receta, Reporte
- Puede incluir:
  - **Archivo físico** (PDF, imagen) en S3 → `file_path`
  - **Contenido estructurado** (JSON) → `content`
  - **Ambos** (archivo + metadata JSON)

### **Ejemplo de Flujo:**

```
Paciente: Juan Pérez
└── CLINICAL_RECORD (Historia Clínica HC-2025-000001)
    ├── CLINICAL_FORM (Triaje) - 01/11/2025
    ├── CLINICAL_FORM (Consulta) - 01/11/2025
    ├── CLINICAL_FORM (Receta) - 01/11/2025
    ├── CLINICAL_DOCUMENT (Consulta Médica) - 01/11/2025 ✅ Visible en frontend
    ├── CLINICAL_DOCUMENT (Resultado Lab) - 05/11/2025 ✅ Visible en frontend
    └── CLINICAL_DOCUMENT (Receta) - 05/11/2025 ✅ Visible en frontend
```

---

## 📊 Estadísticas del Seeder Mejorado

Al ejecutar `python scripts/seed_data.py`, ahora se crean:

| Item                     | Cantidad | Descripción                                   |
| ------------------------ | -------- | --------------------------------------------- |
| **Tenants**              | 2        | Hospital Santa Cruz + Clínica La Paz          |
| **Usuarios**             | 10       | 2 Admin TI, 4 Doctores, 4 Pacientes           |
| **Pacientes**            | 70       | 50 para Pro, 20 para Basic                    |
| **Historias Clínicas**   | 70       | Con alergias, condiciones, medicaciones       |
| **Formularios Clínicos** | ~120     | Triaje + Consultas + Recetas + Labs           |
| **Documentos Clínicos**  | ~75      | Consultas + Labs + Recetas con contenido JSON |

---

## 🧪 Cómo Probar

### 1. **Ejecutar el Seeder Completo**

```bash
cd cr_backend
python scripts/seed_data.py
```

### 2. **Verificar en el Backend (Django Admin)**

```
http://localhost:8000/admin

Revisar:
- Clinical Records → Deberían tener alergias, medicaciones
- Clinical Forms → Deberían existir formularios de triaje, consultas
- Clinical Documents → Deberían tener campo "content" lleno
```

### 3. **Verificar en el Frontend**

```
http://localhost:5173/patients/9b4fff00-ed1a-4799-99ff-0a7b1d25cc53

✅ Deberías ver:
- Sección "Historia Clínica" con alergias y medicaciones
- Lista de documentos clínicos
- Al hacer clic en un documento → SE VISUALIZA el contenido estructurado

http://localhost:5173/documents/87469dd9-fc1f-4361-8d67-a94908dd5b55

✅ Ahora debería mostrar:
- Contenido estructurado del documento (signos vitales, diagnóstico, etc.)
- NO el error "Page not found (404)"
```

---

## 🎯 Próximos Pasos Sugeridos

### Backend

1. ✅ ~~Crear formularios clínicos (triaje, consultas)~~ **COMPLETADO**
2. ✅ ~~Mejorar documentos con contenido estructurado~~ **COMPLETADO**
3. 🔲 Crear CRUD completo para `ClinicalForm` en el frontend
4. 🔲 Agregar endpoint para subir archivos físicos a documentos existentes
5. 🔲 Implementar OCR para extraer texto de PDFs/imágenes

### Frontend

1. ✅ ~~Visualizar documentos sin archivo físico~~ **COMPLETADO**
2. 🔲 Crear página para ver y llenar formularios clínicos
3. 🔲 Agregar página de "Triaje" para pacientes nuevos
4. 🔲 Mejorar visualización de historia clínica (mostrar timeline)
5. 🔲 Agregar gráficos de signos vitales en el tiempo

---

## 📝 Archivos Modificados

### Backend

- ✅ `cr_backend/scripts/seed_data.py` - **Seeder completo mejorado**

### Frontend

- ✅ `cr_frontend/src/modules/documents/types/index.ts` - **Tipos actualizados**
- ✅ `cr_frontend/src/modules/documents/pages/DocumentViewerPage.tsx` - **Visualización mejorada**

---

## 🐛 Bugs Corregidos

1. ✅ **Error 404 al descargar documentos** → Ahora verifica si existe `file_path` antes de intentar descargar
2. ✅ **"Vista previa no disponible"** → Ahora muestra contenido JSON estructurado cuando no hay archivo
3. ✅ **Historias clínicas vacías** → Ahora incluyen alergias, condiciones crónicas y medicaciones
4. ✅ **Falta de formularios clínicos** → Ahora se crean triajes, consultas, recetas y órdenes de lab

---

## 💡 Notas Importantes

### Diferencia entre `ClinicalForm` y `ClinicalDocument`

| Aspecto            | ClinicalForm                                    | ClinicalDocument                          |
| ------------------ | ----------------------------------------------- | ----------------------------------------- |
| **Propósito**      | Formularios estructurados para captura de datos | Documentos finales con archivos/contenido |
| **Estructura**     | JSON en `form_data`                             | JSON en `content` + opcional `file_path`  |
| **Ejemplos**       | Triaje, Nota de evolución                       | Consulta, Resultado Lab, PDF              |
| **Firmable**       | ❌ No                                           | ✅ Sí                                     |
| **Archivo físico** | ❌ No                                           | ✅ Opcional                               |
| **Uso**            | Durante la atención                             | Registro permanente                       |

### ¿Cuándo usar cada uno?

**ClinicalForm** →

- Llenado de triaje al ingresar paciente
- Notas de evolución durante hospitalización
- Órdenes médicas (lab, imagen)
- Formularios interactivos

**ClinicalDocument** →

- Guardar consultas finalizadas
- Almacenar resultados de laboratorio
- Adjuntar PDFs de estudios
- Documentos que requieren firma digital

---

## ✨ Mejoras Adicionales Implementadas

1. **Datos Médicos Realistas**

   - Diagnósticos basados en CIE-10
   - Signos vitales con rangos normales
   - Medicamentos con dosis estándar

2. **Mejor Experiencia de Usuario**

   - Visualización profesional de documentos
   - Colores y badges para estados
   - Tablas para resultados de laboratorio
   - Cards organizadas por tipo de contenido

3. **Resumen Visual en Seeder**

   ```
   ✅ SEEDER COMPLETADO EXITOSAMENTE

   📊 RESUMEN FINAL
   • Tenants: 2
   • Usuarios totales: 10
   • Historias clínicas: 70
   • Formularios clínicos: 120  ← NUEVO
   • Documentos clínicos: 75

   💡 Flujo del Sistema:
   1. CLINICAL_RECORD (Historia Clínica)
   2. CLINICAL_FORM (Formulario Clínico)
   3. CLINICAL_DOCUMENT (Documento Clínico)
   ```

---

## 🎉 Conclusión

El sistema ahora tiene:

- ✅ Seeder completo con datos médicos realistas
- ✅ Historias clínicas completas (alergias, medicaciones)
- ✅ Formularios clínicos (triaje, consultas, recetas)
- ✅ Documentos clínicos con contenido estructurado
- ✅ Visualización profesional en el frontend
- ✅ Flujo claro entre historias → formularios → documentos

**¡El problema de visualización de documentos está resuelto!** 🚀
