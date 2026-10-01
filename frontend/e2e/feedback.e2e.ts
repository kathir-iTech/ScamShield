import { test, expect } from '@playwright/test';

test.describe('Feedback', () => {
  test('feedback form renders and submitting a verdict shows success', async ({ page }) => {
    await page.route(
      (url) => url.pathname.endsWith('/feedback'),
      async (route) => {
        const type = route.request().resourceType();
        if (type !== 'xhr' && type !== 'fetch') {
          await route.continue();
          return;
        }
        await route.fulfill({
          status: 202,
          contentType: 'application/json',
          body: JSON.stringify({ detail: 'Feedback accepted', id: 'e2e-feedback' }),
        });
      },
    );

    await page.goto('/feedback');

    await expect(page.getByRole('heading', { level: 1, name: /^feedback$/i })).toBeVisible();
    await expect(page.getByRole('radio', { name: 'Correct', exact: true })).toBeVisible();
    await expect(page.getByRole('button', { name: /send feedback/i })).toBeVisible();

    await page.getByRole('radio', { name: 'Correct', exact: true }).check({ force: true });
    await page.getByRole('button', { name: /send feedback/i }).click();

    await expect(page.getByText(/thank you/i)).toBeVisible();
    await expect(page.getByText(/feedback was recorded/i)).toBeVisible();
  });
});
