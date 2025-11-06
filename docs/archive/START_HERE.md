# 🚀 START HERE - GUÍA DE INICIO RÁPIDO

## 👋 Bienvenido al Proyecto

Este documento te guiará a través de los primeros pasos para empezar a trabajar en el proyecto.

---

## 🎯 Elige Tu Rol

### 👨‍💻 Soy Backend Developer
**Tiempo:** 2 horas  
**Pasos:**
1. [Leer: DOCUMENTATION_INDEX.md](./DOCUMENTATION_INDEX.md) (5 min)
2. [Ejecutar: SYSTEM_VERIFICATION.md](./SYSTEM_VERIFICATION.md) (30 min)
3. [Estudiar: DEVELOPMENT_GUIDE.md](./DEVELOPMENT_GUIDE.md) (45 min)
4. [Explorar: API_ENDPOINTS_REFERENCE.md](./API_ENDPOINTS_REFERENCE.md) (20 min)
5. [Entender: LOGGING_GUIDE.md](./LOGGING_GUIDE.md) (10 min)

**Primer código:**
```bash
# En terminal
cd cr_backend
python manage.py runserver
# Abre http://localhost:8000/admin
```

---

### 👨‍💼 Soy Frontend Developer
**Tiempo:** 2 horas  
**Pasos:**
1. [Leer: DOCUMENTATION_INDEX.md](./DOCUMENTATION_INDEX.md) (5 min)
2. [Ejecutar: SYSTEM_VERIFICATION.md](./SYSTEM_VERIFICATION.md) (30 min)
3. [Aprender: RBAC_FRONTEND_GUIDE.md](../cr_frontend/RBAC_FRONTEND_GUIDE.md) (30 min)
4. [Explorar: API_ENDPOINTS_REFERENCE.md](./API_ENDPOINTS_REFERENCE.md) (20 min)
5. [Practicar: TESTING_GUIDE.md](./TESTING_GUIDE.md) (20 min)

**Primer código:**
```bash
# En terminal
cd cr_frontend
npm install
npm run dev
# Abre http://localhost:5173
```

---

### 🧪 Soy QA / Tester
**Tiempo:** 1.5 horas  
**Pasos:**
1. [Leer: DOCUMENTATION_INDEX.md](./DOCUMENTATION_INDEX.md) (5 min)
2. [Verificar: SYSTEM_VERIFICATION.md](./SYSTEM_VERIFICATION.md) (30 min)
3. [Aprender: TESTING_GUIDE.md](./TESTING_GUIDE.md) (30 min)
4. [Referencia: API_ENDPOINTS_REFERENCE.md](./API_ENDPOINTS_REFERENCE.md) (15 min)
5. [Bookmark: TROUBLESHOOTING_GUIDE.md](./TROUBLESHOOTING_GUIDE.md) (5 min)

**Primer test:**
```bash
# Abre Postman o Thunder Client
# POST http://localhost:8000/api/login/
# Body: {"email": "admin@example.com", "password": "admin123"}
```

---

### 👔 Soy Project Manager / Lead
**Tiempo:** 1 hora  
**Pasos:**
1. [Leer: DOCUMENTATION_INDEX.md](./DOCUMENTATION_INDEX.md) (5 min)
2. [Revisar: RESUMEN_FINAL.md](./RESUMEN_FINAL.md) (20 min)
3. [Explorar: DOCUMENTATION_STATUS.md](./DOCUMENTATION_STATUS.md) (15 min)
4. [Planificar: NEXT_STEPS_US3.md](./NEXT_STEPS_US3.md) (15 min)
5. [Referencia: README.md](./README.md) (5 min)

**Primer análisis:**
```
- ¿Status actual? Ver DOCUMENTATION_STATUS.md
- ¿Roadmap? Ver NEXT_STEPS_US3.md
- ¿Architecture? Ver DEVELOPMENT_GUIDE.md
- ¿Equipo? Ver roles en DOCUMENTATION_INDEX.md
```

---

## ⚡ ACCIONES INMEDIATAS (5 MIN)

### 1️⃣ Verifica que todo funciona
```powershell
# En PowerShell
cd cr_backend
python manage.py runserver
# En otra ventana:
cd cr_frontend
npm run dev
# Abre http://localhost:5173
```

### 2️⃣ Haz login
```
Email: admin@example.com
Password: admin123
```

### 3️⃣ Explora la interfaz
- Click en "Users" para ver lista de usuarios
- Click en "Roles" para ver roles y permisos
- Click en "Settings" para ver preferencias

---

## 📚 DOCUMENTOS MÁS IMPORTANTES

### Top 5 para Leer
1. **[DOCUMENTATION_INDEX.md](./DOCUMENTATION_INDEX.md)** - Punto de entrada
2. **[SYSTEM_VERIFICATION.md](./SYSTEM_VERIFICATION.md)** - Verificación del sistema
3. **[API_ENDPOINTS_REFERENCE.md](./API_ENDPOINTS_REFERENCE.md)** - API reference
4. **[TESTING_GUIDE.md](./TESTING_GUIDE.md)** - Testing
5. **[TROUBLESHOOTING_GUIDE.md](./TROUBLESHOOTING_GUIDE.md)** - Solución de problemas

### Top 5 para Bookmark
1. 📌 DOCUMENTATION_INDEX.md
2. 📌 TROUBLESHOOTING_GUIDE.md
3. 📌 API_ENDPOINTS_REFERENCE.md
4. 📌 LOGGING_GUIDE.md
5. 📌 TESTING_GUIDE.md

---

## 🎓 ROADMAP PERSONALIZADO

### Si es tu primer día...

**Hora 1:**
- [ ] Leer DOCUMENTATION_INDEX.md
- [ ] Ejecutar SYSTEM_VERIFICATION.md checklist
- [ ] Haz login en http://localhost:5173

**Hora 2:**
- [ ] Lee documentación de tu rol
- [ ] Explora la interfaz
- [ ] Intenta una acción (crear usuario, rol, etc)

**Fin del día:**
- [ ] Haz tu primer commit
- [ ] Entender git workflow
- [ ] Setup IDE/editor

### Si es tu primera semana...

**Día 2-3:**
- [ ] Leer DEVELOPMENT_GUIDE.md (backend) o RBAC_FRONTEND_GUIDE.md (frontend)
- [ ] Entender API endpoints
- [ ] Aprender testing approach

**Día 4-5:**
- [ ] Hacer código pequeño
- [ ] Pasar tests
- [ ] Code review
- [ ] Merge a main

---

## 🔧 CONFIGURACIÓN INICIAL

### Backend Setup (20 min)
```powershell
# 1. Clonar repo
git clone <repo-url>
cd cr_backend

# 2. Virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Migrations
python manage.py migrate

# 5. Crear superuser
python manage.py createsuperuser

# 6. Correr servidor
python manage.py runserver
# Visita http://localhost:8000/admin
```

### Frontend Setup (20 min)
```powershell
# 1. Entrar a carpeta
cd cr_frontend

# 2. Instalar dependencias
npm install

# 3. Instalar extensión de navegador
# Recomendado: React Developer Tools

# 4. Correr dev server
npm run dev
# Visita http://localhost:5173
```

---

## 🚦 ESTADO ACTUAL DEL SISTEMA

**Sprint 2:** 40% Completado ✅

### ✅ Completado
- US-1: Sistema de Notificaciones
- US-2: RBAC y Permisos Dinámicos

### 🔄 En Progreso
- Documentación (¡HECHO!)

### 📋 Próximo
- US-3: Búsqueda Avanzada (Iniciar próxima semana)

---

## 💡 TIPS ÚTILES

### Para Backend
```powershell
# Ver logs en tiempo real
cd cr_backend
.\watch_logs.ps1

# Hacer migraciones
python manage.py makemigrations
python manage.py migrate

# Shell interactivo
python manage.py shell
```

### Para Frontend
```powershell
# Type check
npm run type-check

# Lint
npm run lint

# Build
npm run build

# Preview build
npm run preview
```

### Para Todos
```bash
# Ver status de git
git status

# Ver últimos commits
git log --oneline -10

# Crear rama nueva
git checkout -b feature/my-feature

# Hacer commit
git add .
git commit -m "feat: Mi feature"

# Push a GitHub
git push origin feature/my-feature
```

---

## 🆘 PROBLEMAS COMUNES

### "No puedo conectar a BD"
→ Ver [TROUBLESHOOTING_GUIDE.md - Base de datos](./TROUBLESHOOTING_GUIDE.md)

### "Error 404 en API"
→ Ver [TROUBLESHOOTING_GUIDE.md - 404 Not Found](./TROUBLESHOOTING_GUIDE.md)

### "No puedo hacer login"
→ Ver [TROUBLESHOOTING_GUIDE.md - 401 Unauthorized](./TROUBLESHOOTING_GUIDE.md)

### "¿Dónde está el endpoint X?"
→ Ver [API_ENDPOINTS_REFERENCE.md](./API_ENDPOINTS_REFERENCE.md)

---

## 📞 NECESITAS AYUDA?

### Paso 1: Busca en documentación
- DOCUMENTATION_INDEX.md - Índice general
- TROUBLESHOOTING_GUIDE.md - Problemas
- API_ENDPOINTS_REFERENCE.md - Endpoints

### Paso 2: Revisa los logs
```powershell
cd cr_backend
.\watch_logs.ps1
# O ver archivo
Get-Content logs\django.log -Tail 50
```

### Paso 3: Pregunta en el equipo
- Chat del equipo
- Daily standup
- Slack/Discord

### Paso 4: Crea issue en GitHub
- Describe el problema
- Pasos para reproducir
- Logs relevantes
- Tu ambiente (OS, versiones)

---

## ✅ CHECKLIST DE BIENVENIDA

- [ ] He leído DOCUMENTATION_INDEX.md
- [ ] He ejecutado SYSTEM_VERIFICATION.md
- [ ] He hecho login en la aplicación
- [ ] He leído documentación de mi rol
- [ ] He revisado README.md
- [ ] Tengo bookmark de guías principales
- [ ] Sé dónde está TROUBLESHOOTING_GUIDE.md
- [ ] He explorado el código base
- [ ] He hecho mi primer commit
- [ ] Entiendo el git workflow

---

## 🎯 PRÓXIMOS PASOS

### Semana 1
- [ ] Setup completo
- [ ] Entender arquitectura
- [ ] Hacer código pequeño
- [ ] Pasar code review
- [ ] Mergear a main

### Semana 2
- [ ] Trabaja en feature pequeña
- [ ] Aprende testing
- [ ] Documenta tu código
- [ ] Help al equipo

### Semana 3+
- [ ] Trabaja en US-3
- [ ] Mentorea nuevos miembros
- [ ] Mejora documentación
- [ ] Code reviews

---

## 🎓 RECURSOS EXTERNOS

### Documentación Oficial
- [Django Docs](https://docs.djangoproject.com/)
- [React Docs](https://react.dev/)
- [PostgreSQL Docs](https://www.postgresql.org/docs/)

### Tutoriales
- [Django REST Framework Tutorial](https://www.django-rest-framework.org/tutorial/quickstart/)
- [React Tutorial](https://react.dev/learn)
- [PostgreSQL Tutorial](https://www.postgresql.org/docs/current/tutorial.html)

### Comunidades
- [Stack Overflow](https://stackoverflow.com/)
- [Django Discord](https://discord.gg/django)
- [React Community](https://react.dev/community)

---

## 🎉 BIENVENIDA

**¡Bienvenido al equipo!**

Nos alegra tenerte aquí. Esperamos que esta documentación sea útil y clara.

Si tienes sugerencias para mejorar la documentación:
1. Crea un issue en GitHub
2. O contribuye directamente
3. Tu feedback es importante

---

**Status:** ✅ Listo para empezar  
**Versión:** 1.0.0  
**Última actualización:** Noviembre 2025  

**¡Vamos a hacer código increíble! 🚀**
