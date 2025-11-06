# Guía de Contribución - Clinic Record

¡Gracias por tu interés en contribuir al proyecto GD Backend! Esta guía te ayudará a seguir las mejores prácticas para mantener un código limpio y un historial de cambios ordenado.

## 📋 Proceso de Contribución

### 1. Crear una Nueva Rama

Antes de comenzar a trabajar en una nueva funcionalidad, crea una rama específica para tu tarea:

```bash
git checkout dev
git pull origin dev
git checkout -b <tipo>/<nombre-descriptivo>
```

#### Ejemplos de Nombres de Ramas Convencionales

**Features (nuevas funcionalidades):**

```
feature/user-authentication
feature/hospital-management
feature/email-notifications
feature/patient-dashboard
feature/appointment-system
```

**Bugfixes (corrección de errores):**

```
bugfix/login-validation-error
bugfix/hospital-search-filter
bugfix/email-template-rendering
bugfix/user-permissions-check
```

**Hotfixes (correcciones urgentes):**

```
hotfix/security-vulnerability
hotfix/database-connection-leak
hotfix/api-rate-limiting
```

**Refactoring:**

```
refactor/user-service-cleanup
refactor/database-queries-optimization
refactor/auth-middleware-restructure
```

**Documentación:**

```
docs/api-endpoints-documentation
docs/deployment-guide
docs/contributing-guidelines
```

### 2. Commits Convencionales

Utilizamos [Conventional Commits](https://www.conventionalcommits.org/) para mantener un historial claro y generar changelogs automáticamente.

#### Estructura del Commit

```
<tipo>[ámbito opcional]: <descripción>

[cuerpo opcional]

[footer opcional]
```

#### Tipos de Commit

- **feat**: Nueva funcionalidad
- **fix**: Corrección de errores
- **docs**: Cambios en documentación
- **style**: Cambios de formato (espacios, comas, etc.)
- **refactor**: Refactorización de código
- **perf**: Mejoras de rendimiento
- **test**: Agregar o corregir tests
- **chore**: Tareas de mantenimiento
- **ci**: Cambios en configuración de CI/CD
- **build**: Cambios en el sistema de build

#### Ejemplos de Commits

```bash
# Nueva funcionalidad
git commit -m "feat(auth): agregar autenticación con JWT"
git commit -m "feat(hospital): implementar CRUD de hospitales"
git commit -m "feat(users): agregar validación de email único"

# Corrección de errores
git commit -m "fix(auth): corregir validación de contraseña"
git commit -m "fix(hospital): resolver error en búsqueda por nombre"
git commit -m "fix(email): arreglar plantilla de notificaciones"

# Documentación
git commit -m "docs(api): actualizar documentación de endpoints"
git commit -m "docs: agregar guía de instalación"

# Refactoring
git commit -m "refactor(users): simplificar validación de datos"
git commit -m "refactor(database): optimizar consultas de hospitales"

# Tests
git commit -m "test(auth): agregar pruebas unitarias para login"
git commit -m "test(hospital): implementar tests de integración"

# Configuración
git commit -m "chore(deps): actualizar dependencias de seguridad"
git commit -m "ci: configurar pipeline de testing automático"
```

### 3. Subir Cambios

Antes de subir tus cambios, asegúrate de que tu rama esté actualizada:

```bash
# Actualizar rama dev
git checkout dev
git pull origin dev

# Regresar a tu rama y hacer rebase
git checkout tu-rama
git rebase dev

# Resolver conflictos si existen
# Después del rebase exitoso, subir cambios
git push origin tu-rama
```

### 4. Crear Pull Request

1. Ve a GitHub y crea un Pull Request desde tu rama hacia `dev`
2. Usa un título descriptivo siguiendo convenciones similares a los commits
3. Completa la plantilla de PR con:
   - **Descripción**: Explica qué hace tu cambio
   - **Cambios realizados**: Lista los principales cambios
   - **Testing**: Describe cómo probaste tus cambios
   - **Screenshots**: Si aplica, incluye capturas de pantalla

#### Ejemplo de Título de PR

```
feat(auth): implementar autenticación con JWT y roles
fix(hospital): corregir filtros de búsqueda avanzada
refactor(users): mejorar estructura de servicios de usuario
```

### 5. Proceso de Revisión

- ✅ **Mantén tu PR sin conflictos**: Haz rebase regularmente
- ✅ **Responde a comentarios**: Atiende feedback de los revisores
- ✅ **Tests pasando**: Asegúrate de que todos los tests pasen
- ✅ **Código limpio**: Sigue los estándares del proyecto
- ✅ **Sin archivos innecesarios**: No incluyas archivos temporales o de configuración local

## 🔍 Checklist Antes del PR

- [ ] Mi rama está basada en `dev` actualizado
- [ ] Los commits siguen convenciones de naming
- [ ] Los tests pasan localmente
- [ ] **El build se ejecuta sin errores (`npm run build`)**
- [ ] No hay conflictos de merge
- [ ] La documentación está actualizada (si aplica)
- [ ] He probado mis cambios localmente
- [ ] No incluyo archivos de configuración personal
- [ ] El código sigue las convenciones del proyecto

## 🚨 Importantes

1. **Nunca hagas push directamente a `main` o `dev`**
2. **Siempre crea una rama específica para tu trabajo**
3. **Mantén tus commits pequeños y enfocados**
4. **Haz rebase en lugar de merge para mantener un historial limpio**
5. **Espera la aprobación antes de hacer merge de tu PR**

## 🛠️ Configuración Local Recomendada

```bash
# Configurar git para commits más fáciles
git config --global alias.co checkout
git config --global alias.br branch
git config --global alias.ci commit
git config --global alias.st status

# Instalar commitizen para commits convencionales (opcional)
npm install -g commitizen
npm install -g cz-conventional-changelog
echo '{ "path": "cz-conventional-changelog" }' > ~/.czrc
```

Luego puedes usar `git cz` en lugar de `git commit` para commits interactivos.

---

¿Tienes alguna duda sobre el proceso de contribución? No dudes en contactar al equipo de desarrollo.
