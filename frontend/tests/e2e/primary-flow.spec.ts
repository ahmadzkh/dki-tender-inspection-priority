import { test, expect } from '@playwright/test';

test.describe('Primary Flow', () => {
  test('User can navigate from dashboard to package details and filter data', async ({ page }) => {
    // 1. Visit Dashboard
    await page.goto('/dashboard');
    await expect(page).toHaveTitle(/Prioritas Pemeriksaan/i);
    await expect(page.getByRole('heading', { name: /Dashboard Analitik/i })).toBeVisible();

    // Verify summary cards are loaded
    await expect(page.getByText('Total Paket')).toBeVisible();
    await expect(page.getByText('Total Satuan Kerja')).toBeVisible();
    await expect(page.getByRole('heading', { name: /Distribusi Paket per Tahun/i })).toBeVisible();
    await expect(page.getByRole('heading', { name: /Distribusi Skor Prioritas/i })).toBeVisible();

    // 2. Interact with Filters
    const yearSelect = page.locator('select[name="year"]');
    await yearSelect.selectOption('2024');

    // URL should update to include year=2024
    await expect(page).toHaveURL(/year=2024/);

    // Wait for the table to refresh (opacity changes)
    await expect(page.locator('.transition-opacity.opacity-60')).not.toBeVisible();
    await expect(page.locator('.transition-opacity.opacity-100')).toBeVisible();

    // 3. Click first package in the ranking table
    const firstPackageLink = page.locator('table tbody tr').first().locator('a').first();
    const href = await firstPackageLink.getAttribute('href');
    expect(href).toBeTruthy();

    const packageId = href?.split('/').pop();
    expect(packageId).toBeTruthy();

    await firstPackageLink.click();

    // 4. Verify Package Detail Page
    await expect(page).toHaveURL(new RegExp(`/packages/${packageId}`));
    await expect(page.getByRole('heading', { name: /Identitas Paket/i })).toBeVisible();
    await expect(page.getByText(packageId as string)).toBeVisible();

    // Verify inspection-priority explanation section
    await expect(page.getByRole('heading', { name: /Analisis Prioritas Pemeriksaan/i })).toBeVisible();
    await expect(page.getByText('Skor Prioritas')).toBeVisible();
  });
});
