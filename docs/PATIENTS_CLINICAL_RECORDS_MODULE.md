# 👥 Módulo de Pacientes e Historiales Clínicos

**Documento**: Guía técnica completa del módulo de gestión de pacientes y historiales clínicos  
**Fecha**: 19 de Noviembre de 2025  
**Versión**: 2.0  
**Estado**: ✅ En Producción

---

## 📋 Índice

1. [Descripción General](#descripción-general)
2. [Arquitectura del Sistema](#arquitectura-del-sistema)
3. [Módulo de Pacientes](#módulo-de-pacientes)
4. [Módulo de Historiales Clínicos](#módulo-de-historiales-clínicos)
5. [Flujo de Datos](#flujo-de-datos)
6. [API Endpoints](#api-endpoints)
7. [Casos de Uso](#casos-de-uso)
8. [Base de Datos](#base-de-datos)

---

## 🎯 Descripción General

El módulo de **Pacientes e Historiales Clínicos** es el núcleo del sistema de gestión médica. Permite:

- ✅ **Registro de pacientes** con información demográfica y de contacto
- ✅ **Historiales clínicos** por paciente con datos médicos
- ✅ **Seguimiento de alergias** y condiciones crónicas
- ✅ **Gestión de medicamentos** actuales
- ✅ **Documentación médica** (consultas, recetas, resultados)
- ✅ **Multi-tenancy**: Cada clínica/hospital independiente

### Modelos Principales

```
┌──────────────────┐
│     PATIENT      │ (Información demográfica)
│  (70 registros)  │
└────────┬─────────┘
         │ One-to-One
         ▼
┌──────────────────────┐
│  CLINICAL_RECORD     │ (Historia Clínica)
│   (70 registros)     │
└────────┬─────────────┘
         │ One-to-Many
         ▼
┌─────────────────────────┐
│  CLINICAL_FORM          │ (Formularios)
│  CLINICAL_DOCUMENT      │ (Documentos)
│  (149+101 registros)    │
└─────────────────────────┘
```

---

## 🏗️ Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────┐
│              CAPA DE PRESENTACIÓN                        │
│  • Frontend React (Web)                                  │
│  • Mobile Flutter (Aplicación)                           │
└──────────────────┬──────────────────────────────────────┘
                   │ REST API
┌──────────────────▼──────────────────────────────────────┐
│         CAPA DE API (Django REST Framework)              │
│  GET    /api/patients/                                   │
│  POST   /api/patients/                                   │
│  GET    /api/clinical-records/{patient_id}/              │
│  POST   /api/clinical-records/                           │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────┐
│      CAPA DE SERVICIOS Y LÓGICA DE NEGOCIO              │
│  • PatientService: CRUD de pacientes                     │
│  • ClinicalRecordService: Gestión de historiales        │
│  • ClinicalFormService: Formularios médicos              │
│  • ValidationService: Validación de datos                │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────┐
│           CAPA DE PERSISTENCIA                           │
│  • PostgreSQL Database                                   │
│  • Modelos Django ORM                                    │
│  • Migrations                                            │
└─────────────────────────────────────────────────────────┘
```

---

## 👥 Módulo de Pacientes

### Modelo: Patient

**Ubicación**: `apps/patients/models.py`

```python
class Patient(TenantAwareModel):
    """Información personal y demográfica del paciente"""
    
    # Identificación
    identity_document_type  # Tipo: CI, Pasaporte, DNI, RUT
    identity_document       # Número de documento (único por tenant)
    
    # Información Personal
    first_name              # Nombres
    last_name               # Apellidos
    date_of_birth           # Fecha de nacimiento
    gender                  # M/F/O
    
    # Contacto
    phone                   # Teléfono
    email                   # Email
    address                 # Dirección
    city                    # Ciudad
    
    # Emergencia
    emergency_contact       # JSON: {name, relationship, phone}
    
    # Metadata
    created_by              # FK a User
    tenant                  # Multi-tenant
    created_at              # Auto-set
    updated_at              # Auto-set
```

### Campos Detallados

| Campo | Tipo | Validación | Descripción |
|-------|------|-----------|-------------|
| `id` | UUID | - | Identificador único |
| `identity_document_type` | Choice | [CI, Pasaporte, DNI, RUT] | Tipo de documento |
| `identity_document` | String(100) | Único por tenant | Número de documento |
| `first_name` | String(100) | Requerido | Nombres |
| `last_name` | String(100) | Requerido | Apellidos |
| `date_of_birth` | Date | Requerido | Fecha de nacimiento |
| `gender` | Choice | [M, F, O] | Género |
| `phone` | String(50) | Opcional | Teléfono |
| `email` | Email | Opcional | Correo electrónico |
| `address` | Text | Opcional | Dirección |
| `city` | String(100) | Opcional | Ciudad |
| `emergency_contact` | JSON | Opcional | Contacto de emergencia |
| `tenant` | FK | Requerido | Clínica/Hospital |
| `created_by` | FK | Requerido | Usuario creador |
| `created_at` | DateTime | Auto | Fecha de creación |
| `updated_at` | DateTime | Auto | Última actualización |

### Estructura JSON: emergency_contact

```json
{
  "name": "Juan Pérez",
  "relationship": "Esposa",
  "phone": "+591 76123456",
  "email": "emergencia@example.com"
}
```

### Métodos Principales

```python
def __str__(self):
    return f"{self.first_name} {self.last_name}"

def get_age(self):
    """Calcula la edad actual del paciente"""
    return (date.today() - self.date_of_birth).days // 365

def get_full_name(self):
    """Retorna el nombre completo formateado"""
    return f"{self.last_name}, {self.first_name}"

def has_clinical_record(self):
    """Verifica si tiene historia clínica"""
    return hasattr(self, 'clinical_record')
```

### ViewSet: PatientViewSet

**Ubicación**: `apps/patients/views.py`

```python
class PatientViewSet(viewsets.ModelViewSet):
    """
    CRUD completo de pacientes
    
    Endpoints:
    - GET    /api/patients/
    - POST   /api/patients/
    - GET    /api/patients/{id}/
    - PUT    /api/patients/{id}/
    - DELETE /api/patients/{id}/
    """
    
    serializer_class = PatientSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['first_name', 'last_name', 'identity_document']
    ordering = ['-created_at']
```

---

## 📋 Módulo de Historiales Clínicos

### Modelo: ClinicalRecord (Historia Clínica)

**Ubicación**: `apps/clinical_records/models.py`

```python
class ClinicalRecord(TenantAwareModel):
    """Historia Clínica del paciente (One-to-One con Patient)"""
    
    # Relación
    patient         # FK a Patient (One-to-One)
    
    # Identificación
    record_number   # Número de expediente (auto-generado)
    status          # active | archived | closed
    
    # Información Médica
    blood_type      # O, A, B, AB
    allergies       # JSON: [{allergen, severity, reaction}]
    chronic_conditions  # JSON: [Diabetes, Hipertensión, ...]
    medications     # JSON: [{name, dose, frequency}]
    family_history  # Text: Antecedentes familiares
    social_history  # Text: Antecedentes sociales (alcohol, tabaco)
    
    # Metadata
    created_by      # FK a User
    tenant          # Multi-tenant
    created_at      # Auto-set
    updated_at      # Auto-set
```

### Estructura JSON: Alergias

```json
[
  {
    "allergen": "Penicilina",
    "severity": "Alta",
    "reaction": "Anafilaxis"
  },
  {
    "allergen": "Polen",
    "severity": "Media",
    "reaction": "Rinitis alérgica"
  }
]
```

### Estructura JSON: Medicamentos

```json
[
  {
    "name": "Metformina",
    "dose": "500 mg",
    "frequency": "Dos veces al día"
  },
  {
    "name": "Lisinopril",
    "dose": "10 mg",
    "frequency": "Una vez al día"
  }
]
```

### Estados de la Historia Clínica

| Estado | Descripción |
|--------|-------------|
| `active` | Historia clínica activa (en uso) |
| `archived` | Archivada (no se puede editar, solo ver) |
| `closed` | Cerrada (paciente fallecido o transferido) |

### Métodos Principales

```python
def __str__(self):
    return f"HC-{self.record_number} | {self.patient.get_full_name()}"

def generate_record_number(self):
    """Genera número de expediente único"""
    # Formato: HCXXXXX (HC + 5 dígitos)
    return f"HC{str(self.id)[:5].upper()}"

def get_active_medications(self):
    """Retorna medicamentos actuales"""
    return self.medications or []

def get_allergies_summary(self):
    """Retorna resumen de alergias"""
    return [a['allergen'] for a in self.allergies]

def add_allergy(self, allergen, severity, reaction):
    """Agrega una alergia a la lista"""
    if not self.allergies:
        self.allergies = []
    self.allergies.append({
        "allergen": allergen,
        "severity": severity,
        "reaction": reaction
    })
    self.save()

def update_chronic_conditions(self, conditions):
    """Actualiza condiciones crónicas"""
    self.chronic_conditions = conditions
    self.save()
```

### ViewSet: ClinicalRecordViewSet

**Ubicación**: `apps/clinical_records/views.py`

```python
class ClinicalRecordViewSet(viewsets.ModelViewSet):
    """
    CRUD completo de historiales clínicos
    
    Endpoints:
    - GET    /api/clinical-records/
    - POST   /api/clinical-records/
    - GET    /api/clinical-records/{id}/
    - PUT    /api/clinical-records/{id}/
    - DELETE /api/clinical-records/{id}/
    - GET    /api/clinical-records/?patient={patient_id}
    """
    
    serializer_class = ClinicalRecordSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['patient', 'status', 'blood_type']
    search_fields = ['patient__first_name', 'record_number']
```

---

### Modelo: ClinicalForm (Formulario Clínico)

**Ubicación**: `apps/clinical_records/models.py`

```python
class ClinicalForm(TenantAwareModel):
    """Formulario clínico (Triaje, Consulta, Receta, Laboratorio)"""
    
    # Relación
    clinical_record     # FK a ClinicalRecord
    
    # Identificación
    form_type           # triaje | consulta | receta | laboratorio
    form_template_id    # FK a FormTemplate (si aplica)
    
    # Datos
    form_data           # JSON: Datos específicos del formulario
    
    # Llenado
    filled_by           # FK a User
    filled_by_name      # String: Nombre de quien llenó
    doctor_name         # String: Nombre del doctor
    doctor_specialty    # String: Especialidad
    form_date           # DateTime: Fecha del formulario
    
    # Metadata
    tenant              # Multi-tenant
    created_at          # Auto-set
    updated_at          # Auto-set
```

### Tipos de Formulario

| Tipo | Código | Descripción |
|------|--------|-------------|
| Triaje | `triaje` | Evaluación inicial de paciente |
| Consulta | `consulta` | Registro de consulta médica |
| Receta | `receta` | Prescripción de medicamentos |
| Laboratorio | `laboratorio` | Resultados de análisis lab |

### Estructura form_data por Tipo

**Triaje**:
```json
{
  "heart_rate": 72,
  "blood_pressure": "120/80",
  "temperature": 36.5,
  "respiratory_rate": 16,
  "oxygen_saturation": 98,
  "chief_complaint": "Dolor de cabeza"
}
```

**Consulta**:
```json
{
  "chief_complaint": "Dolor de cabeza recurrente",
  "duration": "3 días",
  "symptoms": ["Fotofobia", "Náuseas"],
  "diagnosis": "Migraña",
  "treatment": "Reposo, analgésicos",
  "notes": "Paciente con historial de migrañas"
}
```

**Receta**:
```json
{
  "medications": [
    {
      "name": "Acetaminofén",
      "dose": "500 mg",
      "frequency": "Cada 6 horas",
      "duration": "7 días"
    }
  ],
  "instructions": "Tomar con alimentos"
}
```

**Laboratorio**:
```json
{
  "test_type": "Hemoglobina glicosilada",
  "result": "6.8%",
  "reference_value": "< 7%",
  "status": "Normal",
  "notes": "Control de diabetes satisfactorio"
}
```

---

## 🔄 Flujo de Datos

### Creación de Paciente

```
1. Usuario Admin crea paciente
   ↓
2. Validar documento único por tenant
   ↓
3. Crear registro en tabla Patient
   ↓
4. Asignar a tenant actual
   ↓
5. Registrar en auditoría
   ↓
6. Retornar datos del paciente (201 Created)
```

### Creación de Historia Clínica

```
1. Usuario (Admin/Doctor) crea historia clínica
   ↓
2. Sistema verifica One-to-One con Patient
   ↓
3. Generar número de expediente (HCXXXXX)
   ↓
4. Crear registro en tabla ClinicalRecord
   ↓
5. Inicializar JSON fields vacíos
   ↓
6. Registrar auditoría
   ↓
7. Retornar historia clínica (201 Created)
```

### Agregación de Formulario

```
1. Doctor llena formulario clínico
   ↓
2. Validar datos según tipo de formulario
   ↓
3. Auto-asignar filled_by del contexto
   ↓
4. Auto-completar doctor_name, specialty
   ↓
5. Crear registro en tabla ClinicalForm
   ↓
6. Vincular a ClinicalRecord
   ↓
7. Actualizar documents_count en ClinicalRecord
   ↓
8. Registrar en auditoría
   ↓
9. Retornar formulario (201 Created)
```

---

## 📡 API Endpoints

### Pacientes

#### GET `/api/patients/`
Lista todos los pacientes del tenant actual

**Query Parameters**:
- `search`: Buscar por nombre o documento
- `page`: Número de página
- `page_size`: Registros por página

**Response**:
```json
{
  "count": 70,
  "next": "http://...",
  "previous": null,
  "results": [
    {
      "id": "uuid",
      "identity_document": "1234567",
      "identity_document_type": "CI",
      "first_name": "Juan",
      "last_name": "Pérez",
      "date_of_birth": "1980-05-15",
      "gender": "M",
      "phone": "+591 76123456",
      "email": "juan@example.com",
      "address": "Calle Principal 123",
      "city": "La Paz",
      "emergency_contact": {
        "name": "María Pérez",
        "relationship": "Esposa",
        "phone": "+591 76654321"
      },
      "created_at": "2025-11-15T10:30:00Z",
      "updated_at": "2025-11-15T10:30:00Z"
    }
  ]
}
```

#### POST `/api/patients/`
Crear nuevo paciente

**Request**:
```json
{
  "identity_document_type": "CI",
  "identity_document": "1234567",
  "first_name": "Juan",
  "last_name": "Pérez",
  "date_of_birth": "1980-05-15",
  "gender": "M",
  "phone": "+591 76123456",
  "email": "juan@example.com",
  "address": "Calle Principal 123",
  "city": "La Paz",
  "emergency_contact": {
    "name": "María Pérez",
    "relationship": "Esposa",
    "phone": "+591 76654321"
  }
}
```

**Response** (201 Created): Mismo JSON del paciente creado

#### GET `/api/patients/{id}/`
Obtener detalles de un paciente

#### PUT `/api/patients/{id}/`
Actualizar información del paciente

#### DELETE `/api/patients/{id}/`
Eliminar paciente (soft delete)

---

### Historiales Clínicos

#### GET `/api/clinical-records/`
Lista todas las historias clínicas del tenant

**Query Parameters**:
- `patient={patient_id}`: Filtrar por paciente
- `status=active`: Filtrar por estado
- `blood_type=O+`: Filtrar por tipo de sangre

**Response**:
```json
{
  "count": 70,
  "results": [
    {
      "id": "uuid",
      "patient": "uuid-paciente",
      "patient_info": {
        "id": "uuid",
        "first_name": "Juan",
        "last_name": "Pérez",
        "identification": "1234567",
        "date_of_birth": "1980-05-15",
        "gender": "M"
      },
      "record_number": "HC-001",
      "status": "active",
      "blood_type": "O+",
      "allergies": [
        {
          "allergen": "Penicilina",
          "severity": "Alta",
          "reaction": "Anafilaxis"
        }
      ],
      "chronic_conditions": ["Diabetes tipo 2", "Hipertensión"],
      "medications": [
        {
          "name": "Metformina",
          "dose": "500 mg",
          "frequency": "Dos veces al día"
        }
      ],
      "family_history": "Diabetes en padre y abuelo",
      "social_history": "Exfumador, consume alcohol ocasionalmente",
      "documents_count": 5,
      "created_by": "uuid-user",
      "created_by_name": "Dr. García",
      "created_at": "2025-11-15T10:30:00Z",
      "updated_at": "2025-11-18T14:45:00Z"
    }
  ]
}
```

#### POST `/api/clinical-records/`
Crear nueva historia clínica

**Request**:
```json
{
  "patient": "uuid-paciente",
  "blood_type": "O+",
  "allergies": [
    {
      "allergen": "Penicilina",
      "severity": "Alta",
      "reaction": "Anafilaxis"
    }
  ],
  "chronic_conditions": ["Diabetes tipo 2"],
  "medications": [
    {
      "name": "Metformina",
      "dose": "500 mg",
      "frequency": "Dos veces al día"
    }
  ],
  "family_history": "Diabetes en familia",
  "social_history": "Exfumador"
}
```

#### GET `/api/clinical-records/{id}/`
Obtener detalles de una historia clínica

#### PUT `/api/clinical-records/{id}/`
Actualizar historia clínica

#### DELETE `/api/clinical-records/{id}/`
Eliminar historia clínica

---

### Formularios Clínicos

#### GET `/api/clinical-records/{record_id}/forms/`
Listar formularios de una historia clínica

**Response**:
```json
{
  "count": 5,
  "results": [
    {
      "id": "uuid",
      "clinical_record": "uuid",
      "record_number": "HC-001",
      "patient_name": "Juan Pérez",
      "form_type": "triaje",
      "form_type_display": "Triaje",
      "form_template_id": null,
      "form_data": {
        "heart_rate": 72,
        "blood_pressure": "120/80",
        "temperature": 36.5,
        "respiratory_rate": 16,
        "oxygen_saturation": 98,
        "chief_complaint": "Dolor de cabeza"
      },
      "filled_by": "uuid-user",
      "filled_by_name": "María García",
      "doctor_name": "Dr. García",
      "doctor_specialty": "General",
      "form_date": "2025-11-18T14:00:00Z",
      "created_at": "2025-11-18T14:00:00Z",
      "updated_at": "2025-11-18T14:00:00Z"
    }
  ]
}
```

#### POST `/api/clinical-records/{record_id}/forms/`
Crear nuevo formulario

**Request**:
```json
{
  "form_type": "triaje",
  "form_data": {
    "heart_rate": 72,
    "blood_pressure": "120/80",
    "temperature": 36.5,
    "respiratory_rate": 16,
    "oxygen_saturation": 98,
    "chief_complaint": "Dolor de cabeza"
  },
  "form_date": "2025-11-18T14:00:00Z"
}
```

---

## 📚 Casos de Uso

### Caso 1: Registro Completo de Nuevo Paciente

```
1. Admin accede a "Nuevo Paciente"
2. Ingresa datos demográficos:
   - Documento: 1234567
   - Nombre: Juan
   - Apellidos: Pérez García
   - Nacimiento: 15/05/1980
   - Género: Masculino
   - Teléfono: +591 76123456
   - Correo: juan@example.com
   - Dirección: Calle Principal 123
   - Ciudad: La Paz
   - Contacto de emergencia: Esposa María
3. Sistema crea registro Patient
4. Sistema crea automáticamente ClinicalRecord One-to-One
5. Asignar historia clínica con:
   - Tipo de sangre: O+
   - Alergias: Penicilina (Alta - Anafilaxis)
   - Condiciones crónicas: Diabetes, Hipertensión
   - Medicamentos actuales: Metformina 500mg 2x/día
   - Antecedentes familiares: Diabetes padre/abuelo
6. Paciente registrado completamente
```

### Caso 2: Seguimiento de Consulta

```
1. Doctor accede a paciente Juan Pérez
2. Ver historia clínica completa:
   - Alergias, medicamentos, antecedentes
3. Crear nueva consulta (Formulario):
   - Motivo: Dolor de cabeza recurrente
   - Síntomas: Fotofobia, náuseas
   - Diagnóstico: Migraña
   - Tratamiento: Reposo y analgésicos
   - Prescripciones: Acetaminofén 500mg
4. Sistema registra formulario
5. Actualiza documents_count en ClinicalRecord
6. Crea entrada en auditoría
```

### Caso 3: Análisis de Predicción de Diabetes

```
1. Sistema ML extrae features de Juan:
   - Edad: 45 años
   - IMC: 31.2
   - Glucosa: 145 mg/dL
   - Presión: 130/85
   - Historial familiar: Sí
   - Medicamentos: Metformina (ya diagnosticado)
2. Modelo Decision Tree predice:
   - Probabilidad: 0.78 (Alta)
   - Risk Level: Alto
   - Factores: Glucosa elevada, BMI alto, historial familiar
3. Genera recomendaciones:
   - Control de glucosa más frecuente
   - Dieta baja en carbohidratos
   - Aumentar actividad física
4. Almacena predicción en DiabetesPrediction
5. Notifica al médico tratante
```

---

## 🗄️ Base de Datos

### Tabla: patient

```sql
CREATE TABLE patient (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES core_tenant(id),
    identity_document_type VARCHAR(20) DEFAULT 'CI',
    identity_document VARCHAR(100) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    date_of_birth DATE NOT NULL,
    gender VARCHAR(1),
    phone VARCHAR(50),
    email VARCHAR(254),
    address TEXT,
    city VARCHAR(100),
    emergency_contact JSONB DEFAULT '{}',
    created_by_id UUID REFERENCES accounts_user(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(tenant_id, identity_document),
    INDEX ON (first_name, last_name),
    INDEX ON (tenant_id, created_at)
);
```

### Tabla: clinical_records_clinicalrecord

```sql
CREATE TABLE clinical_records_clinicalrecord (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES core_tenant(id),
    patient_id UUID NOT NULL UNIQUE REFERENCES patient(id),
    record_number VARCHAR(100) UNIQUE NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    blood_type VARCHAR(10),
    allergies JSONB DEFAULT '[]',
    chronic_conditions JSONB DEFAULT '[]',
    medications JSONB DEFAULT '[]',
    family_history TEXT,
    social_history TEXT,
    created_by_id UUID REFERENCES accounts_user(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX ON (patient_id),
    INDEX ON (tenant_id, status),
    INDEX ON (record_number)
);
```

### Tabla: clinical_records_clinicalform

```sql
CREATE TABLE clinical_records_clinicalform (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES core_tenant(id),
    clinical_record_id UUID NOT NULL REFERENCES clinical_records_clinicalrecord(id),
    form_type VARCHAR(50) NOT NULL,
    form_template_id UUID,
    form_data JSONB NOT NULL DEFAULT '{}',
    filled_by_id UUID NOT NULL REFERENCES accounts_user(id),
    doctor_name VARCHAR(255),
    doctor_specialty VARCHAR(100),
    form_date TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX ON (clinical_record_id),
    INDEX ON (form_type),
    INDEX ON (form_date),
    INDEX ON (tenant_id, created_at)
);
```

---

## 📊 Estadísticas Actuales

```
┌───────────────────────────────────────────────┐
│     ESTADÍSTICAS DEL SISTEMA (Nov 19, 2025)    │
├───────────────────────────────────────────────┤
│                                               │
│  Pacientes totales:               70          │
│  ├─ Hospital Santa Cruz:          50          │
│  └─ Clínica La Paz:              20          │
│                                               │
│  Historias clínicas:              70 (100%)   │
│  ├─ Activas:                     65          │
│  ├─ Archivadas:                   5          │
│  └─ Cerradas:                     0          │
│                                               │
│  Formularios clínicos:           149          │
│  ├─ Triaje:                      45          │
│  ├─ Consulta:                    52          │
│  ├─ Receta:                      35          │
│  └─ Laboratorio:                 17          │
│                                               │
│  Documentos clínicos:            101          │
│  ├─ Consulta:                    45          │
│  ├─ Resultados Lab:              35          │
│  ├─ Recetas:                     15          │
│  └─ Reportes:                     6          │
│                                               │
│  Alergias registradas:           127          │
│  ├─ Penicilina:                  34          │
│  ├─ Aspirina:                    28          │
│  ├─ Otros:                       65          │
│                                               │
│  Condiciones crónicas:           185          │
│  ├─ Diabetes:                    42          │
│  ├─ Hipertensión:                55          │
│  ├─ Asma:                        28          │
│  └─ Otras:                       60          │
│                                               │
│  Medicamentos activos:           312          │
│  ├─ Metformina:                  38          │
│  ├─ Lisinopril:                  32          │
│  ├─ Otros:                      242          │
│                                               │
└───────────────────────────────────────────────┘
```

---

## 🔒 Seguridad y Privacidad

### Autenticación
- ✅ JWT Token requerido en todos los endpoints
- ✅ Validación de tenant en cada solicitud
- ✅ Rate limiting implementado

### Autorización
- ✅ Admin: CRUD completo de pacientes
- ✅ Doctor: Solo ver y editar historias de sus pacientes
- ✅ Paciente: Solo ver su propia historia (cuando está implementado)

### Privacidad de Datos
- ✅ GDPR compliant
- ✅ Auditoría de acceso a datos sensibles
- ✅ Encriptación de documentos
- ✅ Soft delete (no eliminar, solo marcar)

---

## 📁 Estructura de Archivos

```
apps/patients/
├── models.py
│   └── Patient
├── views.py
│   └── PatientViewSet
├── serializers.py
│   ├── PatientSerializer
│   └── PatientListSerializer
├── urls.py
├── permissions.py
└── migrations/

apps/clinical_records/
├── models.py
│   ├── ClinicalRecord
│   └── ClinicalForm
├── views.py
│   ├── ClinicalRecordViewSet
│   └── ClinicalFormViewSet
├── serializers.py
│   ├── ClinicalRecordSerializer
│   └── ClinicalFormSerializer
├── urls.py
├── permissions.py
└── migrations/
```

---

## 🎓 Referencias

- **Framework**: Django 4.2.7 + Django REST Framework
- **Database**: PostgreSQL
- **ORM**: Django ORM
- **Validation**: DRF Serializers
- **Permissions**: IsAuthenticated, Custom Permissions
- **Multi-tenancy**: TenantAwareModel base class

---

## ✅ Checklist de Funcionalidades

- [x] Modelo Patient con campos completos
- [x] Modelo ClinicalRecord (One-to-One)
- [x] Modelo ClinicalForm con múltiples tipos
- [x] CRUD de pacientes
- [x] CRUD de historias clínicas
- [x] CRUD de formularios clínicos
- [x] Búsqueda y filtrado
- [x] Multi-tenancy
- [x] Auditoría de cambios
- [x] Validación de datos
- [x] Serializers de validación
- [x] Permisos y autenticación
- [x] Paginación
- [x] Docs API Swagger/OpenAPI

---

## 🐛 Troubleshooting

### Problema: One-to-One conflict
```
Error: Intentar crear otra ClinicalRecord para paciente existente
Solución: Validar que patient_id sea único en ClinicalRecord
```

### Problema: JSON fields vacíos
```
Error: Acceder a allergies[0] cuando está vacío
Solución: Siempre verificar antes: if record.allergies and len(record.allergies) > 0
```

### Problema: Documento duplicado
```
Error: Duplicate key value violates unique constraint
Solución: El documento (CI/DNI/Pasaporte) ya existe en el tenant
```

---

**Documento generado automáticamente** | **Última actualización**: 19/Nov/2025 02:00 UTC
