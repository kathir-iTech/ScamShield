import { test, expect } from '@playwright/test';

test.describe('Analysis result empty state', () => {
  test('shows empty state when no analysis', async ({ page }) => {
    await page.goto('/analysis/result');
    await expect(page.getByText(/nothing to review/i)).toBeVisible();
  });

  test('navigates to text analysis from empty state', async ({ page }) => {
    await page.goto('/analysis/result');
    await page.getByRole('button', { name: /analyse/i }).first().click();
    await expect(page).toHaveURL(/\/analyze\/text/);
  });
});
