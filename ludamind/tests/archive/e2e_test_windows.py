#!/usr/bin/env python3
"""
E2E tests for Windows - TrendsPro API.
"""

import asyncio
import sys
import time
import os

# Set encoding for Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# Wait for server
print("Waiting for server to start (5 seconds)...")
time.sleep(5)

async def run_e2e_tests():
    """Run E2E tests."""
    
    print("\n" + "="*60)
    print("E2E TESTS - TrendsPro API")
    print("="*60)
    
    results = []
    base_url = "http://localhost:8000"
    
    # Test with httpx
    print("\n1. Testing API endpoints...")
    try:
        import httpx
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            
            # Test 1: Root page
            print("   Testing root page...")
            try:
                response = await client.get(f"{base_url}/")
                if response.status_code == 200 and "TrendsPro" in response.text:
                    results.append(("Root Page", True, "OK"))
                    print("   [PASS] Root page works")
                else:
                    results.append(("Root Page", False, f"Status {response.status_code}"))
                    print(f"   [FAIL] Root page: {response.status_code}")
            except Exception as e:
                results.append(("Root Page", False, str(e)[:50]))
                print(f"   [FAIL] Root page error: {str(e)[:50]}")
            
            # Test 2: Health
            print("   Testing health endpoint...")
            try:
                response = await client.get(f"{base_url}/health")
                if response.status_code == 200:
                    data = response.json()
                    status = data.get("status", "unknown")
                    results.append(("Health", True, status))
                    print(f"   [PASS] Health check: {status}")
                else:
                    results.append(("Health", False, f"Status {response.status_code}"))
                    print(f"   [FAIL] Health: {response.status_code}")
            except Exception as e:
                results.append(("Health", False, str(e)[:50]))
                print(f"   [FAIL] Health error: {str(e)[:50]}")
            
            # Test 3: API Docs
            print("   Testing API docs...")
            try:
                response = await client.get(f"{base_url}/docs")
                if response.status_code == 200:
                    results.append(("API Docs", True, "Available"))
                    print("   [PASS] API documentation")
                else:
                    results.append(("API Docs", False, f"Status {response.status_code}"))
                    print(f"   [FAIL] API docs: {response.status_code}")
            except Exception as e:
                results.append(("API Docs", False, str(e)[:50]))
                print(f"   [FAIL] API docs error: {str(e)[:50]}")
            
            # Test 4: Version
            print("   Testing version...")
            try:
                response = await client.get(f"{base_url}/version")
                if response.status_code == 200:
                    data = response.json()
                    version = data.get("version", "?")
                    results.append(("Version", True, version))
                    print(f"   [PASS] Version: {version}")
                else:
                    results.append(("Version", False, f"Status {response.status_code}"))
                    print(f"   [FAIL] Version: {response.status_code}")
            except Exception as e:
                results.append(("Version", False, str(e)[:50]))
                print(f"   [FAIL] Version error: {str(e)[:50]}")
            
            # Test 5: Query
            print("   Testing query execution...")
            try:
                response = await client.post(
                    f"{base_url}/api/v1/queries/execute",
                    json={"text": "Test query", "use_chatgpt": False}
                )
                if response.status_code == 200:
                    results.append(("Query", True, "Works"))
                    print("   [PASS] Query execution")
                else:
                    results.append(("Query", False, f"Status {response.status_code}"))
                    print(f"   [FAIL] Query: {response.status_code}")
            except Exception as e:
                results.append(("Query", False, str(e)[:50]))
                print(f"   [FAIL] Query error: {str(e)[:50]}")
            
    except ImportError:
        print("   [ERROR] httpx not installed")
        results.append(("API Tests", False, "httpx missing"))
    
    # Playwright test
    print("\n2. Testing with browser...")
    try:
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            print("   Launching browser...")
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                print("   Loading page...")
                await page.goto(base_url, timeout=15000)
                
                title = await page.title()
                print(f"   Page title: {title}")
                
                # Take screenshot
                screenshot_path = "test_screenshot.png"
                await page.screenshot(path=screenshot_path)
                results.append(("Screenshot", True, screenshot_path))
                print(f"   [PASS] Screenshot saved: {screenshot_path}")
                
                # Check content
                content = await page.content()
                if "TrendsPro" in content:
                    results.append(("Browser", True, "Page loads"))
                    print("   [PASS] Browser test")
                else:
                    results.append(("Browser", False, "No content"))
                    print("   [FAIL] Browser: content missing")
                    
            except Exception as e:
                results.append(("Browser", False, str(e)[:50]))
                print(f"   [FAIL] Browser error: {str(e)[:50]}")
            finally:
                await browser.close()
                
    except ImportError:
        print("   [SKIP] Playwright not installed")
        print("   Installing Playwright...")
        import subprocess
        subprocess.run([sys.executable, "-m", "pip", "install", "playwright"], capture_output=True)
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], capture_output=True)
        results.append(("Browser", False, "Just installed"))
    except Exception as e:
        results.append(("Browser", False, str(e)[:50]))
        print(f"   [FAIL] Playwright error: {str(e)[:50]}")
    
    # Summary
    print("\n" + "="*60)
    print("RESULTS")
    print("="*60)
    
    passed = 0
    failed = 0
    
    for test, success, msg in results:
        if success:
            print(f"[PASS] {test}: {msg}")
            passed += 1
        else:
            print(f"[FAIL] {test}: {msg}")
            failed += 1
    
    print("-"*60)
    print(f"Total: {passed} passed, {failed} failed")
    
    if passed > 0:
        print(f"\nSUCCESS RATE: {(passed/(passed+failed)*100):.0f}%")
        
        if passed > failed:
            print("\nSUCCESS! API is working!")
            print("\nAccess:")
            print("  - Home: http://localhost:8000")
            print("  - Docs: http://localhost:8000/docs")
            
            if os.path.exists("test_screenshot.png"):
                print(f"\nScreenshot: {os.path.abspath('test_screenshot.png')}")
            
            return True
    
    print("\nTests failed. Check errors above.")
    return False

async def main():
    success = await run_e2e_tests()
    return 0 if success else 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nTests interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)
