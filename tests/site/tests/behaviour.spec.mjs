// What the script does on top of the pages, which read in full without it.
import { test, expect } from '@playwright/test';

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
  await page.locator('[data-pick-cat="HUD"]').click();
  await expect(page.locator('[data-pick-cat="HUD"]')).toHaveAttribute('aria-pressed', 'true');
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
