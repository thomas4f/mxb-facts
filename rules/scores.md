# Scores

A tool's score is a number out of 100, worked out from its answers by the rules below, and pinned to one release, like the card. Each area has its own score beside the overall one, so a closed-source HUD and a tool that patches the game, which are different kinds of concern, show in different areas.

A score sums up what a tool does and how much of it you can check. It isn't a verdict on whether a tool is safe or harmful, and it doesn't rate its features or quality: a low Transparency score means you can't check the code, not that the tool hides something, and an antivirus detection is not proof of malware.

Every number on this page lives in [`scoring.yaml`](https://github.com/thomas4f/mxb-facts/blob/main/rules/scoring.yaml), under `scores`, and the build writes the tables here from it.

## Area scores

Each of the five scored areas (Your PC and files, Your data, Your game, Creators' content, Transparency) starts at 100. Every answer that is a Concern by default takes off its cost from the area of its letter (P, D, G, C, T), and an area stops at 0. Good answers and Notes cost nothing, and neither does behaviour behind a choice you make (rule 5). Money isn't part of the score.

The costs come in tiers, set first:

<!-- rules/scoring.yaml: score_tiers. Written by site/build.py; edit rules/scoring.yaml instead. -->
| Tier | Cost |
|---|---|
| small | 5 |
| low | 10 |
| medium | 15 |
| large | 25 |
| severe | 40 |
| malware | 100 |
<!-- /rules/scoring.yaml -->

- **small:** it only limits how far you can check, or it is expected and has little effect (not signed, no licence, starts with Windows).
- **low:** it changes or reads something it doesn't own, in a way that stays on your PC and is easy to undo or stops when the tool does (changes game files, reads other people's data, changes only what you see while you're online).
- **medium:** something you didn't ask for that stays on your PC and can be undone (installs updates without asking, takes over input).
- **large:** a lasting or wider effect: on Windows, on other tools, on creators' work, or data that becomes public; or the source isn't public, so every other answer rests on weaker evidence.
- **severe:** by default, data tied to you or other people leaves your PC, protected content is shared, the game's play is changed online (physics, timing, lap data or what it sends) or its protection got around, other files are deleted, or updates run with no check.
- **malware:** signs of malware take the area to 0, and the result reads "Signs of malware" in place of a score.

Each question that can be a Concern has one cost:

<!-- rules/scoring.yaml: score_costs. Written by site/build.py; edit rules/scoring.yaml instead. -->
| ID | Area | Concern by default | Cost |
|---|---|---|---|
| P1 | Your PC and files | Do antivirus engines flag the release files (VirusTotal hash lookups)? | 15 |
| P2 | Your PC and files | Does it install updates without asking? | 15 |
| P3 | Your PC and files | Are updates checked before they are installed? | No: 40, Partly: 15 |
| P4 | Your PC and files | Can it delete or overwrite files that aren't its own? | 40 |
| P5 | Your PC and files | Are the release files code-signed? | 5 |
| P6 | Your PC and files | Does it change Windows settings or the registry beyond its own entries? | 25 |
| P7 | Your PC and files | Does it write into the game's folders beyond its own plugin and settings? | 10 |
| P8 | Your PC and files | Does uninstalling leave changes behind? | 5 |
| P9 | Your PC and files | Did the analysis find signs of malware: code that is hidden, disguised, or does something the tool doesn't show you? | 100 |
| P10 | Your PC and files | Does it ask Windows for administrator rights, or install a service or driver? | 15 |
| D2 | Your data | Is anything about you or your game sent (not counting a plain update check)? | 15 |
| D3 | Your data | Is an identifier sent (install ID, machine ID, Steam ID, GUID)? | 40 |
| D4 | Your data | Is other players' data sent? | 40 |
| D5 | Your data | Does it run a local web server that any website open in your browser can read? | 40 |
| D6 | Your data | Does it read other programs' files or data on your PC? | 10 |
| D7 | Your data | Is data about its users published? | 25 |
| D8 | Your data | Can every connection it makes be switched off? | 25 |
| D9 | Your data | Does it need, or create, an online account? | 5 |
| D10 | Your data | Does it share your game data with other programs on your PC? | 5 |
| G1 | Your game | Does it inject code into the game from another program? | 25 |
| G2 | Your game | Does it change the game's code or memory (hooks, patches, pointer swaps, writing records)? | 25 |
| G3 | Your game | Does it change the game while you're on online servers? | Yes: 40, Partly: 10 |
| G5 | Your game | Does it take over the game window's input, or press keys for you? | 15 |
| G6 | Your game | Does it change other plugins or tools, their files or their memory? | 25 |
| G9 | Your game | Does it start with Windows? | 5 |
| G12 | Your game | Does it get around a check or protection in the game itself (an integrity or version check, anti-cheat, or the game's own Steam or licence check)? | 40 |
| C1 | Creators' content | Does it decrypt protected content? | 25 |
| C2 | Creators' content | Does it save copies of other people's models or textures as files? | 25 |
| C3 | Creators' content | Does it share other people's content with the protection removed? | 40 |
| T1 | Transparency | Is the full source of the analysed release public? | 25 |
| T2 | Transparency | Do its docs say something its code doesn't do, on a point these questions ask about? | 25 |
| T3 | Transparency | Are the releases built by CI from a public tag? | 5 |
| T4 | Transparency | Was the release rebuilt and matched to the source? | 5 |
| T6 | Transparency | Are its dependencies pinned to exact versions? | 5 |
| T7 | Transparency | Does it have an open-source licence? | 5 |
<!-- /rules/scoring.yaml -->

## One behaviour counts once

Some questions describe the same behaviour from another side: a change to the game made online is still one change. In each group below, only the highest cost counts; the others show 0 and say where they are counted.

<!-- rules/scoring.yaml: score_groups. Written by site/build.py; edit rules/scoring.yaml instead. -->
| Behaviour | Questions |
|---|---|
| changes the game | G1, G2, G3 |
| sends data about you | D2, D3 |
| decrypts and shares content | C1, C3 |
| release not traced to public source | T1, T3, T4 |
<!-- /rules/scoring.yaml -->

G12 (a protection got around) is counted beside the group that changes the game: what was changed and that a check was got around are two facts.

Fixed groups prevent the common overlaps; they don't promise that every behaviour is counted exactly once on every tool, since two questions can describe one behaviour in one tool and two in another.

A release traced to public source by either check needs nothing more: T3 No costs nothing when T4 is Yes, T4 No nothing when T3 is Yes, and P5 (not signed) nothing when either is. A tool whose source isn't public (T1) has no CI build to pin and no licence to name, so T6 and T7 cost nothing while T1 is a Concern: closed source is counted once.

## The score

The overall score gives half its weight to the average of the five areas and half to the lowest-scoring area. So the lowest area counts for 60% in all and each other area for 10%: one area with serious findings can't be averaged away by clean ones, and two severe findings in one area cost more than one in each of two areas (a second severe finding takes 24 points off the score in the same area, 4 in another), which is why the area scores stay beside it. It is shown as a whole number out of 100, such as "72 / 100", rounded half up (72.5 shows as 73).

The score stays a number: a letter would need one more set of chosen cut-offs on top of the costs. Where a number would mislead, the result is said in words:

| Case | Shown |
|---|---|
| Every answer checked | the score, such as "72 / 100" |
| Some answers not checked or held back (rule 9) | the score, such as "30 / 100": the open answers count at their full cost, and a line under the score says how many are open |
| The licence forbids the analysis (rule 6) | "Not scored", with no number |
| The analysis found signs of malware (P9) | "Signs of malware", with no number |

## What we don't know

A lack of evidence must never look like evidence. So:

- An answer not checked or held back is charged its highest cost until it is answered, so less analysis never gives a higher score. A line under the score says how many answers are still open, and each of them says "Not checked" or "Held back" with its reason. "Not checked" is only for what genuinely can't be checked here; a gap in our own setup is closed rather than left open (the analysis prompt, step 7).
- An answer not allowed by the licence counts the same way, and the tool isn't scored: what couldn't be checked can't count for it or against it, and a no-analysis clause never reads as a better result. The card quotes the clause (its "Licence clause" row); a clause added in a later release applies from that release on, and the card for an earlier release keeps its score (rule 2).
- If the malware check (P9) wasn't done, the tool isn't scored either: a number with Your PC and files at 0 would read as a finding, and "Signs of malware" needs one.

## Where the numbers come from

The tiers were set first, from what an answer means for you: whether it changes anything, whether it can be undone, whether it leaves your PC, and whether it touches what someone else made. Each question then got a tier from its wording alone, the same for every tool.

## Versions

The rubric has a version, shown with every score and badge. A change to a tier, a cost, a group or how the score is combined is a new version: it rescores every card at once, and is recorded once in the table below with every card's old and new score. Cards get no history row for it: a rubric change says nothing new about any tool, and every score names its version.

## Badge

Each card gets six badges, shown under "For the tool's author" on its page, each with the MXB Facts wordmark: four shields in the shields.io styles (flat, plastic, flat-square, for-the-badge), drawn as shields.io draws them so they sit with a README's other shields on a light or dark page, and a score tile and a card with the area scores in the site's own colours, each pinned to the card's version and linked to its page (`badge/<tool-slug>/<version>…svg`, with a `.json` for other shields.io styles). A badge's title adds the rubric version, the analysis date and that the score is worked out from the answers' costs. A release the weekly inventory has seen (`registry/releases.json`), dated after the tool's newest card and with no card yet, gets the same six badges saying "Not analysed yet", under its version as published and without a leading v, so a README that moves to the new version before its card shows that; it scores nothing. Any other version without a card has no badge. Each card is also an image, the picture its page shows in chat apps (`badge/<tool-slug>/<version>-card.png`), with the tool, the release, the analysis date, the score, the area scores and the AI note on it, so it can stand alone; such a pending release gets one saying "Not analysed yet" too. `badge/<tool-slug>/card.png` is always the tool's newest card, at an address that doesn't change, and names any newer release that has no card yet, so it never reads as that release's result; badges, which don't name their release, are only ever pinned. An address the site doesn't have shows its 404 page, which names the tool or release asked for when it can.

## Changes to this rubric

| Date | Change |
|---|---|
| 21 Nov 2026 | v1, the rubric the site launches with. |
| 23 Nov 2026 | v2: G3 gains a Partly answer, for a tool that changes only what you see on your own screen while you're online (not physics, timing, lap data or what the game sends); it costs 10 (low), a Yes still costs 40 (severe), and both are counted with G1 and G2. Scores: FIXXER's Controller Rumble 1.0 85 → 85, MaXHUD 2.2.7 85 → 85, MXB Damage 1.3.0 69 → 78, MXB Discord RPC 2024-10-06 71 → 71, MXB FPS Booster V1 85 → 85. |
| 23 Nov 2026 | v3: P7 is a Concern by default only when the tool adds content you didn't pick. Changing the game's own files is a Note on P7, because P4 (deleting or overwriting files that aren't the tool's own) already counts it; before, one file change cost both. Scores: FIXXER's Controller Rumble 1.0 85 → 85, MaXHUD 2.2.7 85 → 85, MX Dirt Mod 1.7.1 83 → 83, MX Dirt Mod Alt 1.7.1-alt.1 85 → 85, MXB Damage 1.3.0 78 → 78, MXB Discord RPC 2024-10-06 71 → 71, MXB FPS Booster V1 85 → 85, MXBFix 0.1.8 62 → 68. |
| 26 Nov 2026 | v4: P4 and G6 count a file that is copied before it is changed like one that is moved and kept: Partly, a Note, when for each file the latest version that anything other than the tool wrote is kept. Before, a move was Partly and a backup with a rewrite was Yes, so the same outcome was answered two ways. This was chosen over keeping every version something else wrote, which differs when a player replaces a file the tool set and the tool then backs up the player's version over an earlier copy: that rule would answer such a tool Yes, this one Partly. A run showed that Suspension Tuner keeps only its first copy, so it is Yes under both. T2 is a Note when every line of the docs that the code doesn't do describes riskier behaviour than the code has; docs that overstate the risk no longer cost points. Scores: Dirt Gear 1.1.1 97 → 97, Dirt Gear 1.2.0 82 → 82, Dirt Gear 1.2.1 97 → 97, FIXXER's Controller Rumble 1.0 85 → 85, HoleShot HUD 0.24.0 70 → 70, HoleShot HUD 0.24.2 97 → 97, MaXHUD 2.2.7 85 → 85, MX Bikes Setup Duper 0.1.8674.29660 97 → 97, MX Dirt Mod 1.7.1 83 → 83, MX Dirt Mod Alt 1.7.1-alt.1 85 → 85, MXB Damage 1.3.0 78 → 78, MXB Discord RPC 2024-10-06 71 → 71, MXB DualSense Support 1.1.0 85 → 85, MXB FPS Booster V1 85 → 85, MXB Ragdoll 1.0 62 → 62, mxbfix 0.1.8 68 → 68, Pitbox 3.0.4 38 → 40, ProjectGPB2 v2 67 → 67, Suspension Tuner 1.4.1 56 → 56, TrackRelief 1.2.2 85 → 85. |
| 27 Nov 2026 | v5: a new question, P10 (Does it ask Windows for administrator rights, or install a service or driver?), answered on every card from its release files: each program's manifest, the installer's own settings, and the calls and text that ask for or check those rights (`lab/evidence/privileges.py`, and `lab/evidence/innosetup.py` for Inno Setup 6.7). A tool that asks each time it starts, or installs a service or driver, is a Concern that costs 15 (medium), like installing updates without asking (P2): both widen what the tool can reach without changing anything by themselves. Only an installer or uninstaller asking is Partly, a Note, and asking only for something you choose (an install for all users, a "Retry as administrator" button) is "Yes, on request", a Note. No card's tool asks each time it starts or installs a service or driver. Scores: Dirt Gear 1.1.1 97 → 97, Dirt Gear 1.2.0 82 → 82, Dirt Gear 1.2.1 97 → 97, FIXXER's Controller Rumble 1.0 85 → 85, HoleShot HUD 0.24.0 70 → 70, HoleShot HUD 0.24.2 97 → 97, Knee Down 0.1.8 56 → 56, MaXHUD 2.2.7 85 → 85, MX Bikes Setup Duper 0.1.8674.29660 97 → 97, MX Dirt Mod 1.7.1 83 → 83, MX Dirt Mod Alt 1.7.1-alt.1 85 → 85, MXB Damage 1.3.0 78 → 78, MXB Discord RPC 2024-10-06 71 → 71, MXB DualSense Support 1.1.0 85 → 85, MXB FPS Booster V1 85 → 85, MXB Ragdoll 1.0 62 → 62, mxbfix 0.1.8 68 → 68, MXRP Ragdoll 3.2 36 → 36, Pitbox 3.0.4 40 → 40, ProjectGPB2 v2 67 → 67, Suspension Tuner 1.4.1 59 → 59, TrackRelief 1.2.2 85 → 85; Heightmap Studio 26.11.7 and MXB Studio 1.0.1 stay Not scored. |
