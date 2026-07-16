import { test, expect } from '@playwright/test';

test.describe('Transparency & Informational Pages', () => {
  test('User can navigate and read Dataset page', async ({ page }) => {
    await page.goto('/dataset');
    await expect(page).toHaveTitle(/Transparansi Dataset/i);
    await expect(page.getByRole('heading', { name: /Transparansi Dataset/i })).toBeVisible();
    await expect(page.getByRole('heading', { name: /Populasi per Tahap Pemrosesan/i })).toBeVisible();
    await expect(page.getByRole('heading', { name: /Enrichment INAPROC/i })).toBeVisible();
    await expect(page.getByRole('heading', { name: /Batas Data/i })).toBeVisible();
    await expect(page.getByText(/baris tanpa penyedia/i)).toBeVisible();
  });

  test('User can navigate and read Methodology page', async ({ page }) => {
    await page.goto('/methodology');
    await expect(page).toHaveTitle(/Metodologi/i);
    await expect(page.getByRole('heading', { name: /Metodologi/i })).toBeVisible();
    await expect(page.getByText('CRISP-DM (Untuk Pipeline Data)')).toBeVisible();
    await expect(page.getByRole('heading', { name: /Mengapa Isolation Forest\?/i })).toBeVisible();
    // Verify strict disclaimer
    await expect(page.getByText(/TIDAK mendeteksi fraud/i)).toBeVisible();
  });
});
