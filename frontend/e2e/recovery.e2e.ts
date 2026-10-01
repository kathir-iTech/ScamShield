import { test, expect } from '@playwright/test';

test.describe('Recovery', () => {
  test('recovery page shows heading and core controls', async ({ page }) => {
    await page.goto('/recovery');

    await expect(page.getByRole('heading', { level: 1, name: /recovery pack/i })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Copy pack', exact: true })).toBeVisible();
    await expect(page.getByRole('link', { name: /call 1930/i })).toBeVisible();
    await expect(page.getByLabel('Amount involved')).toBeVisible();
  });
});
