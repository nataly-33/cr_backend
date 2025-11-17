# 🧪 Test Firebase Backend - Guía Rápida

**Para:** Nataly y Luis  
**Propósito:** Verificar que Firebase funciona end-to-end

---

## 📋 Prerequisitos

✅ `firebase-admin` instalado:

```bash
cd cr_backend
pip install firebase-admin
```

✅ `FIREBASE_SERVICE_ACCOUNT_KEY` en `.env` ← Ya está hecho

✅ Celery corriendo (si quieres envío asíncrono):

```bash
celery -A config worker -l info
```

---

## 🧪 Test 1: Credenciales Cargadas

```bash
cd cr_backend
python manage.py shell
```

```python
import os
import json

# Método correcto: usar os.getenv()
cred_json = os.getenv('FIREBASE_SERVICE_ACCOUNT_KEY')

if cred_json and cred_json.strip():
    try:
        # Limpiar comillas si las tiene
        cred_json = cred_json.strip().strip("'\"")
        cred_dict = json.loads(cred_json)
        print("✅ FIREBASE_SERVICE_ACCOUNT_KEY encontrada")
        print(f"✅ Project ID: {cred_dict.get('project_id')}")
        print(f"✅ Client Email: {cred_dict.get('client_email')}")
    except json.JSONDecodeError as e:
        print(f"❌ JSON inválido: {e}")
        print(f"Primer 100 caracteres: {cred_json[:100]}")
else:
    print("❌ FIREBASE_SERVICE_ACCOUNT_KEY NO está en .env o está vacía")
```

**Resultado esperado:**

```
✅ FIREBASE_SERVICE_ACCOUNT_KEY encontrada
✅ Project ID: clinicrecords-4f581
✅ Client Email: firebase-adminsdk-fbsvc@clinicrecords-4f581.iam.gserviceaccount.com
```

**Si falla con "JSON inválido":**

- Verifica que el JSON en `.env` NO tiene líneas vacías dentro
- Las comillas simples `'` alrededor del JSON son correctas
- El JSON debe ser VÁLIDO (puedes testear en https://jsonlint.com/)

---

## 🧪 Test 2: Firebase Admin SDK Inicializado

```python
import firebase_admin
from firebase_admin import credentials
import json
import os

cred_json = os.getenv('FIREBASE_SERVICE_ACCOUNT_KEY')
cred_dict = json.loads(cred_json)
cred = credentials.Certificate(cred_dict)

try:
    firebase_admin.initialize_app(cred)
    print("✅ Firebase Admin SDK inicializado")
except ValueError as e:
    print(f"ℹ️ Firebase ya estaba inicializado: {e}")
```

**Resultado esperado:**

```
✅ Firebase Admin SDK inicializado
```

O si lo ejecutas 2 veces:

```
ℹ️ Firebase ya estaba inicializado: [Errno 4] An app named "__default__" already exists
```

---

## 🧪 Test 3: Enviar Notificación (paso final)

**Primero, Luis debe ejecutar su app Flutter y copiar el token FCM.**

Luego, reemplaza `TOKEN_AQUI` y ejecuta:

```python
from firebase_admin import messaging

# REEMPLAZAR CON EL TOKEN REAL DE LUIS
TOKEN_FCM = 'TOKEN_AQUI'

message = messaging.Message(
    notification=messaging.Notification(
        title='🎉 ¡Prueba exitosa!',
        body='Si ves esto en tu teléfono, Firebase funciona',
    ),
    data={
        'timestamp': '2025-11-17T10:00:00Z',
        'test': 'true'
    },
    token=TOKEN_FCM,
)

try:
    response = messaging.send(message)
    print(f"✅ Notificación enviada exitosamente")
    print(f"   Message ID: {response}")
except Exception as e:
    print(f"❌ Error: {e}")
```

**Resultado esperado en consola:**

```
✅ Notificación enviada exitosamente
   Message ID: projects/clinicrecords-4f581/messages/xxxxxxxxxx
```

**Resultado esperado en teléfono de Luis:**

- ✅ Aparecerá notificación en la bandeja (app cerrada)
- ✅ Aparecerá notificación en app (app abierta)

---

## 🧪 Test 4: Test End-to-End (Completo)

Este test simula lo que pasará en producción:

```python
from django.contrib.auth import get_user_model
from apps.notifications.models import Notification, NotificationStatus
from firebase_admin import messaging
import json
import os

User = get_user_model()

# 1️⃣ Obtener usuario de Luis (o crear uno para test)
user = User.objects.filter(email='luis@example.com').first()
if not user:
    print("❌ Usuario 'luis@example.com' no existe")
    print("📝 Usuarios disponibles:")
    for u in User.objects.all()[:5]:
        print(f"   - {u.email}")
else:
    print(f"✅ Usuario encontrado: {user.email}")

    # 2️⃣ Verificar que tiene FCM token
    if user.fcm_token:
        print(f"✅ Token FCM guardado: {user.fcm_token[:20]}...")
    else:
        print("⚠️ Usuario no tiene FCM token guardado")
        print("   (Luis debe enviar token desde la app Flutter)")

    # 3️⃣ Crear notificación
    notification = Notification.objects.create(
        user=user,
        tenant=user.tenant,
        type='system.test',
        channel='push',
        title='Test Notificación Push',
        body='Esta es una notificación de prueba',
        status=NotificationStatus.QUEUED,
        event_id=f'test_{user.id}',
        data={
            'test': True,
            'source': 'manual_test'
        }
    )
    print(f"✅ Notificación creada: {notification.id}")

    # 4️⃣ Enviar con Firebase
    if user.fcm_token:
        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=notification.title,
                    body=notification.body,
                ),
                data=notification.data,
                token=user.fcm_token,
            )

            response = messaging.send(message)
            print(f"✅ Notificación enviada: {response}")

            # Actualizar estado
            notification.status = NotificationStatus.SENT
            notification.save()
            print("✅ Estado actualizado a SENT")

        except Exception as e:
            print(f"❌ Error enviando: {e}")
            notification.status = NotificationStatus.FAILED
            notification.last_error = str(e)
            notification.save()
```

---

## 📊 Troubleshooting

| Síntoma                                                                    | Causa                               | Solución                               |
| -------------------------------------------------------------------------- | ----------------------------------- | -------------------------------------- |
| `ModuleNotFoundError: No module named 'firebase_admin'`                    | No instalado                        | `pip install firebase-admin`           |
| `TypeError: the JSON object must be str, bytes or bytearray, not NoneType` | No hay FIREBASE_SERVICE_ACCOUNT_KEY | Verificar `.env`                       |
| `KeyError: 'client_email'`                                                 | JSON malformado                     | Copiar JSON completo y válido a `.env` |
| `messaging.UnregisteredError`                                              | Token inválido                      | Generar nuevo token en Flutter         |
| Notificación no llega                                                      | FCM token expirado                  | Actualizar desde app Flutter           |

---

## 🔄 Ciclo de Test Completo

### Paso 1: Nataly prepara backend ✅ (ya hecho)

- ✅ firebase-admin instalado
- ✅ FIREBASE_SERVICE_ACCOUNT_KEY en .env
- ✅ Endpoints listos en backend

### Paso 2: Luis ejecuta app Flutter 🚀

- ☐ App se inicia
- ☐ Obtiene token FCM
- ☐ Envía token a backend (POST `/api/accounts/users/update_fcm_token/`)
- ☐ Copia token del log de Flutter

### Paso 3: Nataly testea 🧪

```bash
python manage.py shell
# Ejecutar Test 3 o Test 4
```

### Paso 4: Verificar en dispositivo ✅

- ☐ Notificación aparece en bandeja (app cerrada)
- ☐ Notificación aparece en app (app abierta)
- ☐ Tap en notificación funciona

---

## 📞 Si algo falla

**1. Revisar logs de Firebase:**

```bash
# En shell de Django
from django.contrib.auth import get_user_model
User = get_user_model()
user = User.objects.first()
print(f"FCM Token: {user.fcm_token}")
```

**2. Revisar logs de Celery:**

```bash
# Terminal separada
tail -f logs/celery.log
```

**3. Revisar logs de Django:**

```bash
# Terminal separada
tail -f logs/django.log
```

**4. Contactar a soporte:**

- Enviar: Token FCM de Luis + Mensaje de error completo
- Verificar: ¿Está la app en desarrollo o producción?

---

¡Éxito! 🚀
