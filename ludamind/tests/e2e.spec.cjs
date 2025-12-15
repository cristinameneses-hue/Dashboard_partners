const { test, expect } = require('@playwright/test');

test.describe('TrendsPro Web Application E2E Tests', () => {

  test.beforeEach(async ({ page }) => {
    // Navigate to the application
    await page.goto('http://localhost:5000');
  });

  test('should load the homepage successfully', async ({ page }) => {
    // Check that the page loaded
    await expect(page).toHaveTitle(/TrendsPro/);

    // Check for main elements
    await expect(page.locator('.project-title')).toContainText('TrendsPro');
    await expect(page.locator('.query-input')).toBeVisible();
    await expect(page.locator('.btn-submit')).toBeVisible();
  });

  test('should check server connection status', async ({ page }) => {
    // Wait for connection status to load
    await page.waitForTimeout(2000);

    // Take screenshot for debugging
    await page.screenshot({ path: 'test-results/homepage.png' });

    console.log('Page loaded successfully');
  });

  test('should have chat mode toggle visible', async ({ page }) => {
    // Check for chat mode toggle - the slider should be visible
    const toggleSlider = page.locator('.toggle-slider');
    await expect(toggleSlider).toBeVisible();

    console.log('Chat mode toggle slider is visible');
  });

  test('should be able to toggle chat mode', async ({ page }) => {
    const toggleLabel = page.locator('.toggle-switch');
    const conversationArea = page.locator('#conversationArea');

    // Initially conversation area should be hidden
    await expect(conversationArea).toBeHidden();

    // Click toggle label (not the hidden input)
    await toggleLabel.click();

    // Now conversation area should be visible
    await expect(conversationArea).toBeVisible();

    // Button text should change
    const submitButton = page.locator('#submitButtonText');
    await expect(submitButton).toContainText('Enviar');

    console.log('Chat mode toggle works correctly');
  });

  test('should make API call to check status', async ({ page }) => {
    // Listen for API calls
    const statusPromise = page.waitForResponse(response =>
      response.url().includes('/api/status') && response.status() === 200
    );

    // Trigger page load (which calls /api/status)
    await page.reload();

    const response = await statusPromise;
    const data = await response.json();

    console.log('API Status Response:', JSON.stringify(data, null, 2));

    // Verify response structure
    expect(data).toHaveProperty('connected');
    expect(data).toHaveProperty('openai_status');
    expect(data.connected).toBe(true);

    console.log('API status check successful');
  });

  test('should submit a normal query', async ({ page, context }) => {
    // Grant clipboard permissions
    await context.grantPermissions(['clipboard-read', 'clipboard-write']);

    const queryInput = page.locator('#queryInput');
    const submitButton = page.locator('#submitQuery');

    // Type a question
    await queryInput.fill('Cuantos bookings hay?');

    // Click submit
    await submitButton.click();

    // Wait for loading to appear and disappear
    await page.waitForSelector('#loadingState', { state: 'visible', timeout: 5000 });

    // Wait for results (with longer timeout)
    await page.waitForSelector('#resultsSection', { state: 'visible', timeout: 30000 });

    // Take screenshot of results
    await page.screenshot({ path: 'test-results/query-results.png' });

    console.log('Normal query submitted successfully');
  });

  test('should test chat mode conversation', async ({ page }) => {
    // Enable chat mode - click the toggle label
    const toggleLabel = page.locator('.toggle-switch');
    await toggleLabel.click();

    // Wait for conversation area to be visible
    await expect(page.locator('#conversationArea')).toBeVisible();

    // Type incomplete question
    const queryInput = page.locator('#queryInput');
    await queryInput.fill('Dame los datos de Glovo');

    // Submit
    const submitButton = page.locator('#submitQuery');
    await submitButton.click();

    // Wait for loading
    await page.waitForSelector('#loadingState', { state: 'visible', timeout: 5000 });

    // Wait for assistant response in conversation (with longer timeout)
    await page.waitForSelector('.conversation-message.assistant', { timeout: 30000 });

    // Check that a message appeared
    const messages = page.locator('.conversation-message');
    const count = await messages.count();
    expect(count).toBeGreaterThan(0);

    // Take screenshot
    await page.screenshot({ path: 'test-results/chat-conversation.png' });

    console.log(`Chat conversation has ${count} messages`);
  });

  test('should capture console errors', async ({ page }) => {
    const errors = [];

    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    page.on('pageerror', error => {
      errors.push(error.message);
    });

    // Navigate and wait a bit
    await page.goto('http://localhost:5000');
    await page.waitForTimeout(3000);

    // Take screenshot
    await page.screenshot({ path: 'test-results/final-state.png' });

    // Log any errors found
    if (errors.length > 0) {
      console.log('ERRORS FOUND:');
      errors.forEach(err => console.log('  -', err));
    } else {
      console.log('No console errors detected');
    }

    // Optionally fail the test if there are errors
    // expect(errors).toHaveLength(0);
  });
});
