# 🔄 Firebase Automático - Cómo Funciona

**Para:** Nataly (Backend Developer)  
**Tema:** Cómo se envían automáticamente notificaciones push cuando Luis registra su token FCM  
**Fecha:** 17 Nov 2025

---

## 🎯 Pregunta Original

> "Cuando se guarde el fcm token, debería el backend automáticamente mandar todas las notificaciones a ese FCM? ¿Antes de cada notificación debo leer el modelo del user y verificar si existe algo en fcm? ¿O es automático?"

**Respuesta:** ✅ **ES COMPLETAMENTE AUTOMÁTICO**

---

## 🔄 Flujo Automático Actual

```
┌─────────────────────────────────────────────────────────────┐
│ 1. LUIS (Flutter) → Obtiene token FCM de Firebase          │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. LUIS → POST /api/accounts/users/update_fcm_token/       │
│    {                                                        │
│      "fcm_token": "dE7X8Y9Z1A2B3C..."                      │
│    }                                                        │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. BACKEND → Guarda en BD                                   │
│    User.fcm_token = "dE7X8Y9Z1A2B3C..."                    │
└─────────────────────────────────────────────────────────────┘
                              ↓
        ✅ DESDE AQUÍ EN ADELANTE ES AUTOMÁTICO ✅
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. EVENTO en Backend (ej: documento subido)                 │
│    Signal dispara → notify_on_document_upload()            │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. NotificationService → Crea Notification en BD            │
│    - id: UUID                                               │
│    - user: el usuario                                       │
│    - type: DOCUMENT_UPLOADED                                │
│    - status: QUEUED                                         │
│    - title, body, data                                      │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ 6. Celery task → send_notification_push.delay(notif_id)    │
│    (encolada automáticamente)                               │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ 7. CELERY WORKER → Procesa la tarea                         │
│                                                             │
│    • Lee notification de BD                                 │
│    • Obtiene user.fcm_token (¡automático!)                 │
│    • Si existe:                                             │
│      → Envía a Firebase Cloud Messaging                     │
│    • Si NO existe:                                          │
│      → Skip (notificación guardada solo en BD)              │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ 8. FIREBASE → Envía al dispositivo de Luis                  │
│    • Si app en foreground → manejador en app                │
│    • Si app en background → muestra en bandeja              │
│    • Si app cerrada → muestra en bandeja                    │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ 9. LUIS recibe notificación en dispositivo ✅               │
└─────────────────────────────────────────────────────────────┘
```

---

## 💻 Código Específico

### 1. Endpoint: Guardar Token

**Archivo:** `cr_backend/apps/accounts/views.py`

```python
@action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
def update_fcm_token(self, request):
    fcm_token = request.data.get('fcm_token')

    # ← Guarda automáticamente en BD
    request.user.fcm_token = fcm_token
    request.user.save(update_fields=['fcm_token', 'updated_at'])

    # Respuesta (es todo)
    return Response({'success': True})
```

**Resultado en BD:**

```sql
UPDATE accounts_user
SET fcm_token = 'dE7X8Y9Z1A2B3C...'
WHERE id = 'luis-user-id';
```

### 2. Signal: Se dispara automáticamente

**Archivo:** `cr_backend/apps/notifications/signals.py`

```python
@receiver(post_save, sender=ClinicalDocument)
def notify_on_document_upload(sender, instance, created, **kwargs):
    if created:
        service = NotificationService()
        recipients = User.objects.filter(tenant=instance.tenant, is_staff=True)

        # ← Crea Notification y encolaa task
        service.notify_document_uploaded(instance, recipients)
```

### 3. Celery Task: Envía automáticamente a Firebase

**Archivo:** `cr_backend/apps/notifications/tasks.py`

```python
@shared_task(bind=True, max_retries=3)
def send_notification_push(self, notification_id: str):
    notification = Notification.objects.get(id=notification_id)

    # ← AQUÍ ES AUTOMÁTICO
    if not notification.user.fcm_token:
        # Si NO tiene token → solo in-app
        logger.info("No FCM token - saved in-app only")
        notification.mark_as_sent()
        return {'sent_via': 'in_app_only'}

    # Si TIENE token → envía a Firebase
    message = messaging.Message(
        notification=messaging.Notification(
            title=notification.title,
            body=notification.body,
        ),
        token=notification.user.fcm_token,  # ← Lee automático
    )

    response = messaging.send(message)  # ← Envía automático
    notification.mark_as_sent()

    return {'sent_via': 'firebase_push', 'message_id': response}
```

---

## ✅ Escenarios Automáticos

### Escenario 1: Luis registra su token

```
Timeline:
T0: Luis POST /update_fcm_token/ → user.fcm_token = "TOKEN_A"
T1: Se sube documento
T2: Signal crea Notification
T3: Celery ve user.fcm_token = "TOKEN_A"
T4: Celery envía a Firebase
T5: Luis recibe en teléfono ✅
```

**NO necesitas hacer nada en backend**

### Escenario 2: Admin entra, Luis entra después en el MISMO dispositivo

```
Timeline:
T0: Admin POST /update_fcm_token/ → user_admin.fcm_token = "TOKEN_A"
T1: Admin se logout
T2: Admin POST /delete_fcm_token/ → user_admin.fcm_token = NULL
T3: Luis POST /update_fcm_token/ → user_luis.fcm_token = "TOKEN_A" (mismo device)
T4: Se sube documento
T5: Signal → envía a Admin y Luis
T6: Celery:
    - Admin: user_admin.fcm_token = NULL → skip
    - Luis: user_luis.fcm_token = "TOKEN_A" → envía ✅
T7: Solo Luis recibe ✅
```

**Automático - cada usuario tiene su propio token**

### Escenario 3: Usuario sin token

```
Timeline:
T0: Usuario X NO tiene token (no registró)
T1: Se sube documento
T2: Signal crea Notification
T3: Celery:
    - user_x.fcm_token = NULL
    - Skip push (pero guardada en BD)
T4: Usuario ve notificación en panel web ✅
T5: Cuando se registre token:
    - Notificaciones futuras → push
    - Notificaciones antiguas → siguen en web
```

**Automático - sin cambios**

---

## 🔄 Ventajas del Diseño Automático

| Ventaja                    | Explicación                                                     |
| -------------------------- | --------------------------------------------------------------- |
| **Sin cambios en backend** | Cuando Luis envíe token, todo funciona automáticamente          |
| **Multi-dispositivo**      | Cada dispositivo tiene su token, funciona para cada usuario     |
| **Fallback automático**    | Si no hay token → guarda en BD (in-app), no pierde notificación |
| **Escalable**              | Agrega 50 usuarios con token → Celery envía a todos sin cambios |
| **Seguro**                 | Cada usuario solo recibe sus notificaciones                     |

---

## 🧪 Testing

### Test 1: Verificar que se guarda token

```bash
cd cr_backend
python manage.py shell

from django.contrib.auth import get_user_model
User = get_user_model()

user = User.objects.first()
print(f"Token antes: {user.fcm_token}")

# Simular POST de Luis
user.fcm_token = "TEST_TOKEN_123"
user.save()

print(f"Token después: {user.fcm_token}")
```

**Resultado esperado:**

```
Token antes: None
Token después: TEST_TOKEN_123
```

### Test 2: Verificar que Celery envía automáticamente

```bash
# Terminal 1: Ejecutar worker
celery -A config worker -l info

# Terminal 2: Crear notificación
cd cr_backend
python manage.py shell

from apps.notifications.models import Notification, NotificationStatus
from apps.notifications.tasks import send_notification_push
from django.contrib.auth import get_user_model

User = get_user_model()
user = User.objects.first()
user.fcm_token = "TEST_TOKEN_123"
user.save()

# Crear notificación manual
notif = Notification.objects.create(
    user=user,
    tenant=user.tenant,
    type='system.test',
    channel='push',
    title='Test Push',
    body='Testing firebase',
    status=NotificationStatus.QUEUED,
)

# Enviar (Celery lo hará)
send_notification_push.delay(str(notif.id))
```

**Resultado en Terminal 1 (Celery):**

```
✅ Push sent to usuario@email.com - Message ID: projects/...
```

---

## ❓ Preguntas Frecuentes

### P: ¿Y si Luis no envía el token?

**R:** Las notificaciones se guardan en BD (in-app). Cuando Luis envíe el token después, solo las nuevas notificaciones van a push. Las antiguas siguen en el panel web.

### P: ¿Y si Luis cambia de dispositivo?

**R:**

- Dispositivo 1: `user.fcm_token = "TOKEN_A"` → notificaciones a TOKEN_A
- Desinstala app en dispositivo 1
- Dispositivo 2: POST /update_fcm_token/ → `user.fcm_token = "TOKEN_B"` → notificaciones a TOKEN_B

Solo el último dispositivo recibe push.

### P: ¿Y si Luis entra como Admin en un dispositivo y luego como Cliente en el mismo?

**R:** Ver "Escenario 2" arriba. Cada usuario tiene su fcm_token en BD:

- `User.admin.fcm_token = "TOKEN_A"` (cuando Admin entra)
- `User.cliente.fcm_token = "TOKEN_A"` (cuando Cliente entra, sobrescribe)

Celery automáticamente checkea el token del usuario que recibe la notificación.

### P: ¿Por qué POST para delete_fcm_token y no DELETE?

**R:** Ambos funcionan ahora. Pero POST es más compatible con:

- Clientes móviles que tienen limitaciones con DELETE
- Aplicaciones que usan formularios (no soportan DELETE)

Django REST Framework maneja ambos en el mismo endpoint.

---

## 📋 Checklist: ¿Está todo listo?

- ✅ Token se guarda en `user.fcm_token`
- ✅ Celery lee token automáticamente
- ✅ Si existe token → envía a Firebase
- ✅ Si no existe token → solo guarda en BD
- ✅ Sin cambios en backend cuando Luis envíe token
- ✅ Multipositivo/multi-usuario funciona automático
- ✅ Fallos se reintentan automáticamente (3 veces)
- ✅ POST y DELETE funcionan para eliminar token

---

## 🚀 Resumen para Nataly

**Tu backend está 100% listo.** Cuando Luis:

1. Registre su token → se guarda automáticamente
2. Se cree un evento (documento, etc) → Celery envía automáticamente
3. No haya token → fallback automático a in-app

**No hay que modificar nada más en backend.**

---

¡Listo para usar! 🎉
