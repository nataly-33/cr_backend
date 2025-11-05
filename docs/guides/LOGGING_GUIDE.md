# 📋 LOGGING DEL BACKEND - GUÍA

## Descripción

El backend de Django está configurado con un sistema completo de logging que registra:

- ✅ Todas las peticiones HTTP
- ✅ Errores y excepciones
- ✅ Eventos del sistema
- ✅ Validaciones y acciones

## 📁 Ubicación de Logs

```
cr_backend/
├── logs/
│   ├── django.log      # Logs generales del sistema
│   └── requests.log    # Logs detallados de peticiones HTTP
```

## 🔍 Ver Logs en Tiempo Real

### Opción 1: PowerShell (Recomendado)

```powershell
.\watch_logs.ps1
```

O manualmente:

```powershell
Get-Content logs\django.log -Wait -Tail 50
```

### Opción 2: Ver archivo estático

```bash
cat logs\django.log
```

### Opción 3: Buscar en logs

```bash
# Buscar errores
Select-String "ERROR" logs\django.log

# Buscar peticiones POST
Select-String "POST" logs\requests.log

# Últimas 50 líneas
Get-Content logs\django.log -Tail 50
```

## 📊 Formato de Logs

### Django Log (django.log)

```
DEBUG 2025-11-03 18:55:10,123 middleware 12345 67890 GET /api/users/me/ HTTP/1.1
DEBUG 2025-11-03 18:55:10,456 views 12345 67890 Usuario autenticado: user@example.com
INFO 2025-11-03 18:55:10,789 models 12345 67890 Objeto creado: Patient#uuid123
ERROR 2025-11-03 18:55:11,000 serializers 12345 67890 Error de validación: campo requerido
```

### Requests Log (requests.log)

```
DEBUG 2025-11-03 18:55:10,123 django.request 12345 67890 Method: GET, Path: /api/users/me/, Status: 200
DEBUG 2025-11-03 18:55:10,456 django.request 12345 67890 GET /api/users/me/ HTTP/1.1" 200
DEBUG 2025-11-03 18:55:10,789 django.request 12345 67890 User-Agent: PostmanRuntime/7.32.3
```

## 🎯 Ejemplos de Uso

### Ver todas las peticiones HTTP

```powershell
# Ver últimas 100 peticiones
Get-Content logs\requests.log -Tail 100

# Ver peticiones en tiempo real
Get-Content logs\requests.log -Wait
```

### Buscar errores específicos

```powershell
# Encontrar todos los errores
Select-String "ERROR" logs\django.log

# Encontrar errores de autenticación
Select-String "token|auth" logs\django.log -CaseSensitive:$False

# Encontrar peticiones fallidas (4xx, 5xx)
Select-String " 4[0-9][0-9]| 5[0-9][0-9]" logs\requests.log
```

### Monitorear en tiempo real

```powershell
# Ver logs conforme llegan
Get-Content logs\django.log -Wait

# Ver requests conforme llegan
Get-Content logs\requests.log -Wait

# Ver con filtro (solo errores)
Get-Content logs\django.log -Wait | Select-String "ERROR"
```

## ⚙️ Configuración

Los logs se configuran en: `config/settings/logging.py`

### Niveles de Log

- `DEBUG` - Información detallada para diagnóstico
- `INFO` - Confirmación de que todo está funcionando
- `WARNING` - Algo inesperado (por defecto)
- `ERROR` - Problema grave
- `CRITICAL` - Problema muy grave

### Modificar Verbosidad

Para más detalles al ejecutar:

```bash
python manage.py runserver --verbosity=3
```

## 📝 Qué se Registra

### Peticiones HTTP

```
[Timestamp] [Nivel] [Módulo] [PID] [TID] [Método] [Ruta] [Status]
```

### Errores

```
[Timestamp] [ERROR] [Módulo] [PID] [TID] [Mensaje de error]
[Traceback completo]
```

### Eventos del Sistema

```
[Timestamp] [INFO] [Módulo] [PID] [TID] Acción realizada
```

## 🔧 Troubleshooting

### Los logs no aparecen

1. ✅ Verifica que la carpeta `logs/` existe
2. ✅ Verifica que Django está corriendo: `python manage.py runserver`
3. ✅ Verifica que `DEBUG=True` en .env
4. ✅ Haz una petición para generar logs: `curl http://127.0.0.1:8000/api/`

### Los logs están vacíos

- Es normal si no se han hecho peticiones
- Haz una petición: `Invoke-WebRequest http://127.0.0.1:8000/api/`
- Los logs aparecerán instantáneamente

### Logs muy grandes

Para limpiar:

```powershell
# Limpiar django.log
Clear-Content logs\django.log

# Limpiar requests.log
Clear-Content logs\requests.log
```

## 📌 Mejores Prácticas

✅ **DO:**
- Monitorear logs durante desarrollo
- Buscar patrones de errores
- Revisar logs después de cambios
- Limpiar logs regularmente

❌ **DON'T:**
- Ignorar los errores en logs
- Dejar DEBUG=True en producción
- Acumular gigabytes de logs
- Modificar archivos de log mientras se escriben

## 🚀 Script Automático

Para facilitar el monitoreo, usa el script incluido:

```powershell
# En PowerShell
.\watch_logs.ps1

# Con follow de errores
Get-Content logs\django.log -Wait | Select-String "ERROR|WARNING"
```

---

**Creado:** Noviembre 2025  
**Status:** ✅ Logging completamente funcional
