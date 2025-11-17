# 🔗 Configuración de Webhooks en Stripe

**Fecha**: 17/11/2025  
**Estado**: ⏳ EN PROGRESO - Necesita configuración manual en Stripe Dashboard

---

## ❓ ¿Qué es un Webhook?

Un **webhook** es como un **timbre para tu servidor**. Cuando sucede algo en Stripe (un pago completado, un reembolso, etc.), Stripe toca el timbre y **envía un evento POST a tu servidor** para que se entere.

**Sin webhook**: Tu servidor nunca se entera de que un pago fue completado ❌  
**Con webhook**: Tu servidor recibe notificación y activa el tenant ✅

---

## 🎯 En tu caso

Cuando el usuario completa el pago en Stripe Checkout:

```
1. Usuario en Stripe: "Pagar"
2. Stripe procesa la tarjeta
3. ✅ Pago exitoso
4. Stripe envía POST a tu servidor:
   POST http://localhost:8000/api/payments/webhook/
   {
     "type": "checkout.session.completed",
     "data": {...}
   }
5. Tu servidor recibe el evento
6. Tu servidor activa el tenant + envía email
7. Redirige al usuario a /billing/success
```

---

## 📝 Paso 1: Obtener el Webhook Signing Secret

En **Stripe Dashboard**:

1. Ve a **Developers** (en el menú de arriba)
2. Click en **Webhooks**
3. Busca la sección "Endpoints" o "Listening for events"
4. Verás un botón **"+ Add an endpoint"** (o similar)

⚠️ **IMPORTANTE**: Si ves endpoints existentes, puedes tener más de uno (por ambiente: local, staging, producción).

---

## 🔧 Paso 2: Agregar un Nuevo Endpoint (LOCAL)

Para **desarrollo local**, Stripe NO puede alcanzar tu máquina (localhost:8000) directamente desde internet.

Tienes **2 opciones**:

### Opción A: Usar Stripe CLI (Recomendado para DEV) ✅

**Stripe CLI** es una herramienta que:

- Escucha eventos de Stripe en la nube
- Los redirige a tu localhost
- Es perfecto para desarrollo

**Pasos**:

1. **Instala Stripe CLI**:

   - Windows: Descarga desde https://github.com/stripe/stripe-cli/releases
   - O con Chocolatey: `choco install stripe-cli`

2. **Loguéate con Stripe**:

   ```powershell
   stripe login
   ```

   Te pedirá que abras navegador → confirmes que es tu cuenta → generará API key local

3. **Redirige eventos a tu localhost**:

   ```powershell
   stripe listen --forward-to localhost:8000/api/payments/webhook/
   ```

   **Resultado**:

   ```
   > Ready! Your webhook signing secret is: whsec_test_...
   ```

   ⚠️ **COPIA ESE SECRET** - es tu `STRIPE_WEBHOOK_SECRET`

4. **Actualiza tu `.env`**:

   ```
   STRIPE_WEBHOOK_SECRET=whsec_test_...
   ```

5. **Reinicia Django**

Ahora cuando hagas un pago de prueba, Stripe te enviará los eventos directamente a tu localhost! 🎉

---

### Opción B: Agregar Endpoint Público (Para PRODUCCIÓN)

Si tu servidor está en la nube (AWS, Heroku, etc.), puedes:

1. Ve a **Stripe Dashboard** → **Developers** → **Webhooks**
2. Click **"+ Add an endpoint"**
3. URL: `https://tudominio.com/api/payments/webhook/`
4. Selecciona eventos:
   - ✅ `checkout.session.completed`
   - ✅ `charge.refunded`
5. Click **"Add endpoint"**
6. Copia el **Signing secret**
7. Agrega a `.env`:
   ```
   STRIPE_WEBHOOK_SECRET=whsec_live_...
   ```

---

## 🧪 Paso 3: Probar que el Webhook Funciona

### ⚠️ IMPORTANTE: NECESITAS 3 TERMINALES ABIERTAS AL MISMO TIEMPO

**El error más común**: Ejecutar `stripe trigger` sin que Django esté corriendo.

### Con Stripe CLI (Opción A):

**TERMINAL 1** (Stripe CLI escuchando - ABRE PRIMERO):

```powershell
cd d:\1NATALY\Proyectos\clinic_records\cr_backend
stripe listen --forward-to localhost:8000/api/payments/webhook/
```

**Verás**:

```
> Ready! Your webhook signing secret is: whsec_62f37...

Forwarding Events to http://localhost:8000/api/payments/webhook/

Waiting for events... (Ctrl+C to exit)
```

**TERMINAL 2** (Django corriendo - ABRE SEGUNDO):

```powershell
cd d:\1NATALY\Proyectos\clinic_records\cr_backend
.\venv\Scripts\Activate.ps1
python manage.py runserver 8000
```

**Verás**:

```
Starting development server at http://127.0.0.1:8000/
```

**TERMINAL 3** (Simular evento - ABRE TERCERO):

```powershell
stripe trigger checkout.session.completed
```

**Resultado esperado**:

- **Terminal 1 (Stripe CLI)** muestra:
  ```
  [200] POST http://localhost:8000/api/payments/webhook/
  ```
- **Terminal 2 (Django)** muestra:
  ```
  [INFO] Webhook recibido: checkout.session.completed
  ```
- **Terminal 3** muestra:
  ```
  Trigger succeeded! Check dashboard for event details.
  ```

---

## 📋 Resumen: ¿Qué tienes que hacer?

### Para DESARROLLO LOCAL (Ahora):

```
1. Instala Stripe CLI
2. Ejecuta: stripe login
3. Ejecuta: stripe listen --forward-to localhost:8000/api/payments/webhook/
4. Copia el secret: whsec_test_...
5. Agrega a .env: STRIPE_WEBHOOK_SECRET=whsec_test_...
6. Reinicia Django
7. ¡Listo! Tus webhooks están activos
```

### Para PRODUCCIÓN (Después):

```
1. Ve a Stripe Dashboard → Developers → Webhooks
2. Add endpoint: https://tudominio.com/api/payments/webhook/
3. Selecciona eventos
4. Copia signing secret
5. Agrega a .env de producción
6. Deploy
```

---

## 🔐 Verificación de Seguridad

Tu backend ya tiene código para **verificar la firma** del webhook:

**Archivo**: `apps/payments/stripe_config.py`

```python
def verify_webhook_signature(payload, sig_header):
    """Verifica que el evento realmente viene de Stripe"""
    try:
        event = stripe_sdk.Webhook.construct_event(
            payload,
            sig_header,
            settings.STRIPE_WEBHOOK_SECRET  ← NECESITA ESTE SECRET
        )
        return event
    except stripe_sdk.error.SignatureVerificationError:
        raise Exception('Firma de webhook no válida')
```

**Por qué es importante**:

- Sin esta verificación, cualquiera podría simular webhooks falsos
- Con Stripe CLI o endpoint oficial, Stripe firma cada evento
- Tu código rechaza eventos no firmados correctamente

---

## ❓ Preguntas Comunes

**P: ¿Necesito crear múltiples webhooks?**  
R: No, uno es suficiente. Stripe enviará TODOS los eventos configurados al mismo endpoint.

**P: ¿Qué pasa si mi webhook falla?**  
R: Stripe reintentar automáticamente (3 veces más en las próximas horas).

**P: ¿Puedo probar webhooks sin Stripe CLI?**  
R: Sí, en Stripe Dashboard puedes simular eventos manualmente desde la pestaña "Events" (botón "Send test webhook").

**P: ¿El webhook secret es diferente entre TEST y LIVE?**  
R: Sí. Los keys de TEST (`sk_test_`, `pk_test_`) tienen su webhook secret (`whsec_test_`). Los de LIVE tienen otro (`whsec_live_`).

---

## ✅ Checklist Webhook

Para **DESARROLLO LOCAL** con Stripe CLI:

- [ ] Instalé Stripe CLI
- [ ] Ejecuté `stripe login`
- [ ] Ejecuté `stripe listen --forward-to localhost:8000/api/payments/webhook/`
- [ ] Copié el webhook signing secret: `whsec_test_...`
- [ ] Agregué `STRIPE_WEBHOOK_SECRET=whsec_test_...` a `.env`
- [ ] Reinicié Django
- [ ] Ejecuté `stripe trigger checkout.session.completed` para probar
- [ ] Ví logs en Django: `[INFO] Webhook recibido`
- [ ] Todo funciona ✅

---

## 🔗 Próximo Paso

Una vez que completes esta configuración, podrás:

1. Ir a `http://localhost:5173/register`
2. Completa el formulario
3. Redirige a Stripe Checkout
4. Paga con `4242 4242 4242 4242`
5. **Stripe webhooks entra en acción** ✨
6. Email se envía automáticamente
7. Usuario activa cuenta
8. ¡Listo!

---

## 📞 Si tienes problemas

1. Verifica que `STRIPE_WEBHOOK_SECRET` esté en `.env`
2. Verifica que Stripe CLI siga corriendo (`stripe listen ...`)
3. Revisa logs de Django: `[ERROR]` o `[INFO]`
4. En Stripe Dashboard → Events → mira los eventos
5. Si ves `Failed`: haz click y mira el error

¡Avísame cuando lo tengas configurado! 🚀
