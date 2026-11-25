// Layout consistency the eye catches and axe doesn't: no two borders meeting in a double line, and no framed box inside
// another framed box (steps, tables and rows inside a box drop their own frame). Every fold is opened first, so what a
// reader can reach is checked, not only what shows on load.
import { test, expect } from '@playwright/test';
import { readFileSync } from 'node:fs';
import { PAGES } from './pages.mjs';

const check = readFileSync(new URL('./borders.js', import.meta.url), 'utf8');

for (const [name, path] of [...PAGES, ['tool-releases', 'dirt-gear/']]) {
  test(`${name}: no double borders and no box in a box`, async ({ page }) => {
    await page.goto(path);
    await page.evaluate(() => document.querySelectorAll('details').forEach((d) => { d.open = true; }));
    expect(await page.evaluate(check)).toEqual([]);
  });
}

// A word is never split across lines just to make room: a narrow table column once showed "Dat e" and "No v" (the page's
// break-anywhere rule, meant for hashes, reached table cells). Every one-word table heading and date sits on one line.
for (const [name, path] of PAGES) {
  test(`${name}: table headings and dates keep their words whole`, async ({ page }) => {
    await page.goto(path);
    await page.evaluate(() => document.querySelectorAll('details').forEach((d) => { d.open = true; }));
    const split = await page.evaluate(() => [...document.querySelectorAll('th, td')]
      .filter((c) => c.getClientRects().length && /^(\w+|\d{1,2} \w{3} \d{4})$/.test(c.textContent.trim()))
      .flatMap((c) => {
        const words = c.textContent.trim().split(' ');
        return words.filter((w) => {
          const r = document.createRange(); const t = [...c.childNodes].find((n) => n.nodeType === 3 && n.textContent.includes(w));
          if (!t) return false;
          const i = t.textContent.indexOf(w); r.setStart(t, i); r.setEnd(t, i + w.length);
          return new Set([...r.getClientRects()].map((x) => Math.round(x.top))).size > 1;
        }).map((w) => `${c.textContent.trim()} (${w})`);
      }));
    expect(split).toEqual([]);
  });
}
