# Same questions for every tool

Every card answers every question below, each in its area's section of the card's answers and evidence. The page build stops if a card misses one, so nothing checked on one tool goes unchecked on another.

The tables on this page are written by the build from [`scoring.yaml`](scoring.yaml), the one file that holds every question, mark, cost, tag, threshold and Money label; a change is made there, never in the tables.

When a new check is made on any tool, it is added as a new question first, and then answered for every card before the page is published again.

## Key questions

Most players won't read every question, so each card starts with ten key questions, ordered by the highest cost among the answers they come from (`rules/scores.md`), and by area where two are equal. They aren't separate checks: each one is answered from the full questions it lists below. Its mark is the strongest mark among those answers (Concern before Note before Good), except where the Mark column says Best: there any one good answer settles it, so the best mark counts. "Not checked", "Not allowed" and "Doesn't apply" don't count. The build refuses a key answer whose sources or mark don't match. Where one key question covers different behaviours, a source that is a Concern must be named in its answer: K5's answer says "gets around" whenever G12 is a Concern, so a tool that gets around a game check doesn't read like one that only changes game memory. The full answers stay on the card, in the area sections of the full report.

<!-- rules/scoring.yaml: keys. Edit that file, not this table: the build writes it. -->
| Key | Key question | Short | From | Mark |
|---|---|---|---|---|
| K1 | Did the analysis find signs of malware, and do antivirus engines flag it? | Malware? Antivirus flags? | P1, P9 | Strongest |
| K2 | Does it update itself without asking, or without checking the file? | Updates unchecked? | P2, P3 | Strongest |
| K3 | Can it delete or change files that aren't its own? | Touches other files? | P4, P6, P7 | Strongest |
| K4 | Does it send data about you? | Sends your data? | D2, D3 | Strongest |
| K5 | Does it change the game, or get around one of its checks? | Changes the game? | G1, G2, G3, G12 | Strongest |
| K6 | Does it unlock, copy or share other people's content? | Uses others' content? | C1, C2, C3 | Strongest |
| K7 | Is the source code public? | Open source? | T1 | Strongest |
| K8 | Does it do what its docs say? | Does what it says? | T2 | Strongest |
| K9 | Can you check the download is the real one? | Download checkable? | P5, T3, T4 | Best |
| K10 | Does it connect to the internet? | Goes online? | D1 | Strongest |
<!-- /rules/scoring.yaml -->

## All questions

Each answer starts with a mark, then one of these verdicts, then a short reason. Each answer has evidence, like every other line.

- **Yes** or **No**: with the tool's default settings, as it installs. "By default" means without any choice you make: no setting you turn on, no folder you pick, no button you click.
- **Yes, not by default.** It happens only after a choice that isn't the default: a setting you turn on, a folder you pick, a mode you start. The answer names the choice. So a question never says "by default" itself: the verdict does.
- **Yes, on request.** It happens only when you start that very action, each time: a button you click, a dialog you confirm.
- **Partly**: Yes for one part of what the question asks and No for the rest, with default settings; the answer names both parts. The table's Partly column gives its mark: a Note, or a Concern on P3 and G3, where it costs points. Where the column also says what Partly means on that question (P3, P4, G3, G6), Partly means exactly that, and every Partly answer on a card shows it. Where the column says None, the question has no Partly: a tool connects, runs in the game, opens other people's content or costs money, or it doesn't; any part of the release whose source isn't public makes T1 No, and any claim its code contradicts makes T2 Yes. For T1, prebuilt program files (executables, libraries, plugins, native modules) in the release or the repository count as public source only when their source at that exact version is public (the tool's own source at the commit, or a named open-source project and version, such as an Electron or NSIS release), or when they are the runtime of the platform the tool runs on (Windows, Steam, the game), named on the line. Any other prebuilt file makes T1 No. The T1 answer lists every prebuilt file found and where its source is; data files such as images and fonts aren't program files.
- **Not checked.** or **Not allowed.** with the reason, when we didn't check, or the tool's licence forbids the analysis. **Doesn't apply.** only for P3, when there is no updater.

The mark comes from the table, not from judgement, so the same answer gets the same mark on every card. The Yes and No columns give the mark for that verdict; where a cell names a condition, the first mark applies unless the condition holds. "Yes, not by default" and "Yes, on request" take the Yes column's mark; where a cell says "Note if only on request", "Yes, on request" is a Note and every other Yes a Concern, and the build checks that. For the other conditions the card's answer says why the condition holds, and the build checks only that the mark is one the cell allows. **Partly** takes the mark in its column. "Not checked", "Not allowed" and "Doesn't apply" carry no mark.

Only Concerns by default cost points (see "Marks and scores" in the template); "Yes, not by default" and "Yes, on request" never do, and Partly does only on P3 and G3.

"Traced" means the release files can be tied to the public source: T3 or T4 is Yes. A hash the author publishes doesn't count.

P1 counts antivirus engines only, with fixed thresholds, because packers and unsigned files are often flagged by a few engines:

<!-- rules/scoring.yaml: p1. Edit that file, not this table: the build writes it. -->
| P1 | When |
|---|---|
| No | no engine flagged any release file |
| Partly | fewer than 1 in 10 engines flagged a file |
| Yes | 1 in 10 or more flagged a file |
<!-- /rules/scoring.yaml -->

It always gives the count and links each file's VirusTotal entry, and nothing else: no link to the lookup run (a GitHub Actions run readers can't open). A file VirusTotal has no record of is "not on VirusTotal (hash lookup on <date>)"; a file uploaded because VirusTotal had no record of it (by the analysis run, or by hand by the maintainer; CLAUDE.md, "VirusTotal") says so, with the date, and while its scan isn't finished it counts as not on VirusTotal. **No** is Good only when every file players download (each file in the card's list that isn't inside another) is on VirusTotal; otherwise it is a Note, since no engine has looked at that file. The build checks P1 against the latest lookup in `vt/results.json`. What our own analysis found is P9, a separate question: engine counts alone are never called signs of malware.

Areas, and the questions within each area, are listed most critical first: what can do the most harm to your PC, your data or your game comes before what is only worth knowing. IDs follow that order, except that a question added later goes at the end of its area.

<!-- rules/scoring.yaml: questions. Edit that file, not this table: the build writes it. -->
| ID | Area | Question | Yes | No | Partly |
|---|---|---|---|---|---|
| P1 | Your PC and files | Do antivirus engines flag the release files (VirusTotal hash lookups)? | Concern | Good; Note if a file players download isn't on VirusTotal | Note |
| P2 | Your PC and files | Does it install updates without asking? | Concern | Good | Note |
| P3 | Your PC and files | Are updates checked before they are installed? | Good | Concern | Concern: the only check comes from the same place as the file |
| P4 | Your PC and files | Can it delete or overwrite files that aren't its own? | Concern; Note if only on request | Good | Note: it only moves, renames or backs up such files, and each one, as it was just before the tool changed it, is kept beside it or in a folder the tool names, so it can be put back |
| P5 | Your PC and files | Are the release files code-signed? | Good | Concern; Note if the files can be traced to public source (T3 or T4 is Yes) | Note |
| P6 | Your PC and files | Does it change Windows settings or the registry beyond its own entries? | Concern; Note if only on request | Good | Note |
| P7 | Your PC and files | Does it write into the game's folders beyond its own plugin and settings? | Note; Concern if, by default, it adds content you didn't pick | Good | Note |
| P8 | Your PC and files | Does uninstalling leave changes behind? | Note; Concern if changes to Windows or to files that aren't its own stay | Good | Note |
| P9 | Your PC and files | Did the analysis find signs of malware: code that is hidden, disguised, or does something the tool doesn't show you? | Concern; a second check must confirm it | Good | Note |
| D1 | Your data | Does it connect to the internet? | Note | Good | None |
| D2 | Your data | Is anything about you or your game sent (not counting a plain update check)? | Concern | Good | Note |
| D3 | Your data | Is an identifier sent (install ID, machine ID, Steam ID, GUID)? | Concern; Note if the only identifier is a random install ID the tool makes itself | Good | Note |
| D4 | Your data | Is other players' data sent? | Concern | Good | Note |
| D5 | Your data | Does it run a local web server that any website open in your browser can read? | Concern | Good | Note |
| D6 | Your data | Does it read other programs' files or data on your PC? | Note; Concern if it reads other people's data | Good | Note |
| D7 | Your data | Is data about its users published? | Concern | Good | Note |
| D8 | Your data | Can every connection it makes be switched off? | Good | Concern; Note if what has no switch carries nothing about you | Note |
| D9 | Your data | Does it need, or create, an online account? | Concern | Good | Note |
| D10 | Your data | Does it share your game data with other programs on your PC? | Note; Concern if any program can read your identifiers or other riders' data from it | Good | Note |
| G1 | Your game | Does it inject code into the game from another program? | Concern | Good | Note |
| G2 | Your game | Does it change the game's code or memory (hooks, patches, pointer swaps, writing records)? | Concern | Good; Note if a tool it runs or installs by default does | Note |
| G3 | Your game | Does it change the game while you're on online servers? | Concern | Good; Note if a tool it runs or installs by default does | Concern: it changes only what you see on your own screen, not physics, timing, lap data or what the game sends |
| G4 | Your game | Does it read the game's memory outside the plugin interface? | Note | Good | Note |
| G5 | Your game | Does it take over the game window's input, or press keys for you? | Concern; Note if it only takes input for its own menu or for buttons you click | Good | Note |
| G6 | Your game | Does it change other plugins or tools, their files or their memory? | Concern; Note if installing or updating that tool is its stated job | Good | Note: it only moves, renames or backs up their files, and each one, as it was just before the tool changed it, is kept beside it or in a folder the tool names, so it can be put back |
| G7 | Your game | Does it read the keyboard through Windows, also while the game isn't focused? | Note | Good | Note |
| G8 | Your game | Does it install a crash handler for the whole game? | Note | Good | Note |
| G9 | Your game | Does it start with Windows? | Concern | Good | Note |
| G10 | Your game | Does it run a separate program next to the game? | Note | Good | Note |
| G11 | Your game | Does it run inside the game (as a plugin, or loaded into it)? | Note | Good | None |
| G12 | Your game | Does it get around a check or protection in the game itself (an integrity or version check, anti-cheat, or the game's own Steam or licence check)? | Concern | Good | Note |
| C1 | Creators' content | Does it decrypt protected content? | Concern | Good | Note |
| C2 | Creators' content | Does it save copies of other people's models or textures as files? | Concern | Good | Note |
| C3 | Creators' content | Does it share other people's content with the protection removed? | Concern | Good | Note |
| C4 | Creators' content | Does it credit third-party code it ships? | Good | Note | Note |
| C5 | Creators' content | Does it open other people's mods, paints, tracks or models (files, or the game's copy outside the plugin interface)? | Note | Good | None |
| T1 | Transparency | Is the full source of the analysed release public? | Good | Concern | None |
| T2 | Transparency | Do its docs say something its code doesn't do, on a point these questions ask about? | Concern; Note if each such line describes riskier behaviour than the code has | Good | None |
| T3 | Transparency | Are the releases built by CI from a public tag? | Good | Concern | Note |
| T4 | Transparency | Was the release rebuilt and matched to the source? | Good | Concern | Note |
| T5 | Transparency | Is the day-to-day development history public? | Good | Note | Note |
| T6 | Transparency | Are its dependencies pinned to exact versions? | Good | Concern | Note |
| T7 | Transparency | Does it have an open-source licence? | Good | Concern | Note |
| M1 | Money | Does it cost money to use? | Note | Good | None |
| M2 | Money | Are features or versions sold separately? | Note | Good; Note if it opens or links to someone else's shop | None |
| M3 | Money | Does it ask for donations? | Note | Good | Note |
<!-- /rules/scoring.yaml -->

A question ID is never reused for another question.

## Tags

The front page shows each tool as a row of tags instead of its ten answers, so a reader sees at once what stands out. A tag is not a new check: each one comes from one question below, by this table, never picked by hand.

- A **critical** tag shows when the question's answer has the verdict in the Answer column and a Concern mark (for a Partly row, the verdict is enough). With the answer "Yes, not by default" or "Yes, on request", it shows in grey, as "Off by default" or "On request", folded until clicked.
- A tag marked "not when" is left out when any of those answers holds, because another tag or answer already says it (a closed-source tool shows "Closed source", not also "Not traced to source"; a release that a matching rebuild traces isn't "Not traced to source" either).
- No gaps: every answer the mark table can make a Concern has a row here. A row of kind **None** shows no tag and says which tag covers it. The build refuses a table with a gap.
- A **positive** tag shows when the answer has the verdict in the Answer column and a Good mark.
- Three tags come from the card itself: "<n> held back" (the Held back row), "<n> not checked" (answers "Not checked", not counting those held back) and "Licence forbids analysis" (any answer "Not allowed"). A tool shows "No critical findings" only when it has no critical tag, every question is answered and nothing is held back.

<!-- rules/scoring.yaml: tags. Edit that file, not this table: the build writes it. -->
| From | Answer | Tag | Kind | Icon | What it means |
|---|---|---|---|---|---|
| P9 | Yes | Signs of malware | Critical | bug | The analysis found code that is hidden, disguised, or does something the tool doesn't show you, and a second check confirmed it. This replaces the score. |
| P1 | Yes | Some antivirus engines flag it | Critical | shield-x | Enough antivirus engines on VirusTotal flag a release file to count; the answer gives the count. Unsigned hobby builds are often flagged by mistake. |
| P2 | Yes | Updates without asking | Critical | refresh-cw | New code can reach your PC without you choosing it, so what you run can change after this card was made. |
| P3 | No | Unchecked updates | Critical | refresh-cw-off | Updates are installed without a check that they really come from the author, so a tampered download would not be caught. |
| P3 | Partly | Updates partly checked | Critical | refresh-ccw-dot | Updates are checked in some ways but not all, so some tampering would not be caught; the answer says which part is missing. |
| P4 | Yes | Deletes or overwrites others' files | Critical | trash-2 | Files that belong to the game, Windows or another tool can be lost or replaced, without a copy kept to put them back. |
| P5 | No | Not signed or traceable | Critical | badge-x | The files carry no signature and can't be traced to public source, so you can't confirm who built them or that they weren't changed on the way to you. |
| P6 | Yes | Changes Windows settings | Critical | monitor-cog | It changes how Windows is set up beyond its own entries, which can affect other programs and may stay after you remove it. |
| P7 | Yes | Changes game files | Critical | folder-pen | It writes into the game's folders beyond its own files, which can affect the game, other mods, or a reinstall. |
| P8 | Yes | Leaves changes behind | Critical | footprints | Removing it doesn't undo everything it did; the answer lists what stays. |
| D2 | Yes | Sends your data | Critical | send | Something about you or your game leaves your PC; the answer says what and to whom. |
| D3 | Yes | Sends an identifier | Critical | fingerprint | An identifier is sent that can link your sessions together over time, beyond a random install ID the tool makes itself. |
| D4 | Yes | Sends other players' data | Critical | users | Data about other riders in your session leaves your PC, without them having chosen this tool. |
| D5 | Yes | Open local web server | Critical | server | Any website open in your browser can read what the local server shares while the tool runs. |
| D6 | Yes | Reads other people's data | Critical | file-search | It reads files or data that belong to other programs on your PC. |
| D7 | Yes | Publishes riders' data | Critical | megaphone | Data about its users is made public, where anyone can see it. |
| D8 | No | No off switch | Critical | power-off | At least one connection that carries something about you can't be turned off; you can only stop using the tool. |
| D9 | Yes | Needs an online account | Critical | circle-user | You need an account with an online service to use it, which ties your use to that account. |
| D10 | Yes | Shares game data locally | Critical | share-2 | It passes your game data to other programs on your PC, which can then use or send it. |
| G1 | Yes | Injects into the game | Critical | syringe | Another program puts code into the running game, rather than the game loading it as a plugin. |
| G2 | Yes | Changes game memory | Critical | memory-stick | It changes the game's own code or memory while it runs, beyond what the plugin interface offers. |
| G3 | Yes | Changes the game online | Critical | globe | It changes how the game behaves on online servers, in physics, timing or what the game sends, which affects the other riders on the server. |
| G3 | Partly | Changes what you see online | Critical | scan-eye | It changes only what you see on your own screen while you're online, not physics, timing or what the game sends. |
| G12 | Yes | Gets around a game check | Critical | shield-off | It gets around a check the game makes, such as a version or licence check or anti-cheat. |
| G5 | Yes | Takes over game input | Critical | keyboard | It takes over the game's input or presses keys for you, so the game may do things you didn't press. |
| G6 | Yes | Changes other plugins | Critical | puzzle | It changes another plugin or tool, which can stop that one working the way its own author intended. |
| G9 | Yes | Starts with Windows | Critical | rocket | It runs every time Windows starts, even when you aren't playing. |
| C1 | Yes | Decrypts protected content | Critical | key-round | It removes the protection creators put on their models or textures. |
| C2 | Yes | Copies others' content | Critical | copy | It saves copies of other creators' models or textures as files on your PC. |
| C3 | Yes | Shares unprotected content | Critical | lock-open | It shares other creators' content with its protection removed. |
| T7 | No | No open-source licence (not when T1 is No) | Critical | scale | There is no open-source licence, so others may not be allowed to fix, fork or keep it alive if the author stops. |
| T1 | No | Closed source | Critical | file-lock | The source isn't public, so nobody outside can read what the release does; the card relies on what the files themselves show. |
| T2 | Yes | Docs contradict code | Critical | book-x | Its docs describe something its code doesn't do, on a point these questions ask about, so the docs aren't a reliable guide there. |
| T3 | No | Not traced to source (not when T1 is No or T4 is Yes) | Critical | route-off | The release wasn't built in public from tagged source, so the files can't be tied to the source that is public. |
| T4 | No | Covered by "Not traced to source", "Not signed or traceable" or "Closed source": the answer is also No when there is no public source to rebuild from | None |  |  |
| T6 | No | Dependencies not pinned | Critical | pin-off | Its dependencies aren't pinned to exact versions, so a rebuild can pull in different code than the release used. |
| T1 | Yes | Open source | Positive | code-xml | Anyone can read the full source of this release. |
| T3 | Yes | Built from public source | Positive | workflow | The release was built in public from tagged source, so the files can be tied to that source. |
| T4 | Yes | Rebuild matches source | Positive | git-compare | The release was rebuilt from its source and gave the same files. |
| P5 | Yes | Code-signed | Positive | badge-check | The files are code-signed, so you can confirm who published them and that they weren't changed since. |
| D1 | No | No internet connections | Positive | wifi-off | It makes no internet connections, so nothing leaves your PC through it. |
<!-- /rules/scoring.yaml -->
