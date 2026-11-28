# MXB Facts

Check before you install. Fact-only cards about MX Bikes and GP Bikes tools, for players: what each plugin, app or mod does to your PC, your data, your game and creators' content, and how open it is. Each card covers one release and links every line to the exact code, the release file, or a test anyone can repeat.

**Read the cards:** https://thomas4f.github.io/mxb-facts/

## Conflict of interest

This project is run by Thomas (GitHub [thomas4f](https://github.com/thomas4f)), who also makes **MXBMRP3**, a HUD plugin covered here alongside tools that do similar things. To keep that from steering the cards:

- Every tool, MXBMRP3 included, answers the same list of questions ([`rules/questions.md`](rules/questions.md)) and is scored by the same fixed costs ([`rules/scores.md`](rules/scores.md)). The build refuses a card that skips a question or an answer whose mark doesn't match the mark table.
- Every line carries its evidence, so you don't have to trust us.
- Donations ([Ko-fi](https://ko-fi.com/thomas4f)) change nothing: not a card, a score or a place in the queue, whoever gives, a tool's author included.
- The analysis is done by an AI assistant (Claude) working under [`CLAUDE.md`](CLAUDE.md), which tells it to treat MXBMRP3 like any other tool and to refuse requests that would break that. Every analysis starts from one published prompt, [`prompts/analyse-tool.md`](prompts/analyse-tool.md), so anyone can rerun it.
- This repository is separate from MXBMRP3's, and shares no code with it.

If you think a card is unfair, suggest a correction (the form below): it will be answered in public.

## Ask for a tool, or correct a card

- [Request an analysis](../../issues/new?template=analyse-tool.yml) of a tool or a newer release.
- [Suggest a correction](../../issues/new?template=correction.yml): a correction, something missing, or the author's context. Name the card, the answer and your evidence.
- [Suggest a question](../../issues/new?template=question.yml) the cards don't ask yet; it is asked of every tool.

Authors are welcome to use all three, and can check a release before anyone else does: the site's "For authors" page shows what earns a Good answer on each question, with a check their agent runs ([`authors/`](authors/mxb-facts-check/SKILL.md)). Publishing your source, or allowing analysis in your licence, lets a card cover more.

## Layout

How the pieces connect and how the main jobs run: [`docs/DEVELOPING.md`](docs/DEVELOPING.md).

| Path | What's there |
|---|---|
| `cards/` | One card per tool release, as data (YAML), checked against `rules/card.schema.json` |
| `rules/template.md` | Card format and marks |
| `rules/scores.md` | How scores are worked out |
| `rules/scoring.yaml` | Every question, mark, cost, tag, threshold and Money label, in one file the build reads |
| `rules/questions.md` | The questions every card answers |
| `prompts/analyse-tool.md` | The prompt every analysis starts from, with the model and effort we use |
| `authors/` | The check authors drop into their own repository (`mxb-facts-check/SKILL.md`), shown on the "For authors" page |
| `site/` | `build.py` (checks the cards and builds the site) with `rules.py` (the rules and scores), `cards.py` (card checks), `feed.py` (the data feed, `api/v1/`), `render.py` and `templates/` (every page, made from the feed only), `static/` (styles, script, fonts) and `content.yaml` (the site's own text) |
| `tools/` | Link checker, corrections check, issue labels, VirusTotal hash lookup, mods-site and release fetchers, the runner and release downloader for the "Analyse a tool" workflow, unpackers for PyInstaller and Tauri apps |
| `registry/` | Every tool covered or queued, its mods-site page snapshot and its newest releases ([`registry/README.md`](registry/README.md)) |
| `vt/results.json` | Latest VirusTotal hash lookups for every card (written by the "VirusTotal lookup" workflow) |
| `lab/real-game/` | Runs plugins in the public demo of the game, offline (Wine in sessions, a throwaway Windows runner in "Analyse a tool"), with the download pinned by SHA-256 |
| `lab/evidence/` | The output of every command a card's lines name (`objdump`, `strings`, searches), one folder per card with the `run.sh` that repeats it |
| `lab/results/` | What each run recorded (logs, files written, connections tried, screenshots), one folder per card and run |
| `lab/plugin-test-host/` | A fake `mxbikes.exe` that loads plugins and logs what they do: under Wine, or on a throwaway Windows machine in the "Analyse a tool" workflow |
| `tests/` | Tests for how the build sets scores, marks and tags (`test_build.py`), and checks on the built site (`site/`: valid HTML, accessibility, behaviour, screenshots, Lighthouse) |
| `docs/` | Developer overview, queue of tools to analyse |

## Build

```
pip install -r requirements.txt
python3 -I tests/test_build.py   # the build's own tests
python3 -I site/build.py         # writes _site/ (the data feed and every page)
python3 -I tools/check_links.py  # checks every pinned code link
```

## Licence

[MIT](LICENSE) covers this project's own code. Its cards (`cards/`), rules (`rules/`), site text and the data feed (`api/v1/`, [docs/FEED.md](docs/FEED.md)) are under [CC BY 4.0](LICENSE-DATA): reuse them, commercially too, crediting MXB Facts with a link. What it quotes or records from the tools it covers (their strings and disassembly under `lab/evidence/`, their logs and files under `lab/results/`, page excerpts under `registry/`) stays with its owners.
