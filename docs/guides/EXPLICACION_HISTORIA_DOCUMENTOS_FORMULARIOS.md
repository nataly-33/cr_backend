# 📚 DIFERENCIAS: Historia Clínica vs Documentos vs Formularios

## 1️⃣ HISTORIA CLÍNICA (ClinicalRecord)

**Es el EXPEDIENTE PRINCIPAL del paciente**

```
┌─────────────────────────────────────┐
│     HISTORIA CLÍNICA                │
│  (1 por paciente)                   │
├─────────────────────────────────────┤
│ • Tipo de sangre                    │
│ • Alergias                          │
│ • Condiciones crónicas              │
│ • Medicamentos actuales             │
│ • Información médica general        │
└─────────────────────────────────────┘
```

**Características:**

- ✅ **1 historia por paciente** (única)
- ✅ Información estructurada en la BD
- ✅ Se actualiza con el tiempo
- ✅ NO tiene archivos adjuntos
- ❌ NO usa OCR (datos estructurados)

**Permisos:**

- **Admin TI:** CRUD completo
- **Doctor:** CRUD completo
- **Paciente:** Solo lectura (ver su propia historia)

---

## 2️⃣ DOCUMENTOS CLÍNICOS (ClinicalDocument)

**Son ARCHIVOS FÍSICOS escaneados o PDFs**

```
┌─────────────────────────────────────┐
│     DOCUMENTOS CLÍNICOS             │
│  (Muchos por historia)              │
├─────────────────────────────────────┤
│ • Recetas médicas (PDF/imagen)      │
│ • Resultados de laboratorio (PDF)   │
│ • Informes de rayos X (imagen)      │
│ • Notas quirúrgicas (PDF)           │
│ • Consentimientos (PDF)             │
└─────────────────────────────────────┘
         ↓
    📄 ARCHIVO FÍSICO
         ↓
    🤖 OCR TEXTRACT ← ¡AQUÍ SE USA OCR!
         ↓
    📝 Texto extraído
```

**Características:**

- ✅ **Muchos documentos por historia**
- ✅ Tiene archivo físico (PDF, imagen)
- ✅ **USA OCR para extraer texto** del archivo
- ✅ Texto extraído se guarda en `ocr_text`
- ✅ Permite buscar dentro del contenido

**Permisos:**

- **Admin TI:** CRUD completo
- **Doctor:** CRUD completo (puede subir/ver/eliminar documentos)
- **Paciente:** Solo lectura (ver sus propios documentos)

**🎯 OBJETIVO DEL OCR EN DOCUMENTOS:**

1. Doctor sube PDF de receta médica
2. OCR extrae automáticamente el texto
3. Ahora puedes BUSCAR "paracetamol" y encontrar todos los documentos que lo mencionen
4. NO llena formularios automáticamente (el doc es una "foto" del papel)

---

## 3️⃣ FORMULARIOS CLÍNICOS (ClinicalForm)

**Son DATOS ESTRUCTURADOS que el doctor llena**

```
┌─────────────────────────────────────┐
│     FORMULARIOS CLÍNICOS            │
│  (Muchos por historia)              │
├─────────────────────────────────────┤
│ • Triaje (signos vitales)           │
│ • Consulta médica                   │
│ • Nota de evolución                 │
│ • Receta (estructurada)             │
│ • Orden de laboratorio              │
└─────────────────────────────────────┘
         ↓
    📋 DATOS JSON
    (no es archivo físico)
```

**Ejemplo de formulario de Triaje:**

```json
{
  "vital_signs": {
    "blood_pressure": "120/80",
    "heart_rate": 75,
    "temperature": 36.5,
    "weight": 70,
    "height": 170
  },
  "chief_complaint": "Dolor de cabeza",
  "triage_level": "3"
}
```

**Características:**

- ✅ **Muchos formularios por historia**
- ✅ Datos estructurados (JSON)
- ✅ Se llenan manualmente en el frontend
- ❌ NO tiene archivo físico
- ❌ NO usa OCR (ya son datos estructurados)

**Permisos:**

- **Admin TI:** CRUD completo
- **Doctor:** CRUD completo (llena formularios en consultas)
- **Paciente:** Solo lectura (ver sus formularios)

---

## 🤔 ¿CUÁNDO USAR CADA UNO?

### Usar HISTORIA CLÍNICA cuando:

- Quieres ver la info general del paciente
- Necesitas tipo de sangre, alergias, condiciones crónicas
- Es información que cambia poco

### Usar DOCUMENTOS cuando:

- Tienes un papel o PDF que quieres adjuntar
- Necesitas escanear recetas, análisis, imágenes médicas
- Quieres usar OCR para extraer texto del PDF
- Es información en formato físico/digital externo

### Usar FORMULARIOS cuando:

- Doctor está en consulta y necesita registrar datos
- Quieres triaje con signos vitales
- Necesitas datos estructurados para reportes
- Es información nueva que se crea en el sistema

---

## 🎯 FLUJO TÍPICO EN LA CLÍNICA

### Paciente nuevo llega:

```
1. Secretaria crea PACIENTE
2. Sistema crea HISTORIA CLÍNICA automáticamente
3. Enfermera llena FORMULARIO de Triaje
4. Doctor ve al paciente y llena FORMULARIO de Consulta
5. Doctor genera receta → puede:
   - Opción A: Llenar FORMULARIO de receta (datos estructurados)
   - Opción B: Subir PDF de receta → DOCUMENTO con OCR
6. Paciente trae resultados de laboratorio en papel
7. Doctor sube el PDF → DOCUMENTO con OCR
8. El OCR extrae "hemoglobina: 12.5 g/dL" del PDF
9. Ahora puedes buscar "hemoglobina" en todos los documentos
```

---

## ⚡ ENTONCES, ¿PARA QUÉ SIRVE EL OCR?

**OCR NO llena formularios automáticamente** ❌

**OCR SIRVE PARA:** ✅

1. **Buscar contenido dentro de PDFs**
   - "Quiero encontrar todos los documentos que mencionen 'diabetes'"
2. **Digitalizar documentos físicos**
   - Paciente trae receta en papel → escaneamos → OCR extrae texto
3. **Hacer consultables documentos viejos**
   - PDFs históricos sin texto → OCR los hace buscables
4. **Auditoría y compliance**
   - Poder buscar menciones de medicamentos específicos

---

## 📊 PERMISOS RESUMIDOS

| Acción               | Admin TI | Doctor              | Paciente          |
| -------------------- | -------- | ------------------- | ----------------- |
| **Historia Clínica** |
| Ver                  | ✅ Todas | ✅ De sus pacientes | ✅ Solo la suya   |
| Crear                | ✅       | ✅                  | ❌                |
| Editar               | ✅       | ✅                  | ❌                |
| Eliminar             | ✅       | ✅                  | ❌                |
| **Documentos**       |
| Ver                  | ✅ Todos | ✅ De sus pacientes | ✅ Solo los suyos |
| Subir                | ✅       | ✅                  | ❌                |
| Eliminar             | ✅       | ✅                  | ❌                |
| Ver OCR              | ✅       | ✅                  | ✅                |
| **Formularios**      |
| Ver                  | ✅ Todos | ✅ De sus pacientes | ✅ Solo los suyos |
| Crear                | ✅       | ✅                  | ❌                |
| Editar               | ✅       | ✅ (solo los suyos) | ❌                |
| Eliminar             | ✅       | ✅                  | ❌                |

---

## 🚀 EN RESUMEN

```
PACIENTE
    └── HISTORIA CLÍNICA (1) ← Info general estructurada
            ├── DOCUMENTOS (N) ← PDFs/imágenes con OCR
            │   ├── Receta.pdf 🤖 OCR→ "Paracetamol 500mg"
            │   ├── Lab.pdf 🤖 OCR→ "Glucosa: 95 mg/dL"
            │   └── RayosX.jpg 🤖 OCR→ "Fractura distal..."
            │
            └── FORMULARIOS (N) ← Datos estructurados JSON
                ├── Triaje (PA: 120/80, FC: 75)
                ├── Consulta (Diagnóstico: Gripe)
                └── Receta estructurada (Medicamentos: [...])
```

**OCR = Solo para DOCUMENTOS (archivos físicos)**
**Formularios = Se llenan manualmente en la interfaz**
**Historia = Resumen general del paciente**
