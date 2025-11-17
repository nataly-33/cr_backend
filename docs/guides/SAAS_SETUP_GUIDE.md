# 🚀 GUÍA COMPLETA: IMPLEMENTACIÓN SISTEMA SAAS MULTITENANT

## 📋 RESUMEN DE IMPLEMENTACIÓN

Este documento detalla la implementación completa del sistema SaaS multitenant con:

- ✅ Planes de suscripción (Basic $1, Professional $19, Enterprise $49)
- ✅ Landing page pública con planes
- ✅ Registro de nuevos tenants
- ✅ Simulación de pagos (desarrollo)
- ✅ Sistema de emails con SendGrid (producción)
- ✅ Activación con nueva contraseña
- ✅ Integración con Stripe (producción)

---

## 🏗️ ARQUITECTURA DEL FLUJO SAAS

```
1. Usuario visita landing page (/)
   └─> Ve planes de suscripción
   └─> Selecciona un plan

2. Usuario se registra (/register)
   └─> Completa formulario: nombre hospital, subdomain, datos admin
   └─> POST /api/public/register/
   └─> Se crea TenantRegistration (status: pending_payment)

3. Simulación de pago (desarrollo) o pago real (producción)
   └─> POST /api/public/payments/simulate/{registration_id}/
   └─> Stripe webhook (producción)
   └─> Status cambia a: payment_completed

4. Email automático con credenciales
   └─> Email enviado a admin_email personal
   └─> Contiene: subdomain, email interno (admin@hospital-santacruz.com), token de activación
   └─> Link para establecer contraseña

5. Usuario activa cuenta (/activate/{token})
   └─> Usuario establece su propia contraseña
   └─> POST /api/public/activate/
   └─> Se crea: Tenant + Roles + Usuario Admin
   └─> Status: activated

6. Redirige a login con credenciales
   └─> Email: admin@hospital-santacruz.com
   └─> Password: la que el usuario eligió
```

---

## 📦 ARCHIVOS IMPLEMENTADOS

### Backend:

1. **apps/tenants/models.py** - SubscriptionPlan y TenantRegistration
2. **apps/tenants/services.py** - TenantRegistrationService (lógica completa)
3. **apps/tenants/serializers.py** - Serializers para registro público
4. **apps/tenants/views.py** - APIs públicas (sin autenticación)
5. **apps/tenants/urls.py** - Rutas públicas
6. **scripts/seed_subscription_plans.py** - Seeder de planes de pago
7. **apps/tenants/templates/emails/tenant_activation.html** - Template email

### Frontend:

1. **src/modules/public/pages/LandingPage.tsx** - Landing page pública
2. **src/modules/public/pages/RegisterPage.tsx** - Registro de tenant
3. **src/modules/public/pages/ActivationPage.tsx** - Activación con contraseña
4. **src/modules/public/services/public.service.ts** - Servicios públicos
5. **src/modules/public/types/index.ts** - Tipos TypeScript
6. **src/core/routes/index.tsx** - Rutas públicas (sin auth)

---

## 🔧 CONFIGURACIÓN BACKEND

### 1. Instalar dependencias (si faltan)

```bash
cd cr_backend
pip install stripe  # Para pagos reales
```

### 2. Variables de entorno (.env)

```env
# Generales
FRONTEND_URL=http://localhost:5173
BASE_DOMAIN=localhost  # En prod: clinidocs.com

# SendGrid (Producción)
SENDGRID_API_KEY=your_sendgrid_api_key
DEFAULT_FROM_EMAIL=noreply@clinidocs.com
SENDGRID_ENABLED=False  # True en producción

# Stripe (Producción)
STRIPE_SECRET_KEY=your_stripe_secret_key
STRIPE_PUBLISHABLE_KEY=your_stripe_publishable_key
STRIPE_WEBHOOK_SECRET=your_webhook_secret
STRIPE_ENABLED=False  # True en producción
```

### 3. Crear migraciones

```bash
python manage.py makemigrations tenants
python manage.py migrate
```

### 4. Ejecutar seeder de planes

```bash
python scripts/seed_subscription_plans.py
```

**Planes creados:**

- 📦 **Basic** ($1/mes, $10/año) - 10 users, 500 pacientes, 50GB
- 💼 **Professional** ($19/mes, $190/año) - 50 users, 2000 pacientes, 200GB
- 🏢 **Enterprise** ($49/mes, $490/año) - 200 users, 10000 pacientes, 1000GB

### 5. Registrar URLs en config/urls.py

```python
urlpatterns = [
    # ...
    path('api/public/', include('apps.tenants.urls')),  # Rutas públicas
]
```

---

## 🎨 CONFIGURACIÓN FRONTEND

### 1. Instalar dependencias (si faltan)

```bash
cd cr_frontend
npm install
```

### 2. Variables de entorno (.env)

```env
VITE_API_URL=http://localhost:8000/api
VITE_STRIPE_PUBLISHABLE_KEY=your_stripe_public_key  # Para producción
```

### 3. Actualizar rutas (ya implementado)

```tsx
// src/core/routes/index.tsx
const routes = [
  { path: "/", element: <LandingPage />, public: true },
  { path: "/register", element: <RegisterPage />, public: true },
  { path: "/activate/:token", element: <ActivationPage />, public: true },
  { path: "/login", element: <LoginPage />, public: true },
  // ... rutas privadas
];
```

---

## 📧 CONFIGURACIÓN SENDGRID (PRODUCCIÓN)

### Paso 1: Crear cuenta en SendGrid

1. Ve a https://sendgrid.com/
2. Crea cuenta gratuita (100 emails/día)
3. Verifica tu email

### Paso 2: Crear API Key

1. Settings → API Keys → Create API Key
2. Tipo: Full Access
3. Nombre: "CliniDocs Production"
4. Copia la clave (solo se muestra una vez)

### Paso 3: Verificar dominio (para producción)

1. Settings → Sender Authentication → Verify Single Sender
2. O mejor: Authenticate Your Domain (dominio propio)
3. Completa datos:
   - From Email: noreply@clinidocs.com
   - From Name: CliniDocs
   - Reply To: support@clinidocs.com

### Paso 4: Crear plantilla de email (opcional)

**Archivo:** `apps/tenants/templates/emails/tenant_activation.html`

```html
<!DOCTYPE html>
<html>
  <head>
    <meta charset="UTF-8" />
    <title>Activa tu cuenta en CliniDocs</title>
  </head>
  <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
      <h1 style="color: #4F46E5;">¡Bienvenido a CliniDocs!</h1>

      <p>Hola <strong>{{ admin_name }}</strong>,</p>

      <p>
        Tu registro en CliniDocs ha sido completado exitosamente. A continuación
        encontrarás la información de tu cuenta:
      </p>

      <div
        style="background: #F3F4F6; padding: 20px; border-radius: 8px; margin: 20px 0;"
      >
        <h3 style="margin-top: 0;">Datos de tu cuenta</h3>
        <p><strong>Hospital/Clínica:</strong> {{ tenant_name }}</p>
        <p><strong>Subdomain:</strong> {{ subdomain }}</p>
        <p><strong>Plan:</strong> {{ plan_name }}</p>
        <p>
          <strong>Email de acceso:</strong> admin@{{ subdomain }}.clinidocs.com
        </p>
      </div>

      <h3>Importante: Establece tu contraseña</h3>
      <p>
        Para activar tu cuenta, haz clic en el siguiente botón y establece tu
        contraseña personalizada:
      </p>

      <div style="text-align: center; margin: 30px 0;">
        <a
          href="{{ activation_url }}"
          style="background: #4F46E5; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; display: inline-block;"
        >
          Activar mi cuenta
        </a>
      </div>

      <p style="font-size: 14px; color: #666;">
        Si el botón no funciona, copia y pega este enlace en tu navegador:<br />
        <a href="{{ activation_url }}">{{ activation_url }}</a>
      </p>

      <p style="font-size: 14px; color: #666;">
        Este enlace expira en 48 horas por seguridad.
      </p>

      <hr
        style="margin: 40px 0; border: none; border-top: 1px solid #E5E7EB;"
      />

      <p style="font-size: 12px; color: #999;">
        Si no solicitaste esta cuenta, puedes ignorar este email.<br />
        CliniDocs - Sistema de Gestión Documental<br />
        <a href="{{ login_url }}">{{ login_url }}</a>
      </p>
    </div>
  </body>
</html>
```

### Paso 5: Configurar en Django

```python
# config/settings/production.py
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.sendgrid.net'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'apikey'  # Literalmente "apikey"
EMAIL_HOST_PASSWORD = os.getenv('SENDGRID_API_KEY')
DEFAULT_FROM_EMAIL = 'noreply@clinidocs.com'
```

### Paso 6: Test de envío

```python
# En Django shell
python manage.py shell

from django.core.mail import send_mail
send_mail(
    'Test Email',
    'Este es un email de prueba',
    'noreply@clinidocs.com',
    ['tu_email@gmail.com'],
    fail_silently=False,
)
# Si no da error, está configurado correctamente
```

---

## 💳 CONFIGURACIÓN STRIPE (PAGOS REALES)

### Paso 1: Crear cuenta en Stripe

1. Ve a https://stripe.com/
2. Crea cuenta
3. Verifica email y teléfono

### Paso 2: Obtener API Keys

1. Developers → API Keys
2. **Test Mode:**
   - Publishable key: `pk_test_...`
   - Secret key: `sk_test_...`
3. **Live Mode (producción):**
   - Publishable key: `pk_live_...`
   - Secret key: `sk_live_...`

### Paso 3: Crear productos y precios

```python
# Script para crear productos en Stripe
import stripe
from django.conf import settings

stripe.api_key = settings.STRIPE_SECRET_KEY

# Producto Basic
product_basic = stripe.Product.create(
    name='CliniDocs Basic',
    description='Plan básico para clínicas pequeñas'
)

price_basic_monthly = stripe.Price.create(
    product=product_basic.id,
    unit_amount=100,  # $1.00 en centavos
    currency='usd',
    recurring={'interval': 'month'}
)

price_basic_yearly = stripe.Price.create(
    product=product_basic.id,
    unit_amount=1000,  # $10.00
    currency='usd',
    recurring={'interval': 'year'}
)

# Guardar IDs en SubscriptionPlan
plan = SubscriptionPlan.objects.get(slug='basic')
plan.stripe_product_id = product_basic.id
plan.stripe_price_id_monthly = price_basic_monthly.id
plan.stripe_price_id_yearly = price_basic_yearly.id
plan.save()
```

### Paso 4: Configurar Webhooks

1. Developers → Webhooks → Add endpoint
2. URL: `https://tudominio.com/api/public/payments/webhook/`
3. Eventos a escuchar:
   - `payment_intent.succeeded`
   - `payment_intent.payment_failed`
   - `customer.subscription.created`
   - `customer.subscription.deleted`
4. Copiar **Signing Secret** (whsec\_...)

### Paso 5: Implementar webhook en Django

```python
# apps/tenants/views.py
import stripe
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def stripe_webhook(request):
    """Webhook para recibir eventos de Stripe"""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)

    # Manejar evento
    if event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        registration_id = payment_intent['metadata']['registration_id']

        # Procesar pago
        TenantRegistrationService.process_payment(
            registration_id,
            payment_intent['id']
        )

    return HttpResponse(status=200)
```

### Paso 6: Frontend - Integrar Stripe Checkout

```bash
npm install @stripe/stripe-js
```

```tsx
// src/modules/public/pages/RegisterPage.tsx
import { loadStripe } from "@stripe/stripe-js";

const stripePromise = loadStripe(import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY);

const handlePayment = async (registrationId: number) => {
  const stripe = await stripePromise;

  // Crear sesión de pago
  const response = await publicService.createCheckoutSession(registrationId);

  // Redirigir a Stripe Checkout
  await stripe?.redirectToCheckout({
    sessionId: response.session_id,
  });
};
```

---

## 🧪 PRUEBAS

### 1. Modo Desarrollo (Simulación)

```bash
# 1. Ejecutar backend
cd cr_backend
python manage.py runserver

# 2. Ejecutar frontend
cd cr_frontend
npm run dev
```

**Probar flujo:**

1. Ir a http://localhost:5173/
2. Seleccionar plan Basic ($1)
3. Completar registro:
   - Hospital: "Clínica Test"
   - Subdomain: "clinica-test"
   - Email: tu_email_real@gmail.com
4. Click "Registrar"
5. Simular pago (botón de desarrollo)
6. Revisar email (simulado en consola)
7. Copiar token de activación
8. Ir a /activate/{token}
9. Establecer contraseña: "TestPass123!"
10. Login con: admin@clinica-test.localhost

### 2. Tarjetas de Prueba Stripe

```
Card Number: 4242 4242 4242 4242
CVC: cualquier 3 dígitos
Date: cualquier fecha futura
ZIP: cualquier código
```

**Otros escenarios:**

- `4000 0000 0000 0002` → Pago rechazado
- `4000 0000 0000 9995` → Insuficientes fondos

---

## 🚀 DEPLOYMENT EN PRODUCCIÓN

### Checklist de Producción:

- [ ] SendGrid configurado y verificado
- [ ] Dominio propio (clinidocs.com)
- [ ] SSL configurado
- [ ] Stripe en modo Live
- [ ] Variables de entorno seguras
- [ ] `DEBUG=False`
- [ ] `SENDGRID_ENABLED=True`
- [ ] `STRIPE_ENABLED=True`
- [ ] Webhook Stripe apuntando a URL de producción
- [ ] Templates de email testeados
- [ ] Backup de base de datos configurado

---

## 📊 RESUMEN DE COSTOS

### Plan MÍNIMO para probar (Gratuito):

- **Stripe Test Mode:** Gratis, ilimitado
- **SendGrid Free:** 100 emails/día (suficiente para testing)
- **Heroku/Render Free Tier:** Backend
- **Vercel Free:** Frontend
- **PostgreSQL Free:** Supabase o Render

### Plan PRODUCCIÓN (Mínimo $15/mes):

- **Stripe:** Comisión 2.9% + $0.30 por transacción
- **SendGrid Essentials:** $15/mes (40,000 emails)
- **Heroku Hobby:** $7/mes (backend)
- **Vercel Pro:** $20/mes (frontend)
- **PostgreSQL:** $7-15/mes (Render o Digital Ocean)

**Total estimado:** $49-57/mes para producción básica

---

## ❓ FAQ

### ¿Cómo pruebo los emails sin SendGrid?

En desarrollo, los emails se imprimen en consola. Para verlos bonitos:

```python
# config/settings/development.py
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

### ¿Puedo usar PayPal en lugar de Stripe?

Sí, pero Stripe es más fácil. Para PayPal:

- Usar SDK de PayPal
- Implementar webhooks similares
- Cambiar lógica en `TenantRegistrationService`

### ¿Cómo agrego más planes?

Edita `scripts/seed_subscription_plans.py` y agrega:

```python
{
    'name': 'Premium',
    'slug': 'premium',
    'plan_type': 'premium',
    'monthly_price': Decimal('99.00'),
    'annual_price': Decimal('990.00'),
    'max_users': 500,
    'max_patients': 50000,
    'storage_gb': 5000,
    'features': [
        'API access',
        'White label',
        'Soporte 24/7'
    ]
}
```

---

## 📝 SIGUIENTES PASOS

1. ✅ Implementar backend de planes
2. ✅ Implementar frontend landing page
3. ✅ Configurar SendGrid (desarrollo: consola)
4. ⏳ Testear flujo completo
5. ⏳ Configurar Stripe (modo test)
6. ⏳ Deploy a staging
7. ⏳ Configurar producción
8. ⏳ Testear con usuarios reales

---

**Última actualización:** 4 de Noviembre de 2025
**Versión:** 1.0.0
**Autor:** Sistema CliniDocs
