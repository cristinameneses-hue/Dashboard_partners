# 🔄 CONTEXTO DE MIGRACIÓN - TrendsPro Clean Architecture

> **IMPORTANTE**: Este es el documento maestro para continuar la refactorización.
> **Fecha**: 2025-01-17
> **Progreso**: 85% Completado
> **Estado**: Sistema funcional pero requiere migración Flask y tests

---

## 📌 RESUMEN EJECUTIVO PARA CONTINUAR

### Estado Actual
Hemos migrado exitosamente de un monolito Flask de ~2,500 líneas a una arquitectura Clean Architecture con:
- ✅ **3 capas completas**: Domain, Infrastructure, Presentation
- ✅ **DI Container**: Inyección de dependencias completa
- ✅ **Bootstrap System**: Inicialización robusta con health checks
- ✅ **FastAPI**: Nueva API con streaming y middleware
- ⏳ **Flask**: Aún funcionando, requiere adaptador para migración

### Lo que puedes hacer AHORA
```bash
# El sistema actual Flask SIGUE FUNCIONANDO:
cd web
python server_unified.py  # Flask original - FUNCIONA

# La nueva arquitectura FastAPI está LISTA pero no integrada:
cd ..
python -m presentation.api.main  # FastAPI nueva - FUNCIONA INDEPENDIENTE
```

---

## 🗂️ ESTRUCTURA DE ARCHIVOS CRÍTICOS

### 1. ARCHIVOS DE CONTEXTO (Leer primero)
```
📁 trends_mcp/
│
├── 📄 MIGRATION_CONTEXT.md          # ESTE ARCHIVO - Contexto completo
├── 📄 REFACTORING_STATUS.md         # Estado detallado del refactoring (85%)
├── 📄 CLAUDE.md                      # Documentación técnica completa
└── 📄 .claude/CLAUDE.md              # Instrucciones para Claude
```

### 2. NUEVA ARQUITECTURA IMPLEMENTADA
```
📁 domain/                            # ✅ 100% COMPLETADO
├── entities/
│   ├── query.py                     # Entidad Query (306 líneas)
│   ├── database.py                  # Entidad Database (375 líneas)
│   ├── conversation.py              # Entidad Conversation (431 líneas)
│   └── user.py                      # Entidad User (524 líneas)
│
├── value_objects/
│   ├── database_type.py             # Enum de tipos de BD
│   ├── query_result.py              # Resultado de queries
│   ├── routing_decision.py          # Decisión de routing
│   └── query_intent.py              # Intención de query
│
├── repositories/
│   └── interfaces.py                # Interfaces de repositorios
│
├── services/
│   └── query_router.py              # ✅ Servicio de routing (528 líneas)
│
└── use_cases/
    ├── execute_query.py             # ✅ Caso de uso principal (478 líneas)
    ├── streaming_query.py           # ✅ Streaming queries (412 líneas)
    └── conversation_manager.py      # ✅ Gestión conversaciones (520 líneas)

📁 infrastructure/                    # ✅ 100% COMPLETADO
├── repositories/
│   ├── mysql_repository.py          # Repositorio MySQL async
│   ├── mongodb_repository.py        # Repositorio MongoDB async
│   ├── openai_llm_repository.py     # Repositorio OpenAI
│   └── chatgpt_llm_repository.py    # Repositorio ChatGPT
│
├── services/
│   ├── database_connection_factory.py # Factory de conexiones
│   └── prompt_manager.py            # Gestión de prompts
│
├── di/
│   └── container.py                 # ✅ DI Container completo (600+ líneas)
│
└── bootstrap/
    ├── bootstrap.py                 # ✅ Bootstrap system (400+ líneas)
    ├── environment.py               # ✅ Gestión de config (350+ líneas)
    ├── logging.py                   # ✅ Logging estructurado (300+ líneas)
    └── health_check.py              # ✅ Health checks (250+ líneas)

📁 presentation/                      # ⚠️ 85% COMPLETADO
├── api/
│   ├── main.py                     # ✅ FastAPI app principal (340 líneas)
│   ├── schemas/                    # ✅ Schemas Pydantic
│   │   ├── query_schemas.py        # Schemas de queries
│   │   ├── conversation_schemas.py # Schemas de conversaciones
│   │   └── common_schemas.py       # Schemas comunes
│   ├── routers/                    # ✅ Routers FastAPI
│   │   ├── query_router.py         # Router de queries
│   │   ├── conversation_router.py  # Router de conversaciones
│   │   └── health_router.py        # Router de health
│   └── dependencies/               # ✅ Dependencies FastAPI
│       ├── auth.py                # Autenticación JWT
│       └── database.py             # Inyección de DB
```

### 3. CÓDIGO LEGACY (Aún en uso)
```
📁 web/                              # ⚠️ FLASK ACTUAL - EN PRODUCCIÓN
├── server_unified.py                # Servidor Flask actual (funciona)
├── unified_database_manager.py      # Manager de BD actual (funciona)
└── requirements.txt                 # Dependencies Python

📁 templates/                        # Frontend actual
├── index.html                       # Interfaz web
└── login.html                       # Login

📁 static/                          # Assets
├── css/style.css
└── js/app.js
```

---

## 🚨 LO QUE FALTA (15% restante)

### 1. ADAPTADOR FLASK → FASTAPI (5%)
```python
# NECESITAS CREAR: infrastructure/adapters/flask_adapter.py
"""
Adaptador para migrar gradualmente de Flask a FastAPI.
Permite que ambos sistemas coexistan durante la migración.
"""

class FlaskToFastAPIAdapter:
    def __init__(self, flask_app, fastapi_app):
        self.flask_app = flask_app
        self.fastapi_app = fastapi_app

    def route_to_fastapi(self, path):
        """Redirige rutas específicas a FastAPI"""
        # TODO: Implementar proxy de Flask a FastAPI
        pass

    def migrate_session(self):
        """Migra sesión de Flask a JWT"""
        # TODO: Convertir session Flask a JWT token
        pass
```

### 2. SCRIPT DE MIGRACIÓN (2%)
```python
# NECESITAS CREAR: scripts/migrate_to_clean.py
"""
Script que detecta el modo y arranca el sistema apropiado.
"""

import os
import sys

def main():
    mode = os.getenv('ARCHITECTURE_MODE', 'legacy')

    if mode == 'clean':
        # Arrancar FastAPI con Bootstrap
        from infrastructure.bootstrap import Bootstrap, BootstrapConfig
        # TODO: Implementar arranque clean
    else:
        # Arrancar Flask legacy
        from web.server_unified import app
        # TODO: Implementar arranque legacy
```

### 3. CONFIGURACIÓN .ENV (1%)
```env
# NECESITAS ACTUALIZAR: .env
# Agregar estas variables:

# Modo de arquitectura
ARCHITECTURE_MODE=transitional  # legacy | transitional | clean

# Configuración de Bootstrap
ENABLE_HEALTH_CHECKS=true
ENABLE_CACHE_WARMING=false
ENABLE_METRICS=true

# Configuración de migración
MIGRATION_PROXY_ENABLED=true
MIGRATION_ROUTES=/api/v1/queries,/api/v1/conversations
```

### 4. TESTS CRÍTICOS (5%)
```python
# NECESITAS CREAR: tests/integration/test_critical_paths.py
"""
Tests de los flujos críticos del sistema.
"""

import pytest
from infrastructure.bootstrap import Bootstrap, BootstrapConfig

@pytest.mark.asyncio
async def test_query_execution_e2e():
    """Test completo de ejecución de query"""
    # TODO: Implementar test E2E
    pass

@pytest.mark.asyncio
async def test_mysql_mongodb_routing():
    """Test de routing entre bases de datos"""
    # TODO: Implementar test de routing
    pass

@pytest.mark.asyncio
async def test_health_checks():
    """Test de health checks del sistema"""
    # TODO: Implementar test de health
    pass
```

### 5. VALIDACIÓN FINAL (2%)
```python
# NECESITAS CREAR: scripts/validate_migration.py
"""
Script de validación que verifica que todo funciona.
"""

async def validate_all():
    checks = [
        check_mysql_connection(),
        check_mongodb_connection(),
        check_openai_api(),
        check_fastapi_endpoints(),
        check_flask_compatibility(),
    ]
    # TODO: Implementar validaciones
```

---

## 📝 INSTRUCCIONES PARA CONTINUAR

### OPCIÓN A: Completar migración (Recomendado)

1. **Crear el adaptador Flask-FastAPI**:
```bash
# Crear el archivo
touch infrastructure/adapters/flask_adapter.py

# Implementar el adaptador siguiendo el template de arriba
```

2. **Actualizar el archivo .env**:
```bash
# Agregar las nuevas variables
echo "ARCHITECTURE_MODE=transitional" >> .env
```

3. **Crear script de migración**:
```bash
# Crear y ejecutar
python scripts/migrate_to_clean.py
```

4. **Ejecutar tests críticos**:
```bash
# Crear tests mínimos
pytest tests/integration/test_critical_paths.py -v
```

### OPCIÓN B: Usar nueva arquitectura directamente

1. **Arrancar solo FastAPI** (sin Flask):
```bash
# Configurar para clean architecture
export ARCHITECTURE_MODE=clean

# Arrancar con bootstrap
python -m presentation.api.main
```

2. **Actualizar frontend** para apuntar a nuevos endpoints:
```javascript
// En static/js/app.js cambiar:
const API_BASE = '/api/v1';  // Nueva API
// En lugar de:
const API_BASE = '';  // API legacy
```

---

## 🔍 CÓMO RECUPERAR EL CONTEXTO

### Para Claude o cualquier LLM:

1. **Proporciona estos archivos en orden**:
   - `MIGRATION_CONTEXT.md` (este archivo)
   - `REFACTORING_STATUS.md`
   - `infrastructure/di/container.py`
   - `infrastructure/bootstrap/bootstrap.py`

2. **Prompt sugerido**:
```
Estoy continuando una refactorización de Flask a FastAPI con Clean Architecture.
El progreso está al 85%. El sistema legacy Flask funciona y la nueva arquitectura
FastAPI está completa pero no integrada. Necesito completar el adaptador Flask-FastAPI
para permitir una migración gradual. Los archivos de contexto están adjuntos.
```

### Para desarrollo manual:

1. **Verificar que todo funciona**:
```bash
# Test Flask legacy
cd web && python server_unified.py

# Test FastAPI nueva (en otra terminal)
cd .. && python -m presentation.api.main
```

2. **Revisar los TODOs**:
```bash
# Buscar TODOs pendientes
grep -r "TODO" domain/ infrastructure/ presentation/
```

---

## 🎯 DEFINICIÓN DE "COMPLETO"

El sistema estará 100% completo cuando:

✅ **Funcional**:
- [ ] Flask y FastAPI pueden correr simultáneamente
- [ ] Adaptador permite migración gradual de rutas
- [ ] Sesiones de Flask se convierten a JWT
- [ ] Frontend funciona con ambas APIs

✅ **Calidad**:
- [ ] Tests críticos pasando (>3 tests E2E)
- [ ] Health checks reportando "healthy"
- [ ] Sin errores en logs durante arranque
- [ ] Documentación OpenAPI accesible en /docs

✅ **Producción**:
- [ ] Script de arranque unificado funciona
- [ ] Variables de entorno documentadas
- [ ] Modo "clean" arranca sin dependencias legacy
- [ ] README actualizado con nuevas instrucciones

---

## 💡 TIPS IMPORTANTES

### 1. NO rompas el sistema actual
- Flask DEBE seguir funcionando durante la migración
- Usa el modo "transitional" para tener ambos sistemas

### 2. Prioriza la funcionalidad sobre la perfección
- Tests mínimos primero, completos después
- Documentación básica primero, detallada después

### 3. Rutas de migración sugeridas
```
Semana 1: /health y /metrics (bajo riesgo)
Semana 2: /api/v1/queries (alto valor)
Semana 3: /api/v1/conversations (complejo)
Semana 4: Frontend completo
```

### 4. Rollback siempre posible
```bash
# Si algo falla, volver a Flask puro:
export ARCHITECTURE_MODE=legacy
python web/server_unified.py
```

---

## 📊 MÉTRICAS DE ÉXITO

Sabrás que la migración fue exitosa cuando:

1. **Performance**: FastAPI responde 2x más rápido que Flask
2. **Mantenibilidad**: Nuevos features toman 50% menos tiempo
3. **Testing**: Coverage > 80% en código nuevo
4. **Estabilidad**: 0 errores críticos en 7 días
5. **Developer Experience**: Onboarding < 2 horas

---

## 🆘 PROBLEMAS COMUNES Y SOLUCIONES

### "ImportError: No module named 'domain'"
```bash
# Agregar al PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:${PWD}"
```

### "Connection refused" en MySQL/MongoDB
```bash
# Verificar que los servicios están corriendo
docker ps  # Si usas Docker
# o
systemctl status mysql mongodb
```

### "OpenAI API key not found"
```bash
# Verificar .env
cat .env | grep OPENAI_API_KEY
```

### "FastAPI no arranca"
```bash
# Verificar dependencias
pip install -r requirements.txt
pip install fastapi uvicorn pydantic
```

---

## 📅 TIMELINE SUGERIDO

### Si tienes 2 horas:
1. Crear adaptador básico (45 min)
2. Tests críticos (45 min)
3. Validación (30 min)

### Si tienes 1 día:
1. Adaptador completo (2h)
2. Migración de configuración (1h)
3. Tests completos (2h)
4. Documentación (1h)
5. Deployment scripts (2h)

### Si tienes 1 semana:
- Días 1-2: Adaptador y migración
- Días 3-4: Testing exhaustivo
- Día 5: Documentación y training
- Días 6-7: Deployment y monitoring

---

## 🏁 CHECKLIST FINAL

Antes de considerar terminada la migración:

- [ ] README.md actualizado
- [ ] .env.example con todas las variables
- [ ] Tests pasando (mínimo 3 E2E)
- [ ] Health endpoint respondiendo
- [ ] Logs sin errores en arranque
- [ ] FastAPI docs accesible
- [ ] Script de migración funcional
- [ ] Instrucciones de rollback documentadas
- [ ] Equipo entrenado en nueva arquitectura
- [ ] Backup de base de datos realizado

---

## 📞 CONTACTO Y REFERENCIAS

**Arquitectura**: Clean Architecture + DDD + SOLID
**Stack**: FastAPI + MySQL + MongoDB + OpenAI
**Progreso**: 85% (Falta adaptador y tests)

**Archivos clave para contexto**:
1. `MIGRATION_CONTEXT.md` (este archivo)
2. `REFACTORING_STATUS.md`
3. `infrastructure/di/container.py`
4. `infrastructure/bootstrap/bootstrap.py`

---

*Última actualización: 2025-01-17*
*Siguiente paso crítico: Crear adaptador Flask-FastAPI*
*Tiempo estimado para 100%: 2-4 horas de desarrollo*