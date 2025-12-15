/**
 * Test de verificación - Pregunta de KPIs de Glovo en modal
 * Verifica que la pregunta aparezca correctamente en el modal de ejemplos
 */

const { test, expect } = require('@playwright/test');

const BASE_URL = 'http://localhost:5000';

test('verificar que la pregunta de KPIs de Glovo aparece en el modal de Partners', async ({ page }) => {
    // Navegar a la aplicación
    await page.goto(BASE_URL);
    await page.waitForLoadState('networkidle');

    console.log('✅ Página cargada');

    // Seleccionar modo Partners
    const partnerButton = page.locator('[data-mode="partner"]');
    await partnerButton.click();
    await page.waitForTimeout(500);

    console.log('✅ Modo Partners seleccionado');

    // Hacer click en el indicador de modo para abrir ejemplos
    const modeIndicator = page.locator('#modeIndicator');
    await modeIndicator.click();
    await page.waitForTimeout(1000);

    console.log('✅ Click en indicador de modo');

    // Buscar todos los elementos con clase example-item
    const examples = page.locator('.example-item');
    const count = await examples.count();

    console.log(`📊 Total de ejemplos encontrados: ${count}`);

    if (count > 0) {
        // Listar todos los ejemplos
        for (let i = 0; i < count; i++) {
            const text = await examples.nth(i).textContent();
            console.log(`  ${i + 1}. ${text}`);
        }

        // Buscar específicamente nuestra pregunta
        const glovoKpisQuery = examples.filter({ hasText: /Dame los KPIs de Glovo del mes pasado/i });
        const glovoCount = await glovoKpisQuery.count();

        if (glovoCount > 0) {
            console.log('✅ ¡Pregunta de KPIs de Glovo ENCONTRADA en el modal!');
            await expect(glovoKpisQuery.first()).toBeVisible();

            // Hacer click en la pregunta
            await glovoKpisQuery.first().click();
            await page.waitForTimeout(300);

            // Verificar que se llenó el input
            const input = page.locator('#queryInput');
            const inputValue = await input.inputValue();
            console.log(`📝 Input rellenado con: ${inputValue}`);

            expect(inputValue).toContain('KPIs');
            expect(inputValue).toContain('Glovo');

        } else {
            console.log('❌ Pregunta de KPIs de Glovo NO encontrada');
            throw new Error('La pregunta de KPIs de Glovo no aparece en el modal');
        }
    } else {
        console.log('❌ No se encontraron ejemplos en el modal');

        // Intentar tomar screenshot para debugging
        await page.screenshot({ path: 'test-results/modal-sin-ejemplos.png' });
        console.log('📸 Screenshot guardado en test-results/modal-sin-ejemplos.png');

        throw new Error('El modal de ejemplos está vacío');
    }
});
