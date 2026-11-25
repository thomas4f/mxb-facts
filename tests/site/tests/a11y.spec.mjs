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
      const r = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa']).analyze();
      expect(r.violations.map(v => `${v.id}: ${v.nodes.slice(0, 3).map(n => n.target.join(' ')).join(' | ')}`)).toEqual([]);
    });
  }
}

for (const [name, url] of PAGES) {
  test(`${name}: touch targets are 44 px tall and nothing scrolls sideways`, async ({ page }, info) => {
    test.skip(info.project.name !== 'phone', 'phone only');
    await page.goto(url);
    const small = await page.evaluate(() => [...document.querySelectorAll('button, select, input, summary, .chip, .btn, .nav a, .back, .cmt, label')]
      .filter(e => { const r = e.getBoundingClientRect(); const hit = Math.max(r.height, parseFloat(getComputedStyle(e, '::after').height) || 0);
        return r.height > 0 && hit < 44 && !(e.type === 'checkbox' && e.closest('label')); })
      .map(e => `${e.tagName.toLowerCase()}.${e.className} ${Math.round(e.getBoundingClientRect().height)}px`));
    expect(small).toEqual([]);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  });
}
