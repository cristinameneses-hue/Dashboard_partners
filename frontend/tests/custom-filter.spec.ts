import { test, expect } from '@playwright/test';

test.describe('Filtro de Período Custom', () => {
  
  test('debe mostrar selector de fechas al hacer clic en Personalizado sin hacer petición', async ({ page }) => {
    // Ir a la página principal
    await page.goto('/');
    
    // Esperar a que cargue la página
    await page.waitForSelector('text=Ecommerce Metrics');
    
    // Hacer clic en el dropdown de Período
    await page.click('button:has-text("Período")');
    
    // Esperar a que aparezca el menú
    await page.waitForSelector('text=Este Mes');
    
    // Hacer clic en "Personalizado"
    await page.click('button:has-text("Personalizado")');
    
    // Verificar que aparecen los campos de fecha
    const fromInput = page.locator('input[type="date"]').first();
    const toInput = page.locator('input[type="date"]').last();
    
    await expect(fromInput).toBeVisible();
    await expect(toInput).toBeVisible();
    
    // Verificar que el botón "Aplicar fechas" está visible pero deshabilitado
    const applyButton = page.locator('button:has-text("Aplicar fechas")');
    await expect(applyButton).toBeVisible();
    await expect(applyButton).toBeDisabled();
    
    // Verificar que aparece el mensaje de ayuda
    await expect(page.locator('text=Selecciona ambas fechas para aplicar')).toBeVisible();
    
    console.log('✅ Test 1 pasado: El selector de fechas aparece sin hacer petición');
  });

  test('debe hacer petición solo cuando se aplican ambas fechas', async ({ page }) => {
    // Capturar peticiones de red
    const requests: string[] = [];
    page.on('request', (request) => {
      if (request.url().includes('/api/ecommerce')) {
        requests.push(request.url());
      }
    });
    
    await page.goto('/');
    await page.waitForSelector('text=Ecommerce Metrics');
    
    // Contar peticiones iniciales
    const initialRequests = requests.length;
    console.log(`Peticiones iniciales: ${initialRequests}`);
    
    // Abrir dropdown de período
    await page.click('button:has-text("Período")');
    await page.waitForSelector('text=Este Mes');
    
    // Hacer clic en Personalizado
    await page.click('button:has-text("Personalizado")');
    
    // Esperar un momento para verificar que NO se hizo petición
    await page.waitForTimeout(500);
    const afterCustomClick = requests.length;
    console.log(`Peticiones después de clic en Personalizado: ${afterCustomClick}`);
    
    // Verificar que NO se hizo nueva petición al hacer clic en "Personalizado"
    expect(afterCustomClick).toBe(initialRequests);
    console.log('✅ No se hizo petición al hacer clic en Personalizado');
    
    // Llenar las fechas
    const fromInput = page.locator('input[type="date"]').first();
    const toInput = page.locator('input[type="date"]').last();
    
    await fromInput.fill('2025-01-01');
    await toInput.fill('2025-01-31');
    
    // Verificar que el botón ahora está habilitado
    const applyButton = page.locator('button:has-text("Aplicar fechas")');
    await expect(applyButton).toBeEnabled();
    
    // Hacer clic en Aplicar
    await applyButton.click();
    
    // Esperar a que se haga la petición
    await page.waitForTimeout(1000);
    const afterApply = requests.length;
    console.log(`Peticiones después de aplicar: ${afterApply}`);
    
    // Verificar que se hizo una nueva petición con las fechas
    expect(afterApply).toBeGreaterThan(afterCustomClick);
    
    // Verificar que la petición incluye las fechas correctas
    const lastRequest = requests[requests.length - 1];
    expect(lastRequest).toContain('period_type=custom');
    expect(lastRequest).toContain('start_date=2025-01-01');
    expect(lastRequest).toContain('end_date=2025-01-31');
    
    console.log('✅ Test 2 pasado: La petición se hace con las fechas correctas');
  });

  test('no debe haber error 500 al usar filtro custom', async ({ page }) => {
    // Capturar respuestas
    const responses: { url: string; status: number }[] = [];
    page.on('response', (response) => {
      if (response.url().includes('/api/')) {
        responses.push({
          url: response.url(),
          status: response.status()
        });
      }
    });

    await page.goto('/');
    await page.waitForSelector('text=Ecommerce Metrics');
    
    // Abrir dropdown y seleccionar custom
    await page.click('button:has-text("Período")');
    await page.waitForSelector('text=Este Mes');
    await page.click('button:has-text("Personalizado")');
    
    // Llenar fechas
    await page.locator('input[type="date"]').first().fill('2025-11-01');
    await page.locator('input[type="date"]').last().fill('2025-11-30');
    
    // Aplicar
    await page.click('button:has-text("Aplicar fechas")');
    
    // Esperar respuesta
    await page.waitForTimeout(2000);
    
    // Verificar que no hay errores 500
    const errors = responses.filter(r => r.status >= 500);
    console.log('Respuestas con error:', errors);
    
    expect(errors.length).toBe(0);
    console.log('✅ Test 3 pasado: No hay errores 500');
    
    // Verificar que los datos se cargaron (debe aparecer la tabla con el header)
    await expect(page.locator('text=Todos los Partners')).toBeVisible();
  });
});

