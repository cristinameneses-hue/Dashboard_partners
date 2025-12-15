# Contributing to TrendsPro MCP Server

¡Gracias por tu interés en contribuir a TrendsPro! Este documento proporciona las pautas y mejores prácticas para contribuir al proyecto.

## Tabla de Contenidos

- [Código de Conducta](#código-de-conducta)
- [Git Flow Workflow](#git-flow-workflow)
- [Estructura de Branches](#estructura-de-branches)
- [Proceso de Contribución](#proceso-de-contribución)
- [Convenciones de Commits](#convenciones-de-commits)
- [Pull Requests](#pull-requests)
- [Testing](#testing)
- [Estándares de Código](#estándares-de-código)

---

## Código de Conducta

Este proyecto y todos los participantes están sujetos a un código de conducta. Al participar, se espera que mantengas este código. Por favor reporta comportamientos inaceptables a los mantenedores del proyecto.

## Git Flow Workflow

Este proyecto utiliza **Git Flow** como estrategia de branching. Git Flow es un modelo de ramificación que define una estructura estricta diseñada alrededor de los releases del proyecto.

### Ramas Principales

```
main (producción)
├── pre (pre-producción/staging)
│   └── develop (desarrollo activo)
│       ├── feature/* (nuevas características)
│       ├── bugfix/* (corrección de bugs)
│       └── refactor/* (refactorización)
├── hotfix/* (correcciones urgentes en producción)
└── release/* (preparación de releases)
```

## Estructura de Branches

### 1. Ramas Permanentes

#### `main`
- **Propósito**: Código en producción
- **Protección**: ✅ Protegida - Solo merges desde `release/*` o `hotfix/*`
- **Despliegue**: Automático a producción
- **Tags**: Cada merge a `main` debe tener un tag de versión (ej: `v2.1.0`)

#### `pre`
- **Propósito**: Pre-producción / Staging / QA
- **Source**: Merges desde `develop` o `release/*`
- **Testing**: Validación final antes de producción
- **Protección**: ✅ Protegida

#### `develop`
- **Propósito**: Rama principal de desarrollo
- **Source**: Base para `feature/*`, `bugfix/*`, `refactor/*`
- **Integración**: Todas las features se integran aquí primero
- **Protección**: ✅ Protegida

### 2. Ramas Temporales

#### `feature/*`
- **Propósito**: Desarrollo de nuevas características
- **Naming**: `feature/<nombre-descriptivo>`
- **Source**: Creada desde `develop`
- **Target**: Merge a `develop`
- **Ejemplos**:
  - `feature/add-postgresql-support`
  - `feature/improve-query-parser`
  - `feature/add-user-authentication`

#### `bugfix/*`
- **Propósito**: Corrección de bugs encontrados en desarrollo
- **Naming**: `bugfix/<nombre-descriptivo>`
- **Source**: Creada desde `develop`
- **Target**: Merge a `develop`
- **Ejemplos**:
  - `bugfix/fix-connection-pool-leak`
  - `bugfix/resolve-query-timeout`

#### `hotfix/*`
- **Propósito**: Correcciones urgentes en producción
- **Naming**: `hotfix/<version>-<descripcion>`
- **Source**: Creada desde `main`
- **Target**: Merge a `main` Y `develop`
- **Ejemplos**:
  - `hotfix/v2.1.1-critical-security-fix`
  - `hotfix/v2.1.2-database-connection-error`

#### `release/*`
- **Propósito**: Preparación para un nuevo release
- **Naming**: `release/<version>`
- **Source**: Creada desde `develop`
- **Target**: Merge a `main` y `develop`
- **Tareas**: Bumping de versión, cambios menores, actualización de CHANGELOG
- **Ejemplos**:
  - `release/v2.2.0`
  - `release/v3.0.0`

#### `refactor/*`
- **Propósito**: Refactorización de código sin cambiar funcionalidad
- **Naming**: `refactor/<nombre-descriptivo>`
- **Source**: Creada desde `develop`
- **Target**: Merge a `develop`
- **Ejemplos**:
  - `refactor/improve-error-handling`
  - `refactor/optimize-database-queries`

---

## Proceso de Contribución

### 1. Setup Inicial

```bash
# Fork el repositorio en GitHub

# Clonar tu fork
git clone https://github.com/tu-usuario/trends_mcp.git
cd trends_mcp

# Agregar el repositorio original como upstream
git remote add upstream https://github.com/original/trends_mcp.git

# Verificar remotes
git remote -v
```

### 2. Crear una Feature Branch

```bash
# Actualizar develop
git checkout develop
git pull upstream develop

# Crear nueva feature branch
git checkout -b feature/nombre-descriptivo

# Ejemplo:
git checkout -b feature/add-postgresql-support
```

### 3. Desarrollo

```bash
# Hacer cambios en el código
# ...

# Agregar cambios
git add .

# Commit con mensaje descriptivo (ver Convenciones de Commits)
git commit -m "feat: add PostgreSQL connection support"

# Push a tu fork
git push origin feature/add-postgresql-support
```

### 4. Mantener la Branch Actualizada

```bash
# Actualizar tu branch con los últimos cambios de develop
git checkout develop
git pull upstream develop
git checkout feature/add-postgresql-support
git rebase develop

# Resolver conflictos si existen
# ...

# Push con force (solo en tu branch de feature)
git push origin feature/add-postgresql-support --force-with-lease
```

### 5. Crear Pull Request

1. Ve a GitHub y crea un Pull Request desde tu `feature/*` branch hacia `develop` del repositorio original
2. Completa la plantilla de PR con:
   - Descripción clara de los cambios
   - Issue relacionado (si existe)
   - Screenshots (si aplica)
   - Checklist de testing

---

## Convenciones de Commits

Usamos **Conventional Commits** para mensajes de commit estructurados:

### Formato

```
<tipo>[scope opcional]: <descripción>

[cuerpo opcional]

[footer opcional]
```

### Tipos

- **feat**: Nueva característica
- **fix**: Corrección de bug
- **docs**: Cambios en documentación
- **style**: Cambios de formato (sin afectar funcionalidad)
- **refactor**: Refactorización de código
- **perf**: Mejoras de performance
- **test**: Agregar o modificar tests
- **build**: Cambios en build system o dependencias
- **ci**: Cambios en CI/CD
- **chore**: Tareas de mantenimiento

### Ejemplos

```bash
# Feature
git commit -m "feat: add support for PostgreSQL connections"

# Fix
git commit -m "fix: resolve memory leak in connection pool"

# Docs
git commit -m "docs: update installation instructions"

# Refactor
git commit -m "refactor: improve query parser performance"

# Breaking change
git commit -m "feat!: change API response format

BREAKING CHANGE: API now returns data in camelCase instead of snake_case"
```

---

## Pull Requests

### Checklist antes de crear PR

- [ ] El código compila sin errores (`npm run build`)
- [ ] Todos los tests pasan (`npm test`)
- [ ] Linter pasa sin errores (`npm run lint`)
- [ ] Agregaste tests para nueva funcionalidad
- [ ] Actualizaste la documentación (README, comentarios)
- [ ] El código sigue los estándares del proyecto
- [ ] Hiciste rebase con `develop` reciente
- [ ] El commit message sigue Conventional Commits

### Plantilla de PR

```markdown
## Descripción
Breve descripción de los cambios realizados.

## Tipo de cambio
- [ ] Bug fix (non-breaking change)
- [ ] Nueva feature (non-breaking change)
- [ ] Breaking change (fix o feature que causa cambios en funcionalidad existente)
- [ ] Documentación

## ¿Cómo se ha testeado?
Describe las pruebas realizadas.

## Checklist
- [ ] Mi código sigue los estándares del proyecto
- [ ] He realizado self-review de mi código
- [ ] He comentado código complejo
- [ ] He actualizado la documentación
- [ ] Mis cambios no generan nuevas warnings
- [ ] He agregado tests
- [ ] Tests nuevos y existentes pasan localmente
```

### Code Review

- Todos los PRs requieren al menos 1 aprobación
- Los mantenedores revisarán el código en máximo 48 horas
- Responde a comentarios y realiza cambios solicitados
- Una vez aprobado, los mantenedores harán el merge

---

## Testing

### Ejecutar Tests

```bash
# Todos los tests
npm test

# Tests unitarios
npm run test:unit

# Tests de integración
npm run test:integration

# Tests E2E
npm run test:e2e

# Tests con coverage
npm run test:coverage

# Tests en modo watch
npm run test:watch
```

### Escribir Tests

- **Unitarios**: Para funciones puras y lógica de negocio
- **Integración**: Para interacción entre módulos
- **E2E**: Para flujos completos de usuario

```typescript
// Ejemplo de test unitario
describe('ConnectionStringParser', () => {
  it('should parse MySQL connection string correctly', () => {
    const result = parseConnectionString('mysql://user:pass@host:3306/db');
    expect(result.protocol).toBe('mysql');
    expect(result.host).toBe('host');
    expect(result.port).toBe(3306);
  });
});
```

---

## Estándares de Código

### TypeScript

- Usar `strict: true` en tsconfig.json
- Evitar `any` - usar types específicos
- Documentar funciones públicas con JSDoc
- Usar `const` por defecto, `let` solo cuando sea necesario
- Preferir arrow functions para callbacks

```typescript
/**
 * Parses a database connection string
 * @param connectionString - The connection string to parse
 * @returns Parsed connection object
 * @throws Error if connection string is invalid
 */
export const parseConnectionString = (
  connectionString: string
): ParsedConnection => {
  // Implementation
};
```

### Python

- Seguir PEP 8
- Type hints para funciones públicas
- Docstrings para módulos, clases y funciones
- Máximo 100 caracteres por línea

```python
def execute_query(query: str, params: dict = None) -> List[dict]:
    """
    Execute a database query with optional parameters.

    Args:
        query: SQL query to execute
        params: Optional query parameters

    Returns:
        List of result rows as dictionaries

    Raises:
        DatabaseError: If query execution fails
    """
    # Implementation
```

### Naming Conventions

- **TypeScript**:
  - Variables/Functions: `camelCase`
  - Classes/Interfaces: `PascalCase`
  - Constants: `UPPER_SNAKE_CASE`
  - Private members: `_prefixed`

- **Python**:
  - Variables/Functions: `snake_case`
  - Classes: `PascalCase`
  - Constants: `UPPER_SNAKE_CASE`
  - Private: `_prefixed`

---

## Workflow Completo - Ejemplo

### Desarrollar una nueva feature

```bash
# 1. Actualizar develop
git checkout develop
git pull upstream develop

# 2. Crear feature branch
git checkout -b feature/add-redis-cache

# 3. Desarrollar
# ... hacer cambios ...

# 4. Commit
git add .
git commit -m "feat: add Redis caching layer for query results"

# 5. Tests
npm test
npm run lint

# 6. Push
git push origin feature/add-redis-cache

# 7. Crear PR en GitHub hacia develop

# 8. Después del merge, limpiar
git checkout develop
git pull upstream develop
git branch -d feature/add-redis-cache
```

### Crear un Release

```bash
# 1. Crear release branch desde develop
git checkout develop
git pull upstream develop
git checkout -b release/v2.2.0

# 2. Bump version en package.json
npm version 2.2.0

# 3. Actualizar CHANGELOG.md

# 4. Commit
git commit -am "chore: bump version to 2.2.0"

# 5. Merge a pre para testing
git checkout pre
git merge release/v2.2.0

# 6. Testing en staging...

# 7. Merge a main
git checkout main
git merge release/v2.2.0

# 8. Tag
git tag -a v2.2.0 -m "Release v2.2.0"

# 9. Merge de vuelta a develop
git checkout develop
git merge release/v2.2.0

# 10. Push todo
git push upstream main develop pre --tags

# 11. Limpiar
git branch -d release/v2.2.0
```

### Hotfix Urgente

```bash
# 1. Crear hotfix desde main
git checkout main
git pull upstream main
git checkout -b hotfix/v2.1.1-critical-fix

# 2. Fix the issue
# ... hacer cambios ...

# 3. Commit
git commit -am "fix: resolve critical security vulnerability"

# 4. Tests
npm test

# 5. Merge a main
git checkout main
git merge hotfix/v2.1.1-critical-fix

# 6. Tag
git tag -a v2.1.1 -m "Hotfix v2.1.1 - Critical security fix"

# 7. Merge a develop
git checkout develop
git merge hotfix/v2.1.1-critical-fix

# 8. Push
git push upstream main develop --tags

# 9. Limpiar
git branch -d hotfix/v2.1.1-critical-fix
```

---

## Recursos Adicionales

- [Git Flow Original](https://nvie.com/posts/a-successful-git-branching-model/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Semantic Versioning](https://semver.org/)
- [GitHub Flow](https://docs.github.com/en/get-started/quickstart/github-flow)

---

## Preguntas o Problemas

Si tienes preguntas o encuentras problemas:

1. Revisa los [Issues existentes](https://github.com/original/trends_mcp/issues)
2. Crea un nuevo Issue con todos los detalles
3. Únete a nuestro canal de Discord/Slack (si aplica)

---

**¡Gracias por contribuir a TrendsPro MCP Server!** 🚀
