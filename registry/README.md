# Registry

`tools.json` lists every tool the project covers or has queued, by its tool slug (the start of its card file names):

| Field | What it holds |
|---|---|
| `name` | The tool's name, as on its cards |
| `author` | The name the author publishes as (GitHub name, the name on a licence or a page), or `null` when none is found. Nothing more (CLAUDE.md, rule 10) |
| `github` | `owner/repo`, or `null` |
| `homepage` | A URL, or `null` |
| `cards` | Its card files in `cards/`, oldest first; empty while the tool waits in `docs/QUEUE.md` |
| `downloads` | Optional: other places the author publishes its files (a Mega, MediaFire or Google Drive link, a forum topic, a homepage download), for the release check. GitHub and the mods-site page are looked at anyway |
| `discussion` | Optional: the number of the tool's thread in the repository's Discussions, "Cards" category, once one is started. Its tool page links it; without it, the page offers to start one, titled with the tool's name |
| `game_version` | Optional: the demo its plugins run in when it needs an older one than the newest, per game, as `{"mxbikes": {"version": "beta21e", "why": "<what its readme, page or code shows>"}}`, from `lab/real-game/games.json` ([its README](../lab/real-game/README.md), "Which demo") |
| `mxb-mods` | `post` (the mxb-mods.com post ID) and `tied_by` (text on that page that ties it to the tool: its GitHub link, the file name or hash of the file checked), or, when nothing on the page ties it, `confirmed` saying who confirmed it and what the page is; or `post: null` with a `note` saying why not. A page that matches by name only is not tied. `tied_by` is looked for in the post's body, its attached files and its public page (download buttons are only on the page) |

A GP Bikes tool has a `gpb-mods` entry instead of `mxb-mods`, the same way, for its gpb-mods.com page; its cards say `Game: GP Bikes`. A tool for both games (`Game: MX Bikes; GP Bikes`) has both entries; one without a page there has `post: null` and a note.

`mxb-mods.json` and `gpb-mods.json` are snapshots of each tied page, written by `tools/mxbmods_fetch.py` through the site's public WordPress API: title, link, excerpt, dates, categories, and whether the page still holds its `tied_by` text. The site shows only the page link, as the tool's mxb-mods.com row. The excerpt is the page's own statement, not a fact, so it is never shown on the site: it is input for the questions that check what a tool says against what its code does, which quote the page and give the finding from the analysis. The "Update inventory" workflow runs the script every Monday and commits any change to `main`; it can also be run from the Actions tab. The file is only rewritten when a page changed, and the workflow fails (and commits no snapshot) when a page no longer holds its `tied_by` text.

`releases.json` holds each tool's newest release in every place it publishes, written by `tools/releases_fetch.py` in the same workflow: its GitHub releases, its tied mods-site page (an attached file, or the Mega, MediaFire or Google Drive link its download button points at), and its `downloads` (for a web page, the files it links to on its own site, else the first Mega, MediaFire or Google Drive file link on it: a file elsewhere, such as a runtime the page asks players to install, is not the tool's release). Each entry has the version or file name, date, size and SHA-256 (from GitHub, or from downloading the file once when it changed; Mega files are encrypted, so only their size is kept), and the date it was first seen. The run's summary lists every tool whose newest release has hashes that none of its newest card's files match. For each, `tools/recheck_issues.py` opens a "Re-check: <tool> <version>" issue, labelled like a request (`analyse`, `tool:<slug>`), unless one with that title is already open. A mods-site page tied only by the maintainer's confirmation is skipped when the tool lists its own `downloads` (a page someone else uploaded). The site doesn't use this file; it tells us what to analyse next.

`site/build.py` refuses a registry that doesn't match `CARDS`, a GitHub repo that differs from the card, and a tied post missing from the snapshot or no longer holding its `tied_by` text.
