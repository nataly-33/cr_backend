# 📱 Firebase Push Notifications - Guía Completa

**Para:** Nataly (Backend) + Luis (Mobile Flutter)  
**Estado:** ✅ Listo para usar  
**Última actualización:** Noviembre 17, 2025

---

## 🎯 Quick Start (5 minutos)

### Backend ya está hecho ✅

- ✅ `fcm_token` field en User model
- ✅ Endpoints `/update_fcm_token/` y `/delete_fcm_token/`
- ✅ Firebase Admin SDK configurado
- ✅ FIREBASE_SERVICE_ACCOUNT_KEY en .env

### Tu tarea hoy (Luis):

1. Copia `google-services.json` → `cr_movil/android/app/`
2. Configura Gradle (Kotlin DSL o Groovy)
3. Agrega dependencias en `pubspec.yaml`
4. Implementa `NotificationService.dart`
5. Prueba en dispositivo físico

---

## 📋 Setup - Backend (Ya Hecho)

### Credenciales Firebase

**Archivo:** `cr_backend/.env`

```bash
FIREBASE_SERVICE_ACCOUNT_KEY='{JSON_AQUI}'
FIREBASE_SERVER_KEY=AAAA...
```

✅ **Ya configurado. Para verificar:**

```bash
cd cr_backend
python manage.py shell

# Test 1: Load credentials
import os, json
cred_json = os.getenv('FIREBASE_SERVICE_ACCOUNT_KEY')
if cred_json:
    cred_dict = json.loads(cred_json)
    print(f"✅ Project: {cred_dict['project_id']}")
else:
    print("❌ NO CONFIGURADO")
```

### Firebase Admin SDK

```bash
pip install firebase-admin  # ✅ Ya instalado
```

---

## 📱 Setup - Mobile (Tarea de Luis)

### 1. Obtener `google-services.json`

**De Nataly:**

1. Firebase Console → Project Settings
2. General tab → Your apps
3. Click app Android
4. Download `google-services.json`

**Copiar a:**

```
cr_movil/android/app/google-services.json
```

### 2. Configurar Gradle

**ELIGE UNO:**

#### Opción A: Kotlin DSL (Moderno)

**Archivo:** `cr_movil/android/build.gradle.kts` (RAÍZ)

```kotlin
plugins {
  id("com.google.gms.google-services") version "4.4.4" apply false
}
```

**Archivo:** `cr_movil/android/app/build.gradle.kts` (APP)

```kotlin
plugins {
  id("com.android.application")
  id("kotlin-android")
  id("com.google.gms.google-services")  // ← AGREGAR
}

android {
  namespace = "com.clinic.records"
  compileSdk = 34
  // ...
}

dependencies {
  // Firebase BoM
  implementation(platform("com.google.firebase:firebase-bom:34.5.0"))

  // Firebase Cloud Messaging
  implementation("com.google.firebase:firebase-messaging")
  implementation("com.google.firebase:firebase-analytics")

  // Otros...
}
```

#### Opción B: Groovy (Legacy)

**Archivo:** `cr_movil/android/build.gradle` (RAÍZ)

```gradle
buildscript {
  dependencies {
    classpath 'com.google.gms:google-services:4.4.4'
  }
}
```

**Archivo:** `cr_movil/android/app/build.gradle` (APP)

```gradle
apply plugin: 'com.google.gms.google-services'  // ← AGREGAR AL FINAL

dependencies {
  // Firebase BoM
  implementation platform('com.google.firebase:firebase-bom:34.5.0')

  // Firebase Cloud Messaging
  implementation 'com.google.firebase:firebase-messaging'
  implementation 'com.google.firebase:firebase-analytics'
}
```

**Luego:** File → Sync Now (sin errores)

### 3. Dependencias Flutter

**Archivo:** `cr_movil/pubspec.yaml`

```yaml
dependencies:
  flutter:
    sdk: flutter
  firebase_core: ^2.24.2
  firebase_messaging: ^14.7.9
  flutter_local_notifications: ^16.3.0
  dio: ^5.3.1 # Para API calls
```

```bash
cd cr_movil
flutter pub get
```

### 4. Permisos Android

**Archivo:** `cr_movil/android/app/src/main/AndroidManifest.xml`

```xml
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="com.clinic.records">

    <!-- Agregar estos permisos -->
    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.POST_NOTIFICATIONS" />

    <application>
        <!-- Resto del contenido... -->
    </application>
</manifest>
```

### 5. NotificationService.dart

**Archivo:** `cr_movil/lib/core/services/notification_service.dart`

```dart
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:dio/dio.dart';

// Background handler (FUERA de la clase)
@pragma('vm:entry-point')
Future<void> _firebaseMessagingBackgroundHandler(RemoteMessage message) async {
  await Firebase.initializeApp();
  print('📨 Mensaje en background: ${message.notification?.title}');
}

class NotificationService {
  static final NotificationService _instance = NotificationService._internal();
  final FirebaseMessaging _fcm = FirebaseMessaging.instance;
  final Dio _dio = Dio();

  factory NotificationService() => _instance;

  NotificationService._internal();

  // ====== INICIALIZAR ======
  Future<void> initialize() async {
    await Firebase.initializeApp();

    // Request permission
    NotificationSettings settings = await _fcm.requestPermission();
    print('✅ Permiso: ${settings.authorizationStatus}');

    // Obtener token
    String? token = await _fcm.getToken();
    if (token != null) {
      print('📱 Token FCM: $token');
      await _sendTokenToBackend(token);
    }

    // Escuchar cambios de token
    _fcm.onTokenRefresh.listen((newToken) {
      print('🔄 Token renovado: $newToken');
      _sendTokenToBackend(newToken);
    });

    // Handlers
    FirebaseMessaging.onMessage.listen(_handleForegroundMessage);
    FirebaseMessaging.onMessageOpenedApp.listen(_handleNotificationTap);
    FirebaseMessaging.onBackgroundMessage(_firebaseMessagingBackgroundHandler);

    print('✅ NotificationService inicializado');
  }

  // ====== HANDLERS ======
  void _handleForegroundMessage(RemoteMessage message) {
    print('📲 Foreground: ${message.notification?.title}');
    // Mostrar notificación local
    _showLocalNotification(
      message.notification?.title ?? 'Notificación',
      message.notification?.body ?? 'Contenido',
    );
  }

  void _handleNotificationTap(RemoteMessage message) {
    print('👆 Tap: ${message.data}');
    // Navegar según datos
  }

  // ====== ENVIAR TOKEN AL BACKEND ======
  Future<void> _sendTokenToBackend(String token) async {
    try {
      final String baseUrl = 'http://localhost:8000';  // Cambiar en producción
      final String accessToken = 'TOKEN_DE_USUARIO';   // Obtener de AuthService

      await _dio.post(
        '$baseUrl/api/accounts/users/update_fcm_token/',
        data: {'fcm_token': token},
        options: Options(
          headers: {'Authorization': 'Bearer $accessToken'},
        ),
      );
      print('✅ Token enviado al backend');
    } catch (e) {
      print('❌ Error enviando token: $e');
    }
  }

  // ====== NOTIFICACIÓN LOCAL ======
  Future<void> _showLocalNotification(String title, String body) async {
    const AndroidNotificationDetails androidDetails =
        AndroidNotificationDetails(
      'channel_id',
      'channel_name',
      channelDescription: 'Notificaciones generales',
      importance: Importance.max,
      priority: Priority.high,
    );

    const NotificationDetails details =
        NotificationDetails(android: androidDetails);

    await FlutterLocalNotificationsPlugin().show(
      0,
      title,
      body,
      details,
    );
  }

  // ====== LOGOUT ======
  Future<void> logout() async {
    try {
      final String baseUrl = 'http://localhost:8000';
      final String accessToken = 'TOKEN_DE_USUARIO';

      await _dio.post(
        '$baseUrl/api/accounts/users/delete_fcm_token/',
        options: Options(
          headers: {'Authorization': 'Bearer $accessToken'},
        ),
      );

      await _fcm.deleteToken();
      print('✅ Token eliminado');
    } catch (e) {
      print('❌ Error: $e');
    }
  }
}
```

### 6. Inicializar en main.dart

**Archivo:** `cr_movil/lib/main.dart`

```dart
import 'package:flutter/material.dart';
import 'core/services/notification_service.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Inicializar notificaciones
  await NotificationService().initialize();

  runApp(MyApp());
}

class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'ClinIDocs',
      home: HomePage(),
    );
  }
}
```

---

## 🧪 Testing

### Test 1: Verificar Backend

```bash
cd cr_backend
python manage.py shell

# Copiar y pegar:
import os, json, firebase_admin
from firebase_admin import credentials, messaging

cred_json = os.getenv('FIREBASE_SERVICE_ACCOUNT_KEY')
if not cred_json:
    print("❌ NO ESTÁ EN .env")
else:
    cred_dict = json.loads(cred_json)
    try:
        firebase_admin.initialize_app(credentials.Certificate(cred_dict))
        print("✅ Firebase inicializado")
    except ValueError:
        print("ℹ️ Ya estaba inicializado")
```

### Test 2: Enviar Notificación

```python
# En Django shell, después de Test 1
from firebase_admin import messaging

TOKEN_FCM = 'TOKEN_REAL_DE_LUIS'  # Reemplazar

message = messaging.Message(
    notification=messaging.Notification(
        title='🎉 Test',
        body='¡Funciona!',
    ),
    token=TOKEN_FCM,
)

response = messaging.send(message)
print(f"✅ Enviado: {response}")
```

### Test 3: En Dispositivo

1. Luis ejecuta app en dispositivo físico
2. Copia token del log (primeras líneas)
3. Nataly ejecuta Test 2 con ese token
4. Luis debe recibir notificación

**Resultado esperado:**

- ✅ Notificación en bandeja (app cerrada)
- ✅ Notificación local (app abierta - foreground)
- ✅ Tap abre la app

---

## 🔄 Flujo Completo

```
Evento en Backend (doc subido)
    ↓
Signal → create Notification
    ↓
Celery → send_notification_push task
    ↓
Firebase Admin SDK → FCM
    ↓
Firebase Cloud Messaging (Google)
    ↓
Dispositivo recibe notificación
    ↓
App muestra/procesa
```

---

## 🎯 Endpoints Importantes

| Método | Endpoint                                | Descripción             |
| ------ | --------------------------------------- | ----------------------- |
| POST   | `/api/accounts/users/update_fcm_token/` | Guardar token           |
| POST   | `/api/accounts/users/delete_fcm_token/` | Eliminar token (logout) |
| GET    | `/api/notifications/`                   | Listar notificaciones   |
| PATCH  | `/api/notifications/{id}/read/`         | Marcar como leída       |

**Ejemplo: Guardar token**

```http
POST /api/accounts/users/update_fcm_token/
Authorization: Bearer <ACCESS_TOKEN>
Content-Type: application/json

{
  "fcm_token": "dE7X8Y9Z1A2B3..."
}
```

**Respuesta:**

```json
{
  "success": true,
  "message": "Token FCM actualizado exitosamente"
}
```

---

## 🆘 Troubleshooting

| Error                                               | Causa                                 | Solución                               |
| --------------------------------------------------- | ------------------------------------- | -------------------------------------- |
| `ModuleNotFoundError: firebase_admin`               | No instalado                          | `pip install firebase-admin`           |
| `TypeError: JSON object must be str...not NoneType` | No hay `FIREBASE_SERVICE_ACCOUNT_KEY` | Verificar .env                         |
| "App not registered"                                | Package name no coincide              | Verificar `build.gradle` applicationId |
| Token no funciona                                   | Inválido o expirado                   | Generar nuevo en Flutter               |
| Notificación no llega                               | FCM token no guardado en DB           | Verificar POST a backend funciona      |

---

## ✅ Checklist Final

### Backend (Nataly) ✅

- [ ] `firebase-admin` instalado
- [ ] `FIREBASE_SERVICE_ACCOUNT_KEY` en `.env`
- [ ] Test 1 y 2 funcionan sin errores
- [ ] Celery corriendo
- [ ] Endpoints creados

### Mobile (Luis)

- [ ] `google-services.json` en `android/app/`
- [ ] Gradle configurado (sin errores de sync)
- [ ] Dependencias en `pubspec.yaml`
- [ ] `NotificationService.dart` creado
- [ ] Inicializado en `main.dart`
- [ ] App compila sin errores
- [ ] Token se obtiene de Firebase
- [ ] Token se envía al backend (visible en logs)
- [ ] Test 3: Notificación recibida en dispositivo

---

## 📞 Dudas

- **Luis:** Pregunta a Nataly
- **Nataly:** Revisa Firebase Console o logs

---

**Fin de la documentación.**
