# Guía de Reset Completo de Base de Datos

Esta guía te llevará paso a paso para resetear completamente la base de datos PostgreSQL y las migraciones de Django.

## Pre-requisitos

- PostgreSQL instalado y corriendo
- Python 3.11 con entorno virtual activado
- DBeaver cerrado (para evitar bloqueos de conexión)

---

## PASO 1: Resetear PostgreSQL

### 1.1 Conectar a PostgreSQL como superusuario

```bash
psql -U postgres
```

Si te pide contraseña, ingresa la contraseña del usuario `postgres`.

### 1.2 Eliminar base de datos y usuario antiguos

```sql
-- Desconectar todas las sesiones activas de las bases de datos
SELECT pg_terminate_backend(pg_stat_activity.pid)
FROM pg_stat_activity
WHERE pg_stat_activity.datname IN ('clinic_record_db', 'clinic_records_db')
  AND pid <> pg_backend_pid();

-- Eliminar bases de datos (antigua y nueva si existe)
DROP DATABASE IF EXISTS clinic_record_db;
DROP DATABASE IF EXISTS clinic_records_db;

-- Eliminar usuarios (antiguo y nuevo si existe)
DROP USER IF EXISTS cr_admin;
DROP USER IF EXISTS clinic_admin;
```

### 1.3 Crear nuevo usuario y base de datos

```sql
-- Crear nuevo usuario
CREATE USER clinic_admin WITH PASSWORD 'clinic2024!';

-- Crear nueva base de datos
CREATE DATABASE clinic_records_db OWNER clinic_admin;

-- Dar todos los privilegios
GRANT ALL PRIVILEGES ON DATABASE clinic_records_db TO clinic_admin;

-- Conectar a la nueva base de datos
\c clinic_records_db

-- Dar permisos sobre el esquema public
GRANT ALL ON SCHEMA public TO clinic_admin;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO clinic_admin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO clinic_admin;

-- Salir de psql
\q
```

### 1.4 Verificar conexión con nuevas credenciales

```bash
psql -U clinic_admin -d clinic_records_db -h localhost
```

Deberías entrar sin problemas. Escribe `\q` para salir.

---

## PASO 2: Verificar archivo .env

Asegúrate de que tu archivo `.env` tenga estas credenciales:

```env
# Database (PostgreSQL)
DATABASE_ENGINE=postgresql
DATABASE_HOST=localhost
DATABASE_NAME=clinic_records_db
DATABASE_USER=clinic_admin
DATABASE_PASSWORD=clinic2024!
DATABASE_PORT=5432
```

---

## PASO 3: Eliminar todas las migraciones

```bash
cd cr_backend
python scripts/reset_migrations.py
```

Cuando te pregunte, escribe: **SI**

Este script eliminará todos los archivos de migración de todas las apps, excepto los `__init__.py`.

---

## PASO 4: Recrear migraciones desde cero

```bash
python manage.py makemigrations
```

Deberías ver algo como:

```
Migrations for 'core':
  apps\core\migrations\0001_initial.py
    - Create model Tenant
Migrations for 'accounts':
  apps\accounts\migrations\0001_initial.py
    - Create model User
    - Create model Role
    ...
```

---

## PASO 5: Aplicar migraciones a la base de datos

```bash
python manage.py migrate
```

Esto creará todas las tablas en PostgreSQL. Deberías ver muchas líneas de:

```
Running migrations:
  Applying core.0001_initial... OK
  Applying accounts.0001_initial... OK
  ...
```

---

## PASO 6: Verificar tablas en PostgreSQL

```bash
psql -U clinic_admin -d clinic_records_db -h localhost
```

Dentro de psql:

```sql
\dt
```

Deberías ver una lista con TODAS las tablas del sistema (tenants, users, roles, patients, etc.).

Escribe `\q` para salir.

---

## PASO 7: Cargar datos de prueba

```bash
python scripts/seed_data.py
```

Este mega seeder creará:

- ✅ 1 Superusuario ASU
- ✅ 3 Planes de suscripción (Básico, Profesional, Empresarial)
- ✅ 2 Tenants (Hospital Santa Cruz, Clínica La Paz)
- ✅ Roles y permisos por tenant
- ✅ 5 usuarios por tenant (1 Admin TI, 2 Doctores, 2 Pacientes)
- ✅ 50 pacientes con datos realistas (Pandas + Faker)
- ✅ 100+ historias clínicas
- ✅ 50+ documentos clínicos
- ✅ Templates de reportes

Al finalizar, verás las credenciales de todos los usuarios creados.

---

## PASO 8: Verificar en DBeaver

1. Abre DBeaver
2. Crea una nueva conexión PostgreSQL con:
   - Host: `localhost`
   - Puerto: `5432`
   - Base de datos: `clinic_records_db`
   - Usuario: `clinic_admin`
   - Contraseña: `clinic2024!`
3. Navega a `public` > `Tables`
4. Deberías ver TODAS las tablas con datos

---

## PASO 9: Verificar con diagnose_activation.py

```bash
python scripts/diagnose_activation.py --list
```

Esto debería mostrar:

- ✅ 2 Tenants (Hospital Santa Cruz, Clínica La Paz)
- ✅ Usuarios, roles, pacientes, historias clínicas de cada uno

---

## PASO 10: Iniciar el servidor Django

```bash
python manage.py runserver
```

---

## PASO 11: Probar el flujo completo

### 11.1 Acceder a Swagger

Abre en tu navegador:

```
http://localhost:8000/api/swagger/
```

### 11.2 Login como ASU (Superusuario)

En Swagger, busca `POST /api/accounts/login/`

```json
{
  "email": "asu@system.com",
  "password": "ASU@2024!"
}
```

Deberías recibir un token JWT. Copia el `access` token.

### 11.3 Verificar endpoint de tenants

En Swagger, click en "Authorize" (candado verde) y pega el token.

Luego busca `GET /api/tenants/` y ejecuta.

Deberías ver 2 tenants:
- `hospital-santacruz`
- `clinica-lapaz`

### 11.4 Probar registro de nuevo tenant

En Swagger, busca `POST /api/tenants/register/`

```json
{
  "tenant_name": "Clínica Test",
  "subdomain": "clinica-test",
  "admin_first_name": "Admin",
  "admin_last_name": "Test",
  "admin_email": "admin@clinica-test.com",
  "plan_slug": "basic"
}
```

Deberías recibir una respuesta 201 con un mensaje de que se envió un email de activación.

### 11.5 Ver el activation_token

Como estamos en desarrollo y SendGrid puede no estar configurado, el token se imprime en la consola del servidor.

Busca en la terminal del `runserver` algo como:

```
[REGISTRO] Token de activación: abc123...
```

Copia ese token.

### 11.6 Activar el tenant

En Swagger, busca `POST /api/tenants/activate/`

```json
{
  "activation_token": "abc123...",
  "new_password": "TestPass123!"
}
```

Deberías recibir una respuesta 200 con:

```json
{
  "message": "Tenant activado exitosamente",
  "tenant": {
    "id": "...",
    "name": "Clínica Test",
    "subdomain": "clinica-test",
    ...
  },
  "admin_user": {
    "id": "...",
    "email": "admin@clinica-test.com",
    ...
  }
}
```

### 11.7 Verificar logs de activación

En la consola del `runserver`, deberías ver logs detallados como:

```
[ACTIVATE] Iniciando activación con token: abc123...
[ACTIVATE] ✅ Tenant CREADO: ID=..., name=Clínica Test
[ACTIVATE] ✅ Rol CREADO: ID=..., name=Administrador TI
[ACTIVATE] ✅ Usuario CREADO: ID=..., email=admin@clinica-test.com
[ACTIVATE] ✅ VERIFICACIÓN: Usuario encontrado en BD
```

### 11.8 Login con el nuevo admin

En Swagger, busca `POST /api/accounts/login/`

```json
{
  "email": "admin@clinica-test.com",
  "password": "TestPass123!"
}
```

Deberías recibir un token JWT y datos del usuario.

---

## PASO 12: Verificar en DBeaver

Actualiza las tablas en DBeaver (F5) y verifica:

1. Tabla `core_tenant`: Deberías ver 3 tenants (los 2 del seeder + clinica-test)
2. Tabla `accounts_user`: Deberías ver el usuario `admin@clinica-test.com`
3. Tabla `accounts_role`: Deberías ver roles para clinica-test
4. Tabla `tenants_tenantregistration`: Deberías ver el registro con `is_activated=True`

---

## Solución de Problemas

### Problema: "password authentication failed"

**Solución**: Asegúrate de que la contraseña en el paso 1.3 sea exactamente `clinic2024!` con el signo de exclamación.

### Problema: "database is being accessed by other users"

**Solución**: Cierra DBeaver y cualquier conexión activa, luego ejecuta el comando `pg_terminate_backend` del paso 1.2.

### Problema: Error al ejecutar reset_migrations.py

**Solución**: Asegúrate de estar en el directorio `cr_backend` y que tu entorno virtual esté activado.

### Problema: Login falla con "User not found"

**Solución**:
1. Verifica los logs de activación en la consola del servidor
2. Ejecuta: `python scripts/diagnose_activation.py --subdomain clinica-test`
3. Verifica en DBeaver que el usuario exista en la tabla `accounts_user`
4. Comparte los logs conmigo para diagnosticar

### Problema: DBeaver no muestra los datos nuevos

**Solución**:
1. Presiona F5 para actualizar
2. Cierra y vuelve a abrir DBeaver
3. Verifica que estés conectado a `clinic_records_db` (no a `clinic_record_db`)

---

## Comandos Rápidos de Referencia

```bash
# Ver tenants en BD
python scripts/diagnose_activation.py --list

# Ver detalles de un tenant específico
python scripts/diagnose_activation.py --subdomain hospital-santacruz

# Resetear completamente la BD (BORRA TODO)
python scripts/seed_data_reset.py

# Volver a cargar datos de prueba
python scripts/seed_data.py

# Ver estructura de BD en psql
psql -U clinic_admin -d clinic_records_db -h localhost -c "\dt"

# Contar registros de una tabla
psql -U clinic_admin -d clinic_records_db -h localhost -c "SELECT COUNT(*) FROM core_tenant;"
```

---

## Resumen de Credenciales

### Base de Datos PostgreSQL
- **Host**: localhost
- **Puerto**: 5432
- **Base de datos**: clinic_records_db
- **Usuario**: clinic_admin
- **Contraseña**: clinic2024!

### Superusuario ASU
- **Email**: asu@system.com
- **Password**: ASU@2024!

### Tenants del Seeder

**Hospital Santa Cruz**
- Admin TI: `admin@hospital-santacruz.com` / `AdminHospital123!`

**Clínica La Paz**
- Admin TI: `admin@clinica-lapaz.com` / `AdminClinica123!`

(Ver más credenciales al ejecutar `seed_data.py`)

---

## Próximos Pasos Después del Reset

1. ✅ Verificar que DBeaver y Django muestren los mismos datos
2. ✅ Probar flujo completo: registro → activación → login
3. ✅ Verificar que los logs de activación sean coherentes
4. ✅ Probar creación de pacientes y historias clínicas
5. ✅ Preparar para deploy

---

**¡Listo! Ahora tienes una base de datos PostgreSQL completamente limpia y sincronizada.**
