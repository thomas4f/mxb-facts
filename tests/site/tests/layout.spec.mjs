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
