// ESLint for the site's one script (site/static/site.js, read on stdin by "npm run lint"): the recommended rules, in a browser.
import js from '@eslint/js';
import globals from 'globals';

export default [
  js.configs.recommended,
  { languageOptions: { ecmaVersion: 2019, sourceType: 'script', globals: globals.browser } },
];
