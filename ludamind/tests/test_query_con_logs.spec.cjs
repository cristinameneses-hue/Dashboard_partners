// Test con Playwright para capturar logs de la query
const { test, expect } = require('@playwright/test');

test.describe('Luda Mind - Test Query con Logs', () => {
  
  test('Top 10 farmacias que mas venden en Glovo - Capturar proceso completo', async ({ page }) => {
    
    console.log('\n' + '='.repeat(80));
    console.log('  TEST PLAYWRIGHT: Query con Logs');
    console.log('='.repeat(80));
    
    // Capturar console logs del navegador
    const consoleLogs = [];
    page.on('console', msg => {
      consoleLogs.push({
        type: msg.type(),
        text: msg.text(),
        timestamp: new Date().toISOString()
      });
    });
    
    // Capturar requests/responses
    const apiCalls = [];
    page.on('response', async response => {
      if (response.url().includes('/api/query')) {
        try {
          const responseData = await response.json();
          apiCalls.push({
            url: response.url(),
            status: response.status(),
            data: responseData
          });
        } catch (e) {
          // Response no es JSON
        }
      }
    });
    
    // Paso 1: Navegar a la app
    console.log('\n1️⃣ Navegando a http://localhost:5000...');
    await page.goto('http://localhost:5000');
    await page.waitForLoadState('networkidle');
    console.log('   ✅ Página cargada');
    
    // Paso 2: Seleccionar modo conversacional
    console.log('\n2️⃣ Seleccionando modo conversacional...');
    await page.click('[data-mode="conversational"]');
    await page.waitForTimeout(500);
    console.log('   ✅ Modo conversacional seleccionado');
    
    // Paso 3: Escribir la query
    const query = 'necesito que me des el top 10 farmacias que mas venden en glovo';
    console.log(`\n3️⃣ Escribiendo query: "${query}"`);
    await page.fill('#queryInput', query);
    console.log('   ✅ Query escrita');
    
    // Paso 4: Enviar
    console.log('\n4️⃣ Enviando query...');
    await page.click('#sendButton');
    
    // Esperar respuesta (hasta 15 segundos)
    console.log('   ⏳ Esperando respuesta del sistema...');
    await page.waitForTimeout(15000);
    
    // Paso 5: Capturar resultado
    console.log('\n5️⃣ Analizando resultado...');
    
    const messages = await page.locator('.message.assistant').count();
    console.log(`   ✅ Mensajes del asistente: ${messages}`);
    
    if (messages > 0) {
      const lastMessage = await page.locator('.message.assistant').last().textContent();
      console.log('\n📨 Respuesta recibida:');
      console.log('─'.repeat(80));
      console.log(lastMessage.substring(0, 300) + '...');
      console.log('─'.repeat(80));
    }
    
    // Paso 6: Mostrar API calls
    console.log('\n' + '='.repeat(80));
    console.log('  📊 API CALLS CAPTURADOS');
    console.log('='.repeat(80));
    
    if (apiCalls.length > 0) {
      const lastCall = apiCalls[apiCalls.length - 1];
      
      console.log('\n📡 Request/Response:');
      console.log(`   URL: ${lastCall.url}`);
      console.log(`   Status: ${lastCall.status}`);
      
      if (lastCall.data) {
        console.log('\n📊 Datos de la respuesta:');
        console.log(`   success: ${lastCall.data.success}`);
        console.log(`   mode: ${lastCall.data.mode}`);
        console.log(`   method: ${lastCall.data.method}`);
        console.log(`   database: ${lastCall.data.database}`);
        console.log(`   confidence: ${(lastCall.data.confidence * 100).toFixed(0)}%`);
        console.log(`   system: ${lastCall.data.system}`);
        
        if (lastCall.data.interpretation) {
          console.log('\n🧠 INTERPRETACIÓN DE GPT:');
          console.log(JSON.stringify(lastCall.data.interpretation, null, 2));
        }
        
        console.log('\n💬 Respuesta (preview):');
        console.log(lastCall.data.answer.substring(0, 300) + '...');
      }
    } else {
      console.log('⚠️ No se capturaron API calls');
    }
    
    // Paso 7: Console logs del navegador
    console.log('\n' + '='.repeat(80));
    console.log('  📋 CONSOLE LOGS DEL NAVEGADOR');
    console.log('='.repeat(80));
    
    const errorLogs = consoleLogs.filter(log => log.type === 'error');
    if (errorLogs.length > 0) {
      console.log('\n❌ Errores detectados:');
      errorLogs.forEach(log => {
        console.log(`   ${log.timestamp}: ${log.text}`);
      });
    } else {
      console.log('\n✅ Sin errores en el navegador');
    }
    
    console.log('\n' + '='.repeat(80));
    console.log('  ✅ TEST COMPLETADO');
    console.log('='.repeat(80));
    
  });
  
});
