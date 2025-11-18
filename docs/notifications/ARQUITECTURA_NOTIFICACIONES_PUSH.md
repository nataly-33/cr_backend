# 🏗️ Arquitectura de Notificaciones Push

**Sistema:** CliniDocs
**Plataforma:** Flutter + Django + Firebase Cloud Messaging
**Fecha:** 17/11/2025

---

## 📊 Flujo Completo

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FLUJO DE NOTIFICACIONES                      │
└─────────────────────────────────────────────────────────────────────┘

1. INICIALIZACIÓN (Al abrir la app)
   ┌──────────────────┐
   │  App Flutter     │
   │  (Celular)       │
   └────────┬─────────┘
            │
            │ 1. initialize()
            ▼
   ┌──────────────────────────┐
   │  NotificationService     │
   │  - Firebase.initializeApp│
   │  - requestPermission     │
   │  - getToken()            │
   └────────┬─────────────────┘
            │
            │ 2. Token FCM obtenido
            │    "dE7X8Y9Z1A2B..."
            ▼
   ┌──────────────────────────┐
   │  NotificationBloc        │
   │  - UpdateFcmToken event  │
   └────────┬─────────────────┘
            │
            │ 3. POST /api/accounts/users/update_fcm_token/
            │    { "fcm_token": "dE7X..." }
            ▼
   ┌──────────────────────────┐
   │  Backend Django          │
   │  - Guarda en User.fcm_token │
   └──────────────────────────┘

═══════════════════════════════════════════════════════════════════════

2. ENVÍO DE NOTIFICACIÓN (Cuando ocurre un evento)
   ┌──────────────────┐
   │  Backend Django  │
   │  - Usuario crea  │
   │    documento     │
   └────────┬─────────┘
            │
            │ 1. Signal post_save
            ▼
   ┌──────────────────────────┐
   │  signals.py              │
   │  - notify_on_document_*  │
   └────────┬─────────────────┘
            │
            │ 2. NotificationService.send()
            ▼
   ┌──────────────────────────┐
   │  Notification Model      │
   │  - type: document.created│
   │  - channel: push         │
   │  - user: admin@hospital  │
   └────────┬─────────────────┘
            │
            │ 3. Celery enqueue
            ▼
   ┌──────────────────────────┐
   │  Celery Worker           │
   │  - send_notification_push│
   └────────┬─────────────────┘
            │
            │ 4. Firebase Admin SDK
            ▼
   ┌──────────────────────────┐
   │  Firebase Cloud Messaging│
   │  - Google servers        │
   └────────┬─────────────────┘
            │
            │ 5. Push notification
            ▼
   ┌──────────────────────────┐
   │  Dispositivo Android     │
   │  - Sistema operativo     │
   └────────┬─────────────────┘
            │
            │ 6. onMessage/onBackgroundMessage
            ▼
   ┌──────────────────────────┐
   │  App Flutter             │
   │  - NotificationService   │
   │  - Muestra notificación  │
   └──────────────────────────┘

═══════════════════════════════════════════════════════════════════════

3. LOGOUT (Eliminar token)
   ┌──────────────────┐
   │  App Flutter     │
   │  - Usuario logout│
   └────────┬─────────┘
            │
            │ 1. AuthLogoutRequested
            ▼
   ┌──────────────────────────┐
   │  AuthBloc                │
   │  - _onAuthLogoutRequested│
   └────────┬─────────────────┘
            │
            │ 2. deleteFcmToken()
            ▼
   ┌──────────────────────────┐
   │  NotificationDataSource  │
   │  - POST /delete_fcm_token│
   └────────┬─────────────────┘
            │
            │ 3. Elimina de BD
            ▼
   ┌──────────────────────────┐
   │  Backend Django          │
   │  - User.fcm_token = NULL │
   └────────┬─────────────────┘
            │
            │ 4. deleteToken()
            ▼
   ┌──────────────────────────┐
   │  Firebase                │
   │  - Invalida token local  │
   └──────────────────────────┘
```

---

## 🗂️ Estructura de Archivos (Flutter)

```
cr_movil/
├── android/
│   ├── app/
│   │   ├── google-services.json          ← Credenciales Firebase
│   │   ├── build.gradle.kts              ← Config Firebase (modificado)
│   │   └── src/main/
│   │       └── AndroidManifest.xml       ← Permisos (modificado)
│   └── build.gradle.kts                  ← Plugin Firebase (modificado)
│
├── lib/
│   ├── core/
│   │   └── services/
│   │       └── notification_service.dart ← Gestión FCM (NUEVO)
│   │
│   ├── features/
│   │   ├── auth/
│   │   │   └── presentation/
│   │   │       └── bloc/
│   │   │           └── auth_bloc.dart    ← Logout con FCM (modificado)
│   │   │
│   │   └── notifications/                ← Feature completo (NUEVO)
│   │       ├── data/
│   │       │   └── datasources/
│   │       │       └── notification_remote_datasource.dart
│   │       └── presentation/
│   │           └── bloc/
│   │               ├── notification_bloc.dart
│   │               ├── notification_event.dart
│   │               └── notification_state.dart
│   │
│   ├── config/
│   │   └── dependency_injection/
│   │       └── injection_container.dart  ← DI Notifications (modificado)
│   │
│   └── main.dart                         ← Init Notifications (modificado)
│
└── pubspec.yaml                          ← Dependencias Firebase (modificado)
```

---

## 🔐 Endpoints del Backend

| Método | Endpoint                              | Descripción                  | Implementado |
| ------ | ------------------------------------- | ---------------------------- | ------------ |
| POST   | `/api/accounts/users/update_fcm_token/` | Guarda token FCM            | ✅           |
| POST   | `/api/accounts/users/delete_fcm_token/` | Elimina token FCM           | ✅           |
| GET    | `/api/notifications/`                 | Lista notificaciones usuario | ✅           |
| PATCH  | `/api/notifications/{id}/read/`       | Marca notificación leída    | ✅           |

---

## 📱 Estados de la Aplicación

### NotificationBloc States

```dart
NotificationInitial          // Estado inicial
NotificationInitializing     // Inicializando Firebase
NotificationReady            // Listo, con token FCM
NotificationTokenUpdating    // Enviando token al backend
NotificationTokenUpdated     // Token actualizado en backend
NotificationTokenDeleted     // Token eliminado (logout)
NotificationError            // Error en cualquier paso
```

### Handlers de Mensajes

```dart
onMessage                    // App en foreground
  └─> _handleForegroundMessage()
      └─> _showLocalNotification()

onBackgroundMessage          // App en background o cerrada
  └─> _firebaseMessagingBackgroundHandler()

onMessageOpenedApp           // Usuario toca notificación
  └─> _handleNotificationTap()
```

---

## 🎯 Tipos de Notificaciones

Según [GUIA_NOTIFICACIONES_Y_OCR.md](./cr_backend/docs/notifications/GUIA_NOTIFICACIONES_Y_OCR.md):

### Canales

- **in_app**: Notificaciones dentro de la app (React frontend)
- **push**: Notificaciones push (Flutter móvil) ← **Implementado**
- **email**: Notificaciones por correo (solo eventos críticos)

### Eventos Automáticos

| Evento                        | Canales             | Receptor     |
| ----------------------------- | ------------------- | ------------ |
| `document.created`            | in_app + push       | Admin TI     |
| `document.updated`            | in_app + push       | Admin TI     |
| `document.deleted`            | in_app + push + email | Admin TI   |
| `clinical_record.created`     | in_app + push       | Admin TI     |
| `clinical_record.updated`     | in_app + push       | Admin TI     |
| `clinical_record.deleted`     | in_app + push + email | Admin TI   |
| `clinical_form.created`       | in_app + push       | Admin TI     |
| `clinical_form.updated`       | in_app + push       | Admin TI     |
| `clinical_form.deleted`       | in_app + push + email | Admin TI   |

---

## 🔄 Ciclo de Vida del Token FCM

```
1. App se instala
   └─> Token FCM generado por Firebase

2. App se abre (primera vez)
   └─> Token obtenido
   └─> Enviado al backend
   └─> Guardado en User.fcm_token

3. Token cambia (raro)
   └─> onTokenRefresh listener
   └─> Nuevo token enviado al backend
   └─> Actualizado en User.fcm_token

4. Usuario hace logout
   └─> Token eliminado del backend
   └─> Token invalidado localmente

5. Usuario hace login de nuevo
   └─> Token regenerado
   └─> Enviado al backend
```

---

## 🛡️ Seguridad

### Autenticación

- Todos los endpoints de notificaciones requieren `Authorization: Bearer <token>`
- El token se obtiene en el login y se guarda en FlutterSecureStorage
- El DioClient automáticamente agrega el header en cada request

### Multi-tenancy

- Las notificaciones respetan el aislamiento de tenants
- Un usuario solo recibe notificaciones de su propio tenant
- El backend valida que `user.tenant == notification.tenant`

### Permisos

- La app solicita permisos de notificación en el primer uso
- Si el usuario deniega, las notificaciones no funcionarán
- Se puede reactivar desde Ajustes del sistema

---

## 📊 Monitoreo y Logs

### En Flutter (Desarrollo)

```bash
flutter run --debug

# Buscar:
✅ Firebase inicializado
📱 Token FCM obtenido
📤 Enviando token FCM al backend
📲 Mensaje en foreground
👆 Usuario tocó notificación
```

### En Backend (Producción)

```python
# Ver notificaciones creadas
from apps.notifications.models import Notification

Notification.objects.filter(
    type__startswith='document',
    channel='push',
    status='sent'
).count()
```

### En Firebase Console

- **Cloud Messaging** → **Campaign Analytics**
- Ver estadísticas de entrega, apertura, etc.

---

## 🚀 Despliegue

### Desarrollo (Local)

```bash
# Backend
cd cr_backend
python manage.py runserver

# Celery
.\run_celery_worker.ps1
.\run_celery_beat.ps1

# Flutter (Debug)
cd cr_movil
flutter run --debug
```

### Producción (Release)

```bash
# Generar APK firmado
cd cr_movil
flutter build apk --release

# O generar App Bundle (para Google Play)
flutter build appbundle --release
```

**APK estará en:**
```
build/app/outputs/flutter-apk/app-release.apk
```

---

## 🔮 Mejoras Futuras

### Corto Plazo
- [ ] Agregar iconos personalizados por tipo de notificación
- [ ] Implementar navegación al tocar notificación (deep linking)
- [ ] Agregar sonidos personalizados
- [ ] Mostrar imagen en notificación (si el documento es imagen)

### Mediano Plazo
- [ ] Notificaciones programadas (recordatorios)
- [ ] Topics de Firebase para grupos de usuarios
- [ ] Notificaciones ricas (botones de acción)
- [ ] Analytics de interacción con notificaciones

### Largo Plazo
- [ ] Notificaciones en iOS (si se desarrolla versión iOS)
- [ ] Web Push Notifications (para frontend React)
- [ ] Chatbot integrado con notificaciones

---

## 📚 Referencias

### Documentación Interna
- [GUIA_COMPLETA_NOTIFICACIONES_PUSH_FLUTTER.md](./GUIA_COMPLETA_NOTIFICACIONES_PUSH_FLUTTER.md)
- [COMANDOS_RAPIDOS_NOTIFICACIONES_PUSH.md](./COMANDOS_RAPIDOS_NOTIFICACIONES_PUSH.md)
- [BACKEND_STATE_NOTIFICACIONES_PUSH.md](./BACKEND_STATE_NOTIFICACIONES_PUSH.md)
- [cr_backend/docs/notifications/FIREBASE_SETUP_COMPLETO.md](./cr_backend/docs/notifications/FIREBASE_SETUP_COMPLETO.md)
- [cr_backend/docs/API_ENDPOINTS_REFERENCE.md](./cr_backend/docs/API_ENDPOINTS_REFERENCE.md)

### Documentación Externa
- [Firebase Cloud Messaging (Flutter)](https://firebase.google.com/docs/cloud-messaging/flutter/client)
- [Flutter Local Notifications](https://pub.dev/packages/flutter_local_notifications)
- [Firebase Admin SDK (Python)](https://firebase.google.com/docs/admin/setup)

---

**Última actualización:** 17/11/2025
**Versión:** 1.0.0
**Autor:** Claude (AI Assistant)
