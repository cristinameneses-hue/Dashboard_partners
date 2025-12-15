const { test, expect } = require('@playwright/test');

test.describe('Debug Mode E2E Tests', () => {
  test('should activate debug mode and show metadata', async ({ page }) => {
    // 1. Ir a la página principal
    await page.goto('http://localhost:5000');
    await page.waitForLoadState('networkidle');

    console.log('✓ Página principal cargada');

    // 2. Activar modo debug
    await page.goto('http://localhost:5000/debug');
    await page.waitForTimeout(2000); // Esperar notificación

    console.log('✓ Modo debug activado');

    // 3. Verificar que nos redirija a la página principal
    await page.waitForURL('http://localhost:5000/', { timeout: 5000 });

    console.log('✓ Redirigido a página principal');

    // 4. Verificar que el indicador de debug esté visible
    const debugIndicator = page.locator('#debugIndicator');
    await expect(debugIndicator).toBeVisible({ timeout: 5000 });
    await expect(debugIndicator).toContainText('Modo Debug');

    console.log('✓ Indicador de debug visible');

    // 5. Hacer una consulta
    const queryInput = page.locator('#queryInput');
    await queryInput.fill('¿Cuántos bookings se hicieron hoy?');

    console.log('✓ Consulta ingresada');

    // 6. Enviar consulta
    const submitButton = page.locator('#submitQuery');
    await submitButton.click();

    console.log('✓ Consulta enviada');

    // 7. Esperar resultados
    await page.waitForSelector('#resultsSection', { state: 'visible', timeout: 15000 });

    console.log('✓ Resultados visibles');

    // 8. Verificar que el metadataSection esté visible (solo en modo debug)
    const metadataSection = page.locator('#metadataSection');
    await expect(metadataSection).toBeVisible({ timeout: 5000 });

    console.log('✓ Metadata section visible');

    // 9. Verificar que aparezcan los campos de debug
    const metadataItems = page.locator('.metadata-item');
    const count = await metadataItems.count();

    console.log(`✓ Encontrados ${count} items de metadata`);
    expect(count).toBeGreaterThan(0);

    // 10. Verificar campos específicos
    const metadataText = await metadataSection.textContent();

    console.log('Metadata encontrada:', metadataText);

    // Debe contener al menos algunos de estos campos
    const hasDatabase = metadataText.includes('Base de Datos') || metadataText.includes('BD Detectada');
    const hasOperation = metadataText.includes('Operación');
    const hasConfidence = metadataText.includes('Confianza');

    expect(hasDatabase || hasOperation || hasConfidence).toBeTruthy();

    console.log('✓ Campos de debug encontrados');

    // 11. Verificar que el JSON output tenga contenido completo
    const jsonOutput = page.locator('#jsonOutput');
    const jsonText = await jsonOutput.textContent();

    console.log('JSON output length:', jsonText.length);

    // En modo debug debe mostrar el objeto completo, no solo "results"
    expect(jsonText).toContain('database_type');
    expect(jsonText).toContain('confidence');

    console.log('✓ JSON completo visible');

    // 12. Desactivar modo debug
    await page.goto('http://localhost:5000/debug');
    await page.waitForTimeout(2000);

    console.log('✓ Modo debug desactivado');

    // 13. Verificar que el indicador desaparezca
    await page.waitForURL('http://localhost:5000/', { timeout: 5000 });
    await expect(debugIndicator).not.toBeVisible({ timeout: 5000 });

    console.log('✓ Indicador de debug oculto');

    // 14. Hacer otra consulta sin modo debug
    await queryInput.fill('¿Cuántos bookings se hicieron hoy?');
    await submitButton.click();

    await page.waitForSelector('#resultsSection', { state: 'visible', timeout: 15000 });

    console.log('✓ Segunda consulta realizada');

    // 15. Verificar que el metadata section NO esté visible (modo normal)
    const metadataDisplayStyle = await metadataSection.evaluate(el => window.getComputedStyle(el).display);
    expect(metadataDisplayStyle).toBe('none');

    console.log('✓ Metadata section oculta en modo normal');

    // 16. Verificar que el JSON solo muestre "results"
    const jsonTextNormal = await jsonOutput.textContent();
    const jsonParsed = JSON.parse(jsonTextNormal);

    // En modo normal debe tener solo "results"
    expect(jsonParsed).toHaveProperty('results');
    expect(jsonParsed).not.toHaveProperty('database_type');

    console.log('✓ JSON simplificado en modo normal');

    console.log('\n✅ TODAS LAS PRUEBAS E2E PASARON');
  });

  test('should persist debug mode across page reloads', async ({ page }) => {
    // 1. Activar modo debug
    await page.goto('http://localhost:5000/debug');
    await page.waitForTimeout(2000);
    await page.waitForURL('http://localhost:5000/', { timeout: 5000 });

    // 2. Verificar que está activo
    const debugIndicator = page.locator('#debugIndicator');
    await expect(debugIndicator).toBeVisible();

    console.log('✓ Debug mode activado');

    // 3. Recargar página
    await page.reload();
    await page.waitForLoadState('networkidle');

    console.log('✓ Página recargada');

    // 4. Verificar que sigue activo
    await expect(debugIndicator).toBeVisible({ timeout: 5000 });

    console.log('✓ Debug mode persiste después de reload');

    // 5. Desactivar
    await page.goto('http://localhost:5000/debug');
    await page.waitForTimeout(2000);

    console.log('✅ PRUEBA DE PERSISTENCIA PASADA');
  });
});
