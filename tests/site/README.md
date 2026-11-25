# Checks on the built site

These check `_site/` as players get it, after `python3 -I site/build.py`. CI runs them on every pull request (the `site` job in `.github/workflows/check.yml`); the versions of every checker are pinned in `package-lock.json`.

| Check | Command | What it catches |
|---|---|---|
| ESLint, stylelint | `npm run lint` | Mistakes in `site/static/site.js`, and in `site/static/site.css` (a selector or property written twice, unknown ones, a padding, margin or gap that isn't a spacing token; `.stylelintrc.json`) |
| W3C Nu validator | `npm run validate` | Invalid HTML on any page (needs Java) |
| axe, WCAG 2.2 AA | `npx playwright test tests/a11y.spec.mjs` | Accessibility on every page, in both themes, on a phone and a desktop; 44 px touch targets and no sideways scrolling on the phone |
| Behaviour | `npx playwright test tests/behaviour.spec.mjs` | Search, categories, "+N more", Compare and "Show only differences", folds opening on a link, old addresses |
| Layout | `npx playwright test tests/layout.spec.mjs` | Two borders meeting in a double line, or a framed box inside another, on every page with every fold open (`tests/borders.js`) |
| Screenshots | `npx playwright test tests/visual.spec.mjs` | Any change to how a page looks, compared with `tests/visual.spec.mjs-snapshots/` |
| Lighthouse | `npm run lighthouse` | Accessibility, best practices and SEO at 100, performance at 90 or more, layout shift under 0.02 |

Run them from this folder:

```
npm ci
npx playwright install chromium    # not needed in cloud sessions, which have it
npm run lint && npm run validate && npx playwright test && npm run lighthouse
# the screenshots compare only in the pinned image, as in CI:
docker run --rm --ipc=host -v "$PWD/../..:/w" -w /w/tests/site mcr.microsoft.com/playwright:v1.63.0-noble npx playwright test
```

`npm test` runs the three Playwright files. The pages it opens are listed once, in `tests/pages.mjs`.

## When a page is meant to look different

Run `npm run screenshots:update`. It takes the screenshots in the Playwright image at the version `package.json` pins (`mcr.microsoft.com/playwright:v1.63.0-noble`, so Docker is needed), the same image CI compares them in: a screenshot taken with another machine's fonts and font settings differs by a few percent of its pixels and fails. Look at every changed image in the diff, and commit them in the same pull request as the change. A screenshot that changed without a reason is the bug this check is for.
