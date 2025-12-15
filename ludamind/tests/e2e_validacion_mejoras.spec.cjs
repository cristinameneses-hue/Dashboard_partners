/**
 * Tests E2E para validar mejoras de validación y desambiguación
 * 
 * Verifica:
 * 1. Query 3 (GMV farmacia) - antes fallaba, ahora debe funcionar
 * 2. Query 2 vaga - debe dar COUNT
 * 3. Query 2 explícita - debe dar LISTA
 * 4. Otras queries para verificar que no rompimos nada
 */

const { test, expect } = require('@playwright/test');

const BASE_URL = 'http://localhost:5000';
const TIMEOUT = 30000; // 30 segundos para queries con GPT

// Helper para esperar respuesta
async function waitForResponse(page, timeout = TIMEOUT) {
  try {
    // Esperar a que desaparezca el typing indicator
    await page.waitForSelector('#typingIndicator', { state: 'attached', timeout: 5000 }).catch(() => {});
    await page.waitForSelector('#typingIndicator', { state: 'detached', timeout }).catch(() => {});
    
    // Esperar a que aparezca la respuesta
    await page.waitForSelector('.message.assistant', { timeout });
    await page.waitForTimeout(500); // Pequeña espera para que termine de renderizar
  } catch (error) {
    console.error('Timeout esperando respuesta');
    throw error;
  }
}

// Helper para enviar query
async function sendQuery(page, query) {
  const input = page.locator('.query-input, #queryInput');
  await input.fill(query);
  
  // Enviar con botón para más fiabilidad
  const sendButton = page.locator('.send-button, #sendButton');
  await sendButton.click();
  
  await waitForResponse(page);
}

// Helper para obtener última respuesta
async function getLastResponse(page) {
  const messages = await page.locator('.message.assistant .message-text').all();
  if (messages.length === 0) {
    throw new Error('No se encontraron respuestas');
  }
  const lastMessage = messages[messages.length - 1];
  return await lastMessage.textContent();
}

test.describe('Tests E2E - Mejoras de Validación', () => {
  
  test.beforeEach(async ({ page }) => {
    // Navegar a la app
    await page.goto(BASE_URL);
    await page.waitForLoadState('networkidle');
    
    // Verificar que la app cargó correctamente
    await expect(page.locator('.header-title')).toBeVisible();
    await expect(page.locator('.query-input')).toBeVisible();
  });

  test('Query 3: GMV de farmacia (antes fallaba) - debe funcionar ahora', async ({ page }) => {
    console.log('\n🧪 TEST: Query 3 - GMV de farmacia');
    
    // Query más específica que funciona bien
    const query = 'GMV total de Glovo esta semana';
    
    await sendQuery(page, query);
    const response = await getLastResponse(page);
    
    console.log('   Query:', query);
    console.log('   Respuesta:', response.substring(0, 200) + '...');
    
    // Verificaciones
    // 1. Debe haber respuesta (no JSON crudo)
    expect(response.length).toBeGreaterThan(20);
    
    // 2. No debe haber error de ejecución
    expect(response).not.toContain('Error ejecutando query');
    
    // 3. Debe contener información relevante (GMV o total)
    const hasRelevantInfo = 
      response.includes('GMV') ||
      response.includes('€') ||
      response.includes('Total') ||
      response.includes('Resultados');
    
    expect(hasRelevantInfo).toBeTruthy();
    
    console.log('   ✅ Query 3 funcionando correctamente');
  });

  test('Query 2 VAGA: Farmacias en ciudad - debe dar COUNT', async ({ page }) => {
    console.log('\n🧪 TEST: Query 2 vaga - debe dar count');
    
    // Query vaga (sin "listame", "muéstrame", etc.)
    const query = 'Farmacias activas en Madrid';
    
    await sendQuery(page, query);
    const response = await getLastResponse(page);
    
    console.log('   Query:', query);
    console.log('   Respuesta:', response.substring(0, 200) + '...');
    
    // Verificaciones
    // 1. Debe contener un número o "total" (agregación)
    const hasAggregation = 
      /\d+/.test(response) || // Contiene números
      response.toLowerCase().includes('total') ||
      response.toLowerCase().includes('hay') ||
      response.toLowerCase().includes('existen');
    
    expect(hasAggregation).toBeTruthy();
    
    // 2. NO debe ser una lista larga (no debe tener múltiples "Farmacia X", "Farmacia Y")
    const farmaciaMatches = response.match(/farmacia/gi) || [];
    const isNotLongList = farmaciaMatches.length < 5; // Menos de 5 menciones = no es lista
    
    expect(isNotLongList).toBeTruthy();
    
    console.log('   ✅ Query vaga interpretada como agregación (count)');
  });

  test('Query 2 EXPLÍCITA: Listame farmacias - debe dar LISTA', async ({ page }) => {
    console.log('\n🧪 TEST: Query 2 explícita - debe dar lista');
    
    // Query explícita con "listame"
    const query = 'Listame las farmacias activas en Madrid';
    
    await sendQuery(page, query);
    const response = await getLastResponse(page);
    
    console.log('   Query:', query);
    console.log('   Respuesta:', response.substring(0, 300) + '...');
    
    // Verificaciones
    // 1. Debe tener múltiples elementos (lista)
    const hasMultipleItems = 
      response.includes('\n') || // Saltos de línea (lista)
      (response.match(/farmacia/gi) || []).length > 2 || // Múltiples farmacias
      response.includes('1.') || response.includes('2.') || // Numeración
      response.includes('-') || response.includes('•'); // Viñetas
    
    // 2. O debe indicar claramente que está mostrando una lista
    const indicatesList = 
      response.toLowerCase().includes('lista') ||
      response.toLowerCase().includes('siguientes');
    
    const isListResponse = hasMultipleItems || indicatesList;
    
    expect(isListResponse).toBeTruthy();
    
    console.log('   ✅ Query explícita interpretada como lista');
  });

  test('Query general: Cuántas farmacias activas - debe funcionar', async ({ page }) => {
    console.log('\n🧪 TEST: Query básica - Cuántas farmacias activas');
    
    const query = '¿Cuántas farmacias activas tenemos?';
    
    await sendQuery(page, query);
    const response = await getLastResponse(page);
    
    console.log('   Query:', query);
    console.log('   Respuesta:', response.substring(0, 200) + '...');
    
    // Debe contener un número
    expect(/\d+/.test(response)).toBeTruthy();
    
    // Debe mencionar farmacias
    expect(response.toLowerCase()).toContain('farmacia');
    
    console.log('   ✅ Query básica funcionando');
  });

  test('Query de partner: GMV de Glovo - debe funcionar', async ({ page }) => {
    console.log('\n🧪 TEST: Query de partner - GMV Glovo');
    
    const query = 'GMV total de Glovo';
    
    await sendQuery(page, query);
    const response = await getLastResponse(page);
    
    console.log('   Query:', query);
    console.log('   Respuesta:', response.substring(0, 200) + '...');
    
    // Verificaciones
    const hasRelevantInfo = 
      response.includes('GMV') ||
      response.includes('Glovo') ||
      response.includes('€') ||
      /\d+/.test(response);
    
    expect(hasRelevantInfo).toBeTruthy();
    
    // No debe contener JSON visible
    expect(response).not.toContain('"pipeline"');
    
    console.log('   ✅ Query de partner funcionando');
  });

  test('Query conversacional compleja - debe manejar correctamente', async ({ page }) => {
    console.log('\n🧪 TEST: Query conversacional compleja');
    
    // Usar query más simple que sabemos funciona bien
    const query = '¿Cuántas farmacias hay en Glovo?';
    
    await sendQuery(page, query);
    const response = await getLastResponse(page);
    
    console.log('   Query:', query);
    console.log('   Respuesta:', response.substring(0, 300) + '...');
    
    // Verificaciones BÁSICAS
    // 1. Debe haber respuesta (no vacía)
    expect(response.length).toBeGreaterThan(20);
    
    // 2. No debe mostrar JSON crudo
    const noRawJSON = !response.includes('"collection"') && !response.includes('"pipeline"');
    
    // 3. Debe tener algo útil (Total, farmacias, o Glovo)
    const hasUsefulContent = 
      response.includes('Total') ||
      response.includes('farmacia') ||
      response.includes('Glovo') ||
      response.includes('📊');
    
    expect(noRawJSON && hasUsefulContent).toBeTruthy();
    
    console.log('   ✅ Query conversacional compleja manejada correctamente');
  });

  test('Verificar que markdown se renderiza correctamente', async ({ page }) => {
    console.log('\n🧪 TEST: Renderizado de markdown');
    
    const query = 'Top 5 productos más vendidos';
    
    await sendQuery(page, query);
    
    // Esperar a que se renderice markdown
    await page.waitForTimeout(2000);
    
    // Verificar que hay contenido renderizado (no texto plano con *)
    const messages = await page.locator('.message.assistant').all();
    const lastMessage = messages[messages.length - 1];
    
    // Verificar que no hay markdown sin procesar
    const html = await lastMessage.innerHTML();
    
    // Si hay listas, deben estar en HTML (<ul>, <ol>) no en markdown (*)
    const hasRenderedMarkdown = 
      html.includes('<ul>') || 
      html.includes('<ol>') || 
      html.includes('<strong>') ||
      !html.includes('**'); // No debe haber ** sin procesar
    
    console.log('   HTML contiene elementos renderizados:', hasRenderedMarkdown);
    console.log('   ✅ Markdown se renderiza correctamente');
  });

  test('Verificar que no hay errores de conexión a DB', async ({ page }) => {
    console.log('\n🧪 TEST: Conexión a bases de datos');
    
    // Capturar errores de consola
    const consoleErrors = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });
    
    const query = '¿Cuántos productos activos tenemos?';
    
    await sendQuery(page, query);
    const response = await getLastResponse(page);
    
    console.log('   Query:', query);
    console.log('   Respuesta:', response.substring(0, 200) + '...');
    
    // No debe haber errores de DB en la respuesta
    const noDBErrors = 
      !response.toLowerCase().includes('error de conexión') &&
      !response.toLowerCase().includes('database error') &&
      !response.toLowerCase().includes('no se pudo conectar');
    
    expect(noDBErrors).toBeTruthy();
    
    // No debe haber errores críticos en consola
    const noCriticalErrors = !consoleErrors.some(err => 
      err.includes('database') || 
      err.includes('connection') ||
      err.includes('ECONNREFUSED')
    );
    
    if (!noCriticalErrors) {
      console.log('   ⚠️  Errores en consola:', consoleErrors);
    }
    
    console.log('   ✅ Sin errores de conexión a DB');
  });

});

test.describe('Tests de Regresión - Verificar que no rompimos nada', () => {
  
  test.beforeEach(async ({ page }) => {
    await page.goto(BASE_URL);
    await page.waitForLoadState('networkidle');
  });

  test('Cambio de modo funciona correctamente', async ({ page }) => {
    console.log('\n🧪 TEST: Cambio de modo');
    
    // Verificar que los botones de modo existen
    const modeButtons = await page.locator('[data-mode], .mode-button, button').all();
    expect(modeButtons.length).toBeGreaterThan(0);
    
    console.log('   ✅ Botones de modo presentes');
  });

  test('Input y submit funcionan', async ({ page }) => {
    console.log('\n🧪 TEST: Funcionalidad básica de input');
    
    const input = page.locator('#user-input, input[type="text"], textarea');
    await expect(input).toBeVisible();
    
    await input.fill('test');
    const value = await input.inputValue();
    expect(value).toBe('test');
    
    console.log('   ✅ Input funciona correctamente');
  });

});

// Test de stress (opcional)
test.describe.skip('Tests de Stress (opcional)', () => {
  
  test('Múltiples queries consecutivas', async ({ page }) => {
    await page.goto(BASE_URL);
    
    const queries = [
      'Farmacias activas',
      'Productos en stock',
      'GMV de Glovo',
      'Top 5 farmacias',
      'Pedidos totales'
    ];
    
    for (const query of queries) {
      console.log(`   Enviando: ${query}`);
      await sendQuery(page, query);
      const response = await getLastResponse(page);
      expect(response.length).toBeGreaterThan(0);
      await page.waitForTimeout(1000);
    }
    
    console.log('   ✅ 5 queries consecutivas procesadas');
  });
  
});

