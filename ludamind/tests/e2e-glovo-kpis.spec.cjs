/**
 * E2E Test - Glovo KPIs Query
 *
 * Tests the complete flow of querying Glovo KPIs from the web interface:
 * 1. Navigate to the application
 * 2. Select Partner mode
 * 3. Click on the predefined question about Glovo KPIs for October 2025
 * 4. Verify the query is sent and response is received
 * 5. Validate that the response contains the expected KPI metrics
 */

const { test, expect } = require('@playwright/test');

// Configuration
const BASE_URL = process.env.BASE_URL || 'http://localhost:5000';
const TIMEOUT = 60000; // 60 seconds for LLM response

test.describe('Glovo KPIs Query - E2E Test', () => {

    test.beforeEach(async ({ page }) => {
        // Navigate to the application
        await page.goto(BASE_URL);

        // Wait for the page to be fully loaded
        await page.waitForLoadState('networkidle');
    });

    test('should load the Luda Mind application', async ({ page }) => {
        // Verify title
        await expect(page).toHaveTitle(/Luda Mind/);

        // Verify main elements are visible
        await expect(page.locator('.header-title')).toBeVisible();
        await expect(page.locator('.sidebar')).toBeVisible();
        await expect(page.locator('.chat-area')).toBeVisible();
    });

    test('should display Partner mode button', async ({ page }) => {
        // Find Partner mode button
        const partnerButton = page.locator('[data-mode="partner"]');

        // Verify it exists and is visible
        await expect(partnerButton).toBeVisible();
        await expect(partnerButton).toContainText('Partners');
    });

    test('should show predefined questions when Partner mode is selected', async ({ page }) => {
        // Click on Partner mode
        const partnerButton = page.locator('[data-mode="partner"]');
        await partnerButton.click();

        // Wait for mode to be activated
        await expect(partnerButton).toHaveClass(/active/);

        // Click on mode indicator to show examples
        const modeIndicator = page.locator('#modeIndicator');
        await modeIndicator.click();

        // Wait for examples dropdown to appear
        await page.waitForTimeout(500);

        // Verify that example questions container exists
        const examplesContainer = page.locator('.examples-dropdown, .example-query');

        // Should have at least one example
        const examplesCount = await examplesContainer.count();
        expect(examplesCount).toBeGreaterThan(0);
    });

    test('should contain Glovo KPIs question in Partner mode examples', async ({ page }) => {
        // Click on Partner mode
        await page.locator('[data-mode="partner"]').click();
        await page.waitForTimeout(300);

        // Click to show examples
        await page.locator('#modeIndicator').click();
        await page.waitForTimeout(500);

        // Search for Glovo KPIs question
        const glovoKpisQuestion = page.locator('.example-query', {
            hasText: /KPIs completos de Glovo.*octubre 2025/i
        });

        // Verify the question exists
        await expect(glovoKpisQuestion).toBeVisible({ timeout: 5000 });
    });

    test('should send Glovo KPIs query and receive response', async ({ page }) => {
        // Click on Partner mode
        await page.locator('[data-mode="partner"]').click();
        await page.waitForTimeout(300);

        // Click to show examples
        await page.locator('#modeIndicator').click();
        await page.waitForTimeout(500);

        // Find and click the Glovo KPIs question
        const glovoKpisQuestion = page.locator('.example-query', {
            hasText: /KPIs completos de Glovo.*octubre 2025/i
        });

        await glovoKpisQuestion.click();

        // Verify input was filled
        const queryInput = page.locator('#queryInput');
        await expect(queryInput).toHaveValue(/octubre 2025/i);

        // Click send button
        const sendButton = page.locator('#sendButton');
        await sendButton.click();

        // Wait for response with extended timeout
        await page.waitForSelector('.message.assistant', { timeout: TIMEOUT });

        // Verify assistant response exists
        const assistantMessage = page.locator('.message.assistant').last();
        await expect(assistantMessage).toBeVisible();
    });

    test('should display Glovo KPIs metrics in response', async ({ page }) => {
        // Click on Partner mode
        await page.locator('[data-mode="partner"]').click();
        await page.waitForTimeout(300);

        // Click to show examples
        await page.locator('#modeIndicator').click();
        await page.waitForTimeout(500);

        // Find and click the Glovo KPIs question
        const glovoKpisQuestion = page.locator('.example-query', {
            hasText: /KPIs completos de Glovo.*octubre 2025/i
        });

        await glovoKpisQuestion.click();
        await page.waitForTimeout(200);

        // Send query
        await page.locator('#sendButton').click();

        // Wait for response
        await page.waitForSelector('.message.assistant', { timeout: TIMEOUT });

        // Get response text
        const assistantMessage = page.locator('.message.assistant').last();
        const responseText = await assistantMessage.textContent();

        // Verify response contains expected KPI keywords
        expect(responseText).toMatch(/GMV|bookings|pedidos/i);
        expect(responseText).toMatch(/Glovo/i);
        expect(responseText).toMatch(/octubre.*2025|2025.*octubre/i);

        // Verify response contains numeric values (at least one number)
        expect(responseText).toMatch(/\d+[,.]?\d*/);
    });

    test('should validate Glovo KPIs response contains all required metrics', async ({ page }) => {
        // Click on Partner mode
        await page.locator('[data-mode="partner"]').click();
        await page.waitForTimeout(300);

        // Click to show examples
        await page.locator('#modeIndicator').click();
        await page.waitForTimeout(500);

        // Find and click the Glovo KPIs question
        const glovoKpisQuestion = page.locator('.example-query', {
            hasText: /KPIs completos de Glovo.*octubre 2025/i
        });

        await glovoKpisQuestion.click();
        await page.waitForTimeout(200);

        // Send query
        await page.locator('#sendButton').click();

        // Wait for complete response
        await page.waitForSelector('.message.assistant', { timeout: TIMEOUT });

        // Wait additional time for streaming to complete
        await page.waitForTimeout(2000);

        // Get full response text
        const assistantMessage = page.locator('.message.assistant').last();
        const responseText = await assistantMessage.textContent();

        // Define expected KPIs (based on our analysis results)
        const expectedMetrics = [
            'GMV',           // Should mention GMV
            'bookings',      // Should mention bookings
            'cancelado',     // Should mention cancelled
            'farmacias'      // Should mention pharmacies
        ];

        // Verify all expected metrics are mentioned
        for (const metric of expectedMetrics) {
            expect(responseText.toLowerCase()).toContain(metric.toLowerCase());
        }

        // Log response for debugging
        console.log('Response received:', responseText.substring(0, 500) + '...');
    });

    test('should add query to history after submission', async ({ page }) => {
        // Click on Partner mode
        await page.locator('[data-mode="partner"]').click();
        await page.waitForTimeout(300);

        // Click to show examples
        await page.locator('#modeIndicator').click();
        await page.waitForTimeout(500);

        // Find and click the Glovo KPIs question
        const glovoKpisQuestion = page.locator('.example-query', {
            hasText: /KPIs completos de Glovo.*octubre 2025/i
        });

        await glovoKpisQuestion.click();
        await page.waitForTimeout(200);

        // Send query
        await page.locator('#sendButton').click();

        // Wait for response
        await page.waitForSelector('.message.assistant', { timeout: TIMEOUT });

        // Check history sidebar
        const historyItems = page.locator('.history-item');
        const historyCount = await historyItems.count();

        // Should have at least one history item
        expect(historyCount).toBeGreaterThan(0);

        // Last history item should contain part of our query
        const lastHistoryItem = historyItems.last();
        const historyText = await lastHistoryItem.textContent();
        expect(historyText).toMatch(/Glovo|KPIs|octubre/i);
    });

    test('should handle errors gracefully if query fails', async ({ page }) => {
        // Type an invalid query manually
        await page.locator('#queryInput').fill('Esta es una pregunta inválida que no debería funcionar 12345 !!!');

        // Send query
        await page.locator('#sendButton').click();

        // Wait for response
        await page.waitForSelector('.message.assistant', { timeout: TIMEOUT });

        // Response should exist (even if it's an error message)
        const assistantMessage = page.locator('.message.assistant').last();
        await expect(assistantMessage).toBeVisible();

        // Should not crash the application
        await expect(page.locator('.header-title')).toBeVisible();
    });

    test('should allow clearing chat after Glovo KPIs query', async ({ page }) => {
        // Click on Partner mode
        await page.locator('[data-mode="partner"]').click();
        await page.waitForTimeout(300);

        // Click to show examples
        await page.locator('#modeIndicator').click();
        await page.waitForTimeout(500);

        // Find and click the Glovo KPIs question
        const glovoKpisQuestion = page.locator('.example-query', {
            hasText: /KPIs completos de Glovo.*octubre 2025/i
        });

        await glovoKpisQuestion.click();
        await page.waitForTimeout(200);

        // Send query
        await page.locator('#sendButton').click();

        // Wait for response
        await page.waitForSelector('.message.assistant', { timeout: TIMEOUT });

        // Click clear button
        const clearButton = page.locator('.clear-button');
        await clearButton.click();

        // Confirm clear (if there's a confirmation dialog)
        // Note: Adjust this if your app has a different clear mechanism

        // Verify messages are cleared
        const messages = page.locator('.message');
        const messageCount = await messages.count();

        // Should have no messages or only welcome message
        expect(messageCount).toBeLessThan(3);
    });
});

test.describe('Glovo KPIs Query - Response Validation', () => {

    test('should validate response format is markdown', async ({ page }) => {
        await page.goto(BASE_URL);

        // Navigate to partner mode and send query
        await page.locator('[data-mode="partner"]').click();
        await page.waitForTimeout(300);
        await page.locator('#modeIndicator').click();
        await page.waitForTimeout(500);

        const glovoKpisQuestion = page.locator('.example-query', {
            hasText: /KPIs completos de Glovo.*octubre 2025/i
        });
        await glovoKpisQuestion.click();
        await page.waitForTimeout(200);
        await page.locator('#sendButton').click();

        // Wait for response
        await page.waitForSelector('.message.assistant', { timeout: TIMEOUT });
        await page.waitForTimeout(2000);

        // Check if response contains markdown elements
        const assistantMessage = page.locator('.message.assistant').last();

        // Look for common markdown elements (rendered as HTML)
        const hasHeading = await assistantMessage.locator('h1, h2, h3, h4').count();
        const hasList = await assistantMessage.locator('ul, ol').count();
        const hasTable = await assistantMessage.locator('table').count();

        // At least one markdown element should be present
        const hasMarkdownElements = hasHeading > 0 || hasList > 0 || hasTable > 0;
        expect(hasMarkdownElements).toBeTruthy();
    });

    test('should verify response time is reasonable', async ({ page }) => {
        await page.goto(BASE_URL);

        const startTime = Date.now();

        // Navigate to partner mode and send query
        await page.locator('[data-mode="partner"]').click();
        await page.waitForTimeout(300);
        await page.locator('#modeIndicator').click();
        await page.waitForTimeout(500);

        const glovoKpisQuestion = page.locator('.example-query', {
            hasText: /KPIs completos de Glovo.*octubre 2025/i
        });
        await glovoKpisQuestion.click();
        await page.waitForTimeout(200);
        await page.locator('#sendButton').click();

        // Wait for response
        await page.waitForSelector('.message.assistant', { timeout: TIMEOUT });

        const endTime = Date.now();
        const responseTime = endTime - startTime;

        // Response should be within 60 seconds
        expect(responseTime).toBeLessThan(60000);

        console.log(`Response time: ${responseTime}ms`);
    });
});
