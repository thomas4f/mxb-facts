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

test('a copy button copies its block and shows a tick, with its words for screen readers', async ({ page, context }) => {
  await context.grantPermissions(['clipboard-read', 'clipboard-write']);
  await page.goto('pitbox/#author');
  const b = page.locator('[data-copy="prompt"]');
  await expect(b).toHaveAccessibleName('Copy');
  await b.click();
  await expect(b).toHaveClass(/done/);
  await expect(b).toHaveAccessibleName('Copied');
  await expect(page.locator('#say')).toHaveText('Copied');
  expect(await page.evaluate(() => navigator.clipboard.readText())).toContain('MXB Facts card for Pitbox');
  await expect(b).toHaveAccessibleName('Copy');
  await expect(b).not.toHaveClass(/done/);
});

test('a tool page\'s path opens the tools list filtered to its game and category', async ({ page }) => {
  await page.goto('pitbox/');
  await page.locator('.crumb a', { hasText: 'Mod managers' }).click();
  await expect(page.locator('#game')).toHaveValue('GP Bikes');
  await expect(page.locator('#cat')).toHaveValue('Mod managers');
  for (const c of await page.locator('.card:visible').all()) {
    await expect(c).toHaveAttribute('data-cat', 'Mod managers');
    await expect(c).toHaveAttribute('data-game', /GP Bikes/);
  }
  await page.locator('#cat').selectOption('');
  await expect(page).toHaveURL(/\?game=GP\+Bikes$/);
});

test('a section\'s link copies its address and leaves a fold as it was; following it opens the fold', async ({ page, context }) => {
  await context.grantPermissions(['clipboard-read', 'clipboard-write']);
  await page.goto('pitbox/');
  await page.locator('.anc[href="#limits"]').click();
  await expect(page).toHaveURL(/#limits$/);
  expect(await page.evaluate(() => navigator.clipboard.readText())).toMatch(/\/pitbox\/#limits$/);
  await page.locator('.anc[href="#a-data"]').click();
  expect(await page.locator('#a-data').getAttribute('open')).toBeNull();
  expect(await page.evaluate(() => navigator.clipboard.readText())).toMatch(/\/pitbox\/#a-data$/);
  await page.goto('pitbox/#q-D3');
  await page.locator('#q-D3 a.id').click();
  expect(await page.evaluate(() => navigator.clipboard.readText())).toMatch(/\/pitbox\/#q-D3$/);
});

test('each release in History opens to its changes since the release before it', async ({ page }) => {
  await page.goto('dirt-gear/1.2.0/');
  const own = page.locator('details[id="v-1.2.0"]');
  await own.locator('summary').click();
  await expect(own).toContainText('Changes since 1.1.1');
  const newer = page.locator('details[id="v-1.2.1"]');
  await expect(newer).not.toHaveAttribute('open', '');
  await newer.locator('summary').click();
  await expect(newer).toContainText('Changes since 1.2.0');
  await expect(newer.getByRole('link', { name: 'Open 1.2.1' })).toHaveAttribute('href', '../../dirt-gear/');
  await expect(page.locator('details[id="v-1.1.1"]')).toContainText('The first release of this tool analysed');
});

test('a tool page shows its name in the sticky header once its title scrolls away (wide screens)', async ({ page }, info) => {
  test.skip(info.project.name === 'phone', 'the header only sticks on wide screens');
  await page.goto('dirt-gear/');
  const here = page.locator('[data-here]');
  await expect(here).toBeHidden();
  await page.locator('#history').scrollIntoViewIfNeeded();
  await expect(here).toBeVisible();
  await expect(here).toContainText('Dirt Gear 1.2.1');
  await page.evaluate(() => scrollTo(0, 0));
  await expect(here).toBeHidden();
});

test('every fold on a tool page starts folded, and a link to a limit opens its fold', async ({ page }) => {
  await page.goto('dirt-gear/');
  expect(await page.locator('main details[open]').count()).toBe(0);
  await page.goto('pitbox/#lim-1');
  await expect(page.locator('#limits')).toHaveAttribute('open', '');
});

test('a link\'s icon comes before its fold, so Tab reaches it before what the fold holds', async ({ page }) => {
  await page.goto('pitbox/');
  const anc = page.locator('.fw > :first-child').first();
  await expect(anc).toHaveClass(/anc/);
});

test('the home page says how scores read beside the count, and points to the marks on How it works', async ({ page }) => {
  await page.goto('');
  await expect(page.locator('.cntr')).toContainText('Scores are out of 100; higher is better.');
  await expect(page.locator('.legend')).toHaveCount(0);
  await page.getByRole('link', { name: 'Reading a card' }).click();
  await expect(page).toHaveURL(/how\/#marks$/);
});

test('the footer has its two groups of links and the licence line', async ({ page }) => {
  await page.goto('');
  const f = page.locator('footer');
  for (const n of ['Comment on a card', 'Request a tool', 'Suggest a question', 'Source on GitHub', 'Data feed']) await expect(f.getByRole('link', { name: n })).toBeVisible();
  await expect(f).toContainText('Cards and data CC BY 4.0');
});

for (const [w, rows] of [[360, 1], [359, 2]]) {
  test(`the four nav links sit in ${rows} row${rows > 1 ? 's' : ''} on a ${w}px screen`, async ({ page }) => {
    await page.setViewportSize({ width: w, height: 700 });
    await page.goto('');
    const tops = new Set(await page.locator('.nav a').evaluateAll((as) => as.map((a) => Math.round(a.getBoundingClientRect().top))));
    expect(tops.size).toBe(rows);
  });
}
