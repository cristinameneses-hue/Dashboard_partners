# 🚀 Luda Mind - Sistema Inteligente de Consultas de Datos

> **Sistema de consultas en lenguaje natural con interpretación semántica inteligente**

[![Python](https://img.shields.io/badge/Python-3.8+-green.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0+-green.svg)](https://flask.palletsprojects.com/)
[![MongoDB](https://img.shields.io/badge/MongoDB-Latest-green.svg)](https://www.mongodb.com/)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-green.svg)](https://openai.com/)

---

## 📖 ¿Qué es Luda Mind?

Luda Mind es un sistema inteligente que permite realizar consultas a bases de datos usando **lenguaje natural en español**. 

El sistema combina:
- 🧠 **Interpretación Semántica** con diccionario de keywords → campos de BD
- ⚡ **Modo Híbrido** (queries predefinidas rápidas + interpretación flexible)
- 🎯 **4 Modos Especializados** (Farmacias, Productos, Partners, Conversacional)
- 💚 **UI Profesional** con branding corporativo verde

---

## ✨ Características Principales

### 🧠 Sistema de Interpretación Inteligente
- **Diccionario semántico** que mapea palabras clave → campos de MongoDB
- **GPT-4o-mini** con contexto de negocio para interpretar queries flexibles
- **Modo híbrido**: Rápido para queries comunes, inteligente para queries nuevas

### 🎯 4 Modos de Consulta
- **🏥 Farmacias**: Análisis por establecimiento
- **💊 Productos**: Catálogo, precios, disponibilidad  
- **🤝 Partners**: GMV, pedidos, rendimiento de canales
- **💬 Conversacional**: Análisis abiertos y KPIs

### 💰 GMV Híbrido Robusto
- Usa `thirdUser.price` si existe
- Calcula desde `items[].pvp × quantity` si no
- Separa **Ecommerce** vs **Shortage** (transferencias internas)

### 🎨 UX Optimizada
- Historial de consultas persistente (localStorage)
- Ejemplos desplegables al seleccionar modo
- Renderizado de Markdown → HTML elegante
- Branding corporativo verde (#41A837)

---

## 🚀 Inicio Rápido

### 1. Requisitos

- Python 3.8+
- MongoDB accesible
- MySQL (solo para sell in/sell out)
- OpenAI API Key

### 2. Instalación

```bash
# Clonar repositorio
git clone <repo-url>
cd trends_mcp

# Instalar dependencias
pip install -r requirements.txt

# Configurar credenciales
# Editar .env con tus credenciales
```

### 3. Lanzar la Aplicación

```bash
python presentation/api/app_luda_mind.py
```

### 4. Acceder

```
http://localhost:5000
```

---

## 📁 Estructura del Proyecto

```
trends_mcp/
├── 📄 README.md                          ← Este archivo
├── 📄 DEVELOPMENT_STANDARDS.md           ← Estándares de código
├── 📄 SECURITY_BEST_PRACTICES.md         ← Prácticas de seguridad
├── 📄 AI_CONTEXT_GUIDE.md                ← Guía para Claude
├── 📄 RESUMEN_SESION_COMPLETA.md         ← Estado actual del proyecto
│
├── 📁 docs/                              ← Documentación técnica
│   ├── DICCIONARIO_SEMANTICO_FINAL.md    ← Estructura BD validada
│   ├── PARTNERS_ACTIVOS_VALIDADOS.md     ← 12 partners oficiales
│   ├── GMV_HIBRIDO_IMPLEMENTADO.md       ← Lógica de GMV
│   ├── MODO_HIBRIDO_IMPLEMENTADO.md      ← Sistema actual
│   ├── ARCHITECTURE_AGENTS.md            ← Arquitectura multi-agente
│   ├── QUICK_START.md                    ← Guía de inicio
│   ├── DATABASE_CONFIG.md                ← Configuración BD
│   └── archive/                          ← Docs históricos
│
├── 📁 domain/                            ← Domain Layer (Clean Architecture)
│   ├── entities/                         ← Entidades de negocio
│   ├── repositories/                     ← Interfaces de repositorios
│   ├── services/                         ← Servicios de dominio
│   ├── use_cases/                        ← Casos de uso
│   ├── value_objects/                    ← Value Objects
│   └── knowledge/
│       └── semantic_mapping.py           ← Diccionario semántico
│
├── 📁 infrastructure/                    ← Infrastructure Layer
│   ├── bootstrap/                        ← Sistema de inicialización
│   ├── di/                               ← Dependency Injection
│   ├── repositories/                     ← Implementaciones concretas
│   └── services/                         ← Servicios de infraestructura
│
├── 📁 presentation/                      ← Presentation Layer
│   ├── api/
│   │   ├── app_luda_mind.py             ← 🚀 APLICACIÓN PRINCIPAL
│   │   ├── routers/                      ← FastAPI routers (futuro)
│   │   └── schemas/                      ← Pydantic schemas
│   └── web/
│       ├── static/
│       │   └── LUDA-LOGO-HOR-COLOR.svg
│       └── templates/
│           └── index_luda_mind_v2.html  ← UI ACTUAL
│
├── 📁 scripts/                           ← Scripts de utilidad
│   ├── migrate_to_clean.py
│   ├── validate_migration.py
│   └── setup/                            ← Scripts de configuración
│
└── 📁 tests/                             ← Tests
    ├── e2e_test_modes.py                 ← E2E principal
    ├── test_template.py                  ← Template para tests
    └── integration/                      ← Tests de integración
```

---

## 💡 Uso

### Ejemplos de Queries

#### 🏥 Modo Farmacias
```
"Mostrar farmacias activas en Madrid"
"Total de farmacias registradas"
"Farmacias por ciudad"
```

#### 💊 Modo Productos
```
"Catálogo de productos disponibles"
"Productos activos vs inactivos"
"Precio del producto con código 154653"
```

#### 🤝 Modo Partners
```
"GMV de Glovo esta semana"
"Comparación entre Glovo y Uber"
"Pedidos totales por partner"
```

#### 💬 Modo Conversacional
```
"Dame un resumen ejecutivo del mes"
"Cuáles son los principales KPIs"
"Qué anomalías detectas en los datos"
```

---

## 🧠 Sistema de Interpretación Inteligente

### Modo Híbrido

**Queries Predefinidas** (⚡ Rápidas ~100ms):
- GMV de partners conocidos
- Farmacias por ciudad
- Totales básicos
- Usa lógica optimizada hardcoded

**Queries No Predefinidas** (🧠 Flexibles ~500ms):
- "Cuántas boticas en Valencia" (synonym)
- "Qué marketplace más ingresos" (keyword alternativa)
- "Precio producto 154653" (búsqueda flexible)
- Usa diccionario semántico + GPT

**Modo Conversacional** (💬 Siempre Inteligente):
- TODAS las queries usan interpretación semántica
- Máxima flexibilidad
- Sin restricciones de patterns

---

## 📊 Base de Datos

### MongoDB (Principal)
- **Farmacias**: description, contact.city, active
- **Productos**: description, code (CN), ean13
- **Bookings**: pedidos con thirdUser (partners) u origin (shortages)
- **Stock**: quantity, pvp, pva por farmacia

### MySQL (Solo Sell In/Sell Out)
- Datos de ventas y análisis temporal
- Reservado para reporting específico

### 12 Partners Activos
glovo, glovo-otc, uber, justeat, carrefour, amazon, danone, procter, enna, nordic, chiesi, ferrer

---

## 🔒 Seguridad

- ✅ Credenciales en `.env` (nunca en código)
- ✅ Queries parametrizadas
- ✅ Validación de inputs
- ✅ Pre-commit hooks para detectar credenciales
- ✅ Principios SOLID aplicados
- ✅ Clean Architecture

Ver: `SECURITY_BEST_PRACTICES.md`

---

## 🛠️ Desarrollo

### Estándares de Código

Ver: `DEVELOPMENT_STANDARDS.md`

- Clean Architecture (Domain, Infrastructure, Presentation)
- Principios SOLID
- Type hints obligatorios
- Docstrings en español
- Coverage mínimo 80%

### Pre-commit Hooks

```bash
# Instalar hooks
pip install pre-commit
pre-commit install

# Ejecutar manualmente
pre-commit run --all-files
```

---

## 📚 Documentación

- **[ARCHITECTURE.md](docs/ARCHITECTURE_AGENTS.md)** - Arquitectura técnica completa
- **[DEVELOPMENT_STANDARDS.md](DEVELOPMENT_STANDARDS.md)** - Estándares de desarrollo
- **[SECURITY_BEST_PRACTICES.md](SECURITY_BEST_PRACTICES.md)** - Seguridad
- **[AI_CONTEXT_GUIDE.md](AI_CONTEXT_GUIDE.md)** - Guía para Claude
- **[DICCIONARIO_SEMANTICO_FINAL.md](docs/DICCIONARIO_SEMANTICO_FINAL.md)** - Estructura BD
- **[GMV_HIBRIDO_IMPLEMENTADO.md](docs/GMV_HIBRIDO_IMPLEMENTADO.md)** - Lógica GMV
- **[MODO_HIBRIDO_IMPLEMENTADO.md](docs/MODO_HIBRIDO_IMPLEMENTADO.md)** - Sistema híbrido

---

## 🎯 Estado Actual

**Versión:** 4.4.0  
**Estado:** ✅ Producción  
**Última Actualización:** 20 Noviembre 2024

### Implementado y Funcionando:
- ✅ Branding Luda Mind (verde corporativo)
- ✅ Sistema semántico con 18 campos mapeados
- ✅ Modo híbrido (predefinidas + flexibles)
- ✅ GMV híbrido robusto
- ✅ 12 partners activos validados
- ✅ Markdown rendering elegante
- ✅ UX optimizada con historial

Ver: **[RESUMEN_SESION_COMPLETA.md](RESUMEN_SESION_COMPLETA.md)** para estado detallado

---

## 🤝 Contribuir

Ver [CONTRIBUTING.md](docs/CONTRIBUTING.md) para guías de contribución.

---

## 📞 Soporte

Para dudas o issues, consultar la documentación en `/docs/`

---

**💚 Luda Mind - IA para tus datos farmacéuticos**

*Construido con Clean Architecture y principios SOLID*