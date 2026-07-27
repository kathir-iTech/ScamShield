import { test, expect } from '@playwright/test';

test.describe('Image analysis flow', () => {
  test('shows upload area', async ({ page }) => {
    await page.goto('/analyze/image');
    await expect(page.getByText(/png|jpeg|webp/i)).toBeVisible();
    await expect(page.getByText(/click or drag/i)).toBeVisible();
  });

  test('shows format restrictions', async ({ page }) => {
    await page.goto('/analyze/image');
    await expect(page.getByText(/10 MB/i)).toBeVisible();
  });

  test('submit is disabled without file', async ({ page }) => {
    await page.goto('/analyze/image');
    const button = page.getByRole('button', { name: /analyse/i });
    await expect(button).toBeDisabled();
  });
});
