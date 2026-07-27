import { test, expect } from '@playwright/test';

test.describe('Navigation', () => {
  test('navigates through all main pages', async ({ page }) => {
    test.skip(test.info().project.name !== 'Desktop Chrome', 'Sidebar only visible on desktop');
    await page.goto('/');
    await expect(page).toHaveURL('/');

    await page.getByRole('link', { name: /text/i }).click();
    await expect(page).toHaveURL(/\/analyze\/text/);

    await page.getByRole('link', { name: /image/i }).click();
    await expect(page).toHaveURL(/\/analyze\/image/);

    await page.getByRole('link', { name: /deep dive/i }).click();
    await expect(page).toHaveURL(/\/investigation/);

    await page.getByRole('link', { name: /status/i }).click();
    await expect(page).toHaveURL(/\/system/);

    await page.getByRole('link', { name: /home/i }).click();
    await expect(page).toHaveURL('/');
  });

  test('404 page shows for unknown routes', async ({ page }) => {
    await page.goto('/nonexistent');
    await expect(page.getByText(/page not found/i)).toBeVisible();
  });
});
