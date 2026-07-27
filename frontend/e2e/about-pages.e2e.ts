import { test, expect } from '@playwright/test';

test.describe('About and legal pages', () => {
  test('about page renders', async ({ page }) => {
    await page.goto('/about');
    await expect(page.getByText(/about scamshield/i)).toBeVisible();
  });

  test('privacy page renders', async ({ page }) => {
    await page.goto('/privacy');
    await expect(page.getByText(/privacy policy/i)).toBeVisible();
  });

  test('terms page renders', async ({ page }) => {
    await page.goto('/terms');
    await expect(page.getByText(/terms of service/i)).toBeVisible();
  });

  test('disclaimer page renders', async ({ page }) => {
    await page.goto('/disclaimer');
    await expect(page.locator('h1')).toContainText(/disclaimer/i);
  });

  test('contact page renders', async ({ page }) => {
    await page.goto('/contact');
    await expect(page.getByText(/contact/i)).toBeVisible();
  });
});
