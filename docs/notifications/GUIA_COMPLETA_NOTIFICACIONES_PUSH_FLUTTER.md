# 📱 GUÍA COMPLETA - Notificaciones Push en Flutter

**Fecha:** 17/11/2025
**Estado:** ✅ Implementación Completada
**Para:** Nataly - Testing en dispositivo físico

---

## 🎯 Lo que se Implementó

### ✅ Configuración Completa

1. **Gradle (Android)**:
   - Firebase plugin agregado en `build.gradle.kts` (root)
   - Firebase dependencies en `app/build.gradle.kts`
   - Google Services plugin configurado

2. **Dependencias Flutter**:
   - `firebase_core: ^2.24.2`
   - `firebase_messaging: ^14.7.9`
   - `flutter_local_notifications: ^16.3.0`

3. **Permisos Android**:
   - `INTERNET`
   - `POST_NOTIFICATIONS`

4. **Código Flutter**:
   - `NotificationService` - Gestiona FCM
   - `NotificationBloc` - Estado de notificaciones
   - `NotificationRemoteDataSource` - Comunicación con backend
   - Integración en `main.dart`
   - Eliminación automática de token en logout

---

## 🚀 PASOS PARA PROBAR (Orden Estricto)

### 1️⃣ Instalar Dependencias de Flutter

Abre una terminal en la carpeta del proyecto móvil:

```bash
# Navegar a la carpeta del proyecto móvil
cd d:\1Nataly\Proyectos\clinic_records\cr_movil

# Instalar todas las dependencias (esto descargará Firebase y todas las librerías)
flutter pub get
```

**Resultado esperado:**
```
Running "flutter pub get" in cr_movil...
Resolving dependencies...
+ firebase_core 2.24.2
+ firebase_messaging 14.7.9
+ flutter_local_notifications 16.3.0
...
Changed X dependencies!
```

---

### 2️⃣ Verificar que google-services.json está en su lugar

```bash
# Desde d:\1Nataly\Proyectos\clinic_records\cr_movil
dir android\app\google-services.json
```

**Debe mostrar:**
```
google-services.json
```

Si NO aparece, copia el archivo manualmente:
- Origen: (obtener de Firebase Console)
- Destino: `d:\1Nataly\Proyectos\clinic_records\cr_movil\android\app\google-services.json`

---

### 3️⃣ Limpiar y Reconstruir el Proyecto

```bash
# Desde d:\1Nataly\Proyectos\clinic_records\cr_movil

# Limpiar build anterior
flutter clean

# Obtener dependencias de nuevo
flutter pub get

# Verificar que no hay errores
flutter doctor
```

**`flutter doctor` debe mostrar:**
```
Doctor summary (to see all details, run flutter doctor -v):
[✓] Flutter (Channel stable, 3.x.x)
[✓] Android toolchain - develop for Android devices
[✓] Chrome - develop for the web
[✓] Visual Studio Code
[!] Android Studio (si no lo tienes, está bien)
[✓] Connected device (1 available)
```

---

### 4️⃣ Conectar tu Celular Android

**Opciones:**

#### Opción A: USB (Recomendado para primera prueba)

1. **Habilitar Modo Desarrollador en tu celular:**
   - Ve a `Ajustes > Acerca del teléfono`
   - Toca 7 veces en `Número de compilación`
   - Verás el mensaje "Eres un desarrollador"

2. **Habilitar Depuración USB:**
   - Ve a `Ajustes > Opciones de desarrollador`
   - Activa `Depuración USB`

3. **Conectar cable USB:**
   - Conecta tu celular a la PC con el cable USB
   - En el celular aparecerá: "¿Permitir depuración USB?"
   - Marca "Permitir siempre desde este equipo" y toca `Permitir`

4. **Verificar conexión:**

```bash
# Desde d:\1Nataly\Proyectos\clinic_records\cr_movil
flutter devices
```

**Debe mostrar tu dispositivo:**
```
Found 2 connected devices:
  SM G950F (mobile) • 1234567890ABCDEF • android-arm64 • Android 11 (API 30)
  Chrome (web)      • chrome           • web-javascript • Google Chrome 120
```

#### Opción B: WiFi (Avanzado)

```bash
# 1. Conecta por USB primero
adb tcpip 5555

# 2. Desconecta el cable

# 3. Averigua la IP de tu celular (en Ajustes > Acerca del teléfono > Estado)
# Ejemplo: 192.168.1.50

# 4. Conecta por WiFi
adb connect 192.168.1.50:5555

# 5. Verifica
flutter devices
```

---

### 5️⃣ Compilar y Ejecutar en tu Celular

```bash
# Desde d:\1Nataly\Proyectos\clinic_records\cr_movil

# Compilar e instalar en modo debug
flutter run --debug
```

**Esto va a:**
1. Compilar la app (tarda 2-5 minutos la primera vez)
2. Instalar en tu celular
3. Ejecutar la app
4. Mostrar logs en la terminal

**Logs importantes a buscar:**
```
🔧 Inicializando NotificationService...
✅ Firebase inicializado
✅ Permisos de notificación concedidos
📱 Token FCM obtenido: dE7X8Y9Z1A2B3C4D5E...
📤 Enviando token FCM al backend...
✅ Token FCM enviado al backend correctamente
✅ NotificationService inicializado correctamente
```

---

### 6️⃣ Verificar que el Token se Guardó en el Backend

#### Opción A: Desde Django Admin

1. Abre en tu navegador:
   ```
   http://localhost:8000/admin
   ```

2. Login como admin

3. Ve a `Accounts > Users`

4. Busca tu usuario (el que usaste para login en la app)

5. Verifica que el campo `FCM Token` tiene un valor largo:
   ```
   dE7X8Y9Z1A2B3C4D5E6F7G8H9I0J1K2L3M4N5O...
   ```

#### Opción B: Desde Django Shell

```bash
# Terminal separada
cd d:\1Nataly\Proyectos\clinic_records\cr_backend
.\venv\Scripts\Activate.ps1
python manage.py shell
```

```python
from apps.accounts.models import User

# Buscar tu usuario
user = User.objects.get(email='tu-email@ejemplo.com')

# Ver el token
print(f"Token FCM: {user.fcm_token}")

# Debería mostrar un token largo
# Si muestra "None" o vacío, el token NO se guardó
```

---

### 7️⃣ Probar Enviando una Notificación desde el Backend

#### Opción A: Usando Django Shell (Manual)

```bash
# En terminal del backend
cd d:\1Nataly\Proyectos\clinic_records\cr_backend
.\venv\Scripts\Activate.ps1
python manage.py shell
```

```python
import os
import json
import firebase_admin
from firebase_admin import credentials, messaging
from apps.accounts.models import User

# 1. Inicializar Firebase (si no está inicializado)
cred_json = os.getenv('FIREBASE_SERVICE_ACCOUNT_KEY')
if cred_json and not firebase_admin._apps:
    cred_dict = json.loads(cred_json)
    firebase_admin.initialize_app(credentials.Certificate(cred_dict))
    print("✅ Firebase inicializado")

# 2. Obtener el token FCM de tu usuario
user = User.objects.get(email='tu-email@ejemplo.com')
token = user.fcm_token
print(f"📱 Token FCM: {token[:30]}...")

# 3. Crear y enviar notificación de prueba
message = messaging.Message(
    notification=messaging.Notification(
        title='🎉 ¡Prueba de Notificación!',
        body='Si ves esto, las notificaciones push funcionan correctamente',
    ),
    data={
        'type': 'test',
        'timestamp': '2025-11-17T10:00:00Z'
    },
    token=token,
)

response = messaging.send(message)
print(f"✅ Notificación enviada: {response}")
```

**En tu celular deberías ver:**
- Si la app está CERRADA: Notificación en la bandeja
- Si la app está ABIERTA: Notificación local dentro de la app

#### Opción B: Crear un Documento (Automático)

1. **Asegúrate de que Celery está corriendo:**

```bash
# Terminal 1: Backend
cd d:\1Nataly\Proyectos\clinic_records\cr_backend
.\venv\Scripts\Activate.ps1
python manage.py runserver

# Terminal 2: Celery Worker
cd d:\1Nataly\Proyectos\clinic_records\cr_backend
.\venv\Scripts\Activate.ps1
.\run_celery_worker.ps1

# Terminal 3: Celery Beat
cd d:\1Nataly\Proyectos\clinic_records\cr_backend
.\venv\Scripts\Activate.ps1
.\run_celery_beat.ps1
```

2. **Login en el frontend React como Doctor:**
   - URL: `http://localhost:5173/login`
   - Usuario: doctor@hospital.com
   - Password: tu password

3. **Crear un documento:**
   - Ve a Documentos → Subir Documento
   - Completa el formulario
   - Guarda

4. **En tu celular Android deberías recibir:**
   ```
   📄 Documento creado
   Dr. [Nombre] creó "Nombre del documento" ([Tipo]) de [Paciente]
   ```

---

### 8️⃣ Probar Notificación en Diferentes Estados

#### Test 1: App CERRADA
1. Cierra completamente la app (swipe desde recientes)
2. Envía notificación desde backend (Opción A del paso 7)
3. **Resultado esperado:** Notificación aparece en la bandeja

#### Test 2: App en BACKGROUND
1. Abre la app
2. Presiona botón Home (app va a background)
3. Envía notificación
4. **Resultado esperado:** Notificación en bandeja

#### Test 3: App en FOREGROUND
1. Mantén la app abierta y visible
2. Envía notificación
3. **Resultado esperado:** Notificación local dentro de la app

---

## 🔍 Verificación de Logs

### En la Terminal de Flutter (donde hiciste `flutter run`)

Busca estos mensajes:

```bash
# Al iniciar la app
✅ Firebase inicializado
✅ Permisos de notificación concedidos
📱 Token FCM obtenido: dE7X8Y9Z...
📤 Enviando token FCM al backend...
✅ Token FCM enviado al backend correctamente

# Al recibir notificación (app en foreground)
📲 Mensaje en foreground: 🎉 ¡Prueba de Notificación!
✅ Notificación local mostrada

# Al tocar notificación
👆 Usuario tocó notificación: {type: test, ...}
```

### En el Backend (Terminal 1)

```bash
# Al guardar token
POST /api/accounts/users/update_fcm_token/ 200
```

### En Celery Worker (Terminal 2)

```bash
# Al enviar notificación
[INFO] Notification created: <uuid> (document.created/push) for admin@hospital.com
[INFO] Sending push notification...
[INFO] Push notification sent successfully
```

---

## 🐛 Solución de Problemas

### ❌ Error: "No se encontró google-services.json"

**Síntoma:**
```
File google-services.json is missing. The Google Services Plugin cannot function without it.
```

**Solución:**
```bash
# Verificar que el archivo existe
dir d:\1Nataly\Proyectos\clinic_records\cr_movil\android\app\google-services.json

# Si no existe, copiarlo desde Firebase Console
# Luego:
flutter clean
flutter pub get
flutter run
```

---

### ❌ Error: "firebase_core no está instalado"

**Síntoma:**
```
Error: Could not resolve the package 'firebase_core'
```

**Solución:**
```bash
cd d:\1Nataly\Proyectos\clinic_records\cr_movil
flutter clean
flutter pub get
```

---

### ❌ Error: "Permisos denegados"

**Síntoma:**
En logs de Flutter:
```
❌ Permisos de notificación denegados
```

**Solución:**
1. En tu celular, ve a `Ajustes > Aplicaciones > CliniDocs`
2. Toca `Permisos`
3. Habilita `Notificaciones`
4. Cierra y reabre la app

---

### ❌ Token no se guarda en backend

**Síntoma:**
```python
# En Django shell
user.fcm_token
# Resultado: None
```

**Posibles causas:**

1. **Backend no está corriendo:**
   ```bash
   cd d:\1Nataly\Proyectos\clinic_records\cr_backend
   python manage.py runserver
   ```

2. **Usuario no está autenticado en la app:**
   - Haz login en la app móvil
   - Verifica que aparece la pantalla principal

3. **Error de red:**
   - Verifica logs en Flutter
   - Busca errores tipo "Connection refused" o "Network error"
   - Si ves esos errores, verifica:
     - Backend está corriendo en `localhost:8000`
     - Firewall no bloquea la conexión

---

### ❌ No llegan notificaciones

**Posibles causas:**

1. **Token no está guardado:**
   - Verifica en Django admin que el usuario tiene `fcm_token`

2. **Firebase credentials incorrectas:**
   ```bash
   # Verificar en .env
   echo $FIREBASE_SERVICE_ACCOUNT_KEY
   ```

3. **Celery no está corriendo:**
   - Las notificaciones automáticas necesitan Celery
   - Verifica que `run_celery_worker.ps1` está ejecutándose

4. **Token expiró:**
   - Desinstala la app
   - Reinstala con `flutter run`
   - El token se regenerará

---

## 📊 Estados de Notificación

### En el Backend (modelo Notification)

| Estado     | Descripción                           |
| ---------- | ------------------------------------- |
| `queued`   | Notificación creada, esperando envío  |
| `sent`     | Enviada a Firebase                    |
| `delivered`| Firebase confirmó entrega             |
| `read`     | Usuario leyó la notificación (in-app) |

### En la App Móvil

| Estado      | Comportamiento                         |
| ----------- | -------------------------------------- |
| `foreground`| Muestra notificación local dentro de la app |
| `background`| Notificación en bandeja del sistema  |
| `terminated`| Notificación en bandeja (app cerrada)|

---

## 🎯 Tipos de Notificaciones Implementadas

Según [GUIA_NOTIFICACIONES_Y_OCR.md](d:\1Nataly\Proyectos\clinic_records\cr_backend\docs\notifications\GUIA_NOTIFICACIONES_Y_OCR.md):

### Documentos
- ✅ `document.created` - Documento creado
- ✅ `document.updated` - Documento actualizado
- ✅ `document.deleted` - Documento eliminado (CRÍTICO)

### Historias Clínicas
- ✅ `clinical_record.created` - Historia creada
- ✅ `clinical_record.updated` - Historia actualizada
- ✅ `clinical_record.deleted` - Historia eliminada (CRÍTICO)

### Formularios Clínicos
- ✅ `clinical_form.created` - Formulario creado
- ✅ `clinical_form.updated` - Formulario actualizado
- ✅ `clinical_form.deleted` - Formulario eliminado (CRÍTICO)

---

## 📱 Comandos de Testing Rápido

### Compilar para Release (APK para distribución)

```bash
cd d:\1Nataly\Proyectos\clinic_records\cr_movil

# Generar APK
flutter build apk --release

# El APK estará en:
# build\app\outputs\flutter-apk\app-release.apk
```

### Instalar APK manualmente en celular

```bash
# Desde d:\1Nataly\Proyectos\clinic_records\cr_movil
adb install build\app\outputs\flutter-apk\app-release.apk
```

### Ver logs en tiempo real

```bash
# Terminal separada, mientras la app está corriendo
flutter logs

# O con adb directamente
adb logcat | findstr "Flutter"
```

### Desinstalar app del celular

```bash
adb uninstall com.clinidocs.clinidocs_mobile
```

---

## ✅ Checklist Final

### Backend
- [ ] `firebase-admin` instalado
- [ ] `FIREBASE_SERVICE_ACCOUNT_KEY` en `.env`
- [ ] Backend corriendo en `localhost:8000`
- [ ] Celery Worker corriendo
- [ ] Celery Beat corriendo

### Mobile
- [ ] `google-services.json` en `android/app/`
- [ ] `flutter pub get` ejecutado sin errores
- [ ] Celular conectado (USB o WiFi)
- [ ] App instalada y corriendo
- [ ] Login exitoso en la app
- [ ] Token FCM visible en logs
- [ ] Token guardado en base de datos (verificado)

### Testing
- [ ] Notificación enviada manualmente (Django shell)
- [ ] Notificación recibida en celular (app cerrada)
- [ ] Notificación recibida (app en background)
- [ ] Notificación recibida (app en foreground)
- [ ] Notificación automática al crear documento
- [ ] Token eliminado correctamente al hacer logout

---

## 🎉 ¡Todo Listo!

Si completaste todos los pasos y los checkboxes están marcados, **las notificaciones push están funcionando al 100%**.

### Próximos Pasos

1. **Testing en producción:**
   - Compila APK release: `flutter build apk --release`
   - Distribuye a usuarios para testing beta

2. **Optimizaciones:**
   - Agregar iconos personalizados para cada tipo de notificación
   - Implementar navegación al tocar notificación
   - Agregar sonidos personalizados

3. **Monitoreo:**
   - Revisar logs de Celery para ver notificaciones enviadas
   - Monitorear Firebase Console para estadísticas de entrega

---

**Documentación creada:** 17/11/2025
**Última actualización:** 17/11/2025
**Versión:** 1.0.0
