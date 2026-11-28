# Contributing

Most help comes as issues: [request an analysis](../../issues/new?template=analyse-tool.yml), [suggest a correction](../../issues/new?template=correction.yml) (a correction, something missing, or the author's context) or [suggest a question](../../issues/new?template=question.yml). Pull requests that change a card are welcome too, under the same rules.

## Rules for a change to a card

The rules are in [`CLAUDE.md`](CLAUDE.md) ("The rules that don't bend") and [`rules/`](rules/); they aren't repeated here, so they can't drift apart. Briefly: evidence on every line, the same questions and scoring rules for every tool, neutral words, a dated "Card history" row for every change to what a card says, and a new card file for a new release.

**Security problems** you find in a tool, and **how a tool gets at creators' protected content**: report them privately to its author, not in an issue (rule 9). The same goes for a comment on an answer that reads "Details withheld (rule 9).": send it privately, so the details stay out of public issues. To reach this project privately, see [`SECURITY.md`](SECURITY.md).

## Before you push

```
pip install -r requirements.txt
python3 -I tests/test_build.py
python3 -I site/build.py
python3 -I tools/check_links.py
```

All three run in CI on every pull request, with the corrections check.

## VirusTotal

`tools/vt_lookup.py` looks up file hashes only; it never uploads. The "Analyse a tool" run uploads the downloaded release files VirusTotal has no record of, within the limits in `CLAUDE.md`, "VirusTotal". It needs your own key in the `VT_API_KEY` environment variable (`--card <file>` for one card, `--all` for every card).

The "VirusTotal lookup" workflow does this with the repository secret. It runs only when the maintainer starts it by hand:

- With `pr`, it looks up the hashes of the cards that pull request adds or changes and posts the results as a comment on it (one comment, updated on each run). Pull requests from forks are skipped.
- With `tool` (pick `all` or one tool from the dropdown, which the build keeps in step with `registry/tools.json`), it looks up that tool's cards, writes the results to `vt/results.json` and commits it to `main`. Each entry has the counts, the engines that flagged the file, the scan date, the lookup date, the permalink and the run that looked it up.

How a result is quoted on a card (P1) is in [`rules/questions.md`](rules/questions.md).
