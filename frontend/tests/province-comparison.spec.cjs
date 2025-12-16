const { test, expect } = require('@playwright/test');

// Aumentar timeout global para tests de LudaMind (respuestas pueden tardar)
test.setTimeout(120000);

test.describe('Luda Mind - Province Comparison Tests', () => {

  test.beforeEach(async ({ page }) => {
    // Navegar directamente a Luda Mind
    await page.goto('/luda-mind');
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(2000);

    // Verificar que estamos en Luda Mind buscando elementos caracteristicos
    const ludaMindHeader = page.locator('text=Luda Mind').first();
    await expect(ludaMindHeader).toBeVisible({ timeout: 10000 });
    await page.screenshot({ path: 'test-results/ludamind-after-navigation.png', fullPage: true });
  });

  test('debe ejecutar comparativa absoluta de provincias', async ({ page }) => {
    // Tomar screenshot inicial de Luda Mind
    await page.screenshot({ path: 'test-results/ludamind-initial.png', fullPage: true });

    // En la interfaz de Luda Mind, hay una seccion "Modos de Consulta" con botones
    // Buscar el boton Partners dentro del area de modos (NO el sidebar principal)
    // El boton Partners tiene "Canales y GMV" como subtexto
    const partnersModeButton = page.locator('text=Partners >> xpath=./ancestor::button | text=Canales y GMV >> xpath=./ancestor::button').first();

    // Alternativa: buscar por el contenedor de modos
    const partnersMode = page.locator('button:has-text("Partners"):has-text("GMV")').first();
    if (await partnersMode.isVisible({ timeout: 2000 })) {
      await partnersMode.click();
    } else {
      // Intentar con otro selector
      const altPartnersMode = page.locator('div:has-text("Modos de Consulta") button:has-text("Partners")').first();
      if (await altPartnersMode.isVisible({ timeout: 2000 })) {
        await altPartnersMode.click();
      } else {
        // Buscar directamente el boton con "Partners" y "Canales y GMV"
        await page.locator('button:has(div:text("Partners"))').first().click();
      }
    }
    await page.waitForTimeout(500);

    // Tomar screenshot despues de seleccionar modo Partners
    await page.screenshot({ path: 'test-results/ludamind-partners-mode.png', fullPage: true });

    // Ahora deberia aparecer el QueryBuilder con los templates de queries
    // Buscar el template "Comparativa Absoluta Provincias"
    const absoluteTemplate = page.locator('text=Comparativa Absoluta').first();
    await expect(absoluteTemplate).toBeVisible({ timeout: 10000 });
    await absoluteTemplate.click();
    await page.waitForTimeout(500);

    // Tomar screenshot despues de seleccionar template
    await page.screenshot({ path: 'test-results/ludamind-absolute-selected.png', fullPage: true });

    // Configurar periodo usando el dropdown de periodo
    const periodSelect = page.locator('select').first();
    if (await periodSelect.isVisible({ timeout: 2000 })) {
      await periodSelect.selectOption('this_month');
    }

    // Seleccionar Provincia 1 (Madrid)
    const province1Input = page.locator('input').first();
    await province1Input.click();
    await province1Input.fill('Madrid');
    await page.waitForTimeout(500);

    // Hacer clic en la opcion Madrid del dropdown
    const madridOption = page.locator('button:has-text("Madrid")').first();
    if (await madridOption.isVisible({ timeout: 2000 })) {
      await madridOption.click();
    }
    await page.waitForTimeout(300);

    // Seleccionar Provincia 2 (Barcelona)
    const province2Input = page.locator('input').nth(1);
    await province2Input.click();
    await province2Input.fill('Barcelona');
    await page.waitForTimeout(500);

    // Hacer clic en la opcion Barcelona
    const barcelonaOption = page.locator('button:has-text("Barcelona")').first();
    if (await barcelonaOption.isVisible({ timeout: 2000 })) {
      await barcelonaOption.click();
    }

    // Tomar screenshot con filtros configurados
    await page.screenshot({ path: 'test-results/ludamind-filters-configured.png', fullPage: true });

    // Hacer clic en "Enviar Consulta"
    const submitBtn = page.locator('button:has-text("Enviar Consulta")');
    await expect(submitBtn).toBeVisible({ timeout: 5000 });
    await submitBtn.click();

    // Esperar a que el boton "Enviando..." desaparezca (es decir, la respuesta llegue)
    // Buscar cuando el boton vuelva a estar habilitado o el texto cambie
    await page.waitForFunction(() => {
      const buttons = document.querySelectorAll('button');
      for (const btn of buttons) {
        if (btn.textContent && btn.textContent.includes('Enviando')) {
          return false; // Todavia enviando
        }
      }
      return true; // Ya no hay boton de "Enviando"
    }, { timeout: 90000 });

    // Dar tiempo para que se renderice la respuesta
    await page.waitForTimeout(5000);

    // Esperar a que aparezca una respuesta que contenga datos de comparativa (no el mensaje de bienvenida)
    await page.waitForFunction(() => {
      const messages = document.querySelectorAll('.luda-message-text:not(.user)');
      if (messages.length < 2) return false; // Debe haber al menos 2 mensajes (bienvenida + respuesta)
      const lastMessage = messages[messages.length - 1];
      const text = lastMessage.textContent || '';
      // La respuesta de comparativa debe contener Madrid Y Barcelona
      return text.includes('Madrid') && text.includes('Barcelona');
    }, { timeout: 90000 });

    // Esperar un poco más para asegurar renderizado completo
    await page.waitForTimeout(2000);

    // Hacer scroll al último mensaje para que sea visible
    const lastMessage = page.locator('.luda-message-text:not(.user)').last();
    await lastMessage.scrollIntoViewIfNeeded();
    await page.waitForTimeout(500);

    // Tomar screenshot solo del mensaje de respuesta
    await lastMessage.screenshot({ path: 'test-results/ludamind-response-absolute.png' });

    // También tomar un screenshot de toda la página para contexto
    await page.screenshot({ path: 'test-results/ludamind-full-page.png', fullPage: true });

    // Capturar el texto de la respuesta (el ultimo mensaje que no sea del usuario)
    const responseText = await page.locator('.luda-message-text:not(.user)').last().textContent();
    console.log('\n========== RESPUESTA COMPARATIVA ABSOLUTA ==========');
    console.log(responseText);
    console.log('====================================================\n');

    // Verificar que la respuesta contiene informacion de la tabla
    expect(responseText).toBeTruthy();
    expect(responseText).toContain('Madrid');
    expect(responseText).toContain('Barcelona');
  });

  test('debe ejecutar comparativa media por farmacia', async ({ page }) => {
    // Seleccionar modo Partners
    const partnersMode = page.locator('button:has-text("Partners"):has-text("GMV")').first();
    if (await partnersMode.isVisible({ timeout: 3000 })) {
      await partnersMode.click();
    } else {
      await page.locator('button:has(div:text("Partners"))').first().click();
    }
    await page.waitForTimeout(500);

    // Seleccionar template "Comparativa Media por Farmacia"
    const avgTemplate = page.locator('text=Comparativa Media').first();
    await expect(avgTemplate).toBeVisible({ timeout: 10000 });
    await avgTemplate.click();
    await page.waitForTimeout(500);

    // Configurar periodo
    const periodSelect = page.locator('select').first();
    if (await periodSelect.isVisible({ timeout: 2000 })) {
      await periodSelect.selectOption('this_month');
    }

    // Seleccionar Provincia 1 (Valencia)
    const province1Input = page.locator('input').first();
    await province1Input.click();
    await province1Input.fill('Valencia');
    await page.waitForTimeout(500);
    const valenciaOption = page.locator('button:has-text("Valencia")').first();
    if (await valenciaOption.isVisible({ timeout: 2000 })) {
      await valenciaOption.click();
    }
    await page.waitForTimeout(300);

    // Seleccionar Provincia 2 (Sevilla)
    const province2Input = page.locator('input').nth(1);
    await province2Input.click();
    await province2Input.fill('Sevilla');
    await page.waitForTimeout(500);
    const sevillaOption = page.locator('button:has-text("Sevilla")').first();
    if (await sevillaOption.isVisible({ timeout: 2000 })) {
      await sevillaOption.click();
    }

    // Tomar screenshot con filtros configurados
    await page.screenshot({ path: 'test-results/ludamind-avg-filters.png', fullPage: true });

    // Hacer clic en "Enviar Consulta"
    const submitBtn = page.locator('button:has-text("Enviar Consulta")');
    await expect(submitBtn).toBeVisible({ timeout: 5000 });
    await submitBtn.click();

    // Esperar a que el boton "Enviando..." desaparezca
    await page.waitForFunction(() => {
      const buttons = document.querySelectorAll('button');
      for (const btn of buttons) {
        if (btn.textContent && btn.textContent.includes('Enviando')) {
          return false;
        }
      }
      return true;
    }, { timeout: 90000 });

    // Dar tiempo para que se renderice la respuesta
    await page.waitForTimeout(5000);

    // Esperar a que aparezca una respuesta con Valencia Y Sevilla
    await page.waitForFunction(() => {
      const messages = document.querySelectorAll('.luda-message-text:not(.user)');
      if (messages.length < 2) return false;
      const lastMessage = messages[messages.length - 1];
      const text = lastMessage.textContent || '';
      return text.includes('Valencia') && text.includes('Sevilla');
    }, { timeout: 90000 });

    await page.waitForTimeout(2000);

    // Tomar screenshot de la respuesta
    await page.screenshot({ path: 'test-results/ludamind-response-avg.png', fullPage: true });

    // Capturar el texto de la respuesta
    const responseText = await page.locator('.luda-message-text:not(.user)').last().textContent();
    console.log('\n========== RESPUESTA COMPARATIVA MEDIA ==========');
    console.log(responseText);
    console.log('=================================================\n');

    // Verificar que la respuesta contiene informacion
    expect(responseText).toBeTruthy();
    expect(responseText).toContain('Valencia');
    expect(responseText).toContain('Sevilla');
  });

});
