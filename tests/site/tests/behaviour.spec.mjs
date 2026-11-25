// What the script does on top of the pages, which read in full without it.
import { test, expect } from '@playwright/test';
import { PAGES } from './pages.mjs';

test('"+N more" shows the rest of a card\'s tags, and "Fewer" folds them again', async ({ page }) => {
  await page.goto('');
  const card = page.locator('.card', { has: page.locator('[data-more]') }).first();
  const more = card.locator('[data-more]');
  const before = await card.locator('.tags .tag:visible').count();
  await more.click();
  await expect(more).toHaveAttribute('aria-expanded', 'true');
  expect(await card.locator('.tags .tag:visible').count()).toBeGreaterThan(before);
  await more.click();
  expect(await card.locator('.tags .tag:visible').count()).toBe(before);
});

test('search and category narrow the tools list and say how many are shown', async ({ page }) => {
  await page.goto('');
  await page.fill('#q', 'holeshot');
  await expect(page.locator('#count')).toHaveText(/^1 of \d+ tools$/);
  await page.fill('#q', '');
  await page.locator('#cat').selectOption('HUD');
  for (const c of await page.locator('.card:visible').all()) await expect(c).toHaveAttribute('data-cat', 'HUD');
});

test('Compare shows only the picked tools, and only the differences when asked', async ({ page }) => {
  await page.goto('compare/?c=holeshot-0.24.2,pitbox-3.0.4');
  await expect(page.locator('#cmp tbody tr:not(.grp)').first().locator('td:visible')).toHaveCount(2);
  const all = await page.locator('#cmp tbody tr:visible').count();
  await page.locator('#diff').check();
  expect(await page.locator('#cmp tbody tr:visible').count()).toBeLessThan(all);
});

test('a link to an answer opens the fold it sits in', async ({ page }) => {
  await page.goto('pitbox/#q-D3');
  await expect(page.locator('#a-data')).toHaveAttribute('open', '');
  await expect(page.locator('#q-D3')).toBeInViewport();
});

test('an address from the old one-page site goes to its page now', async ({ page }) => {
  await page.goto('#holeshot-0.24.0');
  await expect(page).toHaveURL(/\/holeshot\/0\.24\.0\/$/);
  await page.goto('#compare');
  await expect(page).toHaveURL(/\/compare\/$/);
});

test('every page has a link preview: a 1200 by 630 image that exists, and the title and text chat apps show', async ({ page, request }) => {
  for (const [, path] of PAGES) {
    await page.goto(path);
    const img = await page.locator('meta[property="og:image"]').getAttribute('content');
    expect(img).toMatch(/^https:\/\/thomas4f\.github\.io\/mxb-facts\/preview\/[\w.-]+\.png\?v=[0-9a-f]{10}$/);
    // The image is served from this build: the same path under the test server.
    const res = await request.get(new URL(img).pathname.replace('/mxb-facts/', '/'));
    expect(res.ok()).toBeTruthy();
    const png = await res.body();
    expect([png.readUInt32BE(16), png.readUInt32BE(20)]).toEqual([1200, 630]);
    await expect(page.locator('meta[name="twitter:card"]')).toHaveAttribute('content', 'summary_large_image');
    expect(await page.locator('meta[property="og:title"]').getAttribute('content')).toBeTruthy();
    expect(await page.locator('meta[property="og:image:alt"]').getAttribute('content')).toBeTruthy();
  }
});

test('the claims open under T2 from their link', async ({ page }) => {
  await page.goto('pitbox/#says');
  await expect(page.locator('#says')).toHaveAttribute('open', '');
  expect(await page.locator('#a-transparency').getAttribute('open')).not.toBeNull();
});

test('every answer shows its mark\'s word, not only a colour or an icon', async ({ page }) => {
  await page.goto('pitbox/');
  const words = (await page.locator('[id^="q-"] .v .st').allTextContents()).map((w) => w.trim());
  expect(words.length).toBeGreaterThan(40);
  for (const w of words) expect(w).toMatch(/^(Good|Note|Concern|Major|Signs of malware|Off by default|On request|Not checked|Held back|Not allowed|Doesn't apply)\b/);
});

test('the theme button is on screen on a phone', async ({ page }) => {
  await page.goto('');
  const b = await page.locator('[data-theme-toggle]').boundingBox();
  const w = page.viewportSize().width;
  expect(b.x).toBeGreaterThanOrEqual(0);
  expect(b.x + b.width).toBeLessThanOrEqual(w);
});
