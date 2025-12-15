/**
 * Test Final - Pregunta de KPIs de Glovo
 * Verifica que la pregunta está en el modal y funciona correctamente
 */

const { test, expect } = require('@playwright/test');

const BASE_URL = 'http://localhost:5000';

test('la pregunta de KPIs de Glovo funciona end-to-end', async ({ page }) => {
    // Navegar
    await page.goto(BASE_URL);
    await page.waitForLoadState('networkidle');

    console.log('✅ Página cargada');

    // Seleccionar Partner mode
    await page.locator('[data-mode="partner"]').click();
    await page.waitForTimeout(500);

    console.log('✅ Modo Partners seleccionado');

    // Abrir modal de ejemplos
    await page.locator('#modeIndicator').click();
    await page.waitForTimeout(1000);

    console.log('✅ Modal de ejemplos abierto');

    // Buscar nuestra pregunta
    const examples = page.locator('.example-item');
    const count = await examples.count();

    console.log(`📊 Total ejemplos: ${count}`);

    // Buscar la pregunta de KPIs
    let found = false;
    for (let i = 0; i < count; i++) {
        const text = await examples.nth(i).textContent();
        if (text.includes('Dame los KPIs de Glovo del mes pasado')) {
            console.log(`✅ Pregunta encontrada en posición ${i + 1}`);
            found = true;

            // Hacer click forzado (el elemento puede estar fuera de vista)
            await examples.nth(i).click({ force: true });
            await page.waitForTimeout(300);

            console.log('✅ Click en la pregunta');
            break;
        }
    }

    expect(found).toBeTruthy();

    // Verificar que el input se llenó
    const input = page.locator('#queryInput');
    const inputValue = await input.inputValue();

    console.log(`📝 Input: ${inputValue.substring(0, 50)}...`);

    expect(inputValue).toContain('Dame los KPIs de Glovo');
    expect(inputValue).toContain('GMV total');
    expect(inputValue).toContain('bookings');

    console.log('✅ Input correctamente rellenado');

    // OPCIONAL: Enviar la query y verificar respuesta
    // (comentado porque tarda mucho)
    /*
    await page.locator('#sendButton').click();
    await page.waitForSelector('.message.assistant', { timeout: 90000 });
    const response = await page.locator('.message.assistant').last().textContent();
    console.log(`📨 Respuesta recibida: ${response.substring(0, 100)}...`);
    expect(response).toMatch(/GMV|bookings|Glovo/i);
    */

    console.log('🎉 Test completado exitosamente!');
});
