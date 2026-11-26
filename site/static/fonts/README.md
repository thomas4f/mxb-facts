# Fonts

Served with the site so the pages ask no other site for anything. Latin subsets in WOFF2, from the Fontsource npm packages
(`@fontsource/barlow@5.1.1`, `@fontsource/saira@5.1.0`, `@fontsource/jetbrains-mono@5.1.2`), each under the SIL Open Font
License 1.1: Barlow in `OFL-Barlow.txt`, Saira in `OFL-Saira.txt`, JetBrains Mono in `OFL-JetBrainsMono.txt`.

Barlow is the text, Saira Bold the headings and scores, JetBrains Mono the code. Saira ExtraBold Italic is the wordmark's face:
no page loads it, because `tools/wordmark.py` draws the wordmark from it as shapes (`site/brand.json`) and the link-preview
images (`site/preview.py`) set it with Pillow.
