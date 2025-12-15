#!/usr/bin/env python3
"""
E2E tests using Playwright for TrendsPro API.
"""

import asyncio
import sys
import time
from typing import List, Tuple

# Wait for server to start
print("Waiting for server to start (5 seconds)...")
time.sleep(5)

async def run_e2e_tests():
    """Run comprehensive E2E tests with Playwright."""
    
    # First, test with httpx
    print("\n" + "="*60)
    print("E2E TESTS - TrendsPro API")
    print("="*60)
    
    results: List[Tuple[str, bool, str]] = []
    
    # Test with httpx first
    print("\n1. Testing API endpoints with httpx...")
    try:
        import httpx
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            base_url = "http://localhost:8000"
            
            # Test 1: Root page
            print("   Testing root page...")
            try:
                response = await client.get(f"{base_url}/")
                if response.status_code == 200 and "TrendsPro" in response.text:
                    results.append(("Root Page", True, "Page loads with content"))
                    print("   ✓ Root page works")
                else:
                    results.append(("Root Page", False, f"Status {response.status_code}"))
                    print(f"   ✗ Root page failed: {response.status_code}")
            except Exception as e:
                results.append(("Root Page", False, str(e)[:50]))
                print(f"   ✗ Root page error: {e}")
            
            # Test 2: Health check
            print("   Testing health endpoint...")
            try:
                response = await client.get(f"{base_url}/health")
                if response.status_code == 200:
                    data = response.json()
                    status = data.get("status", "unknown")
                    results.append(("Health Check", True, f"Status: {status}"))
                    print(f"   ✓ Health check: {status}")
                else:
                    results.append(("Health Check", False, f"Status {response.status_code}"))
                    print(f"   ✗ Health check failed: {response.status_code}")
            except Exception as e:
                results.append(("Health Check", False, str(e)[:50]))
                print(f"   ✗ Health check error: {e}")
            
            # Test 3: API Docs
            print("   Testing API documentation...")
            try:
                response = await client.get(f"{base_url}/docs")
                if response.status_code == 200:
                    results.append(("API Docs", True, "Swagger UI available"))
                    print("   ✓ API documentation available")
                else:
                    results.append(("API Docs", False, f"Status {response.status_code}"))
                    print(f"   ✗ API docs failed: {response.status_code}")
            except Exception as e:
                results.append(("API Docs", False, str(e)[:50]))
                print(f"   ✗ API docs error: {e}")
            
            # Test 4: Version
            print("   Testing version endpoint...")
            try:
                response = await client.get(f"{base_url}/version")
                if response.status_code == 200:
                    data = response.json()
                    version = data.get("version", "unknown")
                    arch = data.get("architecture", "unknown")
                    results.append(("Version", True, f"v{version} ({arch})"))
                    print(f"   ✓ Version: v{version} ({arch})")
                else:
                    results.append(("Version", False, f"Status {response.status_code}"))
                    print(f"   ✗ Version failed: {response.status_code}")
            except Exception as e:
                results.append(("Version", False, str(e)[:50]))
                print(f"   ✗ Version error: {e}")
            
            # Test 5: Metrics
            print("   Testing metrics endpoint...")
            try:
                response = await client.get(f"{base_url}/metrics")
                if response.status_code == 200:
                    results.append(("Metrics", True, "Metrics available"))
                    print("   ✓ Metrics endpoint works")
                else:
                    results.append(("Metrics", False, f"Status {response.status_code}"))
                    print(f"   ✗ Metrics failed: {response.status_code}")
            except Exception as e:
                results.append(("Metrics", False, str(e)[:50]))
                print(f"   ✗ Metrics error: {e}")
            
            # Test 6: Query execution
            print("   Testing query execution...")
            try:
                response = await client.post(
                    f"{base_url}/api/v1/queries/execute",
                    json={"text": "¿Cuántas farmacias activas hay?", "use_chatgpt": False}
                )
                if response.status_code == 200:
                    data = response.json()
                    results.append(("Query Execution", True, "Query processed successfully"))
                    print("   ✓ Query execution works")
                else:
                    results.append(("Query Execution", False, f"Status {response.status_code}"))
                    print(f"   ✗ Query execution failed: {response.status_code}")
            except Exception as e:
                results.append(("Query Execution", False, str(e)[:50]))
                print(f"   ✗ Query execution error: {e}")
            
            # Test 7: List databases
            print("   Testing list databases...")
            try:
                response = await client.get(f"{base_url}/api/v1/databases")
                if response.status_code == 200:
                    data = response.json()
                    db_count = len(data.get("databases", []))
                    results.append(("List Databases", True, f"{db_count} databases"))
                    print(f"   ✓ List databases: {db_count} found")
                else:
                    results.append(("List Databases", False, f"Status {response.status_code}"))
                    print(f"   ✗ List databases failed: {response.status_code}")
            except Exception as e:
                results.append(("List Databases", False, str(e)[:50]))
                print(f"   ✗ List databases error: {e}")
            
    except ImportError:
        print("   ✗ httpx not installed")
        results.append(("API Tests", False, "httpx not installed"))
    
    # Test with Playwright
    print("\n2. Testing with Playwright browser...")
    try:
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            print("   Launching browser...")
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                # Test home page
                print("   Loading home page...")
                await page.goto("http://localhost:8000", wait_until="networkidle", timeout=15000)
                
                # Check title
                title = await page.title()
                print(f"   Page title: {title}")
                
                # Check for content
                content = await page.content()
                if "TrendsPro" in content:
                    results.append(("Browser - Home", True, f"Title: {title}"))
                    print("   ✓ Home page loads correctly")
                else:
                    results.append(("Browser - Home", False, "Content missing"))
                    print("   ✗ Home page content incorrect")
                
                # Click on API Docs link
                print("   Testing navigation to API docs...")
                await page.click('a[href="/docs"]')
                await page.wait_for_load_state("networkidle")
                
                # Check if Swagger UI loaded
                swagger_visible = await page.is_visible('text="FastAPI"', )
                if swagger_visible:
                    results.append(("Browser - Docs", True, "Swagger UI loads"))
                    print("   ✓ API documentation navigation works")
                else:
                    results.append(("Browser - Docs", False, "Swagger UI not found"))
                    print("   ✗ API documentation not loading")
                
                # Take screenshot
                print("   Taking screenshot...")
                await page.screenshot(path="e2e_screenshot.png", full_page=True)
                results.append(("Screenshot", True, "Saved as e2e_screenshot.png"))
                print("   ✓ Screenshot saved: e2e_screenshot.png")
                
            except Exception as e:
                results.append(("Browser Tests", False, str(e)[:100]))
                print(f"   ✗ Browser test error: {e}")
            finally:
                await browser.close()
                
    except ImportError:
        print("   ⚠ Playwright not installed - installing now...")
        import subprocess
        subprocess.run([sys.executable, "-m", "pip", "install", "playwright"], capture_output=True)
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], capture_output=True)
        results.append(("Browser Tests", False, "Playwright was not installed"))
    except Exception as e:
        results.append(("Browser Tests", False, str(e)[:100]))
        print(f"   ✗ Playwright error: {e}")
    
    # Print summary
    print("\n" + "="*60)
    print("TEST RESULTS SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, success, _ in results if success)
    failed = sum(1 for _, success, _ in results if not success)
    
    for test_name, success, message in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status} | {test_name}: {message}")
    
    print("-"*60)
    print(f"Total: {passed} passed, {failed} failed")
    print(f"Success rate: {(passed/(passed+failed)*100):.1f}%")
    
    if passed > failed:
        print("\n✅ E2E TESTS SUCCESSFUL!")
        print("\nThe TrendsPro API is working correctly.")
        print("\nYou can access it at:")
        print("  - Home: http://localhost:8000")
        print("  - API Docs: http://localhost:8000/docs")
        print("  - Health: http://localhost:8000/health")
        
        if any("Screenshot" in test for test, _, _ in results):
            print("\n📸 Screenshot saved as: e2e_screenshot.png")
        
        return True
    else:
        print("\n❌ E2E TESTS FAILED")
        print("Please check the errors above.")
        return False

async def main():
    """Main function."""
    success = await run_e2e_tests()
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
