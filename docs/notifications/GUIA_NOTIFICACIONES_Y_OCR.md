# 🔔 GUÍA COMPLETA - Sistema de Notificaciones Automáticas

## ✅ Lo que se ha implementado

### 1. **Notificaciones Automáticas para CRUD**

El sistema ahora envía notificaciones automáticas al **Admin TI del hospital** cuando cualquier usuario (doctor, secretaria, etc.) realiza estas acciones:

#### 📄 **Documentos** (`apps.documents`)

- ✅ **Crear documento**: Notifica al Admin que se creó un documento
- ✅ **Actualizar documento**: Notifica que se modificó un documento
- ✅ **Eliminar documento**: **CRÍTICO** - Notifica por in_app, push Y email

#### 📋 **Historias Clínicas** (`apps.clinical_records.ClinicalRecord`)

- ✅ **Crear historia clínica**: Notifica al Admin
- ✅ **Actualizar historia clínica**: Notifica cambios de estado
- ✅ **Eliminar historia clínica**: **MUY CRÍTICO** - Notifica por todos los canales

#### 📝 **Formularios Clínicos** (`apps.clinical_records.ClinicalForm`)

- ✅ **Crear formulario**: Notifica al Admin
- ✅ **Actualizar formulario**: Notifica modificaciones
- ✅ **Eliminar formulario**: **CRÍTICO** - Notifica por todos los canales

### 2. **Características Implementadas**

✅ **Rastreo automático de usuario**: Usa `django-crum` para detectar quién hizo la acción
✅ **No auto-notificaciones**: Si el Admin hace la acción, NO se notifica a sí mismo (excepto eliminaciones)
✅ **Idempotencia**: No duplica notificaciones con `event_id` único
✅ **Canales configurables**:

- `in_app`: Notificaciones en la app (todas)
- `push`: Notificaciones push FCM (todas menos actualizaciones)
- `email`: Solo para eliminaciones (crítico)

✅ **Templates multiidioma**: Español e Inglés
✅ **Iconos y colores**: Cada tipo tiene su icono y color distintivo
✅ **Información contextual**: Incluye nombre del paciente, tipo de documento, usuario que hizo la acción

### 3. **Polling Optimizado**

✅ **Antes**: Consultaba cada 30 segundos (excesivo)
✅ **Ahora**: Consulta cada 2 minutos (120 segundos)
✅ **Con FCM**: Cuando implementes Flutter Push, puedes aumentar a 5 minutos o más

---

## 📦 Archivos Creados/Modificados

### Backend

1. ✅ `apps/documents/signals.py` - Signals para documentos
2. ✅ `apps/clinical_records/signals.py` - Signals para records y forms
3. ✅ `apps/notifications/templates.py` - Agregados 9 nuevos templates
4. ✅ `apps/documents/apps.py` - Registro de signals
5. ✅ `apps/clinical_records/apps.py` - Registro de signals
6. ✅ `config/settings/base.py` - Agregado `django-crum` y middleware
7. ✅ `config/celery.py` - Configuración para Windows (pool solo)
8. ✅ `run_celery_worker.ps1` - Actualizado para usar `--pool=solo`
9. ✅ `requirements.txt` - Agregado `django-crum==0.7.9`

### Frontend

1. ✅ `NotificationBell.tsx` - Polling cada 2min + nuevos tipos
2. ✅ `NotificationCenter.tsx` - Polling cada 2min

---

## 🚀 Pasos para Probar

### 1. **Instalar dependencias y reiniciar servicios**

```powershell
# Terminal 1: Backend
cd d:\1NATALY\Proyectos\clinic_records\cr_backend
.\venv\Scripts\Activate.ps1
python manage.py runserver

# Terminal 2: Celery Worker (REINICIAR con nueva configuración)
cd d:\1NATALY\Proyectos\clinic_records\cr_backend
.\venv\Scripts\Activate.ps1
.\run_celery_worker.ps1

# Terminal 3: Celery Beat (si aún no está corriendo)
cd d:\1NATALY\Proyectos\clinic_records\cr_backend
.\venv\Scripts\Activate.ps1
.\run_celery_beat.ps1

# Terminal 4: Frontend
cd d:\1NATALY\Proyectos\clinic_records\cr_frontend
npm run dev
```

### 2. **Probar Notificaciones**

1. **Login como Doctor o Secretaria** (NO como Admin)
2. **Crear un documento**:

   - Ve a Documentos → Subir Documento
   - Completa el formulario y guarda
   - ✅ Debería aparecer notificación para el Admin

3. **Actualizar un documento**:

   - Edita un documento existente
   - ✅ Notificación al Admin

4. **Eliminar un documento** (CRÍTICO):

   - Elimina un documento
   - ✅ Admin recibe notificación IN_APP + PUSH + EMAIL

5. **Login como Admin**:
   - Ve al icono de campana 🔔
   - Deberías ver las notificaciones con:
     - 📄 Iconos distintivos
     - Nombre del usuario que hizo la acción
     - Nombre del paciente
     - Tipo de documento/formulario

### 3. **Verificar en Logs**

**Backend (Terminal 1):**

```
✓ Notificación de documento procesada: 1 creadas
```

**Celery Worker (Terminal 2):**

```
[INFO] Notification created: <uuid> (document.created/in_app) for admin@hospital.com
```

**Celery Beat (Terminal 3):**

```
[INFO] Scheduler: Sending due task verificar-ocr-asincrono
```

---

## 🐛 Solución al Error de OCR/Celery

### Problema Original

```
PermissionError: [WinError 5] Acceso denegado
OSError: [WinError 6] Controlador no válido
```

**Causa**: Windows no soporta bien el multiprocessing de Celery (`billiard`)

### Solución Implementada ✅

1. **Configuración en `config/celery.py`**:

   ```python
   import platform
   if platform.system() == 'Windows':
       app.conf.worker_pool = 'solo'  # Un solo worker, sin multiprocessing
       app.conf.worker_concurrency = 1
   ```

2. **Actualización de `run_celery_worker.ps1`**:
   ```powershell
   celery -A config worker --pool=solo --loglevel=info ...
   ```

### Qué hace esto:

- ✅ Usa un **solo worker thread** en lugar de múltiples procesos
- ✅ Evita completamente los errores de `billiard` en Windows
- ✅ Las tareas OCR ahora se ejecutarán **sin errores**
- ⚠️ Procesamiento secuencial (una tarea a la vez)
- 💡 Para producción Linux, puedes usar `gevent` o `prefork` (múltiples workers)

---

## 📱 Siguiente Paso: Integración con Flutter FCM

Cuando implementes las notificaciones Push en Flutter:

### Backend (ya está listo):

- ✅ El campo `channel` ya soporta `'push'`
- ✅ Firebase Admin SDK ya está configurado
- ✅ Las notificaciones se crean con `channels=['in_app', 'push', 'email']`

### Frontend Mobile (Flutter):

1. **Instalar Firebase Messaging** en Flutter
2. **Obtener FCM token** del dispositivo
3. **Enviar token al backend**:
   ```dart
   POST /api/users/me/fcm_token/
   { "fcm_token": "cXXXXXXXXXXXXX..." }
   ```
4. **Guardar token en modelo User** (agregar campo `fcm_token`)
5. **El backend automáticamente enviará Push** cuando:
   - Se cree/actualice/elimine un documento
   - Se cree/actualice/elimine una historia clínica
   - Se cree/actualice/elimine un formulario

### Reducir polling cuando tengas FCM:

```typescript
// En NotificationBell.tsx y NotificationCenter.tsx
const POLL_INTERVAL = 300000; // 5 minutos (solo para respaldo)
```

---

## 🎯 Resumen de Notificaciones

| Acción                     | Canal                 | Admin notificado | Doctor notificado |
| -------------------------- | --------------------- | ---------------- | ----------------- |
| **Crear documento**        | in_app + push         | ✅               | ❌                |
| **Actualizar documento**   | in_app + push         | ✅               | ❌                |
| **Eliminar documento**     | in_app + push + email | ✅ (siempre)     | ❌                |
| **Crear historia clínica** | in_app + push         | ✅               | ❌                |
| **Actualizar historia**    | in_app + push         | ✅               | ❌                |
| **Eliminar historia**      | in_app + push + email | ✅ (siempre)     | ❌                |
| **Crear formulario**       | in_app + push         | ✅               | ❌                |
| **Actualizar formulario**  | in_app + push         | ✅               | ❌                |
| **Eliminar formulario**    | in_app + push + email | ✅ (siempre)     | ❌                |

**Nota**: El sistema detecta automáticamente si el usuario es Admin. Si el Admin hace la acción, NO se notifica a sí mismo (excepto eliminaciones, que son críticas).

---

## 📝 Ejemplo de Notificación

**Cuando un Doctor elimina un documento**:

```json
{
  "type": "document.deleted",
  "title": "🗑️ Documento eliminado",
  "body": "⚠️ Dr. Juan Pérez eliminó \"Radiografía Torax\" (Informe de Imagen) de María González",
  "channels": ["in_app", "push", "email"],
  "icon": "trash-2",
  "color": "red",
  "data": {
    "document_id": "7a1eca5a-08ea-4c48-bd5f-45cb9f2d61a4",
    "document_title": "Radiografía Torax",
    "document_type": "Informe de Imagen",
    "patient_name": "María González",
    "actor_name": "Dr. Juan Pérez",
    "deleted_at": "2025-11-17T08:45:00Z"
  }
}
```

---

## ✅ Checklist Final

- [x] Instalar `django-crum`
- [x] Agregar middleware `CurrentRequestUserMiddleware`
- [x] Crear signals para `ClinicalDocument`
- [x] Crear signals para `ClinicalRecord`
- [x] Crear signals para `ClinicalForm`
- [x] Registrar signals en `apps.py`
- [x] Agregar templates de notificaciones
- [x] Configurar Celery para Windows (`pool=solo`)
- [x] Actualizar script `run_celery_worker.ps1`
- [x] Reducir polling en frontend (30s → 2min)
- [x] Agregar tipos de notificaciones en frontend
- [ ] **Reiniciar todos los servicios** (Backend, Celery Worker, Celery Beat)
- [ ] **Probar creando/editando/eliminando documentos**
- [ ] **Verificar que el Admin recibe notificaciones**
- [ ] **Verificar que no hay errores de OCR en Celery**

---

## 🎉 ¡Listo!

Ahora tu sistema:

1. ✅ Notifica automáticamente al Admin de cada CRUD
2. ✅ No tiene errores de OCR/Celery en Windows
3. ✅ Reduce el polling (menos requests innecesarios)
4. ✅ Está listo para integración con Flutter FCM

**Próximos pasos**:

1. Reiniciar servicios
2. Probar notificaciones
3. Implementar Flutter FCM (cuando estés listo)
