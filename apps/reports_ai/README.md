# 🤖 Reports AI - Quick Start

## ¿Qué es?

Módulo que permite generar reportes usando **lenguaje natural** (texto o voz). Ejemplo:

```
"Quiero un reporte de los formularios lab_order emitidos
entre agosto y septiembre de 2025, mostrando el nombre de los pacientes"
```

El sistema automáticamente:

1. Parsea tu consulta con IA
2. Genera SQL seguro
3. Ejecuta y retorna resultados
4. Exporta en JSON, CSV, Excel o PDF

---

## 🚀 Instalación Rápida

### 1. Crear migraciones

```powershell
cd cr_backend
python manage.py makemigrations reports_ai
python manage.py migrate
```

O ejecutar el script:

```powershell
.\setup_reports_ai.ps1
```

### 2. (Recomendado) Configurar AWS Bedrock

Para máxima precisión con **12 meses GRATIS**:

```env
# .env.production o .env
BEDROCK_ENABLED=True
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_REGION=us-east-1
```

Ver guía completa: [`GUIA_BEDROCK_REPORTES_AI.md`](../../GUIA_BEDROCK_REPORTES_AI.md)

### 2B. (Alternativa) Configurar OpenAI

Si prefieres OpenAI, agrega en `.env`:

```env
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4
```

### 3. Iniciar servicios

```powershell
# Terminal 1: Backend
cd cr_backend
python manage.py runserver

# Terminal 2: Frontend
cd cr_frontend
npm run dev
```

### 4. Acceder

Frontend: http://localhost:5173/reports-ai

Backend API: http://localhost:8000/api/reports-ai/

---

## 📝 Uso Básico

### Frontend

1. Ir a: **Reportes → 🤖 Reportes con IA**
2. Escribir o hablar tu consulta
3. Configurar formato (JSON, CSV, Excel, PDF)
4. Click en "✨ Generar Reporte"

### API

```bash
curl -X POST http://localhost:8000/api/reports-ai/direct/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "Dame todos los pacientes de agosto 2025",
    "output_format": "json",
    "row_limit": 100,
    "ai_provider": "local"
  }'
```

---

## 📖 Ejemplos

- ✅ "Pacientes mujeres menores de 40 años"
- ✅ "Formularios lab_order de septiembre 2025"
- ✅ "Documentos de Cardiología firmados"
- ✅ "Usuarios activos ordenados por fecha"
- ✅ "Top 50 historias clínicas más recientes"

---

## 📚 Documentación Completa

Ver: [`REPORTS_AI_MODULE.md`](../REPORTS_AI_MODULE.md)

Incluye:

- 20 ejemplos detallados
- Referencia completa de API
- Configuración de proveedores IA
- Troubleshooting
- Modelos de datos

---

## 🔧 Configuración de Proveedores IA

### 1. Local (Sin costo - Por defecto)

✅ Ya configurado. Precisión: ~75%

Perfecto para desarrollo y fallback.

### 2. AWS Bedrock (✨ RECOMENDADO - Free Tier)

**12 meses GRATIS** con 100,000 tokens/mes (~200 consultas)

```env
BEDROCK_ENABLED=True
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
```

✅ Precisión: ~90%  
✅ Costo después: $0.003/query (5x más barato que OpenAI)  
✅ Mejor para producción

**Guía rápida:** [`GUIA_BEDROCK_REPORTES_AI.md`](../../GUIA_BEDROCK_REPORTES_AI.md)

**Verificar configuración:**

```powershell
python manage.py shell
exec(open('scripts/verify_bedrock_config.py').read())
```

### 3. OpenAI GPT-4 (Alternativa premium)

```env
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4
```

✅ Precisión: ~93% (mejor)  
❌ Costo: $0.01-0.03 por query  
✅ Útil si necesitas máxima precisión

---

## 📊 Endpoints Disponibles

| Endpoint                         | Método | Descripción        |
| -------------------------------- | ------ | ------------------ |
| `/api/reports-ai/parse/`         | POST   | Parsear consulta   |
| `/api/reports-ai/execute/`       | POST   | Ejecutar consulta  |
| `/api/reports-ai/direct/`        | POST   | Parsear + Ejecutar |
| `/api/reports-ai/history/`       | GET    | Historial          |
| `/api/reports-ai/stats/`         | GET    | Estadísticas       |
| `/api/reports-ai/{id}/download/` | GET    | Descargar archivo  |

---

## ⚠️ Notas Importantes

1. **Solo consultas SELECT**: No se permiten DELETE, UPDATE, DROP
2. **Límite de filas**: Máximo 1000 por consulta
3. **Seguridad**: Todas las queries son validadas
4. **Formatos**: JSON, CSV, Excel, PDF
5. **Voz**: Solo funciona en navegadores modernos (Chrome, Edge, Safari)

---

## 🐛 Troubleshooting

**Error: "Tabla no identificada"**
→ Ser más específico: "pacientes" en lugar de "datos"

**Error: "Permiso de micrófono"**
→ Permitir micrófono en configuración del navegador

**Query muy lento**
→ Reducir `row_limit` o agregar filtros de fecha

**Baja confianza (<0.7)**
→ Cambiar a `ai_provider: "openai"` o `"bedrock"`

---

## 🎯 Próximos Pasos

1. Probar con queries de ejemplo
2. Revisar historial de consultas
3. Ver estadísticas de uso
4. Configurar OpenAI para mejor precisión (opcional)
5. Explorar la documentación completa

---

¡Listo para generar reportes con lenguaje natural! 🚀
