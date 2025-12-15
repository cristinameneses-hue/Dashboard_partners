#!/usr/bin/env python3
"""
Test E2E para el sistema de modos en sidebar.
Verifica que toda la funcionalidad esté operativa.
"""

import sys
import time
import json
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Fix encoding for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def test_system():
    """Test E2E completo del sistema."""
    
    print("\n" + "="*70)
    print("  TEST E2E - SISTEMA DE MODOS EN SIDEBAR")
    print("="*70)
    
    try:
        import httpx
    except ImportError:
        print("❌ httpx no instalado. Ejecuta: pip install httpx")
        return False
    
    base_url = "http://localhost:5000"
    session_id = f"test_session_{int(time.time())}"
    
    # Test results tracking
    tests_passed = 0
    tests_failed = 0
    
    print("\n📋 Ejecutando tests...\n")
    
    # ============================================================================
    # TEST 1: Verificar que la aplicación está corriendo
    # ============================================================================
    print("1️⃣  Test: Aplicación respondiendo...")
    try:
        response = httpx.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print(f"   ✅ PASS - Aplicación saludable")
            print(f"      - MySQL: {'✅' if health_data['databases']['mysql'] else '❌'}")
            print(f"      - MongoDB: {'✅' if health_data['databases']['mongodb'] else '❌'}")
            tests_passed += 1
        else:
            print(f"   ❌ FAIL - Status code: {response.status_code}")
            tests_failed += 1
    except Exception as e:
        print(f"   ❌ FAIL - Error: {str(e)[:50]}")
        print("\n   ⚠️  ¿Está la aplicación corriendo?")
        print("   Ejecuta: python presentation/api/app_modes_sidebar.py")
        tests_failed += 1
        return False
    
    # ============================================================================
    # TEST 2: Verificar la página principal
    # ============================================================================
    print("\n2️⃣  Test: Página principal...")
    try:
        response = httpx.get(base_url, timeout=5)
        if response.status_code == 200 and "Modos de Consulta" in response.text:
            print("   ✅ PASS - Interfaz cargando correctamente")
            tests_passed += 1
        else:
            print(f"   ❌ FAIL - Página no contiene elementos esperados")
            tests_failed += 1
    except Exception as e:
        print(f"   ❌ FAIL - Error: {str(e)[:50]}")
        tests_failed += 1
    
    # ============================================================================
    # TEST 3: Cambiar a modo Farmacias
    # ============================================================================
    print("\n3️⃣  Test: Cambiar a modo Farmacias...")
    try:
        response = httpx.post(
            f"{base_url}/api/session/mode",
            json={
                "session_id": session_id,
                "mode": "pharmacy"
            },
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            if data['success'] and data['mode'] == 'pharmacy':
                print("   ✅ PASS - Modo cambiado a Farmacias")
                tests_passed += 1
            else:
                print("   ❌ FAIL - Respuesta inesperada")
                tests_failed += 1
        else:
            print(f"   ❌ FAIL - Status code: {response.status_code}")
            tests_failed += 1
    except Exception as e:
        print(f"   ❌ FAIL - Error: {str(e)[:50]}")
        tests_failed += 1
    
    # ============================================================================
    # TEST 4: Query en modo Farmacias
    # ============================================================================
    print("\n4️⃣  Test: Query en modo Farmacias...")
    try:
        response = httpx.post(
            f"{base_url}/api/query",
            json={
                "query": "¿Cuál es el estado de la farmacia 123?",
                "mode": "pharmacy",
                "session_id": session_id
            },
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and data.get('answer'):
                print("   ✅ PASS - Query procesada correctamente")
                print(f"      - Modo: {data.get('mode')}")
                print(f"      - Base de datos: {data.get('database')}")
                print(f"      - Confianza: {data.get('confidence', 0)*100:.0f}%")
                tests_passed += 1
            else:
                print("   ❌ FAIL - Respuesta sin contenido")
                tests_failed += 1
        else:
            print(f"   ❌ FAIL - Status code: {response.status_code}")
            tests_failed += 1
    except Exception as e:
        print(f"   ❌ FAIL - Error: {str(e)[:50]}")
        tests_failed += 1
    
    # ============================================================================
    # TEST 5: Cambiar a modo Productos
    # ============================================================================
    print("\n5️⃣  Test: Cambiar a modo Productos...")
    try:
        response = httpx.post(
            f"{base_url}/api/session/mode",
            json={
                "session_id": session_id,
                "mode": "product"
            },
            timeout=5
        )
        if response.status_code == 200 and response.json()['mode'] == 'product':
            print("   ✅ PASS - Modo cambiado a Productos")
            tests_passed += 1
        else:
            print("   ❌ FAIL - No se pudo cambiar el modo")
            tests_failed += 1
    except Exception as e:
        print(f"   ❌ FAIL - Error: {str(e)[:50]}")
        tests_failed += 1
    
    # ============================================================================
    # TEST 6: Query en modo Productos
    # ============================================================================
    print("\n6️⃣  Test: Query en modo Productos...")
    try:
        response = httpx.post(
            f"{base_url}/api/query",
            json={
                "query": "Top 10 productos más vendidos",
                "mode": "product",
                "session_id": session_id
            },
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            if data.get('answer') and "producto" in data['answer'].lower():
                print("   ✅ PASS - Query de productos procesada")
                tests_passed += 1
            else:
                print("   ❌ FAIL - Respuesta no relacionada con productos")
                tests_failed += 1
        else:
            print(f"   ❌ FAIL - Status code: {response.status_code}")
            tests_failed += 1
    except Exception as e:
        print(f"   ❌ FAIL - Error: {str(e)[:50]}")
        tests_failed += 1
    
    # ============================================================================
    # TEST 7: Cambiar a modo Partners
    # ============================================================================
    print("\n7️⃣  Test: Cambiar a modo Partners...")
    try:
        response = httpx.post(
            f"{base_url}/api/session/mode",
            json={
                "session_id": session_id,
                "mode": "partner"
            },
            timeout=5
        )
        if response.status_code == 200 and response.json()['mode'] == 'partner':
            print("   ✅ PASS - Modo cambiado a Partners")
            tests_passed += 1
        else:
            print("   ❌ FAIL - No se pudo cambiar el modo")
            tests_failed += 1
    except Exception as e:
        print(f"   ❌ FAIL - Error: {str(e)[:50]}")
        tests_failed += 1
    
    # ============================================================================
    # TEST 8: Query en modo Partners
    # ============================================================================
    print("\n8️⃣  Test: Query en modo Partners...")
    try:
        response = httpx.post(
            f"{base_url}/api/query",
            json={
                "query": "GMV de Glovo esta semana",
                "mode": "partner",
                "session_id": session_id
            },
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            if data.get('answer') and ("glovo" in data['answer'].lower() or "partner" in data['answer'].lower()):
                print("   ✅ PASS - Query de partners procesada")
                tests_passed += 1
            else:
                print("   ❌ FAIL - Respuesta no relacionada con partners")
                tests_failed += 1
        else:
            print(f"   ❌ FAIL - Status code: {response.status_code}")
            tests_failed += 1
    except Exception as e:
        print(f"   ❌ FAIL - Error: {str(e)[:50]}")
        tests_failed += 1
    
    # ============================================================================
    # TEST 9: Modo Conversacional
    # ============================================================================
    print("\n9️⃣  Test: Modo Conversacional...")
    try:
        response = httpx.post(
            f"{base_url}/api/session/mode",
            json={
                "session_id": session_id,
                "mode": "conversational"
            },
            timeout=5
        )
        if response.status_code == 200:
            # Send conversational query
            response = httpx.post(
                f"{base_url}/api/query",
                json={
                    "query": "Dame un resumen general del negocio",
                    "mode": "conversational",
                    "session_id": session_id
                },
                timeout=10
            )
            if response.status_code == 200 and response.json().get('answer'):
                print("   ✅ PASS - Modo conversacional funcionando")
                tests_passed += 1
            else:
                print("   ❌ FAIL - Query conversacional falló")
                tests_failed += 1
        else:
            print("   ❌ FAIL - No se pudo cambiar a modo conversacional")
            tests_failed += 1
    except Exception as e:
        print(f"   ❌ FAIL - Error: {str(e)[:50]}")
        tests_failed += 1
    
    # ============================================================================
    # TEST 10: Verificar endpoint de versión
    # ============================================================================
    print("\n🔟  Test: Endpoint de versión...")
    try:
        response = httpx.get(f"{base_url}/version", timeout=5)
        if response.status_code == 200:
            version_data = response.json()
            if version_data.get('version') == '3.2.0':
                print("   ✅ PASS - Versión correcta (3.2.0)")
                print(f"      - Modos: {', '.join(version_data.get('modes', []))}")
                tests_passed += 1
            else:
                print(f"   ❌ FAIL - Versión incorrecta: {version_data.get('version')}")
                tests_failed += 1
        else:
            print(f"   ❌ FAIL - Status code: {response.status_code}")
            tests_failed += 1
    except Exception as e:
        print(f"   ❌ FAIL - Error: {str(e)[:50]}")
        tests_failed += 1
    
    # ============================================================================
    # RESULTADOS FINALES
    # ============================================================================
    print("\n" + "="*70)
    print("  RESULTADOS DEL TEST E2E")
    print("="*70)
    
    total_tests = tests_passed + tests_failed
    success_rate = (tests_passed / total_tests * 100) if total_tests > 0 else 0
    
    print(f"\n📊 Estadísticas:")
    print(f"   - Tests ejecutados: {total_tests}")
    print(f"   - Tests pasados: {tests_passed} ✅")
    print(f"   - Tests fallidos: {tests_failed} ❌")
    print(f"   - Tasa de éxito: {success_rate:.1f}%")
    
    if tests_failed == 0:
        print("\n🎉 ¡TODOS LOS TESTS PASARON!")
        print("\nEl sistema de modos está funcionando correctamente:")
        print("   ✅ Aplicación respondiendo")
        print("   ✅ Interfaz cargando")
        print("   ✅ Cambio de modos funciona")
        print("   ✅ Queries procesándose por modo")
        print("   ✅ Todos los modos operativos")
    else:
        print(f"\n⚠️  Algunos tests fallaron ({tests_failed}/{total_tests})")
        print("\nRevisa:")
        print("   1. Que la aplicación esté corriendo")
        print("   2. Los túneles SSH si las bases de datos no conectan")
        print("   3. Los logs de la aplicación para más detalles")
    
    print("\n" + "="*70)
    
    return tests_failed == 0

if __name__ == "__main__":
    # Wait a bit for the app to be ready
    print("\n⏳ Esperando 3 segundos para que la aplicación esté lista...")
    time.sleep(3)
    
    # Run tests
    success = test_system()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)
