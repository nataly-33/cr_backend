# 📋 ANTES DE SPRINT 3 - TAREAS OBLIGATORIAS

## ⏱️ CONTEXTO

- **Duración:** 1-2 días
- **Objetivo:** Completar Sprint 2 pendiente y preparar infraestructura
- **Estado actual:** Sprint 2 al 60%
- **Prioridad:** Funcionalidades core del sistema + infraestructura básica

---

## ✅ TAREAS PREVIAS OBLIGATORIAS

**Priorizar:**

1. ✅ Formularios clínicos (mínimo Triaje y Consulta)
2. ✅ Dashboard con 2 gráficos
3. ⚠️ Verificar que S3 funcione (si ya funciona, skip)
4. ❌ Deploy → Dejar para después

### 🎯 BLOQUE 1: Completar Formularios Clínicos (CRÍTICO)

**Tiempo estimado:** 6-8 horas

**Contexto:** Ya existe la tabla `clinical_form` con campo `form_type` que discrimina el tipo de formulario.

#### Tipos de formularios a implementar:

1. **Triaje (form_type='triage')** - Para enfermeras

   ```json
   {
     "signos_vitales": {
       "presion_arterial": "120/80",
       "temperatura": 36.5,
       "frecuencia_cardiaca": 75,
       "frecuencia_respiratoria": 18,
       "saturacion_oxigeno": 98
     },
     "sintomas": "Dolor de cabeza leve",
     "prioridad": "normal", // verde, amarillo, rojo
     "observaciones": "Paciente estable"
   }
   ```

2. **Consulta Médica (form_type='consultation')**

   ```json
   {
     "motivo_consulta": "Dolor abdominal",
     "anamnesis": "Paciente refiere dolor en...",
     "examen_fisico": "Abdomen blando, no doloroso...",
     "diagnostico": "Gastritis aguda",
     "tratamiento": "Omeprazol 20mg cada 12h",
     "indicaciones": "Reposo relativo, dieta blanda",
     "proxima_cita": "2025-11-15"
   }
   ```

3. **Receta (form_type='prescription')**

   ```json
   {
     "medicamentos": [
       {
         "nombre": "Omeprazol",
         "dosis": "20mg",
         "frecuencia": "Cada 12 horas",
         "duracion": "7 días",
         "via": "oral"
       }
     ],
     "indicaciones_generales": "Tomar antes de las comidas"
   }
   ```

4. **Orden de Laboratorio (form_type='lab_order')**
   ```json
   {
     "examenes": ["Hemograma completo", "Glucosa", "Creatinina"],
     "indicaciones": "En ayunas",
     "prioridad": "normal",
     "observaciones": "Control de rutina"
   }
   ```

#### Tareas Frontend:

- [ ] **Página: TriageForm.tsx**

  - Formulario con campos de signos vitales
  - Selector de prioridad (semáforo)
  - Guardar en `clinical_form` con `form_type='triage'`
  - Ubicación: `cr_frontend/src/pages/ClinicalForms/TriageForm.tsx`

- [ ] **Página: ConsultationForm.tsx**

  - Editor de texto enriquecido (react-quill o textarea simple)
  - Campos: motivo, diagnóstico, tratamiento
  - Ubicación: `cr_frontend/src/pages/ClinicalForms/ConsultationForm.tsx`

- [ ] **Página: PrescriptionForm.tsx**

  - Lista dinámica de medicamentos
  - Botón "Generar PDF" (opcional para Sprint 3)
  - Ubicación: `cr_frontend/src/pages/ClinicalForms/PrescriptionForm.tsx`

- [ ] **Página: LabOrderForm.tsx**
  - Checklist de exámenes comunes
  - Input para exámenes personalizados
  - Ubicación: `cr_frontend/src/pages/ClinicalForms/LabOrderForm.tsx`

**Endpoints existentes a usar:**

```
POST   /api/clinical-records/forms/
GET    /api/clinical-records/forms/?clinical_record_id={id}
GET    /api/clinical-records/forms/{id}/
PATCH  /api/clinical-records/forms/{id}/
DELETE /api/clinical-records/forms/{id}/
```

**Criterio de aceptación:**

- Los 4 tipos de formularios se pueden crear y guardar
- Se visualizan correctamente en el detalle del clinical record
- Los datos se guardan en formato JSON estructurado

---

### 🎯 BLOQUE 2: Dashboard con Gráficos (IMPORTANTE)

**Tiempo estimado:** 4-5 horas

#### Tareas:

- [ ] **Instalar Recharts**

  ```bash
  cd cr_frontend
  npm install recharts
  ```

- [ ] **Crear 3 gráficos básicos en Dashboard**

  **Gráfico 1: Pacientes registrados por mes**

  ```typescript
  <LineChart data={patientsPerMonth}>
    <XAxis dataKey="month" />
    <YAxis />
    <Line type="monotone" dataKey="count" stroke="#8884d8" />
  </LineChart>
  ```

  **Gráfico 2: Documentos por tipo**

  ```typescript
  <PieChart>
    <Pie data={documentsByType} dataKey="count" nameKey="type" />
  </PieChart>
  ```

  **Gráfico 3: Actividad semanal**

  ```typescript
  <BarChart data={weeklyActivity}>
    <XAxis dataKey="day" />
    <YAxis />
    <Bar dataKey="documents" fill="#82ca9d" />
    <Bar dataKey="forms" fill="#8884d8" />
  </BarChart>
  ```

- [ ] **Agregar métricas en tiempo real**
  - Total de pacientes
  - Documentos generados hoy
  - Usuarios activos
  - Almacenamiento usado

**Endpoint existente:**

```
GET /api/patients/stats/
```

**Crear nuevo endpoint (opcional):**

```python
# cr_backend/apps/patients/views.py
@action(detail=False, methods=['get'])
def dashboard_stats(self, request):
    tenant = get_current_tenant()

    return Response({
        'total_patients': Patient.objects.filter(tenant=tenant).count(),
        'total_documents': ClinicalDocument.objects.filter(tenant=tenant).count(),
        'documents_today': ClinicalDocument.objects.filter(
            tenant=tenant,
            created_at__date=timezone.now().date()
        ).count(),
        'storage_used_mb': calculate_storage(tenant)
    })
```

---

### 🎯 BLOQUE 3: Infraestructura y Deploy (IMPORTANTE)

**Tiempo estimado:** 4-6 horas

#### 3.1 Subida de Documentos a S3 (MEJORAR)

- [ ] **Verificar configuración actual**

  ```python
  # cr_backend/config/settings.py
  AWS_ACCESS_KEY_ID = env('AWS_ACCESS_KEY_ID')
  AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY')
  AWS_STORAGE_BUCKET_NAME = env('AWS_STORAGE_BUCKET_NAME')
  AWS_S3_REGION_NAME = env('AWS_S3_REGION_NAME', default='us-east-1')
  ```

- [ ] **Mejorar manejo de errores en upload**

  ```python
  # cr_backend/apps/documents/views.py
  def upload_to_s3(file, tenant_id, document_id):
      try:
          s3_client = boto3.client('s3')
          file_path = f'{tenant_id}/documents/{document_id}/{file.name}'

          s3_client.upload_fileobj(
              file,
              settings.AWS_STORAGE_BUCKET_NAME,
              file_path,
              ExtraArgs={'ContentType': file.content_type}
          )

          return file_path
      except Exception as e:
          logger.error(f"Error uploading to S3: {str(e)}")
          raise
  ```

- [ ] **Agregar validación de tamaño y tipo**

  ```python
  MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB
  ALLOWED_TYPES = ['application/pdf', 'image/jpeg', 'image/png']

  if file.size > MAX_UPLOAD_SIZE:
      raise ValidationError("Archivo muy grande")

  if file.content_type not in ALLOWED_TYPES:
      raise ValidationError("Tipo de archivo no permitido")
  ```

#### 3.2 Deploy Backend (BÁSICO)

- [ ] **Crear archivo requirements.txt actualizado**

  ```bash
  pip freeze > requirements.txt
  ```

- [ ] **Configurar variables de entorno para producción**

  ```bash
  # .env.production
  DEBUG=False
  ALLOWED_HOSTS=tu-dominio.com,*.tu-dominio.com
  DATABASE_URL=postgresql://user:pass@host:5432/dbname
  AWS_STORAGE_BUCKET_NAME=tu-bucket
  SECRET_KEY=tu-secret-key-seguro
  ```

- [ ] **Configurar Gunicorn**

  ```bash
  pip install gunicorn

  # Crear gunicorn_config.py
  bind = "0.0.0.0:8000"
  workers = 4
  worker_class = "sync"
  timeout = 120
  ```

- [ ] **Script de deploy básico**
  ```bash
  # deploy.sh
  #!/bin/bash
  git pull origin main
  pip install -r requirements.txt
  python manage.py migrate
  python manage.py collectstatic --noinput
  sudo systemctl restart gunicorn
  ```

#### 3.3 Deploy Frontend (BÁSICO)

- [ ] **Build de producción**

  ```bash
  cd cr_frontend
  npm run build
  ```

- [ ] **Deploy en Vercel/Netlify (SIMPLE)**

  ```bash
  # Opción 1: Vercel
  npm install -g vercel
  vercel --prod

  # Opción 2: Netlify
  npm install -g netlify-cli
  netlify deploy --prod --dir=dist
  ```

- [ ] **Configurar variables de entorno**
  ```bash
  # .env.production
  VITE_API_URL=https://api.tu-dominio.com
  ```

---

### 🎯 BLOQUE 4: Tareas Opcionales (Si hay tiempo)

**Tiempo estimado:** Variable

#### Redis y Caché (OPCIONAL - No prioritario)

- [ ] **Configurar Redis para caché**

  ```python
  # settings.py
  CACHES = {
      'default': {
          'BACKEND': 'django_redis.cache.RedisCache',
          'LOCATION': 'redis://127.0.0.1:6379/1',
          'OPTIONS': {
              'CLIENT_CLASS': 'django_redis.client.DefaultClient',
          }
      }
  }
  ```

- [ ] **Cachear queries frecuentes**

  ```python
  from django.core.cache import cache

  def get_patients_cached(tenant_id):
      cache_key = f'patients_{tenant_id}'
      patients = cache.get(cache_key)

      if not patients:
          patients = Patient.objects.filter(tenant_id=tenant_id)
          cache.set(cache_key, patients, 300)  # 5 minutos

      return patients
  ```

**Nota:** Redis NO es crítico para Sprint 3, se puede implementar después.

---

## ✅ CHECKLIST FINAL

Antes de comenzar Sprint 3, verificar:

- [ ] **Formularios Clínicos:**

  - [ ] Triaje funciona (signos vitales + prioridad)
  - [ ] Consulta funciona (motivo + diagnóstico + tratamiento)
  - [ ] Receta funciona (lista de medicamentos)
  - [ ] Orden Lab funciona (lista de exámenes)
  - [ ] Se guardan correctamente en `clinical_form` con `form_type` adecuado

- [ ] **Dashboard:**

  - [ ] Al menos 2 gráficos funcionando (Recharts)
  - [ ] Métricas básicas se muestran
  - [ ] Datos vienen de la API real

- [ ] **Infraestructura:**

  - [ ] S3 sube archivos correctamente
  - [ ] Backend corre sin errores
  - [ ] Frontend compila sin warnings críticos
  - [ ] Variables de entorno configuradas

- [ ] **Base de Datos:**

  - [ ] Seeder ejecutado con datos frescos
  - [ ] Migraciones aplicadas
  - [ ] Relaciones funcionando correctamente

- [ ] **Testing Manual:**
  - [ ] Crear paciente → OK
  - [ ] Crear clinical record → OK
  - [ ] Crear formulario (cada tipo) → OK
  - [ ] Subir documento → OK
  - [ ] Ver dashboard → OK

---

## 🚨 PRIORIDADES CLARAS

### OBLIGATORIO (No se puede avanzar sin esto):

1. ✅ Formularios clínicos (al menos Triaje y Consulta)
2. ✅ Dashboard básico (aunque sea sin gráficos complejos)

### IMPORTANTE (Intentar completar):

3. ⚠️ Todos los 4 tipos de formularios
4. ⚠️ Gráficos en dashboard
5. ⚠️ S3 funcionando correctamente

---

## 📝 NOTAS IMPORTANTES

1. **Formularios ≠ Triaje:** Triaje es UN TIPO de formulario (`form_type='triage'`)
2. **No crear nueva tabla:** Usar `clinical_form` existente
3. **JSON estructurado:** Cada `form_type` tiene su propio esquema JSON
4. **Deploy básico:** No necesita ser perfecto, solo funcional
5. **Redis NO es crítico:** Se puede implementar después

---

**Una vez completado esto, proceder con:** [SPRINT_3.md](./SPRINT_3.md)
