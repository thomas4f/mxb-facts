# Plugin test host: running plugins outside the game

A fake game that loads `.dlo` plugins and actually runs them. Plugins run in the real game first ([`../real-game/`](../real-game/README.md)); this host is for what the real game can't do on cue (a crash at a given frame, the bystander plugin's checks) and for apps. This page is the Wine lab that sessions use. The "Analyse a tool" workflow runs the same host on a throwaway Windows machine instead: see [`windows/README.md`](windows/README.md).

## What it is

- `mxbikes.exe` (from `src/host.cpp`) is a fake game; `gpbikes.exe` is the same host built with GP Bikes' struct layouts, for GP Bikes plugins. It is named `mxbikes.exe` so the plugins' module checks match. It opens a 1280x720 OpenGL window and draws a bumpy track, a red "bike" box and a 2D HUD the way an old fixed-function engine does (glFrustum/glLoadMatrixf 3D pass, then glOrtho 2D pass). It calls the PiBoSo plugin API with the struct layouts from `mxb_api.h` (or GP Bikes' `gpb_api.h`): Startup, DrawInit, EventInit, RunInit, RunStart, RunTelemetry every frame with a bike circling at 15 m/s, RaceTrackPosition and RaceVehicleData for 3 riders, Draw (it logs what a plugin draws whenever that changes), then RunStop, RunDeinit, EventDeinit, Shutdown, FreeLibrary. It can press keys with `SendInput` (`--key <frame> <vk>`; keys pressed a frame apart overlap, so `--key 100 0x11 --key 101 0x52` is Ctrl+R), click a string a plugin draws (`--click <frame> <text>`), set the crash flag halfway (`--crash`), and save screenshots.
- The host reports whether each GL pointer in its own import table, plus one global from `wglGetProcAddress`, is still the real `opengl32` address or now points into a plugin. It also draws a green box through GL pointers it keeps on the heap. That copies how plugins that draw with their own saved GL pointers work, so it shows whether that path is affected.
- `victim.dlo` (from `src/victim.cpp`) is a bystander plugin that keeps a global table of GL function pointers, as many plugins do. It reports whether anything changed them.
- Environment: Wine 9.0 (64-bit), Mesa llvmpipe (software OpenGL 4.5 compatibility), Xvfb, all inside `unshare -n` (no network at all), traced with `strace -f` and `WINEDEBUG=+loaddll`. Runner: `src/runcase.sh`.

## Limits

- It's not the real game. There are no PiBoSo shaders and no rider mesh, so anything that patches the game's shaders or needs the rider does nothing here, and addresses inside the real `mxbikes.exe` don't exist in this small host.
- Frame times are meaningless (CPU software rendering).
- Wine and Mesa are not Windows and a real GPU driver.
- The F-key panels open (logged), but the screenshots are taken before SwapBuffers, where the panels are drawn, so the panels don't show in them.

## Setting it up

Cloud sessions do this on their own: the session-start hook (`.claude/hooks/session-start.sh`) runs `setup.sh`. Anywhere else, run it yourself (Ubuntu 24.04, as root or with sudo):

```
lab/plugin-test-host/setup.sh
```

It installs Wine, MinGW, Xvfb and strace when missing, builds `mxbikes.exe`, `gpbikes.exe` and `victim.dlo` into `build/` with `src/build.sh`, makes the Wine prefix and runs a smoke test of each host with the bystander plugin only. It skips all of that when nothing changed since the last good run. Binaries and runs stay in `build/`, which git ignores.

`src/build.sh` fetches PiBoSo's `mxb_api.h` and PiBoSo's GP Bikes example `gpb_example.c`, whose struct definitions become `gpb_api.h`. They are PiBoSo's files, so they aren't kept here; `piboso.com` isn't reachable from cloud sessions, so they come from public repositories that carry them unchanged, pinned to a commit and checked by SHA-256.

## Running a plugin

1. Download the release files players get, by the URL and SHA-256 named on the card.
2. Put them in `build/run/<case>/plugins/`, laid out as in the game's `plugins` folder.
3. `S=lab/plugin-test-host/build lab/plugin-test-host/src/runcase.sh <case> --frames 400 --key 100 0x73 plugins/<file>.dlo victim.dlo`. Press the plugin's hotkeys with `--key <frame> <virtual-key code>`; `--crash` and `--helmet` cover crash and helmet-view code. For a GP Bikes plugin, set `GAME=gpbikes`; `WINEDEBUG_EXTRA=+xinput` also logs its controller calls.
4. `lab/plugin-test-host/src/collect.sh <case> <card-slug>` copies the evidence to `lab/results/<card-slug>/<case>/`: `host.log` (hooks seen, plugin output, clean exit), `files.diff` (files added or removed), `network.txt` (internet sockets opened, from strace), `loaded.txt` (DLLs Wine loaded), `plugins.sha256`, the screenshots as PNG, and `raw/` with the originals those are read from, compressed (`strace.log.gz`, the whole trace, and `wine.log.gz`, everything Wine printed), so a line on a card can be checked against what the run recorded. Commit that folder and link its files from the card.

An app or installer (`.exe`) runs the same way, offline: `unshare -n xvfb-run -a strace -f -o strace.log wine <file>` (as a regular user, `unshare -c -n`) with `WINEPREFIX=build/wpfx`, in its own folder under `build/run/`. To also see which host names it looks up, use `unshare -n -m src/runapp.sh <run folder> <app folder under drive_c> <exe>` (with `WINEPREFIX` set): it answers DNS on loopback with `src/dnslog.py`, which writes each name to `dns.log` and resolves none, so nothing leaves the PC. A 32-bit installer needs `wine32`, which `setup.sh` doesn't install; unpack it with 7-Zip and run the app from its folder instead.

Run it only in a throwaway environment, never with real accounts, keys or a real game install, and never on a tool whose licence forbids analysis (see `CLAUDE.md`).
