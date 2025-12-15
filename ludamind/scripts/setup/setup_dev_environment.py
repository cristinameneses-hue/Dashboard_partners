#!/usr/bin/env python3
"""
Script de configuración del entorno de desarrollo.
Automatiza la configuración inicial siguiendo los estándares del proyecto.

Uso: python setup_dev_environment.py
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

# Colores para output (Windows compatible)
class Colors:
    GREEN = '\033[92m' if sys.platform != 'win32' else ''
    YELLOW = '\033[93m' if sys.platform != 'win32' else ''
    RED = '\033[91m' if sys.platform != 'win32' else ''
    BLUE = '\033[94m' if sys.platform != 'win32' else ''
    RESET = '\033[0m' if sys.platform != 'win32' else ''
    BOLD = '\033[1m' if sys.platform != 'win32' else ''

def print_header(message):
    """Imprime encabezado formateado."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}  {message}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}")

def print_success(message):
    """Imprime mensaje de éxito."""
    print(f"{Colors.GREEN}✓ {message}{Colors.RESET}")

def print_warning(message):
    """Imprime advertencia."""
    print(f"{Colors.YELLOW}⚠ {message}{Colors.RESET}")

def print_error(message):
    """Imprime error."""
    print(f"{Colors.RED}✗ {message}{Colors.RESET}")

def run_command(command, description):
    """Ejecuta un comando y muestra el resultado."""
    print(f"\n{Colors.BLUE}→ {description}...{Colors.RESET}")
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode == 0:
            print_success(f"{description} completado")
            return True
        else:
            print_error(f"{description} falló")
            if result.stderr:
                print(f"  Error: {result.stderr[:200]}")
            return False
    except subprocess.TimeoutExpired:
        print_error(f"{description} timeout")
        return False
    except Exception as e:
        print_error(f"{description} error: {e}")
        return False

def check_python_version():
    """Verifica que la versión de Python sea compatible."""
    print_header("Verificando Python")
    
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print_success(f"Python {version.major}.{version.minor}.{version.micro} detectado")
        return True
    else:
        print_error(f"Python 3.8+ requerido (tienes {version.major}.{version.minor})")
        return False

def create_virtual_environment():
    """Crea el entorno virtual."""
    print_header("Configurando Entorno Virtual")
    
    venv_path = Path("venv")
    
    if venv_path.exists():
        print_warning("Entorno virtual ya existe")
        response = input("¿Recrear? (s/n): ").lower()
        if response == 's':
            shutil.rmtree(venv_path)
        else:
            return True
    
    return run_command(
        f"{sys.executable} -m venv venv",
        "Creando entorno virtual"
    )

def install_dependencies():
    """Instala las dependencias del proyecto."""
    print_header("Instalando Dependencias")
    
    # Determinar el comando pip según el OS
    if sys.platform == 'win32':
        pip_cmd = r"venv\Scripts\pip.exe"
    else:
        pip_cmd = "venv/bin/pip"
    
    # Actualizar pip
    run_command(f"{pip_cmd} install --upgrade pip", "Actualizando pip")
    
    # Instalar dependencias de producción
    if Path("requirements.txt").exists():
        if not run_command(f"{pip_cmd} install -r requirements.txt", "Instalando dependencias de producción"):
            return False
    
    # Instalar dependencias de desarrollo
    if Path("requirements-dev.txt").exists():
        run_command(f"{pip_cmd} install -r requirements-dev.txt", "Instalando dependencias de desarrollo")
    else:
        # Si no existe requirements-dev.txt, instalar herramientas básicas
        dev_packages = [
            "pytest",
            "pytest-cov",
            "black",
            "flake8",
            "mypy",
            "bandit",
            "pre-commit",
            "ipython"
        ]
        run_command(f"{pip_cmd} install {' '.join(dev_packages)}", "Instalando herramientas de desarrollo")
    
    return True

def setup_environment_file():
    """Configura el archivo .env."""
    print_header("Configurando Variables de Entorno")
    
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if env_file.exists():
        print_success(".env ya existe")
        return True
    
    if env_example.exists():
        shutil.copy(env_example, env_file)
        print_success(".env creado desde .env.example")
        print_warning("IMPORTANTE: Edita .env con tus credenciales reales")
        print(f"  Archivo: {env_file.absolute()}")
    else:
        # Crear .env básico
        basic_env = """# Configuración de Desarrollo
# NUNCA commitear este archivo!

# MySQL Configuration
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3307
MYSQL_USER=
MYSQL_PASS=
MYSQL_DB=

# MongoDB Configuration
MONGO_LUDAFARMA_URL=

# OpenAI Configuration
OPENAI_API_KEY=

# Flask Configuration
FLASK_SECRET_KEY=dev-secret-key-change-in-production
FLASK_ENV=development

# Security
ALLOW_DEBUG=false
"""
        env_file.write_text(basic_env)
        print_success(".env básico creado")
        print_warning("IMPORTANTE: Completa las credenciales en .env")
    
    return True

def setup_pre_commit():
    """Configura pre-commit hooks."""
    print_header("Configurando Pre-commit Hooks")
    
    if not Path(".pre-commit-config.yaml").exists():
        print_warning(".pre-commit-config.yaml no encontrado")
        return False
    
    # Instalar pre-commit hooks
    if sys.platform == 'win32':
        pre_commit_cmd = r"venv\Scripts\pre-commit"
    else:
        pre_commit_cmd = "venv/bin/pre-commit"
    
    if run_command(f"{pre_commit_cmd} install", "Instalando pre-commit hooks"):
        print_success("Pre-commit hooks instalados")
        print("  Los hooks se ejecutarán automáticamente antes de cada commit")
        return True
    
    return False

def check_git_configuration():
    """Verifica y configura Git."""
    print_header("Verificando Git")
    
    # Verificar que Git esté instalado
    if not shutil.which("git"):
        print_error("Git no está instalado")
        return False
    
    # Verificar .gitignore
    gitignore = Path(".gitignore")
    if not gitignore.exists():
        print_warning(".gitignore no existe, creando...")
        gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/
.venv

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/
.hypothesis/

# Environment
.env
.env.local
.env.*.local
*.env

# Logs
*.log
logs/

# Database
*.db
*.sqlite
*.sqlite3

# OS
.DS_Store
Thumbs.db
desktop.ini

# Project specific
instance/
temp/
tmp/
cache/
"""
        gitignore.write_text(gitignore_content)
        print_success(".gitignore creado")
    
    # Verificar que .env esté en .gitignore
    gitignore_content = gitignore.read_text()
    if ".env" not in gitignore_content:
        print_error("¡ADVERTENCIA! .env no está en .gitignore")
        print("  Agregándolo automáticamente...")
        with open(gitignore, 'a') as f:
            f.write("\n# Environment variables\n.env\n.env.*\n")
        print_success(".env agregado a .gitignore")
    
    return True

def create_directory_structure():
    """Crea la estructura de directorios del proyecto."""
    print_header("Verificando Estructura de Directorios")
    
    directories = [
        "domain/entities",
        "domain/use_cases",
        "domain/services",
        "infrastructure/repositories",
        "infrastructure/services",
        "infrastructure/config",
        "presentation/api",
        "presentation/web",
        "tests/unit",
        "tests/integration",
        "tests/fixtures",
        "docs",
        "scripts",
        "logs"
    ]
    
    for directory in directories:
        path = Path(directory)
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            # Crear __init__.py en directorios Python
            if not directory.startswith(('docs', 'scripts', 'logs')):
                init_file = path / "__init__.py"
                if not init_file.exists():
                    init_file.write_text('"""Package initialization."""\n')
            print_success(f"Creado: {directory}")
        else:
            print(f"  ✓ {directory} existe")
    
    return True

def run_initial_tests():
    """Ejecuta tests iniciales para verificar el setup."""
    print_header("Ejecutando Verificaciones")
    
    # Comando pytest según OS
    if sys.platform == 'win32':
        pytest_cmd = r"venv\Scripts\pytest"
        python_cmd = r"venv\Scripts\python.exe"
    else:
        pytest_cmd = "venv/bin/pytest"
        python_cmd = "venv/bin/python"
    
    # Verificar imports básicos
    test_imports = [
        "flask",
        "fastapi",
        "mysql.connector",
        "pymongo",
        "dotenv"
    ]
    
    for module in test_imports:
        result = subprocess.run(
            f"{python_cmd} -c \"import {module}\"",
            shell=True,
            capture_output=True
        )
        if result.returncode == 0:
            print_success(f"Módulo {module} disponible")
        else:
            print_warning(f"Módulo {module} no disponible")
    
    # Ejecutar tests si existen
    if Path("tests").exists() and any(Path("tests").glob("test_*.py")):
        run_command(f"{pytest_cmd} tests/ -v --tb=short", "Ejecutando tests")
    
    return True

def print_next_steps():
    """Imprime los siguientes pasos para el desarrollador."""
    print_header("✅ CONFIGURACIÓN COMPLETADA")
    
    print(f"\n{Colors.BOLD}Siguientes pasos:{Colors.RESET}")
    print("\n1. Edita el archivo .env con tus credenciales:")
    print(f"   {Colors.BLUE}Archivo: {Path('.env').absolute()}{Colors.RESET}")
    
    print("\n2. Activa el entorno virtual:")
    if sys.platform == 'win32':
        print(f"   {Colors.BLUE}venv\\Scripts\\activate{Colors.RESET}")
    else:
        print(f"   {Colors.BLUE}source venv/bin/activate{Colors.RESET}")
    
    print("\n3. Ejecuta la aplicación:")
    print(f"   {Colors.BLUE}python app_secure.py{Colors.RESET}")
    
    print("\n4. Ejecuta los tests:")
    print(f"   {Colors.BLUE}pytest tests/{Colors.RESET}")
    
    print("\n5. Antes de hacer commit:")
    print(f"   {Colors.BLUE}pre-commit run --all-files{Colors.RESET}")
    
    print(f"\n{Colors.BOLD}{Colors.GREEN}📚 Documentación:{Colors.RESET}")
    print("   - DEVELOPMENT_STANDARDS.md : Estándares de desarrollo")
    print("   - SECURITY_BEST_PRACTICES.md : Mejores prácticas de seguridad")
    print("   - README.md : Documentación general")
    
    print(f"\n{Colors.BOLD}{Colors.YELLOW}⚠ RECORDATORIOS IMPORTANTES:{Colors.RESET}")
    print("   - NUNCA commitear el archivo .env")
    print("   - NUNCA hardcodear credenciales en el código")
    print("   - SIEMPRE ejecutar tests antes de commit")
    print("   - SIEMPRE seguir los principios SOLID")
    
    print(f"\n{Colors.BOLD}{Colors.GREEN}¡Listo para desarrollar!{Colors.RESET}")
    print("="*70)

def main():
    """Función principal del setup."""
    print(f"{Colors.BOLD}")
    print("="*70)
    print("  SETUP DE ENTORNO DE DESARROLLO - TrendsPro")
    print("  Configuración automática siguiendo estándares")
    print("="*70)
    print(f"{Colors.RESET}")
    
    steps = [
        ("Python", check_python_version),
        ("Git", check_git_configuration),
        ("Directorios", create_directory_structure),
        ("Entorno Virtual", create_virtual_environment),
        ("Dependencias", install_dependencies),
        ("Variables de Entorno", setup_environment_file),
        ("Pre-commit", setup_pre_commit),
        ("Tests", run_initial_tests)
    ]
    
    failed = []
    
    for step_name, step_func in steps:
        try:
            if not step_func():
                failed.append(step_name)
                print_warning(f"{step_name} tuvo problemas")
        except Exception as e:
            print_error(f"Error en {step_name}: {e}")
            failed.append(step_name)
    
    if failed:
        print_header("⚠ SETUP COMPLETADO CON ADVERTENCIAS")
        print(f"\nLos siguientes pasos tuvieron problemas:")
        for step in failed:
            print(f"  - {step}")
        print("\nPuedes continuar, pero revisa los errores.")
    else:
        print_header("✅ SETUP COMPLETADO EXITOSAMENTE")
    
    print_next_steps()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Setup cancelado por el usuario{Colors.RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Error inesperado: {e}{Colors.RESET}")
        sys.exit(1)
