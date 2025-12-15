# 🤖 GUÍA DE CONTEXTO PARA IA (Claude)

## REGLAS ABSOLUTAS PARA DESARROLLO

### 🔴 PRODUCCIÓN - NUNCA EXCEPCIONES

```python
# ❌ PROHIBIDO SIEMPRE
password = "cualquier_texto"
api_key = "sk-..."
connection = "mongodb://user:pass@..."

# ✅ OBLIGATORIO SIEMPRE
password = os.getenv('DB_PASSWORD')
api_key = os.getenv('API_KEY')
connection = os.getenv('MONGO_URL')
```

### 🟡 TESTS - FLEXIBILIDAD PERMITIDA

```python
# ✅ OK SOLO EN ARCHIVOS test_*.py
TEST_PASSWORD = "test123"
MOCK_API_KEY = "fake-key-for-testing"
TEST_DB = "sqlite:///test.db"
```

## ESTRUCTURA OBLIGATORIA

```
SIEMPRE usar esta estructura:
├── domain/           # Lógica pura, sin dependencias
├── infrastructure/   # Implementaciones, DB, APIs
├── presentation/     # Web, API endpoints
└── tests/           # Tests con mocks permitidos
```

## PRINCIPIOS SOLID - APLICAR SIEMPRE

### S - Single Responsibility
```python
# ✅ BIEN - Una responsabilidad
class EmailSender:
    def send_email(self, email): pass

class UserRepository:
    def save_user(self, user): pass

# ❌ MAL - Múltiples responsabilidades
class UserManager:
    def save_user(self, user): pass
    def send_email(self, email): pass  # NO!
```

### D - Dependency Injection
```python
# ✅ BIEN - Inyectar dependencias
def __init__(self, repository: Repository):
    self.repository = repository

# ❌ MAL - Crear dependencias
def __init__(self):
    self.repository = MySQLRepository()  # NO!
```

## ARCHIVOS DE REFERENCIA

1. **Código Seguro**: `app_secure.py`
2. **Ejemplo Clean**: `domain/example_clean_code.py`
3. **Template Tests**: `tests/test_template.py`
4. **Estándares**: `DEVELOPMENT_STANDARDS.md`

## CHECKLIST ANTES DE GENERAR CÓDIGO

- [ ] ¿Las credenciales vienen de os.getenv()?
- [ ] ¿El código sigue Clean Architecture?
- [ ] ¿Aplica principios SOLID?
- [ ] ¿Tiene docstrings y type hints?
- [ ] ¿Maneja errores sin exponer info sensible?
- [ ] ¿Si es test, está claramente marcado como tal?

## FORMATO DE CÓDIGO

```python
from typing import Optional, List
import os
from dotenv import load_dotenv

load_dotenv()  # SIEMPRE al inicio


class NombreDescriptivo:
    """
    Documentación clara de la clase.
    """
    
    def __init__(self, dependency: Interface):
        """Constructor con inyección de dependencias."""
        self.dependency = dependency
        # Config desde environment
        self.config_value = os.getenv('CONFIG_KEY', 'default')
    
    def metodo_publico(self, param: str) -> bool:
        """
        Documentación del método.
        
        Args:
            param: Descripción del parámetro
            
        Returns:
            Descripción del retorno
            
        Raises:
            ValueError: Cuándo ocurre
        """
        try:
            # Lógica aquí
            return True
        except Exception as e:
            # Log sin exponer detalles
            logger.error(f"Error: {str(e)[:100]}")
            raise
```

## RESPUESTAS AL USUARIO

Cuando el usuario pida código, SIEMPRE:

1. **Verificar el contexto**: ¿Es producción o test?
2. **Aplicar estándares**: Sin excepciones en producción
3. **Documentar decisiones**: Explicar por qué se hace así
4. **Sugerir mejoras**: Si hay una forma más SOLID

## MEMORIA DEL PROYECTO

- **Nombre**: TrendsPro
- **Arquitectura**: Clean Architecture
- **Bases de datos**: MySQL (analytics) + MongoDB (operations)
- **Puerto**: 5000
- **Archivo principal**: `app_secure.py`
- **Credenciales**: SIEMPRE en `.env`
- **Tests**: pytest con coverage mínimo 80%

## COMANDOS ÚTILES

```bash
# Ejecutar aplicación segura
python app_secure.py

# Ejecutar tests
pytest tests/ -v --cov

# Verificar seguridad
python verify_security.py

# Setup nuevo desarrollador
python setup_dev_environment.py
```

---

**RECORDATORIO FINAL**: 
Si dudas si algo es seguro o sigue los estándares, probablemente no lo es. 
Pregunta al usuario o aplica la opción más restrictiva/segura.
