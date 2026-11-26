# The MXB Facts data feed (v1)

Static JSON files that any site or app can read: the same data the MXB Facts pages show, made by the same build from the checked cards ([`site/feed.py`](../site/feed.py)). No key, no account, no server of ours to call. Base address:

```
https://thomas4f.github.io/mxb-facts/api/v1/
```

GitHub Pages serves every file with `Access-Control-Allow-Origin: *`, so a browser page, an app or a WordPress site can fetch it directly. Files are cached for 10 minutes. Every file starts with the same fields: `feed_version`, the commit it was built from (`commit`) and that commit's date (`built_at`), the rubric (`rubric`) and the licence (`licence`), so the same commit always gives the same files.

## Files

| File | What it holds | Size (Nov 2026) |
|---|---|---|
| `index.json` | Every tool: id, name, author, games (one or both), category, one-line summary, page, card image, its mods-site posts (one per game that has one), every release with its score and card image (newest first), releases seen with no card yet (`not_analysed`), and the newest release's full result, tags and badges. Also the areas, states and tags the other files refer to, and the AI note. | ~55 KB |
| `cards/<card>.json` | One card in full: result, tags, files with SHA-256, the ten key answers, every answer with its state and cost, the report sections, history and corrections. `<card>` is the card's file name without `.yaml`, as in `holeshot-0.24.2`. | 80–125 KB each |
| `match.json` | Lookup keys to tools: GitHub repository (lower case), mods-site post (`mxb-mods:<id>` or `gpb-mods:<id>`), and the SHA-256 of every file a card lists. | ~70 KB |
| `site.json` | Everything the site's own pages need beyond the cards: the questions with what earns a Good answer, the rules, the prompt, the authors' check, the site's text and links, and `closed_cap`, the highest score a closed-source tool can reach. The site's pages are made from this file and the three above alone, so anything a page shows, the feed has. | |
| `schema/feed.schema.json` | JSON Schema for every file above (`$defs`: `index`, `card`, `match`, `site`). Every field the site uses is required, so the promise below is checked on each build. | |

## What you can rely on

- **The feed decides nothing for you.** Scores, area scores, states, costs and tags are worked out by the build from [`rules/scoring.yaml`](../rules/scoring.yaml), with the same functions the site uses. Show them as given; never recompute them. An answer's `cost` is what it takes off its area, as its line on the site shows it: `0` when another answer of the same behaviour counts it (`counted_with` names it), and the highest cost while it is `open` (not checked, not allowed or held back).
- **Stable ids beside labels.** Tool `id`s are the registry's slugs and never change; if one ever must, the old id stays as an alias. Areas: `pc`, `data`, `game`, `creators`, `transparency` (scored) and `money` (a label, not a score). States: `good`, `note`, `concern`, `major`, `malware`, `off`, `req`, `nc`, `held`, `na`, `dna`, and `notscored` for a result that has no score; their labels and meanings are in `index.json` → `states`. Question ids (`P1`, `D2`, …) and key-answer ids (`K1`–`K10`) keep their meaning within a rubric version (`rubric`).
- **A result always has a kind.** `result.kind` is `score` (a number in `score`, 0–100), `notscored` (`score` is `null`; `why` says why) or `malware` (`score` is `null`). `label` is the text the site shows.
- **What is held back stays held back** ([rule 9](../rules/template.md)): a card with a held item isn't published until the hold ends, so on every published card `result.held_back` is 0 items. The field stays so a reader never has to guess.
- **Every release stays** ([rule 2](../rules/template.md)): `releases` lists every card of a tool with its own score, newest first; `latest` is the newest.
- **Every mark comes with its state.** Answers and key answers carry `state`; each row of a "What it says vs what it does" table carries `verdict_state` beside its `Verdict` words. Draw the state; never map the words yourself.
- **Pages.** `page` is the card's address: `…/mxb-facts/<tool>/` for a tool's newest card, `…/mxb-facts/<tool>/<version>/` for an earlier one. Both stay.
- **What the site shows beside an answer is in the feed too:** `cost_note` (why it costs what it does), `rule_note` (the rule that set its mark), `limits` (the numbers of the Limits lines it touches), `under_review` (open corrections) and `comment` (the link to comment on it).
- **Text in two forms.** `text` and `evidence` are the card's Markdown (https links and code, never HTML). `text_plain` is the same answer without Markdown, for lists and apps.
- **Dates in two forms.** `analysed` is the text the site shows ("24 Nov 2026"); `analysed_iso` (and `date_iso` in `history`) is `YYYY-MM-DD`.
- **Versioning.** Within v1, fields are only added, never removed or renamed, and a field's meaning doesn't change. A change that breaks that is published as `api/v2/` beside v1, and v1 keeps being published for at least 6 months after v2 appears. `feed_version` is `1.<n>`; `n` goes up when fields are added.

## Matching a tool you list

- **A mods site:** `match.json` → `mods_post["mxb-mods:<post id>"]` (or `gpb-mods:`) gives the tool ids on that post, usually one.
- **By repository:** `github["owner/repo"]` (lower case), the same way.
- **An app that knows an installed file:** hash it (SHA-256) and look it up in `sha256`. A hit lists every card that lists that exact file, with its tool, version, whether it is the newest card, the file name, the archive it was found `inside` and the card's `note` about it. One file can be on several cards (an installer two tools share, a file unchanged between releases), and a card's note says when a file was listed but not run (for example, a plugin for the other game). Prefer the entry whose `latest` is true for the tool you expect. No hit means this exact file has no card; it says nothing about the tool.

Then read the tool from `index.json` → `tools` by its `id`.

## Using the data

The feed, the cards and the site's text are under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/): use them for anything, commercial use included, as long as you credit **MXB Facts** with a link to the site or the card. The code that builds them is [MIT](../LICENSE). What a card quotes from a tool (its README, strings, files) stays with that tool's owners ([README](../README.md), "Licence"). Every file of the feed says the same in `licence`.

Beyond what the licence requires, wherever you show a score or a state from the feed, please also show:

1. the release the card covers (`latest.version`) and when it was analysed (`latest.analysed`),
2. a link to the card (`latest.page`), and
3. that the analysis is made by AI and not checked by a person: `ai_note` (in `index.json` and in every card) is the wording the site uses ([rule 8](../rules/template.md)).

Don't show a score as the score of another release, and don't put the states into other words: show the labels from `states`.

## Example

```js
const base = 'https://thomas4f.github.io/mxb-facts/api/v1/';
const [index, match] = await Promise.all(['index.json', 'match.json'].map(f => fetch(base + f).then(r => r.json())));
const [id] = match.mods_post['mxb-mods:189700'] || [];   // "holeshot"
const tool = index.tools.find(t => t.id === id);
console.log(tool.name, tool.latest.version, tool.latest.result.label, tool.latest.page);
```

## Showing a card

Most places need no code at all: every card is also an image, and every tool has addresses that don't change.

| What | Address | Feed field |
|---|---|---|
| Card page, newest | `…/mxb-facts/<tool>/` (an earlier release: `<tool>/<version>/`) | `page` |
| Card image, newest | `…/mxb-facts/badge/<tool>/card.png` | tool's `card_image` |
| Card image, one release | `…/mxb-facts/badge/<tool>/<version>-card.png` | a release's `card_image` |
| Badges, one release | `…/mxb-facts/badge/<tool>/<version>.svg`, with `-flat-square`, `-for-the-badge`, `-score` or `-areas` before `.svg`; `.json` for the shields.io endpoint | `latest.badges` |

- **The card image** is 1200 by 630, the same picture a chat app shows for the card's page. It names the tool, the release, the date of the analysis, the score and the area scores, and carries the AI note, so it meets the asks above on its own; link it to the card's page.
- **`card.png` always shows the tool's newest card**, so a post or a plugins list never needs updating. When the weekly inventory has seen a newer release with no card yet (`not_analysed`), the image names it, so it never reads as that release's result. Use it where you show the tool rather than one release: a mods-site post, a forum thread, a tool list.
- **`<version>-card.png` shows one release**, for a place that knows which release it means, such as an app that matched an installed file by its SHA-256. A release in `not_analysed` gets one saying "Not analysed yet", under its version as published and without its leading v, as its badges do; any other version without a card has none.
- **A badge shows a score but not the release it belongs to**, so it is pinned to one release; move it to the new version on release. A badge linked to `latest.page` needs no code; add the AI note beside it.
- **Chat apps** (Discord and others) show the card image under a pasted page address; nothing to embed.
- Addresses are cached for 10 minutes here, and a site or chat app may keep its own copy of an image for longer.

A mods site that shows a card on each post, with the post id it already has:

```js
const base = 'https://thomas4f.github.io/mxb-facts/api/v1/';
const match = await fetch(base + 'match.json').then(r => r.json());
const [id] = match.mods_post['mxb-mods:' + postId] || [];
if (id) {   // no card yet for this post: show nothing
  const page = `https://thomas4f.github.io/mxb-facts/${id}/`;
  postEl.insertAdjacentHTML('beforeend', `<a href="${page}"><img src="https://thomas4f.github.io/mxb-facts/badge/${id}/card.png" width="600" alt="MXB Facts card"></a>`);
}
```

An app that found a file: look its SHA-256 up in `match.json` → `sha256`, then show that card's `card_image` (from `cards/<card>.json`, or the release in `index.json`) and link its `page`. When the entry's `latest` is false, the tool has a newer card: say so, with the tool's `page`.
