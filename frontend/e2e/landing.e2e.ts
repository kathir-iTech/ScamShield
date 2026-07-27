import { test, expect } from '@playwright/test';

test.describe('Landing page', () => {
  test('renders hero heading and CTAs', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('h1')).toContainText('scam');
    await expect(page.getByRole('button', { name: /analyse/i }).first()).toBeVisible();
    await expect(page.getByRole('button', { name: /upload/i })).toBeVisible();
  });

  test('navigates to text analysis via CTA', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: /analyse/i }).first().click();
    await expect(page).toHaveURL(/\/analyze\/text/);
  });

  test('navigates to image analysis via CTA', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: /upload/i }).click();
    await expect(page).toHaveURL(/\/analyze\/image/);
  });

  test('navigates via sidebar', async ({ page }) => {
    test.skip(test.info().project.name !== 'Desktop Chrome', 'Sidebar only visible on desktop');
    await page.goto('/');
    await page.getByRole('link', { name: /status/i }).click();
    await expect(page).toHaveURL(/\/system/);
  });
});
