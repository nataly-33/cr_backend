# 🔄 Flujo Completo: Registro de Tenant + Stripe Checkout

**Fecha**: 17/11/2025  
**Estado**: ✅ Implementado y listo para probar

---

## 📋 Resumen del Flujo

El usuario sigue estos pasos:

1. **Registra información** (nombre, email, subdominio, teléfono)
2. **Selecciona plan** (Basic, Professional, Enterprise)
3. **Procede al pago** con Stripe Checkout
4. **Completa pago** con tarjeta de prueba (4242 4242 4242 4242)
5. **Recibe email** con link de activación
6. **Activa cuenta** con nueva contraseña
7. **Inicia sesión** con su nuevo usuario

---

## 🔧 Paso a Paso Técnico

### PASO 1: Frontend - Registro Inicial

**Archivo**: `cr_frontend/src/modules/public/pages/RegisterPage.tsx`

El usuario completa el formulario:

```tsx
- tenant_name: "Clínica La Paz"
- subdomain: "lapaz"
- admin_first_name: "Juan"
- admin_last_name: "Pérez"
- admin_email: "juan@example.com"  ← EMAIL PERSONAL (recibirá credenciales)
- admin_phone: "+591 77123456" (opcional)
- plan_id: 2  ← De los planes disponibles
- billing_cycle: "monthly" | "annual"
```

**Validaciones**:

- ✅ Subdominio válido (3+ caracteres, minúsculas, sin espacios)
- ✅ Subdominio único (no existe en BD)
- ✅ Email no registrado en otros tenants
- ✅ Plan válido y activo

---

### PASO 2: Backend - Crear Registro Pendiente

**Endpoint**: `POST /api/tenants/public/register/`

**Petición**:

```json
{
  "tenant_name": "Clínica La Paz",
  "subdomain": "lapaz",
  "admin_first_name": "Juan",
  "admin_last_name": "Pérez",
  "admin_email": "juan@example.com",
  "admin_phone": "+591 77123456",
  "plan_id": 2,
  "billing_cycle": "monthly"
}
```

**Respuesta**:

```json
{
  "registration_id": 123,
  "status": "pending_payment",
  "payment_amount": 50.0,
  "message": "Registro creado exitosamente. Proceda al pago."
}
```

**Base de datos**:

- Crea `TenantRegistration` con status=`pending_payment`

---

### PASO 3: Frontend - Guardar Registro y Crear Sesión Stripe

**Archivo**: `cr_frontend/src/modules/public/services/public.service.ts`

```typescript
// 1. Guardar datos en sessionStorage
sessionStorage.setItem(
  "pendingRegistration",
  JSON.stringify({
    registration_id: 123,
    email: "juan@example.com",
    tenant_name: "Clínica La Paz",
    subdomain: "lapaz",
  })
);

// 2. Crear sesión de Stripe Checkout
const checkoutResponse = await publicApiService.createCheckoutSession({
  registration_id: 123,
  plan_id: 2,
  billing_cycle: "monthly",
  tenant_name: "Clínica La Paz",
  admin_email: "juan@example.com",
});

// 3. Redirigir a Stripe
window.location.href = checkoutResponse.checkout_url;
```

---

### PASO 4: Backend - Crear Sesión de Stripe

**Endpoint**: `POST /api/tenants/public/checkout/`

**Petición**:

```json
{
  "registration_id": 123,
  "plan_id": 2,
  "billing_cycle": "monthly",
  "tenant_name": "Clínica La Paz",
  "admin_email": "juan@example.com"
}
```

**Lógica**:

1. Verifica que `TenantRegistration` exista y esté en `pending_payment`
2. Obtiene el plan de suscripción
3. Calcula precio según ciclo (monthly/annual)
4. Crea sesión de Stripe Checkout con:
   - `line_items` con descripción y precio
   - `customer_email` = admin_email
   - `success_url` = `/billing/success?session_id={id}`
   - `cancel_url` = `/billing/cancel`
   - `metadata` con registration_id, tenant_name, admin_email, billing_cycle, plan_id

**Respuesta**:

```json
{
  "checkout_url": "https://checkout.stripe.com/pay/cs_test_...",
  "session_id": "cs_test_..."
}
```

---

### PASO 5: Stripe Checkout Page

El usuario ve la página de Stripe Checkout:

```
┌─────────────────────────────┐
│ Clínica La Paz              │
│ Professional - $50/month    │
│                             │
│ Email: juan@example.com     │
│ Tarjeta: [____________]     │
│ Mes: [__] Año: [__]         │
│ CVC: [___]                  │
│                             │
│ [  Suscribirse  ]           │
└─────────────────────────────┘
```

**Usuario ingresa TARJETA DE PRUEBA**:

- Número: `4242 4242 4242 4242`
- Mes: `12` (cualquier futuro)
- Año: `25` (o cualquier futuro)
- CVC: `123` (cualquier 3 dígitos)

**Resultado**: ✅ Pago exitoso

---

### PASO 6: Stripe Webhook → Backend

**Endpoint**: `POST /api/payments/webhook/`

Stripe envía evento: `checkout.session.completed`

**Metadata en sesión**:

```json
{
  "registration_id": "123",
  "tenant_name": "Clínica La Paz",
  "admin_email": "juan@example.com",
  "billing_cycle": "monthly",
  "plan_id": "2"
}
```

**Lógica del webhook** (`apps/payments/views.py` `_handle_checkout_completed`):

**CASO: registration_id presente → Nuevo tenant**

1. ✅ Obtiene `TenantRegistration`
2. ✅ Marca como `payment_completed`
3. ✅ Genera `activation_token` aleatorio
4. ✅ **ENVÍA EMAIL** a `admin_email` (juan@example.com) con:
   - Link de activación: `http://localhost:5173/activate/{token}`
   - Nombre de tenant: "Clínica La Paz"
   - Subdominio: "lapaz"
5. ✅ Crea `Payment` record (sin tenant aún)
6. ✅ Crea `Invoice` record
7. ✅ Crear `PaymentAudit` log

**Base de datos después del webhook**:

```
✅ TenantRegistration
   - status: 'payment_completed'
   - payment_intent_id: 'pi_...'
   - activation_token: 'random_token_...'
   - activation_email_sent_at: now()

✅ Payment
   - tenant: null (se asignará en activate_tenant)
   - subscription_plan: Professional
   - amount: 50.00
   - status: 'completed'

✅ Invoice
   - invoice_number: 'REG-123-20251117'
   - status: 'paid'
```

---

### PASO 7: Stripe Redirige a Frontend

Stripe redirige a:

```
http://localhost:5173/billing/success?session_id=cs_test_...
```

**Frontend** (`RegistrationSuccessPage.tsx`):

- Obtiene email y tenant_name de sessionStorage
- Muestra: ✅ "¡Pago Completado!"
- Muestra instrucciones: "Revisa tu email en juan@example.com"
- Botón: "Volver al Inicio"

---

### PASO 8: Usuario Recibe Email

**Email enviado por**: Backend (SendGrid o Django Email)

**Contenido**:

```
Asunto: Bienvenido a Clinic Records - Activa tu cuenta

Cuerpo:
¡Hola Juan!

Tu registro en Clinic Records ha sido completado exitosamente.

Tu clínica: Clínica La Paz
Subdominio: lapaz.clinicalrecords.com
Plan: Professional

Para activar tu cuenta, haz clic en el siguiente enlace:
→ http://localhost:5173/activate/{activation_token}

En el siguiente paso, establece tu contraseña personalizada.

¡Bienvenido!
```

---

### PASO 9: Usuario Activa Cuenta

**URL**: `http://localhost:5173/activate/{activation_token}`

**Archivo**: `cr_frontend/src/modules/public/pages/ActivatePage.tsx`

Usuario ve formulario:

```
┌──────────────────────────────┐
│ Activar tu Cuenta            │
│                              │
│ Clínica La Paz               │
│ lapaz.clinicalrecords.com    │
│                              │
│ Nueva Contraseña: [______]   │
│ Confirmar: [______]          │
│                              │
│ [ Activar Cuenta ]           │
└──────────────────────────────┘
```

**Submit**:

```tsx
await publicApiService.activateTenant({
  activation_token: activation_token,
  new_password: "MiPassword123!",
});
```

---

### PASO 10: Backend - Activar Tenant

**Endpoint**: `POST /api/tenants/public/activate/`

**Lógica** (`apps/tenants/services.py` `TenantRegistrationService.activate_tenant`):

1. ✅ Obtiene `TenantRegistration` con `activation_token`
2. ✅ Verifica status = `payment_completed`
3. ✅ **CREA TENANT**:

   ```python
   Tenant.objects.get_or_create(
       subdomain='lapaz',
       defaults={
           'name': 'Clínica La Paz',
           'subscription_plan': 'pro',  # Professional
           'subscription_status': 'active',
           'email': 'juan@example.com',  # admin_email
           'max_users': 10,  # Del plan Professional
           'max_storage_gb': 50,
       }
   )
   ```

4. ✅ **CREA ADMIN ROLE**:

   ```python
   Role.objects.get_or_create(
       tenant=tenant,
       name='AdminTI',
       defaults={
           'description': 'Administrador del tenant',
           'is_system_role': True
       }
   )
   ```

5. ✅ **CREA ADMIN USER**:

   ```python
   User.objects.get_or_create(
       tenant=tenant,
       email='admin@lapaz.clinicalrecords.com',  # Email de sistema
       defaults={
           'personal_email': 'juan@example.com',  # Email personal ← AQUÍ
           'first_name': 'Juan',
           'last_name': 'Pérez',
           'phone': '+591 77123456',
           'is_active': True,
           'role': admin_role,
       }
   )
   ```

   **Establece contraseña**:

   ```python
   admin_user.set_password('MiPassword123!')
   admin_user.save()
   ```

6. ✅ Actualiza `TenantRegistration`:

   ```python
   registration.tenant = tenant
   registration.status = 'activated'
   registration.activated_at = now()
   registration.save()
   ```

7. ✅ Retorna:
   ```json
   {
     "status": "activated",
     "tenant_name": "Clínica La Paz",
     "login_url": "https://lapaz.clinicalrecords.com/login",
     "message": "Tenant activado exitosamente. Ya puedes iniciar sesión."
   }
   ```

---

### PASO 11: Frontend - Confirmación

**Página**: `ActivatePage` muestra:

```
✅ ¡Cuenta Activada!

Tu clínica Clínica La Paz está lista para usar.

URL de login: https://lapaz.clinicalrecords.com/login
Usuario: admin@lapaz.clinicalrecords.com
```

---

### PASO 12: Usuario Inicia Sesión

**URL**: `https://lapaz.clinicalrecords.com/login` (o http://localhost:5173/login)

**Credenciales**:

- Email: `admin@lapaz.clinicalrecords.com` (email de sistema)
- Contraseña: `MiPassword123!` (la que estableció)

**Backend verifica**:

- ✅ Usuario existe
- ✅ Contraseña correcta
- ✅ Usuario activo
- ✅ Tenant activo con suscripción

**Respuesta**: JWT token

**Frontend redirige a**: `/dashboard` con tenant activo

---

## 📊 Base de Datos Final

```sql
-- TENANTS
SELECT * FROM tenants_tenant
WHERE subdomain = 'lapaz';
→ id, name='Clínica La Paz', subscription_plan='pro',
  subscription_status='active', stripe_customer_id=NULL

-- USERS
SELECT * FROM users
WHERE email = 'admin@lapaz.clinicalrecords.com';
→ id, email='admin@lapaz.clinicalrecords.com',
  personal_email='juan@example.com',
  first_name='Juan', last_name='Pérez',
  tenant_id=<tenant_id>, is_active=True

-- PAYMENTS
SELECT * FROM payments_payment
WHERE registration_id = 123;
→ id, stripe_session_id='cs_test_...',
  status='completed', amount=50.00

-- INVOICES
SELECT * FROM payments_invoice
WHERE invoice_number LIKE 'REG-123-%';
→ id, invoice_number='REG-123-20251117',
  status='paid', total=50.00

-- REGISTRATIONS
SELECT * FROM tenants_tenantregistration
WHERE id = 123;
→ id, status='activated', tenant_id=<tenant_id>,
  activation_token=NULL (usado), activated_at=now()
```

---

## 🧪 Testing Checklist

- [ ] Formulario de registro valida correctamente
- [ ] Subdominio check funciona
- [ ] Email check funciona
- [ ] POST `/api/tenants/public/register/` crea registro
- [ ] POST `/api/tenants/public/checkout/` retorna URL de Stripe
- [ ] Redirige a Stripe Checkout
- [ ] Tarjeta de prueba (4242...) se acepta
- [ ] Webhook recibe evento
- [ ] TenantRegistration marca como `payment_completed`
- [ ] Email se envía a juan@example.com
- [ ] Redirige a `/billing/success?session_id=...`
- [ ] Muestra página de éxito con datos correctos
- [ ] Link de activación funciona
- [ ] Usuario puede establecer contraseña
- [ ] Tenant se crea correctamente
- [ ] Admin user se crea correctamente
- [ ] Usuario puede iniciar sesión
- [ ] Dashboard carga con tenant correcto

---

## ❌ Tarjeta de Prueba RECHAZADA

Para probar rechazo:

```
Número: 4000 0000 0000 0002
Mes: 12
Año: 25
CVC: 123
```

**Resultado**: Stripe rechaza el pago
**Frontend**: Redirige a `/billing/cancel`
**BD**: NO se crea pago

---

## 🔐 Notas de Seguridad

✅ **personal_email**:

- Se usa para enviar email de activación
- Se guarda en User model
- Diferente del `email` (que es admin@subdomain.com)
- El usuario verifica propiedad del email al hacer clic en link de activación

✅ **activation_token**:

- Aleatorio y único
- Se usa una sola vez
- Expira después de usar (se borra)
- No se puede reutilizar

✅ **Stripe**:

- En TEST: no cobr dinero real
- Verifica firma de webhook con STRIPE_WEBHOOK_SECRET
- Webhook endpoint protegido por firma de Stripe

✅ **Contraseña**:

- Se establece en PASO 9 (activación)
- Hasheada con Django PBKDF2
- Mínimo 8 caracteres recomendado

---

## 📝 Resumen Visual

```
┌─ FRONTEND ─────────────────────────────────┐
│  1. Formulario Registro                    │ → PASO 1
│  2. Validación Subdominio/Email            │ → PASO 1
│  3. Crea Registro (POST)                   │ → PASO 2
│  4. Crea Sesión Stripe (POST)              │ → PASO 3-4
│  5. window.location.href = checkout_url    │ → PASO 5
│                                            │
│  ☆ USUARIO PAGA EN STRIPE ☆               │ → PASO 5
│                                            │
│  6. Redirige /billing/success              │ → PASO 7
│  7. Muestra confirmación                   │ → PASO 7
│                                            │
│  ☆ USUARIO REVISA EMAIL ☆                 │ → PASO 8
│                                            │
│  8. Hace clic en link de activación        │ → PASO 9
│  9. Establece contraseña                   │ → PASO 9
│ 10. Tenant activado (POST)                 │ → PASO 10
│ 11. Redirige a /login                      │ → PASO 11
│ 12. Inicia sesión                          │ → PASO 12
│ 13. Accede a dashboard                     │ → PASO 12
└────────────────────────────────────────────┘

┌─ BACKEND ──────────────────────────────────┐
│  PASO 2: POST /register                    │
│  → Crea TenantRegistration                 │
│  → status = 'pending_payment'              │
│                                            │
│  PASO 4: POST /checkout                    │
│  → Crea sesión de Stripe                   │
│  → Devuelve checkout_url                   │
│                                            │
│  PASO 6: Webhook checkout.session.completed│
│  → Obtiene registration del metadata       │
│  → Marca como 'payment_completed'          │
│  → Genera activation_token                 │
│  → ENVÍA EMAIL con link de activación      │
│  → Crea Payment y Invoice                  │
│                                            │
│  PASO 10: POST /activate                   │
│  → Valida activation_token                 │
│  → CREA Tenant                             │
│  → CREA Admin Role                         │
│  → CREA Admin User                         │
│  → personal_email = admin_email del form   │
│  → Marca TenantRegistration como activated│
│                                            │
│  PASO 12: POST /login                      │
│  → Valida email + password                 │
│  → Devuelve JWT token                      │
└────────────────────────────────────────────┘
```

---

## 🚀 ¡LISTO PARA PROBAR!

Sigue estos pasos exactos:

1. Abre `http://localhost:5173/register`
2. Llena el formulario:
   - Nombre: "Clínica Test"
   - Subdominio: "testclinic2025"
   - Nombres: Test / User
   - Email: **tu email real** (gmail, outlook, etc.)
   - Teléfono: +591 77123456
   - Plan: Professional
3. Haz clic "Crear Cuenta y Proceder al Pago"
4. Verás Stripe Checkout
5. Ingresa tarjeta: `4242 4242 4242 4242`
6. Completa el pago
7. ¡Recibe email de activación!
8. Activa cuenta y comienza

¿Problemas? Revisar logs en:

- Backend: `cr_backend/logs/`
- Terminal Django: `http://localhost:8000` logs
- Webhook de Stripe: Dashboard → Developers → Webhooks

| Campo      | Valor                         |
| ---------- | ----------------------------- |
| **Número** | `4242 4242 4242 4242`         |
| **Mes**    | `12` (cualquier mes futuro)   |
| **Año**    | `25` (o cualquier año futuro) |
| **CVC**    | `123` (cualquier 3 dígitos)   |
