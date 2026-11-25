// The top of every kind of page, on a phone and a desktop, in the dark theme: a change in how the site looks shows up here.
import { test, expect } from '@playwright/test';
import { PAGES } from './pages.mjs';

for (const [name, url] of PAGES) {
  test(`${name} looks as before`, async ({ page }) => {
    await page.emulateMedia({ colorScheme: 'dark', reducedMotion: 'reduce' });
    await page.goto(url);
    await page.evaluate(() => document.fonts.ready);
    await expect(page).toHaveScreenshot(`${name}.png`);
  });
}
