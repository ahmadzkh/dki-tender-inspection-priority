import { test, expect } from '@playwright/test';

test.describe('Transparency & Informational Pages', () => {
  test('Landing page explains scope and links to the dashboard', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByRole('heading', { name: /Sistem Prioritas Pemeriksaan/i })).toBeVisible();
    await expect(page.getByText(/bukan vonis hukum/i)).toBeVisible();
    await page.getByRole('link', { name: /Buka Dashboard/i }).click();
    await expect(page).toHaveURL(/\/dashboard/);
  });

  test('User can navigate and read Dataset page', async ({ page }) => {
    await page.goto('/dataset');
    await expect(page).toHaveTitle(/Transparansi Dataset/i);
    await expect(page.getByRole('heading', { name: /Transparansi Dataset/i })).toBeVisible();
    await expect(page.getByRole('heading', { name: /Populasi per Tahap Pemrosesan/i })).toBeVisible();
    await expect(page.getByRole('heading', { name: /Enrichment INAPROC/i })).toBeVisible();
    await expect(page.getByRole('heading', { name: /Batas Data/i })).toBeVisible();
    await expect(page.getByText(/baris tanpa penyedia/i)).toBeVisible();
    for (const count of ['1.284', '1.279', '1.277', '1.276']) {
      await expect(page.getByText(count, { exact: true })).toBeVisible();
    }
    await expect(page.getByText('e1787c052ec07fea')).toBeVisible();
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

  test('Evaluation page exposes frozen model evidence and limitations', async ({ page }) => {
    await page.goto('/evaluation');
    await expect(page.getByRole('heading', { name: /Evaluasi Model/i })).toBeVisible();
    await expect(page.getByText('414f1691')).toBeVisible();
    await expect(page.getByRole('heading', { name: /Uji Stabilitas Seed/i })).toBeVisible();
    await expect(page.getByRole('heading', { level: 2, name: 'Perbandingan dengan Baseline', exact: true })).toBeVisible();
    await expect(page.getByRole('heading', { name: /Batasan Evaluasi/i })).toBeVisible();
  });
});
