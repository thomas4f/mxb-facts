# Real game: running plugins in the game itself

Every analysis runs each game plugin (`.dlo`) here first: in the public demo of MX Bikes or GP Bikes, offline, clicked through to a track and ridden. Cloud sessions run it under Wine (`run.sh`); the "Analyse a tool" workflow runs it on a throwaway Windows machine (`windows/run.ps1`, "On Windows" below). The fake game in [`../plugin-test-host/`](../plugin-test-host/README.md) stays for what the real game can't do on cue (a crash at a given frame, the bystander plugin's checks) and for apps.

## What it is

- `games.json` names each game's demo: its download URL, its SHA-256, the exe, and the menu steps that reach a track. The demos are PiBoSo's public downloads; nothing of the game goes into this repository. The run downloads the installer once into `cache/` (which git ignores), checks it against its SHA-256 and unpacks it with 7-Zip (the installers are self-extracting zips). We only run the game: its data files (`.pkz`) are never unpacked and nothing of it is decompiled.
- `run.sh` makes a fresh run folder (the game's small files copied, its `.pkz` files linked from the cache, the plugins under test in its `plugins` folder, a fresh copy of the test host's Wine prefix) and runs the game inside `unshare -n` (no network at all), on a virtual 1280x720 screen (Xvfb), traced with `strace -f` and `WINEDEBUG=+loaddll`.
- It clicks through the menus as `games.json` lists them (Demo, Testing, Start, To Track). Each step waits for the screen to settle (or for a button's colour, `until`), and clicks again when the screen didn't change, three tries at most. On the track it holds the throttle for `--ride` seconds and presses each `--key` at its second, with a screenshot after each.
- Environment: the test host's (Wine 9.0 64-bit, Mesa llvmpipe software OpenGL, Xvfb), which `../plugin-test-host/setup.sh` installs; `run.sh` runs it when the prefix is missing and adds `xdotool` and ImageMagick.

## Running a plugin

1. Download the release files players get, by the URL and SHA-256 named on the card.
2. Run the bare demo once, as the baseline: `lab/real-game/run.sh <game> baseline <card-slug>`, where `<game>` is `mxbikes` or `gpbikes`.
3. Run it with the plugin: `lab/real-game/run.sh <game> <case> <card-slug> --ride 60 --key 20 F8 <file>.dlo [more files or folders]`. Files and folders go into the game's `plugins` folder as given. Key names are `xdotool`'s (`F8`, `ctrl+r`).
4. The evidence is in `lab/results/<card-slug>/<case>/`, laid out as the test host's `collect.sh` does: `host.log` (game, installer SHA-256, the steps with their times), `files.diff` (files added or removed in the game folder and the Wine user folders), `network.txt` (internet sockets, from strace), `loaded.txt` (DLLs Wine loaded), `plugins.sha256`, a screenshot after each step and key, and `raw/` with the originals, compressed (`strace.log.gz`, `wine.log.gz` and `game.log.gz`, everything the game printed). Commit that folder and link its files from the card.

Read the network and file lines against the baseline: the demo itself tries DNS lookups (to 8.8.8.8 and 8.8.4.4) and writes its own profile and log files, so only what the plugin's run adds is the plugin's.

The first run downloads the demo (MX Bikes 2.4 GB, GP Bikes 590 MB) and takes a few minutes more; later runs reuse the cache. A run takes about 3 to 5 minutes.

## On Windows

In the "Analyse a tool" workflow, a throwaway `windows-2025` runner with no keys runs the plan's `realgame` entries (`../plugin-test-host/windows/README.md`, "The plan") with `windows/run.ps1`:

- The demo's installer comes from the Actions cache, keyed by its SHA-256, or is downloaded and checked first; the cache is saved before any plugin runs, and `run.ps1` checks the installer again.
- The game runs full screen at 1280x720 with Mesa's software OpenGL (llvmpipe) beside `mxbikes.exe`, under Process Monitor, with an outbound firewall block on every program in the run folder. Clicks and keys go through `SendInput` (keys by scan code) to the game's window, brought to the front first.
- The bare demo runs first as `baseline`, ridden as long as the longest run; then each run gets a fresh game folder with the release's plugins.
- The evidence has the layout of the Windows test host (`network.txt` from Process Monitor and the firewall's drops, `outside.txt`, `registry.txt`, `procmon.txt`, `raw/` and the rest), plus `host.log` with the steps and a screenshot after each step and key. The analysis copies each run's folder to `../results/<card>/<run>-windows/`.

A run takes about 4 minutes; the first one with an empty cache also downloads the demo.

## Limits

- It's the demo, pinned to one version (`games.json`), not the full game: content behind the full version (online play, other tracks and bikes) can't be reached, and the game never gets a network.
- Neither Wine nor the Windows runner is Windows on a real GPU (both use Mesa's software OpenGL), and frame times are meaningless: say so on the card.
- The clicks go to fixed places at 1280x720. A new demo version can move a button: update its step in `games.json` and the SHA-256 together, and check the screenshots.
- Only what the run reaches is seen: a plugin's code for a race, a crash or a menu the run doesn't open isn't exercised here (use the test host's `--crash`, or say so under "Limits of this analysis").

Run it only in a throwaway environment, never with real accounts, keys or a real game install, and never on a tool whose licence forbids analysis (see `CLAUDE.md`).
