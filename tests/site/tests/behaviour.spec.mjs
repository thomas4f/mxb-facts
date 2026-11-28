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
  await expect(page.locator('.ghead:visible')).toHaveCount(1);
  await expect(page.locator('.ghead:visible')).toHaveAttribute('data-cat', 'HUD');
  await expect(page.locator('.ghead:visible a.anc')).toHaveAttribute('href', '#hud');
});

test('Clear is off until the list changes, then puts the search, filters, sort and address back', async ({ page }) => {
  await page.goto('?game=MX+Bikes');
  const clear = page.locator('#clear');
  await expect(clear).toBeEnabled();
  await page.fill('#q', 'holeshot');
  await page.locator('#sort').selectOption('score');
  await page.locator('#cat').selectOption('HUD');
  await clear.click();
  await expect(page.locator('#q')).toHaveValue('');
  await expect(page.locator('#sort')).toHaveValue('date');
  await expect(page.locator('#game')).toHaveValue('');
  await expect(page.locator('#cat')).toHaveValue('');
  await expect(page).not.toHaveURL(/\?/);
  await expect(page.locator('#count')).toHaveText(/^(\d+) of \1 tools$/);
  await expect(clear).toBeDisabled();
  await expect(page.locator('#q')).toBeFocused();
});

test('the tools list opens newest analysis first, its categories too, with or without the script', async ({ browser }) => {
  for (const javaScriptEnabled of [true, false]) {
    const page = await (await browser.newContext({ javaScriptEnabled })).newPage();
    await page.goto('');
    if (javaScriptEnabled) await expect(page.locator('#sort')).toHaveValue('date');
    const late = await page.locator('#tools-grid > *').evaluateAll(els => {
      const newest = h => els.filter(e => !e.classList.contains('ghead') && e.dataset.cat === h.dataset.cat).map(e => e.dataset.date).sort().pop();
      let cat = null, prev = null, last = null;
      for (const e of els) {
        if (e.classList.contains('ghead')) {
          if (last !== null && newest(e) > last) return 'category ' + e.dataset.cat + ' after an older one';
          cat = e.dataset.cat; last = newest(e); prev = null; continue;
        }
        if (prev && (prev.dataset.date < e.dataset.date || prev.dataset.date === e.dataset.date && prev.dataset.name > e.dataset.name)) return e.dataset.name + ' in ' + cat;
        prev = e;
      }
      return null;
    });
    expect(late).toBeNull();
    await page.context().close();
  }
});

test('the tools list stays grouped by category whatever the sort, each tool under its own category', async ({ page }) => {
  await page.goto('');
  await page.locator('#sort').selectOption('score');
  const cats = await page.locator('#tools-grid > :visible').evaluateAll(els => {
    let cur = null; const seen = [];
    for (const e of els) {
      if (e.classList.contains('ghead')) { cur = e.dataset.cat; seen.push(cur); } else if (e.dataset.cat !== cur) return ['misplaced ' + e.dataset.name];
    }
    return seen;
  });
  expect(new Set(cats).size).toBe(cats.length);
  expect(cats.length).toBeGreaterThan(1);
});

test('Compare shows each answer as its mark, with the answer on hover and for screen readers', async ({ page }) => {
  await page.goto('compare/?c=holeshot-0.24.2,pitbox-3.0.4');
  const cell = page.locator('#cmp td:visible', { has: page.locator('.st') }).nth(2);
  await expect(cell.locator('.vd')).toHaveCount(0);
  const word = (await cell.locator('.vh').textContent()).trim();
  expect(await cell.locator('.st').getAttribute('title')).toMatch(new RegExp('^' + word.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '[:.]?'));
});

test('Compare shows only the picked tools, and only the differences when asked', async ({ page }) => {
  await page.goto('compare/?c=holeshot-0.24.2,pitbox-3.0.4');
  await expect(page.locator('#cmp tbody tr:not(.grp)').first().locator('td:visible')).toHaveCount(2);
  const all = await page.locator('#cmp tbody tr:visible').count();
  await page.locator('#diff').check();
  expect(await page.locator('#cmp tbody tr:visible').count()).toBeLessThan(all);
});

test("Compare keeps the hint's line while picking, clears every pick, and keeps the tools' names in view", async ({ page }) => {
  await page.goto('compare/?c=holeshot-0.24.2,pitbox-3.0.4');
  const hint = page.locator('[data-cmp-hint]');
  await expect(hint).toBeVisible();
  const head = page.locator('#cmp thead th[data-c="holeshot-0.24.2"]');
  if (await head.isVisible()) {  // the phone layout has no head row: each cell names its tool
    await page.locator('#cmp tbody tr').nth(30).scrollIntoViewIfNeeded();
    const box = await head.boundingBox();
    expect(box.y).toBeGreaterThanOrEqual(0); expect(box.y).toBeLessThan(200);
  }
  await page.getByRole('button', { name: 'Clear' }).click();
  await expect(page.locator('#picker input[data-cmp]:checked')).toHaveCount(0);
  await expect(page.locator('#cmp')).toBeHidden();
  await expect(hint).toBeVisible();
  await expect(page.getByRole('button', { name: 'Clear' })).toBeDisabled();
  await expect(page).toHaveURL(/\/compare\/$/);
});

test("Compare's picker groups tools by category and opens a tool's earlier releases on request", async ({ page }) => {
  await page.goto('compare/');
  await expect(page.locator('#picker .pgrp .cat').first()).toBeVisible();
  const older = page.locator('#picker input[data-cmp="holeshot-0.24.0"]');
  await expect(older).toBeHidden();
  await page.getByRole('button', { name: /earlier releases of HoleShot HUD/ }).click();
  await expect(older).toBeVisible();
  // A shared link that picks an earlier release opens that tool's earlier releases by itself.
  await page.goto('compare/?c=holeshot-0.24.0,pitbox-3.0.4');
  await expect(page.locator('#picker input[data-cmp="holeshot-0.24.0"]')).toBeChecked();
  await page.locator('#picker').evaluate(d => { d.open = true; });
  await expect(page.locator('#picker input[data-cmp="holeshot-0.24.0"]')).toBeVisible();
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
    // The site's own image, or a card's, which is also that card's image to embed (beside its badges).
    expect(img).toMatch(/^https:\/\/thomas4f\.github\.io\/mxb-facts\/(preview\/site|badge\/[a-z0-9-]+\/[\w.-]+-card)\.png\?v=[0-9a-f]{10}$/);
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
  await expect(page.locator('.cntr')).toContainText('A score sums up what was found and what could be checked');
  await expect(page.locator('.legend')).toHaveCount(0);
  await page.getByRole('link', { name: 'Reading a card' }).click();
  await expect(page).toHaveURL(/how\/#marks$/);
});

test('the footer has its two groups of links and the licence line', async ({ page }) => {
  await page.goto('');
  const f = page.locator('footer');
  for (const n of ['Suggest a correction', 'Discuss a tool', 'Discuss the site', 'Request a tool', 'Suggest a question', 'Source on GitHub', 'Data feed']) await expect(f.getByRole('link', { name: n })).toBeVisible();
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

// The 404 page as GitHub Pages serves it: under /mxb-facts/, for any address the site doesn't have, with a 404 status.
async function pages(page) {
  const fs = await import('node:fs'), path = await import('node:path');
  const site = path.resolve(import.meta.dirname, '../../../_site');
  await page.route('http://pages.test/mxb-facts/**', (r) => {
    let p = decodeURIComponent(new URL(r.request().url()).pathname.slice('/mxb-facts/'.length));
    if (p === '' || p.endsWith('/')) p += 'index.html';
    const f = path.join(site, p);
    if (fs.existsSync(f) && fs.statSync(f).isFile()) return r.fulfill({ path: f });
    return r.fulfill({ status: 404, path: path.join(site, '404.html'), contentType: 'text/html' });
  });
}

test('a release with no card gets a page that names it and links the newest card', async ({ page }) => {
  await pages(page);
  const res = await page.goto('http://pages.test/mxb-facts/dirt-gear/9.9/');
  expect(res.status()).toBe(404);
  await expect(page.locator('h1')).toHaveText('Dirt Gear 9.9 has no card yet');
  await page.getByRole('link', { name: 'Open Dirt Gear 1.2.1' }).click();
  await expect(page).toHaveURL('http://pages.test/mxb-facts/dirt-gear/');
});

test('an unknown tool gets a page that offers the search and a request', async ({ page }) => {
  await pages(page);
  await page.goto('http://pages.test/mxb-facts/some-new-tool/');
  await expect(page.locator('h1')).toHaveText('No card for “some-new-tool” yet');
  await expect(page.getByRole('link', { name: 'Request a tool or a re-check' })).toBeVisible();
  await page.getByRole('link', { name: /^Search the tools/ }).click();
  await expect(page.locator('#q')).toHaveValue('some new tool');
});

test('the 404 page names only what it is sure of', async ({ page }) => {
  await pages(page);
  await page.goto('http://pages.test/mxb-facts/pitbox/v3.0.4/');
  await expect(page.locator('h1')).toHaveText('Pitbox 3.0.4 has a card');
  await expect(page.getByRole('link', { name: 'Open Pitbox 3.0.4' })).toHaveAttribute('href', '/mxb-facts/pitbox/');
  await page.goto('http://pages.test/mxb-facts/badge/pitbox/1.0-beta.svg');
  await expect(page.locator('h1')).toHaveText('Pitbox 1.0-beta has no card yet');
  for (const u of ['how/nope/', 'api/v1/cards/nope.json', 'dirt-gear/index.htm']) {
    await page.goto('http://pages.test/mxb-facts/' + u);
    await expect(page.locator('h1')).not.toContainText('has no card yet');
    await expect(page.locator('h1')).not.toContainText('No card for');
  }
});

test('on a phone a fold\'s note goes under its title, so the title keeps its width', async ({ page }) => {
  await page.setViewportSize({ width: 360, height: 700 });
  await page.goto('how/');
  for (const w of await page.locator('details.fold > summary .ft').evaluateAll((ts) => ts.map((t) => t.getBoundingClientRect().width))) expect(w).toBeGreaterThan(200);
});
