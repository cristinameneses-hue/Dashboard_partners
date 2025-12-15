# 🔗 Connection Strings - Guía Completa

**Versión:** 2.0.3
**Fecha:** Noviembre 2025
**Estado:** ✅ Implementado y Listo

---

## 📋 Tabla de Contenidos

- [Introducción](#introducción)
- [¿Por qué Connection Strings?](#por-qué-connection-strings)
- [Formatos Soportados](#formatos-soportados)
- [Configuración Básica](#configuración-básica)
- [Configuración Multi-Database](#configuración-multi-database)
- [Permisos Granulares](#permisos-granulares)
- [Ejemplos Completos](#ejemplos-completos)
- [Migración desde Legacy](#migración-desde-legacy)
- [API de Programación](#api-de-programación)
- [Troubleshooting](#troubleshooting)

---

## 🎯 Introducción

El sistema de **Connection Strings** permite configurar múltiples bases de datos MySQL con permisos granulares de escritura/lectura usando un formato compacto basado en URLs.

### Características Principales

- ✅ **Múltiples Bases de Datos** - Conecta a varias bases de datos simultáneamente
- ✅ **Permisos Granulares** - Control fino de INSERT, UPDATE, DELETE, DDL por database
- ✅ **Formato Estándar** - Usa URLs de conexión MySQL estándar
- ✅ **Compatibilidad Total** - Soporta formato legacy (MYSQL_HOST, MYSQL_PORT, etc.)
- ✅ **Unix Sockets** - Soporte para conexiones por socket Unix (más rápidas en localhost)
- ✅ **SSL/TLS** - Configuración de conexiones seguras
- ✅ **Base de Datos por Defecto** - Define cuál DB usar cuando no se especifica

---

## 💡 ¿Por qué Connection Strings?

### Sistema Anterior (Legacy)

```env
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3307
MYSQL_USER=root
MYSQL_PASS=password
MYSQL_DB=trends
ALLOW_INSERT_OPERATION=false
ALLOW_UPDATE_OPERATION=false
ALLOW_DELETE_OPERATION=false
```

❌ **Problemas:**
- Solo una base de datos a la vez
- Permisos globales (no por database)
- 7 variables por configuración
- Difícil de compartir/copiar

### Sistema Nuevo (Connection Strings)

```env
DB_TRENDS_URL=mysql://root:password@127.0.0.1:3307/trends
DB_TRENDS_CAN_INSERT=false
DB_TRENDS_CAN_UPDATE=false
DB_TRENDS_CAN_DELETE=false
DB_TRENDS_IS_DEFAULT=true
```

✅ **Ventajas:**
- Múltiples bases de datos
- Permisos por database
- URL estándar (portable)
- Fácil de copiar/compartir

---

## 📝 Formatos Soportados

### Formato 1: Connection String (Recomendado)

```env
DB_{NAME}_URL=mysql://user:pass@host:port/database
DB_{NAME}_CAN_INSERT=true|false
DB_{NAME}_CAN_UPDATE=true|false
DB_{NAME}_CAN_DELETE=true|false
DB_{NAME}_CAN_DDL=true|false
DB_{NAME}_IS_DEFAULT=true|false
```

### Formato 2: Legacy (Compatibilidad)

```env
{NAME}_CONNECTION_STRING=mysql://user:pass@host:port/database
{NAME}_CAN_INSERT=true|false
{NAME}_CAN_UPDATE=true|false
{NAME}_CAN_DELETE=true|false
{NAME}_CAN_DDL=true|false
```

### Formato 3: Legacy Variables (Compatibilidad Total)

```env
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASS=password
MYSQL_DB=database
ALLOW_INSERT_OPERATION=false
ALLOW_UPDATE_OPERATION=false
ALLOW_DELETE_OPERATION=false
ALLOW_DDL_OPERATION=false
```

---

## ⚙️ Configuración Básica

### Conexión TCP/IP

```env
# Producción (solo lectura)
DB_PRODUCTION_URL=mysql://root:eengeoS2@127.0.0.1:3307/trends
DB_PRODUCTION_CAN_INSERT=false
DB_PRODUCTION_CAN_UPDATE=false
DB_PRODUCTION_CAN_DELETE=false
DB_PRODUCTION_CAN_DDL=false
DB_PRODUCTION_IS_DEFAULT=true
```

### Conexión Unix Socket (Localhost)

```env
# Más rápido para localhost
DB_LOCAL_URL=mysql+socket:///tmp/mysql.sock/trends?user=root&password=pass
DB_LOCAL_CAN_INSERT=false
DB_LOCAL_CAN_UPDATE=false
DB_LOCAL_CAN_DELETE=false
DB_LOCAL_CAN_DDL=false
DB_LOCAL_IS_DEFAULT=true
```

### Conexión con SSL

```env
DB_SECURE_URL=mysql://user:pass@secure-host:3306/db?ssl=true
DB_SECURE_CAN_INSERT=true
DB_SECURE_CAN_UPDATE=true
DB_SECURE_CAN_DELETE=false
DB_SECURE_CAN_DDL=false
```

---

## 🗄️ Configuración Multi-Database

### Ejemplo: Producción + Desarrollo + Test

```env
# ========================================
# PRODUCCIÓN (Solo Lectura)
# ========================================
DB_PRODUCTION_URL=mysql://root:pass@prod-server:3307/trends
DB_PRODUCTION_CAN_INSERT=false
DB_PRODUCTION_CAN_UPDATE=false
DB_PRODUCTION_CAN_DELETE=false
DB_PRODUCTION_CAN_DDL=false
DB_PRODUCTION_IS_DEFAULT=true  # Esta es la DB por defecto

# ========================================
# DESARROLLO (Full Access)
# ========================================
DB_DEVELOPMENT_URL=mysql://dev:devpass@localhost:3306/trends_dev
DB_DEVELOPMENT_CAN_INSERT=true
DB_DEVELOPMENT_CAN_UPDATE=true
DB_DEVELOPMENT_CAN_DELETE=true
DB_DEVELOPMENT_CAN_DDL=true

# ========================================
# TEST (Full Access)
# ========================================
DB_TEST_URL=mysql://test:testpass@localhost:3306/trends_test
DB_TEST_CAN_INSERT=true
DB_TEST_CAN_UPDATE=true
DB_TEST_CAN_DELETE=true
DB_TEST_CAN_DDL=true

# ========================================
# ANALYTICS (Solo Lectura)
# ========================================
DB_ANALYTICS_URL=mysql://analytics:pass@analytics-server:3306/analytics
DB_ANALYTICS_CAN_INSERT=false
DB_ANALYTICS_CAN_UPDATE=false
DB_ANALYTICS_CAN_DELETE=false
DB_ANALYTICS_CAN_DDL=false
```

---

## 🔐 Permisos Granulares

Cada base de datos puede tener permisos diferentes:

| Permiso | Variable | Descripción |
|---------|----------|-------------|
| **INSERT** | `DB_{NAME}_CAN_INSERT` | Permite `INSERT INTO` |
| **UPDATE** | `DB_{NAME}_CAN_UPDATE` | Permite `UPDATE` |
| **DELETE** | `DB_{NAME}_CAN_DELETE` | Permite `DELETE FROM` |
| **DDL** | `DB_{NAME}_CAN_DDL` | Permite `CREATE TABLE`, `ALTER`, etc. |

### Ejemplos de Configuraciones de Permisos

#### Read-Only (Producción)
```env
DB_PRODUCTION_CAN_INSERT=false
DB_PRODUCTION_CAN_UPDATE=false
DB_PRODUCTION_CAN_DELETE=false
DB_PRODUCTION_CAN_DDL=false
```

#### Insert-Only (Logging)
```env
DB_LOGS_CAN_INSERT=true
DB_LOGS_CAN_UPDATE=false
DB_LOGS_CAN_DELETE=false
DB_LOGS_CAN_DDL=false
```

#### Full Access (Desarrollo)
```env
DB_DEV_CAN_INSERT=true
DB_DEV_CAN_UPDATE=true
DB_DEV_CAN_DELETE=true
DB_DEV_CAN_DDL=true
```

---

## 📚 Ejemplos Completos

### Ejemplo 1: E-Commerce Multi-Ambiente

```env
# Producción (Ventas) - Solo Lectura
DB_SALES_URL=mysql://readonly:pass@prod-db:3306/sales
DB_SALES_CAN_INSERT=false
DB_SALES_CAN_UPDATE=false
DB_SALES_CAN_DELETE=false
DB_SALES_CAN_DDL=false
DB_SALES_IS_DEFAULT=true

# Inventario - INSERT/UPDATE (no DELETE)
DB_INVENTORY_URL=mysql://inventory:pass@inv-db:3306/inventory
DB_INVENTORY_CAN_INSERT=true
DB_INVENTORY_CAN_UPDATE=true
DB_INVENTORY_CAN_DELETE=false
DB_INVENTORY_CAN_DDL=false

# Analytics - Solo Lectura
DB_ANALYTICS_URL=mysql://analytics:pass@analytics-db:3306/reports
DB_ANALYTICS_CAN_INSERT=false
DB_ANALYTICS_CAN_UPDATE=false
DB_ANALYTICS_CAN_DELETE=false
DB_ANALYTICS_CAN_DDL=false

# Desarrollo Local - Full Access
DB_LOCAL_URL=mysql://root:root@localhost:3306/dev_db
DB_LOCAL_CAN_INSERT=true
DB_LOCAL_CAN_UPDATE=true
DB_LOCAL_CAN_DELETE=true
DB_LOCAL_CAN_DDL=true
```

### Ejemplo 2: Multi-Tenant SaaS

```env
# Tenant 1
DB_TENANT1_URL=mysql://tenant1:pass@db-cluster:3306/tenant_1
DB_TENANT1_CAN_INSERT=true
DB_TENANT1_CAN_UPDATE=true
DB_TENANT1_CAN_DELETE=false
DB_TENANT1_CAN_DDL=false

# Tenant 2
DB_TENANT2_URL=mysql://tenant2:pass@db-cluster:3306/tenant_2
DB_TENANT2_CAN_INSERT=true
DB_TENANT2_CAN_UPDATE=true
DB_TENANT2_CAN_DELETE=false
DB_TENANT2_CAN_DDL=false

# Shared Services
DB_SHARED_URL=mysql://shared:pass@shared-db:3306/shared_services
DB_SHARED_CAN_INSERT=false
DB_SHARED_CAN_UPDATE=false
DB_SHARED_CAN_DELETE=false
DB_SHARED_CAN_DDL=false
DB_SHARED_IS_DEFAULT=true
```

---

## 🔄 Migración desde Legacy

### Paso 1: Identificar Configuración Actual

```env
# Configuración Legacy
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3307
MYSQL_USER=root
MYSQL_PASS=eengeoS2
MYSQL_DB=trends
ALLOW_INSERT_OPERATION=false
ALLOW_UPDATE_OPERATION=false
ALLOW_DELETE_OPERATION=false
ALLOW_DDL_OPERATION=false
```

### Paso 2: Convertir a Connection String

```env
# Nueva Configuración
DB_TRENDS_URL=mysql://root:eengeoS2@127.0.0.1:3307/trends
DB_TRENDS_CAN_INSERT=false
DB_TRENDS_CAN_UPDATE=false
DB_TRENDS_CAN_DELETE=false
DB_TRENDS_CAN_DDL=false
DB_TRENDS_IS_DEFAULT=true
```

### Paso 3: Actualizar y Probar

```bash
# 1. Actualizar .env con nuevo formato
# 2. Reconstruir proyecto
npm run build

# 3. Reiniciar MCP server
claude mcp restart trends_mysql

# 4. Verificar logs
ENABLE_LOGGING=true npm start
```

### Compatibilidad

✅ **IMPORTANTE:** El sistema legacy sigue funcionando. Si no defines ningún `DB_*_URL`, el sistema usará automáticamente las variables `MYSQL_*`.

---

## 💻 API de Programación

### Cargar Configuración

```typescript
import { loadDatabasesFromEnv } from './src/utils/connection-string-parser.js';

// Cargar todas las databases desde .env
const config = loadDatabasesFromEnv(process.env);

// Ver databases configuradas
console.log(config.databases);
console.log('Default DB:', config.defaultDatabase);
```

### Usar Connection Manager

```typescript
import { getConnectionManager } from './src/db/multi-connection-manager.js';
import { multiDbConfig } from './src/config/index.js';

// Obtener manager
const manager = getConnectionManager(multiDbConfig);

// Obtener pool de conexión
const pool = manager.getPool('production');

// Ejecutar query
const results = await manager.executeQuery(
  'SELECT * FROM products LIMIT 10',
  'production'
);

// Listar databases disponibles
const databases = manager.listDatabases();
console.log('Available databases:', databases);
```

### Verificar Permisos

```typescript
import { isOperationAllowed, getDatabaseConfig } from './src/utils/index.js';

const dbConfig = getDatabaseConfig(multiDbConfig, 'production');

// Verificar si se puede insertar
if (isOperationAllowed(dbConfig!, 'insert')) {
  console.log('INSERT allowed');
} else {
  console.log('INSERT denied');
}
```

---

## 🔧 Troubleshooting

### Error: "Database configuration not found"

**Causa:** El nombre de la base de datos no existe en la configuración.

**Solución:**
```env
# Asegúrate de que el nombre coincida
DB_MYDB_URL=mysql://...  # Nombre: "mydb"

# Al usar en código:
manager.getPool('mydb')  // Usar lowercase
```

### Error: "Failed to parse connection string"

**Causa:** Formato de URL incorrecto.

**Solución:**
```env
# ❌ Incorrecto
DB_PROD_URL=root:pass@localhost/db

# ✅ Correcto
DB_PROD_URL=mysql://root:pass@localhost:3306/db
```

### Error: "Password contains special characters"

**Causa:** La contraseña tiene caracteres especiales que necesitan encoding.

**Solución:**
```env
# Contraseña: p@ss:word

# Encode caracteres especiales:
# @ → %40
# : → %3A

# ✅ Correcto
DB_PROD_URL=mysql://root:p%40ss%3Aword@localhost:3306/db
```

### Logs de Diagnóstico

```env
# Activar logs detallados
ENABLE_LOGGING=true
MYSQL_LOG_LEVEL=info
```

Revisa la consola para ver:
```
[info] Loaded database configuration: production (127.0.0.1:3307/trends)
[info] Created connection pool for database: production
```

---

## 📌 Resumen

### Ventajas del Nuevo Sistema

| Característica | Legacy | Connection Strings |
|---------------|--------|-------------------|
| Múltiples DBs | ❌ No | ✅ Sí |
| Permisos por DB | ❌ Global | ✅ Granular |
| Formato Compacto | ❌ 7 vars | ✅ 1 URL + permisos |
| Fácil Copiar | ❌ No | ✅ Sí |
| Compatible | ✅ Sí | ✅ Sí |

### Checklist de Migración

- [ ] Revisar configuración actual en `.env`
- [ ] Copiar `.env.connections.example` como referencia
- [ ] Convertir cada DB a formato Connection String
- [ ] Definir permisos granulares por DB
- [ ] Marcar una DB como default con `IS_DEFAULT=true`
- [ ] Reconstruir: `npm run build`
- [ ] Probar conexión con logs habilitados
- [ ] Verificar permisos de escritura funcionan correctamente

---

**¿Necesitas ayuda?** Abre un issue en el repositorio o consulta el README principal.

**Versión:** 2.0.3
**Última actualización:** Noviembre 2025
