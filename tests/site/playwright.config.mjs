// Playwright for the built site: _site/ served as it is on GitHub Pages, on a phone and on a desktop.
// Screenshots compare against tests/<spec>-snapshots/ ("npm run screenshots:update" after a change that is meant to look different).
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: 'tests',
  fullyParallel: true,
  reporter: [['list']],
  use: { baseURL: 'http://127.0.0.1:8790/', trace: 'off' },
  expect: { toHaveScreenshot: { maxDiffPixelRatio: 0.01, animations: 'disabled' } },
  webServer: { command: 'node serve.mjs 8790', url: 'http://127.0.0.1:8790/', reuseExistingServer: false },
  projects: [
    { name: 'phone', use: { ...devices['iPhone 13'], browserName: 'chromium' } },
    { name: 'desktop', use: { viewport: { width: 1280, height: 900 }, browserName: 'chromium' } },
  ],
});
