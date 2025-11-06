# 🚀 SPRINT 3: Funcionalidades Esenciales (2 días)

## 📊 CONTEXTO DEL SPRINT

- **Duración:** 2 días (48 horas)
- **Objetivo:** Móvil básico + Notificaciones + Pagos (si da tiempo)
- **Enfoque:** Funcionalidades visibles y usables
- **Equipo:** 3-4 personas
- **Prerequisito:** [TERCER_SPRINT.md](./TERCER_SPRINT.md) completado al 100%

---

**Priorizar:**

1. ✅ Móvil (HU18) - OBLIGATORIO
2. ✅ Notificaciones (HU17) - OBLIGATORIO
3. ⚠️ Stripe (HU15) - Mejor esfuerzo, si no → Sprint 4

## 🎯 HISTORIAS DE USUARIO - SPRINT 3

### ✅ HU14: Gestionar Planes de Suscripción (COMPLETADO)

**Estado:** ✅ LISTO

Ya existe:

- Tabla `subscription_plan` ✅
- Modelo en Django ✅
- CRUD básico ✅

---

### ⚠️ HU15: Gestionar Pagos con Stripe (EN PROCESO - Prioridad ALTA)

**Tiempo estimado:** 10-12 horas (1.5 días)
**Responsable:** 1 persona backend + 1 frontend

**Descripción:**
Como **Admin TI**, quiero procesar pagos de suscripción con Stripe y ver facturas para gestionar los pagos de mi hospital.

**Criterios de Aceptación:**

- [ ] Integrar Stripe Checkout
- [ ] Crear sesión de pago
- [ ] Webhook para confirmar pagos
- [ ] Guardar pagos en tabla `payment`
- [ ] Generar factura básica (sin PDF por ahora)
- [ ] Ver historial de pagos

**Tablas Involucradas:**

- `payment` (ya existe) ✅
- `invoice` (ya existe) ✅
- `subscription_plan` (ya existe) ✅

**Backend (Implementar):**

```python
# cr_backend/apps/payments/views.py
import stripe
from django.conf import settings

stripe.api_key = settings.STRIPE_SECRET_KEY

class CreateCheckoutSessionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        tenant = get_current_tenant()
        plan_id = request.data.get('plan_id')

        plan = SubscriptionPlan.objects.get(id=plan_id)

        try:
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': plan.name,
                            'description': plan.description,
                        },
                        'unit_amount': int(plan.price_monthly * 100),
                    },
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=settings.FRONTEND_URL + '/billing/success?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=settings.FRONTEND_URL + '/billing/cancel',
                client_reference_id=str(tenant.id),
                metadata={
                    'tenant_id': str(tenant.id),
                    'plan_id': str(plan.id),
                }
            )

            return Response({'sessionId': checkout_session.id})

        except Exception as e:
            return Response({'error': str(e)}, status=400)


class StripeWebhookView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        payload = request.body
        sig_header = request.META['HTTP_STRIPE_SIGNATURE']

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except ValueError:
            return Response({'error': 'Invalid payload'}, status=400)

        # Manejar eventos
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']

            # Crear registro de pago
            tenant_id = session['metadata']['tenant_id']
            plan_id = session['metadata']['plan_id']

            payment = Payment.objects.create(
                tenant_id=tenant_id,
                subscription_plan_id=plan_id,
                amount=session['amount_total'] / 100,
                currency=session['currency'].upper(),
                status='completed',
                stripe_payment_intent_id=session['payment_intent'],
                stripe_session_id=session['id'],
                paid_at=timezone.now()
            )

            # Crear factura
            invoice = Invoice.objects.create(
                tenant_id=tenant_id,
                payment=payment,
                invoice_number=f'INV-{timezone.now().strftime("%Y%m%d")}-{payment.id[:8]}',
                subtotal=payment.amount,
                total=payment.amount,
                status='paid',
                issue_date=timezone.now().date(),
                paid_at=timezone.now()
            )

            # Actualizar tenant
            tenant = Tenant.objects.get(id=tenant_id)
            tenant.subscription_plan_id = plan_id
            tenant.subscription_status = 'active'
            tenant.stripe_customer_id = session.get('customer')
            tenant.save()

        return Response({'status': 'success'})


class PaymentListView(generics.ListAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        tenant = get_current_tenant()
        return Payment.objects.filter(tenant=tenant).order_by('-created_at')
```

**Frontend:**

```typescript
// cr_frontend/src/pages/Billing/CheckoutPage.tsx
import { loadStripe } from "@stripe/stripe-js";

const stripePromise = loadStripe(import.meta.env.VITE_STRIPE_PUBLIC_KEY);

export const CheckoutPage = () => {
  const [selectedPlan, setSelectedPlan] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleCheckout = async (planId: string) => {
    setLoading(true);

    try {
      const { sessionId } = await api.post(
        "/api/payments/create-checkout-session/",
        {
          plan_id: planId,
        }
      );

      const stripe = await stripePromise;
      await stripe.redirectToCheckout({ sessionId });
    } catch (error) {
      console.error("Error:", error);
      toast.error("Error al procesar el pago");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6">Selecciona un Plan</h1>

      <div className="grid grid-cols-3 gap-6">
        {plans.map((plan) => (
          <div key={plan.id} className="border rounded-lg p-6">
            <h3 className="text-xl font-bold">{plan.name}</h3>
            <p className="text-3xl font-bold my-4">
              ${plan.price_monthly}
              <span className="text-sm text-gray-500">/mes</span>
            </p>

            <ul className="mb-6">
              <li>✓ {plan.max_users} usuarios</li>
              <li>✓ {plan.max_patients} pacientes</li>
              <li>✓ {plan.max_storage_gb}GB almacenamiento</li>
            </ul>

            <button
              onClick={() => handleCheckout(plan.id)}
              disabled={loading}
              className="w-full bg-blue-600 text-white py-2 rounded"
            >
              {loading ? "Procesando..." : "Seleccionar Plan"}
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};
```

```typescript
// cr_frontend/src/pages/Billing/PaymentHistoryPage.tsx
export const PaymentHistoryPage = () => {
  const [payments, setPayments] = useState([]);

  useEffect(() => {
    api.get("/api/payments/").then((res) => setPayments(res.data));
  }, []);

  return (
    <div className="max-w-6xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6">Historial de Pagos</h1>

      <table className="w-full">
        <thead>
          <tr>
            <th>Fecha</th>
            <th>Monto</th>
            <th>Plan</th>
            <th>Estado</th>
            <th>Factura</th>
          </tr>
        </thead>
        <tbody>
          {payments.map((payment) => (
            <tr key={payment.id}>
              <td>{new Date(payment.created_at).toLocaleDateString()}</td>
              <td>${payment.amount}</td>
              <td>{payment.subscription_plan.name}</td>
              <td>
                <span
                  className={`badge ${
                    payment.status === "completed" ? "badge-success" : ""
                  }`}
                >
                  {payment.status}
                </span>
              </td>
              <td>
                <button>Ver Factura</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
```

**Endpoints nuevos:**

```
POST   /api/payments/create-checkout-session/
POST   /api/payments/webhook/  (Stripe webhook)
GET    /api/payments/
GET    /api/payments/{id}/
GET    /api/invoices/
GET    /api/invoices/{id}/
```

**Configuración (.env):**

```bash
STRIPE_PUBLIC_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
FRONTEND_URL=http://localhost:5173
```

**Dependencias:**

```bash
# Backend
pip install stripe

# Frontend
npm install @stripe/stripe-js
```

**Notas:**

- Usar **Stripe Test Mode** para desarrollo
- Webhook debe estar expuesto públicamente (usar ngrok para testing local)
- **Si no da tiempo:** Dejar para Sprint 4, marcar como "en proceso"

---

### ✅ HU17: Gestionar Notificaciones (Prioridad MEDIA)

**Tiempo estimado:** 3-4 horas
**Responsable:** 1 persona backend + frontend

**Descripción:**
Como **Usuario**, quiero recibir notificaciones automáticas sobre eventos importantes para estar informado en tiempo real.

**Criterios de Aceptación:**

- [ ] Notificaciones automáticas al crear documento
- [ ] Notificaciones al asignar documento a doctor
- [ ] Marcar todas como leídas
- [ ] Filtrar por tipo de notificación

**Tablas Involucradas:**

- `notification` (ya existe) ✅

**Backend (Mejoras):**

```python
# cr_backend/apps/notifications/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.documents.models import ClinicalDocument
from apps.notifications.models import Notification

@receiver(post_save, sender=ClinicalDocument)
def notify_document_created(sender, instance, created, **kwargs):
    if created:
        # Notificar al paciente
        patient = instance.clinical_record.patient
        if hasattr(patient, 'user'):
            Notification.objects.create(
                tenant=instance.tenant,
                user=patient.user,
                title="Nuevo documento médico",
                message=f"Se agregó un documento: {instance.document_type}",
                notification_type="document_created",
                related_resource_type="clinical_document",
                related_resource_id=instance.id,
                related_resource_url=f"/documents/{instance.id}"
            )

        # Notificar al doctor que creó el documento
        if instance.created_by:
            Notification.objects.create(
                tenant=instance.tenant,
                user=instance.created_by,
                title="Documento creado exitosamente",
                message=f"Has creado un documento: {instance.title}",
                notification_type="document_created",
                related_resource_type="clinical_document",
                related_resource_id=instance.id
            )


# cr_backend/apps/notifications/apps.py
class NotificationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.notifications'

    def ready(self):
        import apps.notifications.signals  # Registrar signals
```

**Frontend (Mejoras):**

```typescript
// cr_frontend/src/pages/Notifications/NotificationsPage.tsx
export const NotificationsPage = () => {
  const [notifications, setNotifications] = useState([]);
  const [filter, setFilter] = useState("all");

  useEffect(() => {
    loadNotifications();
    // Polling cada 30 segundos
    const interval = setInterval(loadNotifications, 30000);
    return () => clearInterval(interval);
  }, [filter]);

  const loadNotifications = async () => {
    const params = filter !== "all" ? { notification_type: filter } : {};
    const res = await api.get("/api/notifications/", { params });
    setNotifications(res.data.results);
  };

  const markAllAsRead = async () => {
    await api.patch("/api/notifications/read_all/");
    loadNotifications();
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Notificaciones</h1>
        <button onClick={markAllAsRead} className="btn btn-primary">
          Marcar todas como leídas
        </button>
      </div>

      <div className="mb-4">
        <select value={filter} onChange={(e) => setFilter(e.target.value)}>
          <option value="all">Todas</option>
          <option value="document_created">Documentos</option>
          <option value="appointment">Citas</option>
          <option value="alert">Alertas</option>
        </select>
      </div>

      <div className="space-y-3">
        {notifications.map((notif) => (
          <div
            key={notif.id}
            className={`p-4 rounded border ${
              notif.is_read ? "bg-gray-50" : "bg-blue-50"
            }`}
          >
            <div className="flex justify-between">
              <h3 className="font-bold">{notif.title}</h3>
              <span className="text-sm text-gray-500">
                {new Date(notif.created_at).toLocaleString()}
              </span>
            </div>
            <p className="mt-2">{notif.message}</p>
            {!notif.is_read && (
              <button
                onClick={() => markAsRead(notif.id)}
                className="text-blue-600 text-sm mt-2"
              >
                Marcar como leída
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
```

**Endpoints existentes:**

```
GET    /api/notifications/
PATCH  /api/notifications/{id}/read/
PATCH  /api/notifications/read_all/
GET    /api/notifications/unread_count/
```

---

### ✅ HU16: Gestionar Formularios (Ya implementado en TERCER_SPRINT.md)

**Estado:** ✅ Debería estar completo

Ya se implementaron los 4 tipos de formularios:

- Triaje ✅
- Consulta ✅
- Receta ✅
- Orden Lab ✅

**Si falta algo:** Completarlo antes de continuar con móvil.

---

### 📱 HU18: Acceso Móvil Básico (Prioridad CRÍTICA)

**Tiempo estimado:** 8-10 horas
**Responsable:** 1-2 personas mobile

**Descripción:**
Como **Doctor/Paciente**, quiero acceder desde mi teléfono móvil y ver información esencial para consultar datos en movimiento.

**Criterios de Aceptación:**

- [ ] App móvil (Flutter o PWA)
- [ ] Login con JWT
- [ ] Ver lista de pacientes (Doctores)
- [ ] Ver mi historial clínico (Pacientes)
- [ ] Ver documentos de un paciente
- [ ] Ver formularios clínicos (triaje, consultas, etc.)

**Opción A: PWA con React (MÁS RÁPIDO - RECOMENDADO)**

```typescript
// cr_mobile_pwa/src/main.tsx
import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./index.css";

// Registrar Service Worker para PWA
if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("/sw.js");
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
```

```json
// public/manifest.json
{
  "name": "CliniDocs Mobile",
  "short_name": "CliniDocs",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#3b82f6",
  "icons": [
    {
      "src": "/icon-192.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "/icon-512.png",
      "sizes": "512x512",
      "type": "image/png"
    }
  ]
}
```

**Opción B: Flutter (Si tienen experiencia)**

```dart
// lib/main.dart
import 'package:flutter/material.dart';
import 'screens/login_screen.dart';
import 'screens/patients_list_screen.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'CliniDocs Mobile',
      theme: ThemeData(primarySwatch: Colors.blue),
      home: const LoginScreen(),
      routes: {
        '/patients': (context) => const PatientsListScreen(),
      },
    );
  }
}

// lib/services/api_service.dart
import 'package:http/http.dart' as http;
import 'dart:convert';

class ApiService {
  static const String baseUrl = 'https://api.tu-dominio.com';
  static String? _token;

  static Future<Map<String, dynamic>> login(String email, String password) async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/auth/login/'),
      headers: {'Content-Type': 'application/json'},
      body: json.encode({'email': email, 'password': password}),
    );

    if (response.statusCode == 200) {
      final data = json.decode(response.body);
      _token = data['access'];
      return data;
    } else {
      throw Exception('Error en login');
    }
  }

  static Future<List<dynamic>> getPatients() async {
    final response = await http.get(
      Uri.parse('$baseUrl/api/patients/'),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $_token',
      },
    );

    if (response.statusCode == 200) {
      final data = json.decode(response.body);
      return data['results'];
    } else {
      throw Exception('Error al obtener pacientes');
    }
  }
}
```

**Endpoints a consumir:**

```
POST   /api/auth/login/
GET    /api/patients/
GET    /api/patients/{id}/clinical_records/
GET    /api/documents/?clinical_record_id={id}
GET    /api/clinical-records/forms/?clinical_record_id={id}
```

**Notas:**

- **Recomendación:** Usar PWA si el equipo no tiene experiencia en Flutter
- Solo LECTURA, no implementar edición
- UI minimalista

---

### ✅ HU11: Preferencias de Usuario (Prioridad BAJA - Opcional)

**Tiempo estimado:** 2-3 horas
**Responsable:** 1 persona frontend

**Solo si sobra tiempo:**

- Tema oscuro/claro
- Selector de idioma
- Guardar en `user_preferences`

---

## ✅ CRITERIOS DE ÉXITO

Sprint 3 estará completo cuando:

1. ✅ **Móvil funciona** (PWA o Flutter) con login y visualización
2. ⚠️ **Stripe integrado** (si no da tiempo, dejar en proceso)
3. ✅ **Notificaciones automáticas** al crear documentos
4. ✅ **Formularios clínicos** completados (de TERCER_SPRINT)

---

## 🚨 PLAN B: Si Stripe no da tiempo

## **Dejar HU15 (Stripe) como "EN PROCESO" y moverla a Sprint 4**

**Próximo Sprint:** [SPRINT_4.md](./SPRINT_4.md) - IA y Tecnología Avanzada
