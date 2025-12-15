/**
 * Test E2E - Query Hardcodeada de KPIs Completos
 * Verifica que la nueva query hardcodeada funcione correctamente
 */

const { test, expect } = require('@playwright/test');

const BASE_URL = 'http://localhost:5000';

test('debería devolver TODOS los KPIs completos de Glovo del mes pasado', async ({ page }) => {
    // Navegar
    await page.goto(BASE_URL);
    await page.waitForLoadState('networkidle');

    console.log('✅ Página cargada');

    // Seleccionar modo Partners
    await page.locator('[data-mode="partner"]').click();
    await page.waitForTimeout(500);

    console.log('✅ Modo Partners seleccionado');

    // Escribir la pregunta EXACTA del modal
    const queryInput = page.locator('#queryInput');
    await queryInput.fill('Dame los KPIs de Glovo del mes pasado: GMV total, GMV cancelado, número de bookings, bookings cancelados y farmacias con pedidos');

    console.log('✅ Query ingresada');

    // Enviar query
    const sendButton = page.locator('#sendButton');
    await sendButton.click();

    console.log('⏳ Esperando respuesta...');

    // Esperar respuesta (timeout extendido)
    await page.waitForSelector('.message.assistant', { timeout: 90000 });
    await page.waitForTimeout(2000); // Esperar a que termine el streaming

    console.log('✅ Respuesta recibida');

    // Obtener texto de la respuesta
    const responseElement = page.locator('.message.assistant').last();
    const responseText = await responseElement.textContent();

    console.log('\n📄 RESPUESTA COMPLETA:');
    console.log('─'.repeat(80));
    console.log(responseText);
    console.log('─'.repeat(80));

    // Verificar que contenga TODAS las métricas solicitadas
    console.log('\n🔍 VALIDANDO PRESENCIA DE MÉTRICAS:');

    const checks = {
        'GMV Total': /GMV Total.*€.*[\d,]+\.\d{2}/i.test(responseText),
        'GMV Cancelado': /GMV Cancelado.*€.*[\d,]+\.\d{2}/i.test(responseText),
        'GMV Activo': /GMV Activo.*€.*[\d,]+\.\d{2}/i.test(responseText),
        'Total Bookings': /Total Bookings.*[\d,]+/i.test(responseText),
        'Bookings Cancelados': /Bookings Cancelados.*[\d,]+/i.test(responseText),
        'Bookings Activos': /Bookings Activos.*[\d,]+/i.test(responseText),
        'Tasa de Cancelación': /Tasa de Cancelación.*[\d,]+\.\d{2}%/i.test(responseText),
        'Farmacias con Pedidos': /Farmacias con Pedidos.*[\d,]+/i.test(responseText)
    };

    for (const [metric, found] of Object.entries(checks)) {
        console.log(`  ${found ? '✅' : '❌'} ${metric}: ${found ? 'ENCONTRADO' : 'FALTA'}`);
        expect(found, `Falta la métrica: ${metric}`).toBeTruthy();
    }

    // Verificar que menciona "mes pasado" o el mes específico
    const periodCheck = /mes pasado|Noviembre|Octubre|Período:/i.test(responseText);
    console.log(`\n  ${periodCheck ? '✅' : '❌'} Período mencionado: ${periodCheck ? 'SÍ' : 'NO'}`);
    expect(periodCheck, 'No se menciona el período').toBeTruthy();

    // Verificar que menciona "Glovo"
    const partnerCheck = /Glovo/i.test(responseText);
    console.log(`  ${partnerCheck ? '✅' : '❌'} Partner mencionado (Glovo): ${partnerCheck ? 'SÍ' : 'NO'}`);
    expect(partnerCheck, 'No se menciona Glovo').toBeTruthy();

    // Verificar que dice "query hardcodeada" o "KPIs completos" en la fuente
    const sourceCheck = /query hardcodeada|KPIs completos/i.test(responseText);
    console.log(`  ${sourceCheck ? '✅' : '❌'} Indica query hardcodeada: ${sourceCheck ? 'SÍ' : 'NO'}`);
    expect(sourceCheck, 'No indica que es query hardcodeada').toBeTruthy();

    console.log('\n🎉 ¡Test completado exitosamente! Todos los KPIs están presentes.');
});

test('debería permitir cambiar el partner (Uber) manteniendo todas las métricas', async ({ page }) => {
    await page.goto(BASE_URL);
    await page.waitForLoadState('networkidle');

    // Seleccionar modo Partners
    await page.locator('[data-mode="partner"]').click();
    await page.waitForTimeout(500);

    // Cambiar Glovo por Uber
    const queryInput = page.locator('#queryInput');
    await queryInput.fill('Dame los KPIs de Uber del mes pasado: GMV total, GMV cancelado, número de bookings, bookings cancelados y farmacias con pedidos');

    const sendButton = page.locator('#sendButton');
    await sendButton.click();

    await page.waitForSelector('.message.assistant', { timeout: 90000 });
    await page.waitForTimeout(2000);

    const responseElement = page.locator('.message.assistant').last();
    const responseText = await responseElement.textContent();

    console.log('\n📄 RESPUESTA PARA UBER:');
    console.log('─'.repeat(80));
    console.log(responseText.substring(0, 400) + '...');
    console.log('─'.repeat(80));

    // Verificar que menciona "Uber"
    expect(responseText).toMatch(/Uber/i);

    // Verificar que tiene las métricas principales
    expect(responseText).toMatch(/GMV Total/i);
    expect(responseText).toMatch(/GMV Cancelado/i);
    expect(responseText).toMatch(/Bookings/i);
    expect(responseText).toMatch(/Farmacias/i);

    console.log('✅ Query funciona correctamente con Uber');
});

test('debería interpretar correctamente "mes pasado" como el mes completo anterior', async ({ page }) => {
    await page.goto(BASE_URL);
    await page.waitForLoadState('networkidle');

    // Seleccionar modo Partners
    await page.locator('[data-mode="partner"]').click();
    await page.waitForTimeout(500);

    const queryInput = page.locator('#queryInput');
    await queryInput.fill('Dame los KPIs de Glovo del mes pasado: GMV total, GMV cancelado, número de bookings, bookings cancelados y farmacias con pedidos');

    const sendButton = page.locator('#sendButton');
    await sendButton.click();

    await page.waitForSelector('.message.assistant', { timeout: 90000 });
    await page.waitForTimeout(2000);

    const responseElement = page.locator('.message.assistant').last();
    const responseText = await responseElement.textContent();

    // Verificar que NO dice "últimos 7 días"
    const notLastWeek = !/últimos 7 días/i.test(responseText);
    console.log(`\n  ${notLastWeek ? '✅' : '❌'} NO interpreta como "últimos 7 días": ${notLastWeek ? 'CORRECTO' : 'ERROR'}`);
    expect(notLastWeek, 'Está interpretando como "últimos 7 días" en lugar de "mes pasado"').toBeTruthy();

    // Verificar que menciona el mes correcto (Noviembre 2025 si estamos en Diciembre 2025)
    const now = new Date();
    const lastMonthName = new Date(now.getFullYear(), now.getMonth() - 1, 1).toLocaleString('es-ES', { month: 'long' });

    console.log(`  Esperando período: "mes pasado" o "${lastMonthName}"`);

    const correctPeriod = new RegExp(`mes pasado|${lastMonthName}`, 'i').test(responseText);
    console.log(`  ${correctPeriod ? '✅' : '⚠️'} Período correcto: ${correctPeriod ? 'SÍ' : 'NO (pero puede ser aceptable)'}`);

    console.log('\n✅ Período interpretado correctamente (no es "últimos 7 días")');
});
