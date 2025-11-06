# 📚 Índice de Documentación - Backend

Bienvenido a la documentación del backend de **ClinicRecords**.

---

## 📖 Documentos Principales

### [REVISION.md](./REVISION.md)

**Estado del proyecto, progreso de sprints y funcionalidades implementadas**

- Resumen ejecutivo
- Estado de sprints (1-4)
- Módulos del sistema
- Problemas conocidos
- Próximos pasos

### [DOCUMENTATION_GUIDE.md](./DOCUMENTATION_GUIDE.md)

**Documentación técnica completa del sistema**

- Arquitectura multi-tenant
- Sistema RBAC
- Módulos y endpoints
- Modelos y base de datos
- Servicios y tasks de Celery
- Integración con AWS S3

### [DEVELOPMENT_GUIDE.md](./DEVELOPMENT_GUIDE.md)

**Guía para desarrolladores**

- Configuración del entorno
- Crear nuevos módulos
- Trabajar con modelos
- Crear endpoints (ViewSets)
- Serializers y validación
- Celery y tareas asíncronas
- Testing
- Mejores prácticas

### [API_ENDPOINTS_REFERENCE.md](./API_ENDPOINTS_REFERENCE.md)

**Referencia completa de todos los endpoints de la API**

### [CONTRIBUTING.md](./CONTRIBUTING.md)

**Guía para contribuir al proyecto**

---

## 📂 Guías Específicas (guides/)

### [QUICKSTART.md](./guides/QUICKSTART.md)

Guía rápida para comenzar con el proyecto

### [LOGGING_GUIDE.md](./guides/LOGGING_GUIDE.md)

Sistema de logging y auditoría

### [TESTING_GUIDE.md](./guides/TESTING_GUIDE.md)

Cómo escribir y ejecutar tests

### [TROUBLESHOOTING_GUIDE.md](./guides/TROUBLESHOOTING_GUIDE.md)

Solución de problemas comunes

### [RESET_DATABASE_GUIDE.md](./guides/RESET_DATABASE_GUIDE.md)

Cómo resetear la base de datos

---

## 🚀 Deployment (deployment/)

### [SAAS_SETUP_GUIDE.md](./deployment/SAAS_SETUP_GUIDE.md)

Configuración SaaS multi-tenant

### [SENDGRID_SETUP.md](./deployment/SENDGRID_SETUP.md)

Configuración de SendGrid para emails

---

## 🔧 Temas Avanzados (advanced/)

### [CELERY_BACKUP_SETUP.md](./advanced/CELERY_BACKUP_SETUP.md)

Configuración de Celery y sistema de backups automáticos

---

## 📦 Archivos Archivados (archive/)

Documentos antiguos o supersedidos, mantenidos para referencia histórica:

- `RESUMEN_FINAL.md` - Resumen anterior del proyecto
- `DOCUMENTATION_STATUS.md` - Estado anterior de documentación
- `DOCUMENTATION_INDEX.md` - Índice anterior
- `DOCS_US1_BACKEND.md` - Documentación del Sprint 1
- `NEXT_STEPS_US3.md` - Pasos del Sprint 3
- `START_HERE.md` - Documento de inicio anterior
- `SYSTEM_VERIFICATION.md` - Verificación del sistema
- `CELERY_IMPLEMENTATION_COMPLETE.md` - Implementación de Celery
- `CHANGELOG_RESET.md` - Changelog del reset
- `SESSION_SUMMARY.md` - Resumen de sesión
- `SEEDER_AND_DOCUMENTS_FIX.md` - Fix de seeder y documentos

---

## 🎯 ¿Por Dónde Empezar?

### Nuevo en el Proyecto

1. Lee [QUICKSTART.md](./guides/QUICKSTART.md)
2. Revisa [REVISION.md](./REVISION.md) para entender el estado actual
3. Consulta [DEVELOPMENT_GUIDE.md](./DEVELOPMENT_GUIDE.md) para configurar tu entorno

### Desarrollador Existente

1. Consulta [DOCUMENTATION_GUIDE.md](./DOCUMENTATION_GUIDE.md) para detalles técnicos
2. Usa [API_ENDPOINTS_REFERENCE.md](./API_ENDPOINTS_REFERENCE.md) como referencia
3. Sigue [CONTRIBUTING.md](./CONTRIBUTING.md) para contribuir

### Problemas o Errores

1. Revisa [TROUBLESHOOTING_GUIDE.md](./guides/TROUBLESHOOTING_GUIDE.md)
2. Consulta la sección "Problemas Conocidos" en [REVISION.md](./REVISION.md)

---

## 📝 Estructura del Proyecto

```
docs/
├── INDEX.md                          # Este archivo
├── REVISION.md                       # ⭐ Estado del proyecto
├── DOCUMENTATION_GUIDE.md            # ⭐ Documentación técnica
├── DEVELOPMENT_GUIDE.md              # ⭐ Guía para desarrolladores
├── API_ENDPOINTS_REFERENCE.md        # Referencia API
├── CONTRIBUTING.md                   # Guía de contribución
├── guides/                           # Guías específicas
│   ├── QUICKSTART.md
│   ├── LOGGING_GUIDE.md
│   ├── TESTING_GUIDE.md
│   ├── TROUBLESHOOTING_GUIDE.md
│   └── RESET_DATABASE_GUIDE.md
├── deployment/                       # Deployment y configuración
│   ├── SAAS_SETUP_GUIDE.md
│   └── SENDGRID_SETUP.md
├── advanced/                         # Temas avanzados
│   └── CELERY_BACKUP_SETUP.md
└── archive/                          # Archivos antiguos
    └── ...
```

---

## 🔗 Enlaces Útiles

- **Swagger UI:** http://localhost:8000/api/schema/swagger/
- **ReDoc:** http://localhost:8000/api/schema/redoc/
- **Admin Django:** http://localhost:8000/admin/

---

**Última actualización:** 5 de Noviembre, 2025
