# 📋 ESTÁNDARES DE DESARROLLO - TrendsPro

## 🎯 Principio Fundamental
**"Código de producción SIEMPRE seguro y escalable. Tests pueden ser más flexibles."**

## ✅ Reglas OBLIGATORIAS para Código de Producción

### 1. 🔒 SEGURIDAD

#### SIEMPRE:
```python
# ✅ CORRECTO - Credenciales desde variables de entorno
from dotenv import load_dotenv
load_dotenv()

db_password = os.getenv('DB_PASSWORD')
api_key = os.getenv('API_KEY')
```

#### NUNCA:
```python
# ❌ PROHIBIDO - Credenciales hardcodeadas
db_password = "mi_password_123"  # NUNCA!
api_key = "sk-abc123..."  # NUNCA!
```

### 2. 🏗️ ARQUITECTURA CLEAN

```
proyecto/
├── domain/              # Lógica de negocio pura
│   ├── entities/       # Entidades del dominio
│   ├── use_cases/      # Casos de uso
│   └── interfaces/     # Contratos/interfaces
├── infrastructure/      # Implementaciones externas
│   ├── repositories/   # Acceso a datos
│   ├── services/       # Servicios externos
│   └── config/        # Configuración
├── presentation/       # Capa de presentación
│   ├── api/           # Endpoints REST
│   ├── web/           # Interfaz web
│   └── cli/           # Interfaz CLI
└── tests/             # Tests (pueden ser más flexibles)
```

### 3. 🎨 PRINCIPIOS SOLID

#### Single Responsibility
```python
# ✅ CORRECTO - Una responsabilidad por clase
class UserRepository:
    def get_user(self, id): pass
    def save_user(self, user): pass

class EmailService:
    def send_email(self, email): pass

# ❌ INCORRECTO - Múltiples responsabilidades
class UserManager:
    def get_user(self, id): pass
    def save_user(self, user): pass
    def send_email(self, email): pass  # No debería estar aquí!
```

#### Dependency Injection
```python
# ✅ CORRECTO - Inyección de dependencias
class UserService:
    def __init__(self, repository: UserRepository, email_service: EmailService):
        self.repository = repository
        self.email_service = email_service

# ❌ INCORRECTO - Dependencias hardcodeadas
class UserService:
    def __init__(self):
        self.repository = MySQLUserRepository()  # Acoplado!
        self.email_service = GmailService()      # Acoplado!
```

### 4. 🛡️ MANEJO DE ERRORES

```python
# ✅ CORRECTO - Manejo específico y logging
try:
    result = database.query(sql)
except DatabaseConnectionError as e:
    logger.error(f"Database connection failed: {str(e)[:100]}")  # Truncar info sensible
    raise ServiceUnavailableError("Database temporarily unavailable")
except QueryError as e:
    logger.warning(f"Query failed: {str(e)[:100]}")
    return default_value

# ❌ INCORRECTO - Catch genérico sin contexto
try:
    result = database.query(sql)
except:
    pass  # NUNCA silenciar errores!
```

### 5. 📝 DOCUMENTACIÓN

```python
# ✅ CORRECTO - Documentación clara
def calculate_risk_score(product: Product, sales_data: List[Sale]) -> float:
    """
    Calculate risk score for a product based on sales patterns.
    
    Args:
        product: Product entity with attributes
        sales_data: Historical sales data (last 90 days)
    
    Returns:
        Risk score between 0.0 (low risk) and 1.0 (high risk)
    
    Raises:
        InsufficientDataError: If less than 30 days of data
    """
    if len(sales_data) < 30:
        raise InsufficientDataError("Need at least 30 days of data")
    
    # Implementation...
    return risk_score
```

### 6. 🔄 VERSIONADO Y GIT

```bash
# ✅ CORRECTO - Commits descriptivos
git commit -m "feat: Add MongoDB connection pooling for better performance"
git commit -m "fix: Resolve SQL injection vulnerability in search endpoint"
git commit -m "docs: Update API documentation with new endpoints"

# ❌ INCORRECTO - Commits sin contexto
git commit -m "fix"
git commit -m "updates"
git commit -m "asdfasdf"
```

### 7. 🧪 TESTING OBLIGATORIO

```python
# Para cada función/clase de producción, DEBE existir un test
# src/services/user_service.py → tests/services/test_user_service.py

# Coverage mínimo: 80%
# Critical paths: 100%
```

## 🧪 Excepciones Permitidas en TESTS

### ✅ EN TESTS SÍ PUEDES:

```python
# tests/test_integration.py

# ✅ OK EN TESTS - Credenciales de prueba hardcodeadas
TEST_DB_URL = "sqlite:///test.db"
TEST_API_KEY = "test-key-123"

# ✅ OK EN TESTS - Mocks con datos hardcodeados
def test_user_creation():
    mock_user = {
        'email': 'test@example.com',
        'password': 'test123'  # OK en tests
    }
    
# ✅ OK EN TESTS - Configuración simplificada
class TestConfig:
    DEBUG = True
    TESTING = True
    DATABASE_URL = "sqlite:///:memory:"  # DB en memoria para tests
```

### ⚠️ PERO EN TESTS TAMBIÉN:

1. **Aislar tests** - No depender de datos externos
2. **Limpiar después** - Teardown/cleanup obligatorio
3. **Tests determinísticos** - Mismo resultado siempre
4. **Marcar claramente** - Archivos `test_*.py` o `*_test.py`

## 📁 Estructura de Archivos de Configuración

```
proyecto/
├── .env                    # Producción (NUNCA en Git)
├── .env.example            # Plantilla con valores vacíos
├── .env.test              # Variables para testing (puede ir en Git)
├── .gitignore             # DEBE incluir .env
├── requirements.txt       # Dependencias de producción
├── requirements-dev.txt   # Dependencias de desarrollo
└── requirements-test.txt  # Dependencias de testing
```

### `.env.example` (SÍ en Git)
```env
# MySQL Configuration
MYSQL_HOST=
MYSQL_PORT=
MYSQL_USER=
MYSQL_PASSWORD=
MYSQL_DATABASE=

# MongoDB Configuration
MONGO_URI=

# API Keys
OPENAI_API_KEY=
```

### `.env.test` (SÍ puede ir en Git)
```env
# Test Configuration - NO USAR EN PRODUCCIÓN
TEST_MODE=true
DATABASE_URL=sqlite:///test.db
MOCK_EXTERNAL_APIS=true
```

## 🚨 CHECKLIST ANTES DE COMMIT

- [ ] ¿Las credenciales están en variables de entorno?
- [ ] ¿El código sigue los principios SOLID?
- [ ] ¿Hay manejo de errores apropiado?
- [ ] ¿Existe documentación/docstrings?
- [ ] ¿Los tests pasan? (`pytest`)
- [ ] ¿El linter no da errores? (`pylint`, `black`)
- [ ] ¿El commit message es descriptivo?

## 🔧 HERRAMIENTAS DE ENFORCEMENT

### Pre-commit hooks (`.pre-commit-config.yaml`)
```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    hooks:
      - id: check-ast
      - id: check-yaml
      - id: check-added-large-files
      - id: detect-private-key  # Detecta claves privadas
      
  - repo: https://github.com/psf/black
    hooks:
      - id: black
        
  - repo: https://github.com/PyCQA/pylint
    hooks:
      - id: pylint
```

### GitHub Actions (`.github/workflows/ci.yml`)
```yaml
name: CI
on: [push, pull_request]

jobs:
  security-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Check for hardcoded secrets
        uses: trufflesecurity/trufflehog@main
        
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run tests
        run: |
          pytest --cov=src --cov-report=xml
      - name: Check coverage
        run: |
          coverage report --fail-under=80
```

## 📊 MÉTRICAS DE CALIDAD

### Objetivos:
- **Code Coverage**: ≥ 80%
- **Complejidad Ciclomática**: < 10 por función
- **Duplicación de Código**: < 5%
- **Deuda Técnica**: < 5 días
- **Vulnerabilidades de Seguridad**: 0

### Herramientas:
- **SonarQube**: Análisis de calidad
- **Bandit**: Seguridad en Python
- **Safety**: Vulnerabilidades en dependencias
- **Black**: Formateo consistente
- **Pylint**: Linting

## 🎓 RECURSOS Y REFERENCIAS

- [Clean Architecture - Robert C. Martin](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [SOLID Principles](https://www.digitalocean.com/community/conceptual_articles/s-o-l-i-d-the-first-five-principles-of-object-oriented-design)
- [12 Factor App](https://12factor.net/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Python Best Practices](https://docs.python-guide.org/writing/style/)

## ⚡ INICIO RÁPIDO PARA NUEVOS DESARROLLADORES

```bash
# 1. Clonar repositorio
git clone <repo>
cd proyecto

# 2. Configurar entorno
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements-dev.txt

# 3. Configurar variables
cp .env.example .env
# Editar .env con valores reales

# 4. Instalar pre-commit hooks
pre-commit install

# 5. Ejecutar tests
pytest

# 6. Ejecutar aplicación
python app_secure.py
```

---

## 📌 REGLA DE ORO

> **"Si dudas si algo es seguro o escalable, probablemente no lo es. Pregunta o refactoriza."**

---

**Última actualización**: Diciembre 2024
**Versión**: 1.0.0
**Mantenedor**: Equipo de Desarrollo TrendsPro
