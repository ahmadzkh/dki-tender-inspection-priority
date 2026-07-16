import { expect, test } from '@playwright/test';

function collectConsoleFailures(page: import('@playwright/test').Page) {
  const failures: string[] = [];
  page.on('console', (message) => {
    if (message.type() === 'error') failures.push(message.text());
  });
  page.on('pageerror', (error) => failures.push(error.message));
  return failures;
}

test.describe('Frontend Quality Gate', () => {
  test('dashboard has no console errors and stays under LCP target', async ({ page }) => {
    const failures = collectConsoleFailures(page);
    await page.addInitScript(() => {
      window.__lcp = 0;
      if (PerformanceObserver.supportedEntryTypes?.includes('largest-contentful-paint')) {
        new PerformanceObserver((entryList) => {
          const entries = entryList.getEntries();
          const lastEntry = entries.at(-1);
          if (lastEntry) window.__lcp = lastEntry.startTime;
        }).observe({ type: 'largest-contentful-paint', buffered: true });
      }
    });

    await page.goto('/dashboard');
    await expect(page.getByRole('heading', { name: /Dashboard Analitik/i })).toBeVisible();
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(500);

    const lcp = await page.evaluate(() => window.__lcp ?? 0);
    expect(failures).toEqual([]);
    expect(lcp).toBeLessThan(2500);
  });

  test('dashboard primary controls are keyboard reachable and export CSV', async ({ page }) => {
    const failures = collectConsoleFailures(page);
    await page.goto('/dashboard');
    await page.keyboard.press('Tab');
    await expect(page.locator(':focus')).toBeVisible();

    const downloadPromise = page.waitForEvent('download');
    await page.getByRole('button', { name: /Export CSV/i }).click();
    const download = await downloadPromise;
    expect(download.suggestedFilename()).toMatch(/prioritas_pemeriksaan_.*\.csv/);
    expect(failures).toEqual([]);
  });

  test('dashboard remains usable on mobile viewport', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto('/dashboard');

    await expect(page.getByRole('heading', { name: /Dashboard Analitik/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /Export CSV/i })).toBeVisible();
    await expect(page.locator('table')).toBeVisible();
  });
});

declare global {
  interface Window {
    __lcp?: number;
  }
}
