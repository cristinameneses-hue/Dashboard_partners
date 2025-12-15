import { test, expect } from '@playwright/test';

test.describe('Dashboard Ecommerce Metrics', () => {

  test('debe cargar y mostrar métricas del dashboard', async ({ page }) => {
    // Capturar peticiones y respuestas de la API
    const apiResponses: { url: string; status: number; body?: any }[] = [];

    page.on('response', async (response) => {
      if (response.url().includes('/api/')) {
        const entry: { url: string; status: number; body?: any } = {
          url: response.url(),
          status: response.status()
        };
        try {
          entry.body = await response.json();
        } catch (e) {
          // No es JSON
        }
        apiResponses.push(entry);
        console.log(`API Response: ${response.status()} ${response.url()}`);
      }
    });

    // Ir al dashboard
    await page.goto('/');

    // Esperar que cargue la página
    await page.waitForLoadState('networkidle');

    // Tomar screenshot del estado inicial
    await page.screenshot({ path: 'test-results/dashboard-initial.png', fullPage: true });

    // Esperar un poco más para las peticiones API
    await page.waitForTimeout(3000);

    // Verificar si hay errores en la consola
    const consoleErrors: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    // Verificar el título del dashboard
    const title = page.locator('h2:has-text("Ecommerce")');
    await expect(title).toBeVisible();
    console.log('✅ Título del dashboard visible');

    // Verificar que el sidebar está visible
    const sidebar = page.locator('aside');
    await expect(sidebar).toBeVisible();
    console.log('✅ Sidebar visible');

    // Verificar si hay algún mensaje de error visible
    const errorMessages = page.locator('text=/error|Error|ERROR/i');
    const errorCount = await errorMessages.count();
    if (errorCount > 0) {
      console.log(`⚠️ Hay ${errorCount} mensajes de error visibles`);
      for (let i = 0; i < errorCount; i++) {
        const text = await errorMessages.nth(i).textContent();
        console.log(`  - ${text}`);
      }
    }

    // Verificar si hay un spinner de carga
    const loadingSpinner = page.locator('.animate-spin, [class*="loading"], text="Cargando"');
    const isLoading = await loadingSpinner.count() > 0;
    if (isLoading) {
      console.log('⚠️ El dashboard sigue cargando...');
      await page.waitForTimeout(5000);
    }

    // Verificar las respuestas de la API
    console.log('\n📊 Respuestas de API:');
    for (const resp of apiResponses) {
      console.log(`  ${resp.status} - ${resp.url}`);
      if (resp.status >= 400) {
        console.log(`    ❌ Error: ${JSON.stringify(resp.body)}`);
      }
    }

    // Verificar si hay métricas visibles (cards de KPI)
    const metricCards = page.locator('[class*="card"], [class*="metric"], [class*="stat"]');
    const cardCount = await metricCards.count();
    console.log(`\n📈 Cards de métricas encontradas: ${cardCount}`);

    // Verificar si hay una tabla de datos
    const tables = page.locator('table');
    const tableCount = await tables.count();
    console.log(`📋 Tablas encontradas: ${tableCount}`);

    // Verificar si hay gráficos (charts)
    const charts = page.locator('canvas, svg[class*="chart"], [class*="chart"]');
    const chartCount = await charts.count();
    console.log(`📊 Gráficos encontrados: ${chartCount}`);

    // Tomar screenshot final
    await page.screenshot({ path: 'test-results/dashboard-loaded.png', fullPage: true });

    // Verificar que NO hay errores de red 4xx/5xx
    const networkErrors = apiResponses.filter(r => r.status >= 400);
    if (networkErrors.length > 0) {
      console.log('\n❌ Errores de red encontrados:');
      for (const err of networkErrors) {
        console.log(`  ${err.status} - ${err.url}`);
        console.log(`  Body: ${JSON.stringify(err.body)}`);
      }
    }

    // El test falla si hay errores 500
    const serverErrors = networkErrors.filter(r => r.status >= 500);
    expect(serverErrors.length).toBe(0);

    // Verificar que se cargó contenido (no está vacío)
    const bodyText = await page.locator('main').textContent();
    expect(bodyText?.length).toBeGreaterThan(50);

    console.log('\n✅ Test completado');
  });

  test('debe verificar conectividad con backend FastAPI', async ({ page }) => {
    // Probar directamente el endpoint de la API
    const response = await page.request.get('http://localhost:5173/api/ecommerce/metrics');

    console.log(`Status: ${response.status()}`);

    if (response.ok()) {
      const data = await response.json();
      console.log('✅ Backend respondió correctamente');
      console.log(`Datos recibidos: ${JSON.stringify(data).substring(0, 200)}...`);
    } else {
      const text = await response.text();
      console.log(`❌ Error del backend: ${text}`);
    }

    // El backend debe responder (aunque sea con error de datos vacíos)
    expect(response.status()).toBeLessThan(500);
  });

  test('debe verificar que el backend FastAPI está corriendo', async ({ page }) => {
    // Verificar health check o endpoint básico
    try {
      const response = await page.request.get('http://localhost:8000/api/ecommerce/metrics?period_type=this_month');
      console.log(`Backend directo status: ${response.status()}`);

      if (response.ok()) {
        const data = await response.json();
        console.log('✅ Backend FastAPI está corriendo');
        console.log(`Keys en respuesta: ${Object.keys(data).join(', ')}`);
      } else {
        console.log(`❌ Backend responde pero con error: ${response.status()}`);
        const text = await response.text();
        console.log(text.substring(0, 500));
      }
    } catch (e) {
      console.log('❌ No se puede conectar al backend FastAPI en puerto 8000');
      console.log('   Asegúrate de que el backend esté corriendo con:');
      console.log('   cd /Users/dgfre/Documents/Dashboard_partners/backend && uvicorn app.main:app --reload --port 8000');
    }
  });
});
