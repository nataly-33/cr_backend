# 🔧 TROUBLESHOOTING: Errores Comunes de Webhooks

**Fecha**: 17/11/2025  
**Estado**: Soluciones para errores reportados

---

## ❌ ERROR 1: Connection Refused

```
[ERROR] Failed to POST: Post "http://localhost:8000/api/payments/webhook/":
dial tcp [::1]:8000: connectex: No connection could be made because the
target machine actively refused it.
```

### 🔍 CAUSA

Django **NO está corriendo** en la Terminal 2.

### ✅ SOLUCIÓN

**Terminal 2 DEBE estar ejecutando**:

```powershell
cd d:\1NATALY\Proyectos\clinic_records\cr_backend
.\venv\Scripts\Activate.ps1
python manage.py runserver 8000
```

**Deberías ver**:

```
Starting development server at http://127.0.0.1:8000/
```

**Si no ves eso**: Django no está corriendo.

---

## ⚡ El Flujo Correcto de 3 Terminales

### 🟢 Estado CORRECTO:

```
┌─────────────────────────────────────────────────────────────┐
│ TERMINAL 1: Stripe CLI Escuchando                          │
├─────────────────────────────────────────────────────────────┤
│ $ stripe listen --forward-to localhost:8000/api/...        │
│ > Ready! Your webhook signing secret is: whsec_62f37...    │
│ > Forwarding Events to http://localhost:8000/api/...       │
│ > Waiting for events...                                     │
│ [ABIERTO Y CORRIENDO] ✅                                   │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ TERMINAL 2: Django Corriendo                               │
├─────────────────────────────────────────────────────────────┤
│ $ python manage.py runserver 8000                           │
│ Starting development server at http://127.0.0.1:8000/      │
│ [ABIERTO Y CORRIENDO] ✅                                   │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ TERMINAL 3: Ejecutar Comando de Prueba                     │
├─────────────────────────────────────────────────────────────┤
│ $ stripe trigger checkout.session.completed                │
│ Trigger succeeded!                                          │
│ [EJECUTAR Y CERRAR] ✅                                     │
└─────────────────────────────────────────────────────────────┘
```

### 🔴 Estado INCORRECTO (lo que estaba pasando):

```
┌─────────────────────────────────────────────────────────────┐
│ TERMINAL 1: Stripe CLI Escuchando                          │
├─────────────────────────────────────────────────────────────┤
│ $ stripe listen --forward-to localhost:8000/api/...        │
│ > Ready! Your webhook signing secret is: whsec_62f37...    │
│ > Waiting for events...                                     │
│ [ABIERTO Y CORRIENDO] ✅                                   │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ TERMINAL 2: Django NO CORRIENDO                            │
├─────────────────────────────────────────────────────────────┤
│ $ (vacío, o ejecutando otra cosa)                          │
│ [CERRADO O SIN DJANGO] ❌                                  │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ TERMINAL 3: Ejecutar Comando de Prueba                     │
├─────────────────────────────────────────────────────────────┤
│ $ stripe trigger checkout.session.completed                │
│ [ERROR] Failed to POST: Connection refused ❌              │
└─────────────────────────────────────────────────────────────┘
```

---

## ❌ ERROR 2: Webhook Secret Incorrecto

```
[ERROR] Signature verification failed
```

### 🔍 CAUSA

Tu `.env` tiene el webhook secret ANTIGUO.

### ✅ SOLUCIÓN

1. **Copia el secret NUEVO** de Terminal 1:

   ```
   > Ready! Your webhook signing secret is: whsec_62f37...
                                             ^^^^^^^^^^^
                                             ESTO
   ```

2. **Abre `.env`** y actualiza:

   ```
   STRIPE_WEBHOOK_SECRET=whsec_62f37...
   ```

3. **Reinicia Django** (Ctrl+C en Terminal 2, luego ejecuta de nuevo)

---

## ❌ ERROR 3: Webhook Secret Comienza con `whsec_test_`

### 🔍 ¿Es un Problema?

**NO, es normal**. El formato puede ser:

- `whsec_test_...` (más corto)
- `whsec_62f37...` (más corto, sin `test`)

Ambos son válidos para TEST mode. Lo importante es que empiece con `whsec_`.

---

## ❌ ERROR 4: "Mode LIVE" en Stripe Account

### 🔍 ¿Es un Problema?

**NO, tranquilo**. Lo importante es que tus **claves** sean de TEST:

**Verifica en tu `.env`**:

```
STRIPE_SECRET_KEY=sk_test_...        ← Si empieza con sk_TEST_
STRIPE_PUBLISHABLE_KEY=pk_test_...   ← Si empieza con pk_TEST_
```

Si ambos empiezan con `test`, **estás en TEST mode** ✅

El dashboard puede mostrar "Live" pero son claves de TEST, no importa.

---

## ✅ Verificación Final

Después de que TODO esté configurado:

**Terminal 1**:

```
stripe listen --forward-to localhost:8000/api/payments/webhook/
```

**Terminal 2**:

```
python manage.py runserver 8000
```

**Terminal 3** - Ejecuta estas pruebas:

### Prueba 1: Webhook Básico

```powershell
stripe trigger checkout.session.completed
```

**Esperado en Terminal 1**:

```
[200] POST http://localhost:8000/api/payments/webhook/
```

### Prueba 2: Comprobar Logs en Django

Deberías ver en **Terminal 2**:

```
[INFO] Webhook recibido: checkout.session.completed
```

### Prueba 3: Comprobar que .env tiene el Secret

**Terminal 3**:

```powershell
cd d:\1NATALY\Proyectos\clinic_records\cr_backend
.\venv\Scripts\Activate.ps1
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(os.getenv('STRIPE_WEBHOOK_SECRET'))"
```

**Esperado**:

```
whsec_62f37...
(o whsec_test_...)
```

Si ves `None`, significa que `.env` **no tiene el secret**.

---

## 📊 Estado Actual

| Componente             | Estado          | Acción                            |
| ---------------------- | --------------- | --------------------------------- |
| Stripe CLI             | ✅ Instalado    | Mantener Terminal 1 abierto       |
| Django                 | ❌ NO corriendo | Abrir Terminal 2 y ejecutar       |
| Webhook Secret en .env | ❓ Desconocido  | Copiar de Terminal 1              |
| Prueba de webhook      | ❌ Falló        | Reintentar con Terminal 2 abierto |

---

## 🎯 PRÓXIMO PASO: TESTING REAL

Una vez que `stripe trigger` funcione (veas `[200]`), puedes testear el **flujo real**:

1. **Abre navigador**: `http://localhost:5173/register`
2. **Completa formulario** con EMAIL REAL (recibirás email de activación)
3. **Redirige a Stripe**
4. **Usa tarjeta**: `4242 4242 4242 4242`
5. **En Terminal 1, recibirás eventos**:
   ```
   [200] POST http://localhost:8000/api/payments/webhook/
   ```
6. **En Terminal 2, recibirás logs**:
   ```
   [INFO] Webhook recibido: checkout.session.completed
   [INFO] [WEBHOOK] Procesando registro público: registration_id=1
   [INFO] [WEBHOOK] ✅ Registro 1 pagado. Email enviado a...
   ```
7. **Revisa tu email** → Link de activación
8. ✅ **¡Funciona!**

---

## 📋 Resumen: ¿Qué Tienes que Hacer AHORA?

1. **Terminal 1** (abierto, escuchando):

   ```
   stripe listen --forward-to localhost:8000/api/payments/webhook/
   ```

2. **Copia el webhook secret** que aparece:

   ```
   whsec_62f37...  ← O similar
   ```

3. **Terminal 2** (abierto, Django):

   ```
   python manage.py runserver 8000
   ```

4. **Actualiza `.env`**:

   ```
   STRIPE_WEBHOOK_SECRET=whsec_62f37...
   ```

5. **Reinicia Django** (Ctrl+C en Terminal 2, ejecuta de nuevo)

6. **Terminal 3** (prueba):

   ```
   stripe trigger checkout.session.completed
   ```

7. **Verifica Terminal 1**:
   ```
   [200] POST http://localhost:8000/api/payments/webhook/
   ```

✅ **Si ves `[200]`, ¡está funcionando!**

---

## 🚨 Si TODAVÍA ves errores

1. **¿Django está corriendo?** Verifica Terminal 2:

   ```
   Starting development server at http://127.0.0.1:8000/
   ```

2. **¿El webhook secret está en .env?** Ejecuta:

   ```
   python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(os.getenv('STRIPE_WEBHOOK_SECRET'))"
   ```

3. **¿Reiniciaste Django después de cambiar .env?** (Ctrl+C, ejecuta de nuevo)

4. **¿Está en la carpeta correcta?** Debe estar en:
   ```
   d:\1NATALY\Proyectos\clinic_records\cr_backend\.env
   ```

---

**¡Éxito! Avísame si necesitas ayuda.** 🚀
