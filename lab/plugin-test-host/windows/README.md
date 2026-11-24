# The test host on Windows

The "Analyse a tool" workflow runs the tool under test on a throwaway Windows machine (a GitHub-hosted `windows-2025`
runner), never where Claude runs: its plugins in the real game first (`../../real-game/README.md`, "On Windows"), then
what the real game can't do on cue and its apps here, in the test host. The machine gets no keys, no repository credentials and no write access;
only its evidence leaves it. Cloud sessions run both under Wine (`../README.md`, `../../real-game/README.md`) for quick runs and extra key presses.

## How a run goes

1. Claude's short first pass reads the release's licence and readme and writes **the plan** (below). It plans no runs
   when the licence forbids analysis (rule 6). `tools/check_plan.py` checks the plan before anything runs.
2. A Linux job builds `mxbikes.exe`, `gpbikes.exe` and `victim.dlo` from `../src/` with `../src/build.sh`, and another
   downloads the release files (`tools/fetch_release.py`: a plain https link, a MEGA file link or a file in a MEGA folder), checks each against
   the plan's SHA-256 and hands them on with a `release.json` listing them.
3. The Windows job runs the plan's real-game runs (`../../real-game/windows/run.ps1`, with the bare demo as the
   baseline), then its cases and apps with `run.ps1`. It downloads Process Monitor and Mesa's software OpenGL (llvmpipe, the renderer the Wine
   lab uses), and, when the plan has apps, Microsoft's .NET Desktop Runtimes 6, 7 and 9 (the runner has 8, 10 and 11), so a
   .NET app runs on the version it was built for; `machine.txt` lists the runtimes, takes the release files from the job above (`-Release`), each checked again against its SHA-256. Then, for each run, it:
   - makes a fresh run folder with the host, `victim.dlo`, the Mesa DLLs, the game's `plugins` folder (a folder named
     `plugins` in a release file, else the folder that holds its `.dlo` files) and the unpacked release under `release\`;
   - adds a firewall rule that blocks every program in the run folder from the internet, and logs dropped connections;
   - records it with Process Monitor and stops an app after its time, with every process it started.
4. The full analysis reads the evidence and copies each run's folder to `../../results/<card>/<run>-windows/`.

## The plan

```json
{
 "game": "mxbikes",
 "licence": "allows",
 "files": [{"url": "https://.../tool-1.0.zip", "sha256": "<64 hex>"}],
 "realgame": [{"name": "ride", "ride": 60, "keys": [[15, "F4"], [30, "ctrl+r"]]}],
 "cases": [{"name": "hotkeys", "args": ["--frames", "500", "--key", "120", "0x73", "--crash", "plugins\\tool.dlo", "victim.dlo"]}],
 "apps": [{"name": "app", "exe": "tool-1.0.zip\\Tool\\Tool.exe", "args": [], "seconds": 60}],
 "note": "Why nothing runs, when nothing does"
}
```

- `game`: `mxbikes` or `gpbikes` (a GP Bikes plugin runs in `gpbikes.exe`).
- `licence`: what the release's licence says about analysing it: `allows`, `forbids` (rule 6: nothing runs) or `unclear`.
  The run uploads release files VirusTotal has no record of only on `allows` (CLAUDE.md, "VirusTotal").
- `files`: the files players download, by URL and SHA-256 (at most 5): a direct https link, a MEGA file link
  (`https://mega.nz/file/<id>#<key>`) as the tool's page gives it, or a file in a MEGA folder
  (`https://mega.nz/folder/<id>#<key>/file/<handle>`, as `tools/fetch_release.py list <folder link>` prints it). Each is saved under its name (a MEGA file under its
  own), with characters other than letters, digits, spaces and `._+()-` replaced by `_`; `rel\<that name>\` holds it unpacked.
- `realgame`: a run of the plugins in the real game per sensible way to use them: ride for `ride` seconds (10 to 300)
  and press each key (xdotool's names, as `games.json` uses them) at its second. The bare demo runs first as `baseline`,
  a name no run may take. At most 4.
- `cases`: the host's arguments for each plugin run (`../README.md`, "Running a plugin"), with paths inside the run
  folder: `plugins\<file>.dlo`. At most 6.
- `apps`: an `.exe` that starts without an account or the real game, by its path under `release\` (`<release file
  name>\<path inside it>`), run for `seconds` (10 to 300) and then stopped. At most 3.

## Evidence

In `real-game/` and `test-host/`, each with its `machine.txt`: one folder per run, in the layout `../src/collect.sh` gives, plus what only Windows shows:

| File | What it holds |
|---|---|
| `host.log` | What the host saw (hooks, plugin output, clean exit); for an app, its own output; for the real game, the game and the steps it reached, with their times |
| `files.diff` | Files the run added (`>`) or removed (`<`) in the run folder |
| `network.txt` | Internet connections the run's processes tried (Process Monitor) and the firewall's drops for them; attempts, not traffic |
| `outside.txt` | Files the run's processes wrote outside the run folder |
| `registry.txt` | Registry keys and values the run's processes wrote |
| `procmon.txt` | Every distinct operation of the run's processes with its count, except reads, queries and closes |
| `loaded.txt` | The DLLs the run's processes loaded |
| `raw/procmon.csv.gz` | Every Process Monitor event of the run's processes, unfiltered: what the files above are read from. Other processes on the machine are left out |
| `raw/firewall.log.gz` | The Windows firewall's whole log up to the end of the run |
| `plugins.sha256` | The programs in the run folder |
| `shot_*.png` | The host's screenshots, or the real game's after each step and key |

The run's processes are the one started and every process it started (Process Monitor's Process Create events).
`machine.txt`, beside the run folders, names the machine, the OpenGL renderer (for the real game, also the demo and the
screen size), Process Monitor's SHA-256 (Sysinternals publishes it at one moving URL, so it is recorded, not pinned) and
the release files' SHA-256.

## Limits

- A virtual machine with no GPU: OpenGL is Mesa's software renderer, so it's Windows, but not Windows on a real GPU.
- Keys are sent with `SendInput` to the host's window; a plugin that reads input another way may not see them.
- The firewall blocks the programs in the run folder. A program started from elsewhere (a system tool a plugin launches)
  isn't blocked, but its connections are still in `network.txt`, since it is one of the run's processes.
- Windows writes the firewall log late, so a drop can be missing from it; Process Monitor's record is the one to trust.
