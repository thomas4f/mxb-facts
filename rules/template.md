# Tool card template

## How AI is used

- **Who does the work.** Every card is written by Claude, Anthropic's AI model, running in [Claude Code](https://claude.com/claude-code) with this repository checked out. Thomas directs the work, in chat as well as through these rules; anything that changes how cards are made is written into these public files.
- **Model and effort.** We use Claude Opus 5.5 (`claude-opus-5-5`) at medium effort. Effort is Claude Code's setting for how much the model reasons before it answers (low, medium, high, xhigh, max). Each card's Method row names the model and effort it was made with.
- **The prompt.** Every analysis starts from the same prompt, [`prompts/analyse-tool.md`](https://github.com/thomas4f/mxb-facts/blob/main/prompts/analyse-tool.md), shown in full below. With [`CLAUDE.md`](https://github.com/thomas4f/mxb-facts/blob/main/CLAUDE.md), this page and the [question list](https://github.com/thomas4f/mxb-facts/blob/main/rules/questions.md), that is the written instruction the AI gets; Thomas's directions in chat come on top, and anything they change in how cards are made is written back into these files. Anyone can run the prompt, a tool's author included.
- **Not deterministic.** The same prompt, model and effort can give a different card on another run: other wording, and sometimes a fact found or missed. So you don't have to trust a run: every line links its evidence, the build refuses a card that skips a question or a mark that doesn't match its rule, and a missed or wrong fact is fixed by a correction, not by rerunning until it agrees.

## Rules

The ten rules every card follows. The AI's instructions, [`CLAUDE.md`](https://github.com/thomas4f/mxb-facts/blob/main/CLAUDE.md), list the same rules under the same numbers.

1. **Only provable facts.** Each line says what the tool does, in plain words a player understands, and links its evidence: the exact lines of code at the analysed release's full commit hash (a tag can move, so it isn't used), a file in the release, or a test anyone can repeat (for example "searching the source for `VirtualProtect` finds nothing"). Anything we could not prove, or did not test, goes under "Limits of this analysis" or is left out.
2. **Pinned to one release.** The header names the release, the commit, the hashes of the files players download, and the date of the analysis. A newer release gets a new card; the old one stays.
3. **Same questions for every tool.** Every card answers every question in `questions.md`, each in its area's section: Yes, No, Partly, Not checked with the reason, or Not allowed when the tool's licence forbids the analysis. A new check on any tool is first added there as a question and answered for every card. Where a tool's own docs make a claim, the card quotes it and says whether the code matches. The build stops if a card misses a question.
4. **Scores come from fixed costs** (see "How scores are worked out"), never from a case-by-case judgement. Each area's score and the overall score are worked out from the answers by [`scores.md`](scores.md): each Concern by default has a fixed cost, the same for every tool.
5. **Defaults decide scores.** Where a behaviour can be switched, the card says whether it is on or off when you first install. What only happens after a choice you make is still listed and marked, but costs no points.
6. **Licences that forbid analysis are respected.** Such a tool's card covers only public facts; the rest says "Not allowed", quoting the clause.
7. **No words that judge.** No "safe", "spyware" or "shady". "Sends the full rider list of your server every 30 seconds" is a fact; "spies on you" is not. "No malware found" is the strongest positive phrase.
8. **100% AI-assisted, said on every card.** An AI assistant (Claude) does the analysis from one published prompt; no person reviews it line by line. So every line carries its own evidence, and each card's Method row names the model and effort it was made with.
9. **Undisclosed vulnerabilities are held back for 30 days at most, and how a tool gets at protected content for good.** A security problem that isn't public is reported privately to the tool's author first. Until a fix ships or 30 days have passed since the author was told, the card leaves out the details, and its "Held back" row says that an item is held and which questions it touches. Those answers can't be Good. The dates are kept privately by the maintainer, not on the card. How a tool gets at creators' protected content (C1 to C3) is reported privately too, and never published: the answer still says whether and what, with its mark and cost, and reads "Details withheld (rule 9)."; how it is done goes into a private report the maintainer sends the author. The site isn't published while a vulnerability on MXBMRP3 is held back.
10. **No personal data** about authors beyond the name they publish themselves as their public identity.

## Marks and scores

These help a reader at a glance. They follow fixed rules, so the same fact gets the same mark on every card.

**Each fact is marked:**

- **Good**: protects you or creators (for example signed updates, removals to the Recycle Bin, full source public, opt-in data).
- **Note**: worth knowing, but no harm on its own.
- **Concern**: can affect your PC, your data, your game or creators' rights, or the tool's docs say something different.

**Each area is scored on its own**, out of 100, from fixed costs: [how scores are worked out](scores.md).

- Notes cost nothing. Partly is a Note, except on P3 and G3, where it is a Concern. Moving or renaming a file that isn't the tool's own is a Note, as long as the file is kept and can be put back; deleting, corrupting or permanently disabling such a file counts as deleting or overwriting it (P4). Changing the game's own files is counted under P4 only, so P7 costs points only for content added that you didn't pick. A request that carries nothing about you or your game, such as an update check, is a Note.
- A tool the analysed tool runs or installs (for example FrostMod run by MXB App) has its own card and isn't counted here.
- **Money** isn't scored, because paying for a tool isn't a risk in itself. Its label says what the tool costs, from the answers to M1 and M2, as in the table below.
- Tags and scores are separate. A tag marks one answer worth attention; a tag that another tag already says is left out (a closed-source tool shows "Closed source", not also "Not traced to source").
- **How a Concern answer is shown.** A Concern by default reads "Concern" with its cost beside it, or "Major", when the cost is the severe tier in [`scoring.yaml`](scoring.yaml) or more (40). Major is how a Concern is shown, not another mark: it costs what the cost table says, like any Concern. One that only happens after a choice you make reads "Off by default" ("Yes, not by default") or "On request" ("Yes, on request"), in grey, and costs nothing (rule 5). A Concern line under "Also found" is shown the same way, beside the answers it backs. An answer with no mark shows its state in grey: "Not checked", "Held back" (rule 9), "Not allowed" or "Doesn't apply"; none of them is a Concern, though an open one counts at its highest cost until it is answered. Signs of malware and Not scored replace the score. Each mark and state has its own icon, so none relies on colour alone; the list is `STATES` in `site/rules.py`.

<!-- rules/scoring.yaml: money. Edit that file, not this table: the build writes it. -->
| Label | Shown when | What it means |
|---|---|---|
| Paid | M1 is Yes | You have to pay to use it |
| Paid extras | M1 is No and M2 is Yes | It is free to use, but features, versions or some kinds of use are sold separately |
| Free | M1 is No and M2 is No | It costs nothing to use and sells nothing extra; donation links are allowed |
| Not allowed | No label above applies, because the licence forbids answering M1 or M2 | The tool's licence forbids the analysis, and the questions it does allow don't say what it costs |
| Not checked | No label above applies, and M1 or M2 is not checked or held back | The analysis couldn't settle what it costs; the Money answers say why |
<!-- /rules/scoring.yaml -->

**How a comment is decided.** A mark or a cost follows from what the analysis can see, never from why the author did it: a crash fix and a cheat that change the same code get the same answer. So a comment that a score feels unfair is decided in this order, and the first step that fits is the one taken:

1. **Context.** The fact and its mark are right, but players need more to read it well: the answer's text says more, with a Card history row, and the comment is "noted".
2. **Correction.** The card applies the rules as they're written wrongly, or a fact on it is wrong: the answer is fixed, with a Card history row, and the comment is "fixed".
3. **Wording.** A question reads differently from the rest, and no answer on any card changes: the wording is fixed, and no score moves.
4. **Rubric change.** Only when all three hold: it turns on something the analysis can observe (not intent, and not a judgement such as "gives an advantage"), the reason holds for every tool, and the same pattern shows on two or more tools or the change fixes how something is counted. It is a new rubric version, decided with every card's old and new score in view ([scores.md](scores.md#changes-to-this-rubric)), never on what it does to one card. Otherwise the comment is "declined" with the reason.

**Tools whose licence forbids analysing them.** When a tool's licence forbids reverse engineering, decompiling or similar analysis, its card covers only what is public: the release page, its README, changelog and licence, the update feed, file hashes, and whether the files are code-signed. Everything that would need looking inside the release is shown as **Not allowed**, quoting the licence clause. The tool isn't scored ("Not scored"). The card states the restriction and nothing more: it doesn't guess what the release does.

We don't call any tool "safe": a card can only say what was found, and "No malware found" means nothing hidden or deceptive turned up in what was checked.

## Sections

A card is a data file, `cards/<tool-slug>-<version>.yaml`, in the format of [`card.schema.json`](https://github.com/thomas4f/mxb-facts/blob/main/rules/card.schema.json): the tool's name and version, a `summary` (two short sentences shown on its page, written from the analysis), the header rows, the files, then the parts below. The build checks it against the schema and the rules, sets the marks and scores it can work out, and makes every page from it.

Header block:

<!-- card.schema.json: header. Edit that file, not this table: the build writes it. -->
| | |
|---|---|
| What it is | What the tool is and where it goes, in two or three sentences, from the analysis |
| In one line | What the tool is and does, at most 90 characters, written from the analysis: never the author's own claims and no words that judge. Shown under the tool's name |
| Category | One of: HUD; Setup and coaching; Gameplay and visuals; Fixes and performance; Mod managers; Content creation; Controllers; Social. It says what kind of tool it is, so readers can find similar ones; it says nothing about the tool's quality |
| Author | The name the author publishes as their public identity (GitHub name, the name on its licence or page) |
| Game | One of: MX Bikes; GP Bikes. The PiBoSo game the tool is for |
| mxb-mods.com | For an MX Bikes tool: its mxb-mods.com page, "None found", or "Not checked" with the reason |
| gpb-mods.com | For a GP Bikes tool, in place of mxb-mods.com: its gpb-mods.com page, "None found", or "Not checked" with the reason |
| Homepage | Its own website, or "None found" |
| GitHub | Its GitHub repository or releases, or "None found" |
| Received as | Only for a file sent to us: what was received and where it came from |
| Version analysed | Release name and tag |
| Source commit | Full hash, linked |
| Files checked | File names + SHA-256 of what players download, and of the files inside them that were checked (the `files` list) |
| Analysed on | Date |
| Held back | Only while an item is held back under rule 9: "&lt;n> item(s) (rule 9): &lt;question IDs>". Those answers can't be Good. The dates (when the author was told, and the end, 30 days later at most) are kept privately by the maintainer, not in the repository |
| Licence clause | Only when the licence forbids the analysis (rule 6): the clause, quoted, with a link to it or the SHA-256 of the file it is in. A card has this row if, and only if, an answer is "Not allowed"; that card gets "Not scored" in place of a score. A clause added in a later release applies from that release on; a card for an earlier release stays (rule 2) |
| Earlier reports | Only when the tool has earlier cards: a link to each, newest first, so a reader can see what changed between releases |
| Method | That the analysis was done by an AI assistant, and the model and effort it ran with; read the source at the commit; compared release files to source where possible; what was and wasn't run |
<!-- /card.schema.json -->

The header facts shown at the top of the tool's page (name, what it is, category, author, links, version, date) aren't repeated in the report's header table. Each fact is said once: in its answer, or in an "Also found" line when no answer says it.

1. **Key questions** - the ten key questions from `questions.md`, each with a short answer (a few words, then the detail) and the full questions it comes from. The build sets each mark from those answers. On the page they come after the areas; everything else folds into "All answers and evidence".
2. **Areas** - the five areas and the Money row, each with a one-line reason (the `areas` field). The build sets each area's score from the costs of its answers. The top of the page shows the overall score with a bar per area, beside the key findings; in "All answers and evidence", each area's reason sits beside its score in that area's heading. A held-back item is said once, in the header, not here.
3. **Your PC and files** - What it installs, deletes and updates, and how. Crash handling. Code signing (why antivirus may flag it).
4. **Your data** - What leaves your PC, to whom, how often, whether it is on by default, whether you need an account, what is stored about you and who can read it.
5. **Your game** - Plugin API only? Reads or writes game memory? Hooks or patches the game's code? Gets around one of the game's checks? Changes game files? Runs outside the game (launcher, background app)?
6. **Creators' content** - How it treats other people's protected or paid content. Credits for code it reuses.
7. **Transparency** - Is the source public, and is all of it public? Its licence. Can the release be traced to the source? Do its docs match the code? How is it built and developed?
8. **Money** - Price, paid tiers, donations, shops. Sections 3 to 8 each start with the area's answers to the questions in `questions.md` (also shown side by side under "Compare tools"), then their tables, folded (for example "Connections found"), then **Also found**: lines that add what no answer says. A line that only repeats an answer is left out.
9. **What it says vs what it does** - Quotes from its own docs, each with a verdict: Matches, Partly, Doesn't match, Not checked or Not allowed (`rules/card.schema.json`), drawn like the mark it reads like; a verdict costs nothing itself, T2 is the answer that counts. It shows in "All answers and evidence", after Money.
10. **Limits of this analysis** - Everything we could not prove or run, and why. Each limit names every answer whose verdict or mark could change if the limit were lifted (it was run, the file was tied to its build, the service could be seen), and those answers link to it. A limit on the method as a whole (for example Wine isn't Windows) names none. A held-back question is never named (rule 9), and the one line saying how a tool gets at protected content is withheld names none.
11. **Corrections** - Every comment sent through the "Comment on an answer" form (the `corrections` list): its issue, what it is (a correction, something missing, or the author's context), the questions it names, and its status, open, fixed, declined or noted, with the date and why. Every answer in "All answers and evidence", Good ones included, has a comment icon that opens the form with the card and the question filled in; while a comment is open, that icon shows the count and links here, each key question built from the answer shows "Under review #N", and the tool's findings show "N under review". It is neutral: no answer, mark, tag or score moves until it is decided.
12. **Card history** - A table with a Date and a Change column: one change per row, oldest first. A score change caused by an answer says the old score, the new one and that answer; a rubric change is recorded in [scores.md](scores.md#changes-to-this-rubric) instead. The history records changes to what the card says about the tool (an answer, its evidence, a score, a correction), not changes to the site, the layout or the card format.

## Wording

- Second person ("your PC", "your Steam friends").
- Present tense, for the version analysed.
- Short sentences. One fact per line.
- Name settings exactly as the tool's own screens name them.

