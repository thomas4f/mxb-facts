// WCAG 2.2 AA with axe on every kind of page, in both themes, with every fold open; plus what axe doesn't measure:
// touch targets of at least 44 px (our own bar, above WCAG's 24) and no sideways scroll on a phone.
import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { PAGES } from './pages.mjs';

for (const scheme of ['dark', 'light']) {
  for (const [name, url] of PAGES) {
    test(`${name} (${scheme}) meets WCAG 2.2 AA`, async ({ page }) => {
      await page.emulateMedia({ colorScheme: scheme });
      await page.goto(url);
      await page.evaluate(() => document.querySelectorAll('details').forEach(d => { d.open = true; }));
      // Two frames, so site.js has seen the opened folds' sizes (a table too wide to fit becomes a focusable region).
      await page.evaluate(() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r))));
      const r = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa']).analyze();
      expect(r.violations.map(v => `${v.id}: ${v.nodes.slice(0, 3).map(n => n.target.join(' ')).join(' | ')}`)).toEqual([]);
    });
  }
}

for (const [name, url] of PAGES) {
  test(`${name}: touch targets are 44 px tall and nothing scrolls sideways`, async ({ page }, info) => {
    test.skip(info.project.name !== 'phone', 'phone only');
    await page.goto(url);
    const small = await page.evaluate(() => [...document.querySelectorAll('button, select, input, summary, .chip, .btn, .nav a, .crumb a, .cmt, label')]
      .filter(e => { const r = e.getBoundingClientRect(); const hit = Math.max(r.height, parseFloat(getComputedStyle(e, '::after').height) || 0);
        return r.height > 0 && hit < 44 && !(e.type === 'checkbox' && e.closest('label')); })
      .map(e => `${e.tagName.toLowerCase()}.${e.className} ${Math.round(e.getBoundingClientRect().height)}px`));
    expect(small).toEqual([]);
    // Against the device's width: a phone browser widens innerWidth to fit content that overflows, so innerWidth can't catch it.
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(page.viewportSize().width);
    // And with every fold open, on a small phone with its text at 125%, as people set it.
    await page.setViewportSize({ width: 360, height: 800 });
    await page.evaluate(() => { document.documentElement.style.fontSize = '125%'; document.body.style.zoom = '1.25'; document.querySelectorAll('details').forEach(d => { d.open = true; }); });
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(360);
  });
}

// Every tool page, not only the sample: one long token (a SHA-256, a path) in any answer is enough to widen a phone's page.
test('no tool page scrolls sideways on a small phone with every fold open', async ({ page, request }, info) => {
  test.skip(info.project.name !== 'phone', 'phone only');
  const ix = await (await request.get('api/v1/index.json')).json();
  await page.setViewportSize({ width: 360, height: 800 });
  const wide = [];
  for (const t of ix.tools) for (const r of t.releases) {
    await page.goto(new URL(r.page).pathname.replace(/^\/mxb-facts\//, ''));
    await page.evaluate(() => document.querySelectorAll('details').forEach(d => { d.open = true; }));
    const w = await page.evaluate(() => document.documentElement.scrollWidth);
    if (w > 360) wide.push(`${r.card}: ${w}px`);
  }
  expect(wide).toEqual([]);
});
