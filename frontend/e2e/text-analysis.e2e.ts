import { test, expect } from '@playwright/test';

test.describe('Text analysis flow', () => {
  test('shows text input and example chips', async ({ page }) => {
    await page.goto('/analyze/text');
    await expect(page.getByRole('textbox')).toBeVisible();
    await expect(page.getByText('Bank SMS')).toBeVisible();
    await expect(page.getByText('OTP')).toBeVisible();
    await expect(page.getByText('UPI')).toBeVisible();
  });

  test('example chip fills input', async ({ page }) => {
    await page.goto('/analyze/text');
    await page.getByText('OTP').click();
    await expect(page.getByRole('textbox')).not.toHaveValue('');
  });

  test('shows character counter', async ({ page }) => {
    await page.goto('/analyze/text');
    const textbox = page.getByRole('textbox');
    await textbox.fill('Hello');
    await expect(page.getByText('5/5000')).toBeVisible();
  });

  test('submit is disabled without text', async ({ page }) => {
    await page.goto('/analyze/text');
    const button = page.getByRole('button', { name: /analyse/i });
    await expect(button).toBeDisabled();
  });
});
