# Analysis queue

Which tools get a card:

- every tool someone requests (an issue), in the order requested: that part is a rule;
- beyond requests, every other tool on mxb-mods.com and gpb-mods.com that runs on a player's PC (a plugin, an app, an installer), in the order the maintainer picks: that part is a choice, and this file shows it.

Every tool here has an entry in `registry/tools.json` (its slug is the Registry column), so the weekly "Update inventory" run follows its page and its newest release, and "Analyse a tool" offers it. Authors aren't told before their tool's card is published, except about a security problem (rule 9). They can send a correction afterwards, like anyone else.

## Requests

Requested tools and releases, oldest first. Link the issue; remove the line when the card is published.

| Tool | Version | Issue | Note |
|---|---|---|---|
| GP Bikes Content Manager (GP Bikes) | The newest when it runs | Requested by the maintainer, 20 Nov 2026 | [gpb-mods.com page](https://gpb-mods.com/gp-bikes-content-manager-by-fixxer-1001/), by FIXXER 1001. A large desktop app (C#/WPF). Registry `gpb-content-manager`. On hold: too big for now (the maintainer's choice) |
| Pitbox (GP Bikes) | [v3.0.4](https://github.com/cristianboni22/pitbox/releases/tag/v3.0.4) | Requested by the maintainer, 23 Nov 2026 | [gpb-mods.com page](https://gpb-mods.com/pitbox-launcher-setup-assistant-hud-for-gp-bikes/), by GitHub user [cristianboni22](https://github.com/cristianboni22). A launcher app with an in-game HUD. GitHub [cristianboni22/pitbox](https://github.com/cristianboni22/pitbox). Registry `pitbox`. On hold after two failed runs (the maintainer's choice) |

## To analyse

In the order the maintainer chose (24 Nov 2026): by its weight, the downloads its mods-site page shows, halved for each full year since the page was last updated, so a popular tool comes first and one nobody has updated in years drops back. **Next** overrides the order. Counts and dates read 24 Nov 2026; the licence is read when the tool is analysed. Remove a line when its card is published.

| # | Tool | Game | Author | Page | Hosted on | Downloads | Page updated | Registry | Note |
|---|---|---|---|---|---|---|---|---|---|
| 1 | iNsane's 3D Viewer | MX Bikes | insane | [mxb-mods.com](https://mxb-mods.com/insanes-3d-viewer/) | mxb-mods.com | 11,676 | 2025-01-20 | `insanes-3d-viewer` | Also posted on gpb-mods.com. Zip on file (`dmkrtz3DViewer.exe`, zip SHA-256 `abef11875615b3bea602c07b86a0c2d553cf1b4a69f808643b6bffc63fa2c317`) |
| 2 | MXB App | MX Bikes | Frost (Frostn1) | [mxb-mods.com](https://mxb-mods.com/mxb-app-one-click-mod-manager/) | GitHub ([Frostn1/mxb-app](https://github.com/Frostn1/mxb-app)) | 5,145 | 2026-11-12 | `mxb-app` |  |
| 3 | Resolute MXB Track Builder Helper | MX Bikes | Resolute Kraken | [mxb-mods.com](https://mxb-mods.com/resolute-mxb-track-builder-helper/) | MediaFire | 4,602 | 2025-07-07 | `resolute-track-builder-helper` | Zip on file (MSI installer, zip SHA-256 `1344d35ad68fabddbf128cf3e881252d13d1d50d03b0da18732caaeda19f5e55`) |
| 4 | PaintHub | MX Bikes | OhTea | [mxb-mods.com](https://mxb-mods.com/painthub/) | MediaFire | 1,688 | 2026-02-07 | `painthub` | Zip on file |
| 5 | MXB Studio | MX Bikes | TannyGlover | [mxb-mods.com](https://mxb-mods.com/mxb-studio-create-your-entire-mx-bikes-track-in-one-app/) | MediaFire | 1,506 | 2026-11-21 | `mxb-studio` | Homepage [mxbstudio.com](https://mxbstudio.com) |
| 6 | PitKit MX Bikes Mod Manager | MX Bikes | bobby-rust | [mxb-mods.com](https://mxb-mods.com/pitkit-mx-bikes-mod-manager/) | GitHub ([bobby-rust/Pitkit](https://github.com/bobby-rust/Pitkit)) | 1,765 | 2025-06-05 | `pitkit` |  |
| 7 | MX Bike Mod Manager | MX Bikes | Noxo | [mxb-mods.com](https://mxb-mods.com/mx-bike-mod-manager/) | Google Drive | 863 | 2026-03-11 | `mx-bike-mod-manager` |  |
| 8 | ProjectGPB2 | GP Bikes | X1mk_Z3 | [gpb-mods.com](https://gpb-mods.com/projectgpb2-2/) | gpb-mods.com | 845 | 2026-11-12 | `projectgpb2` |  |
| 9 | MX Bikes Mods Cleaner | MX Bikes | nikomouk | [mxb-mods.com](https://mxb-mods.com/mx-bikes-mods-cleaner/) | MediaFire | 794 | 2025-12-26 | `mods-cleaner` |  |
| 10 | MaXHUD (GP Bikes) | GP Bikes | HornetMaX | [gpb-mods.com](https://gpb-mods.com/maxhud/) | Mega | 6,044 | 2023-08-21 | `maxhud-gpb` | The GP Bikes build of MaXHUD, uploaded by Zonta_84 |
| 11 | MXB Ragdoll | MX Bikes | BoredDev / mxbikesmods | [mxb-mods.com](https://mxb-mods.com/mx-bikes-ragdoll-v1-0-2/) | mxb-mods.com | 687 | 2026-10-30 | `mxb-ragdoll` |  |
| 12 | MXPulse Alpha | MX Bikes | daf0707pro-lgtm | [mxb-mods.com](https://mxb-mods.com/mxpulse/) | GitHub ([daf0707pro-lgtm/MXPulse](https://github.com/daf0707pro-lgtm/MXPulse)) | 607 | 2026-08-01 | `mxpulse` |  |
| 13 | Drag n Drop Creator | MX Bikes | bh5o | [mxb-mods.com](https://mxb-mods.com/drag-n-drop-creator/) | MediaFire | 581 | 2026-03-05 | `drag-n-drop-creator` |  |
| 14 | MxTuner | MX Bikes | dfmc_dadogamer91 | [mxb-mods.com](https://mxb-mods.com/danj/) | MediaFire | 478 | 2026-01-19 | `mxtuner` |  |
| 15 | Studio BW Skin Packer | MX Bikes | Phantomz | [mxb-mods.com](https://mxb-mods.com/studio-bw-skin-packer/) | MediaFire | 735 | 2025-05-14 | `studio-bw-skin-packer` |  |
| 16 | TrackRelief | MX Bikes | Lilian1134 | [mxb-mods.com](https://mxb-mods.com/trackrelief/) | GitHub ([Lilian1134/TrackRelief](https://github.com/Lilian1134/TrackRelief)) | 337 | 2026-10-21 | `trackrelief` |  |
| 17 | MX Ctrl | MX Bikes | itswillyferret | [mxb-mods.com](https://mxb-mods.com/mx-ctrl/) | MediaFire | 336 | 2026-06-04 | `mx-ctrl` |  |
| 18 | MXB Dropper | MX Bikes | KST Design | [mxb-mods.com](https://mxb-mods.com/mxb-dropper-v1/) | MediaFire | 221 | 2026-03-07 | `mxb-dropper` |  |
| 19 | MXB_Haptics_PS5 | MX Bikes | Sixze | [mxb-mods.com](https://mxb-mods.com/mxb_haptics_ps5/) | Google Drive | 209 | 2026-06-15 | `mxb-haptics-ps5` |  |
| 20 | Tyre changer Tool (MX Bike Tool) | MX Bikes | Buck3ts41 | [mxb-mods.com](https://mxb-mods.com/tyre-changer-tool/) | MediaFire | 817 | 2024-11-21 | `tyre-changer` |  |
| 21 | Performance Lab by LMG x JCD | MX Bikes | JahRacing | [mxb-mods.com](https://mxb-mods.com/performance-lab-by-lmg-x-jcd/) | GitHub ([JahRacing/Performance-Lab-by-LMG-x-JCD](https://github.com/JahRacing/Performance-Lab-by-LMG-x-JCD)) | 202 | 2026-09-24 | `performance-lab` | Filed under Bikes, Others on the site |
| 22 | MX Shortcuts | MX Bikes | itswillyferret | [mxb-mods.com](https://mxb-mods.com/140394-2/) | gofile.io | 347 | 2025-09-20 | `mx-shortcuts` |  |
| 23 | Resolute MXB Server Manager | MX Bikes | Resolute Kraken | [mxb-mods.com](https://mxb-mods.com/resolute-mxb-server-manager/) | MX Bikes forum | 1,348 | 2022-12-30 | `resolute-server-manager` |  |
| 24 | Knee Down | GP Bikes | gsv-r | [gpb-mods.com](https://gpb-mods.com/knee-down-launcher/) | GitHub ([gsv-r/knee-down](https://github.com/gsv-r/knee-down)) | 137 | 2026-10-19 | `knee-down` |  |
| 25 | Frost's Studio | MX Bikes | Frost (Frostn1) | [mxb-mods.com](https://mxb-mods.com/frosts-studio/) | GitHub ([Frostn1/frost-studio](https://github.com/Frostn1/frost-studio)) | 128 | 2026-11-12 | `frosts-studio` |  |
| 26 | Simhub Dash 2.0 | GP Bikes | Gonzo46 | [gpb-mods.com](https://gpb-mods.com/simhub-dash-2-0-public/) | Mega | 472 | 2024-08-17 | `simhub-dash-gpb` |  |
| 27 | MX/GP Bikes Server Manager by DazTeamRacing | MX Bikes | DazTeamRacing | [mxb-mods.com](https://mxb-mods.com/mx-gp-bikes-server-manager-by-dazteamracing/) | Mega | 115 | 2026-09-04 | `dazteamracing-server-manager` | Also posted on gpb-mods.com |
| 28 | MXBTT | MX Bikes | DankMaps | [mxb-mods.com](https://mxb-mods.com/mxbtt-com-the-weekly-time-trial-prize-money-racing-platform/) | GitHub ([DankMaps/MXBTT.com-Releases](https://github.com/DankMaps/MXBTT.com-Releases)) | 85 | 2026-08-27 | `mxbtt` | Also its plugin installer from [mxbtt.com](https://mxbtt.com): `MXBTT_Plugin_Setup.exe` on file (SHA-256 `13d0b6e92f4cd165303cdda60cf5bfce8f0e69db81ca21e8db74b00e0eab8047`) |
| 29 | MaxTM | GP Bikes | HornetMaX | [gpb-mods.com](https://gpb-mods.com/maxtm-v2-5/) | Mega | 481 | 2023-08-22 | `maxtm` | Telemetry tool, uploaded by Zonta_84 |
| 30 | Libpnt | MX Bikes | BatZupper | [mxb-mods.com](https://mxb-mods.com/libpnt/) | GitHub ([BatZupper/libpnt](https://github.com/BatZupper/libpnt)) | 56 | 2025-12-25 | `libpnt` | A code library for the paint file format |
| 31 | MXB Coach | MX Bikes | Frost (Frostn1) | [mxb-mods.com](https://mxb-mods.com/mxb-coach/) | GitHub ([Frostn1/mxb-coach](https://github.com/Frostn1/mxb-coach)) | 42 | 2026-11-12 | `mxb-coach` |  |
| 32 | Frost Converter | MX Bikes | Frost (Frostn1) | [mxb-mods.com](https://mxb-mods.com/fbx3edf/) | GitHub ([Frostn1/frost-converter](https://github.com/Frostn1/frost-converter)) | 32 | 2026-11-13 | `frost-converter` |  |
| 33 | MX Bikes Server Configurator | MX Bikes | insane | [mxb-mods.com](https://mxb-mods.com/mx-bikes-server-configurator/) | mxb-mods.com | 940 | 2020-11-07 | `mxb-server-configurator` |  |
| 34 | FrostMod | MX Bikes | Frost (Frostn1) | None | GitHub ([Frostn1/frostmod](https://github.com/Frostn1/frostmod)) | None | None | `frostmod` | Not on the mods sites |

## On hold

Tools that wait for something before they are analysed or published.

| Tool | Game | Author | Page | Registry | Why |
|---|---|---|---|---|---|
| CoreMX | MX Bikes | rare621 | [mxb-mods.com](https://mxb-mods.com/coremx-your-mx-bikes-companion-app-2/) | `coremx` | Waits for the maintainer's go |
| Graphics Overhaul | MX Bikes | Finner24 | [mxb-mods.com](https://mxb-mods.com/graphics-overhaul-2/) | `graphics-overhaul` | Paused (the maintainer's choice) |
| GameFX+ | MX Bikes | Finner24 | [mxb-mods.com](https://mxb-mods.com/gamefx-2/) | `gamefx-plus` | Paused (the maintainer's choice) |
| Rider POV+ | MX Bikes | Finner24 | [mxb-mods.com](https://mxb-mods.com/rider-pov-2/) | `rider-pov-plus` | Paused (the maintainer's choice) |
| MXBMRP3 | MX Bikes | thomas4f | [mxb-mods.com](https://mxb-mods.com/mxbmrp3/) | `mxbmrp3` | The maintainer's own tool; waits for its next release (the maintainer's choice) |

## Not allowed

Tools whose licence or terms forbid reverse engineering, decompiling or AI analysis (rule 6). They are covered from public facts only, unless the author gives written permission.

| Tool | Game | Author | Page | Registry | Terms |
|---|---|---|---|---|---|
| MXB A-Kit Studio | MX Bikes | DankMaps | [mxb-mods.com](https://mxb-mods.com/mxb-a-kit-studio/) | `akit-studio` | [mxbtt.com/terms](https://mxbtt.com/terms), clause 6.3, forbids reverse engineering and decompiling (read 23 Nov 2026) |

Not listed: logo sheets, templates, guides, setups and other files that don't run, and web apps that run only in a browser (MXB Toolbox, Bodyshop). Plugins published only on the PiBoSo forum haven't been searched.

## To revisit

- **When VirusTotal lookups run.** The workflow runs by hand only. If lookups should also run on their own (on each card pull request, or weekly for every card), add those triggers to `.github/workflows/virustotal.yml`.
- **MaXHUD 2.2.7: its Caps Lock menu wasn't seen.** The menu shows while Caps Lock is on, so the real-game run's four presses ended with it closed before the screenshot, and the test host's draw list didn't change after its presses. A real-game run with an odd number of Caps Lock presses (a screenshot while it is on) would show it, and settle the G7 limit on `cards/maxhud-2.2.7.yaml`.
- **MXB Discord RPC (download of 6 Oct 2024): the plugin never ran.** The plan put `discord_game_sdk.dll` in `plugins`, as the zip lays it out, so the game didn't load the plugin. A real-game run with the library beside `mxbikes.exe` (as its readme says), once without a Discord app and once with a logged-out Discord app if the runner allows it, would show what the plugin and Discord's library do (files, start-up of Discord, the game closing) and settle the run limit on `cards/mxb-discord-rpc-2024-10-06.yaml`. T4 there is "Not checked": it needs a Windows build with Visual Studio 2022 (v143), and the release was built with the source's `#define CONSOLE` off.
- **MX Dirt Mod 1.7.1: none of its game code ran, and the rebuild is from Linux.** Both plugins switch themselves off unless `mxbikes.exe` is the Steam build in `SUPPORTED_EXE.txt` (a purchase), so the demo runs only show that. The installer, uninstaller and settings window (PowerShell) weren't run; a run of them on the throwaway Windows machine, with a dummy game folder, would show what they move. A rebuild with Zig 0.16.0 for Windows (it fails under Wine) would show whether the two differing runtime constants come from the build host.
- **HoleShot HUD v0.24.2: the program never ran beside the game, and the crash case didn't crash.** The three real-game runs reached the track, but they ran only the plugin, and the program ran on its own. A run of `Holeshot-HUD.exe` beside the demo with F8 pressed and "Browser Source", the Pit Board widget and "MX Bikes menus" switched on, and "Check for updates" off, would show the pitboard override, the menu pack, the local server's answer to another site's Origin and the startup without a GitHub request, and settle the run limits on `cards/holeshot-0.24.2.yaml`; the test host's `--crash` case logged no crash, so a case that does would show the crash handler (G8). A click-through of Setup and its uninstaller with a dummy game folder, and an unpacker that reads Inno Setup 6.7.0, would cover Setup (P6, P8). T4 there is "Not checked": it needs a Windows build with Visual Studio 2022 and Rust.
- **MXB DualSense Support 1.1.0: the HUD plugin never ran, and no button was clicked.** The plugin (`mxbds_hud64.dlo`) is packed inside the program, not in the zip, and the plan's real-game runs and test-host cases load plugins only from the unpacked release, so it wasn't run. A plan step that takes a file unpacked with `tools/carchive.py` (or a run of the app's `--install-hud` against the demo's folder) would let it ride in the real game with the app sending HUD data, and settle the plugin limit on `cards/mxb-dualsense-1.1.0.yaml`. A click-through of Set up proxy_udp.ini, Install and Uninstall in-game HUD and the Ctrl+Shift+H and Ctrl+Shift+M hotkeys, with a dummy game folder, would settle the buttons limit there.
- **MX Bikes Setup Duper 0.1.8674.29660: the app never ran.** It needs Microsoft's .NET 6 Desktop Runtime, and the throwaway Windows machine had only .NET 8, 10 and 11, so .NET's host stopped before the app's code ran. A run with the .NET 6 Desktop Runtime installed (or `DOTNET_ROLL_FORWARD=Major`), a dummy `Documents\PiBoSo\MX Bikes` with a profile, saved setups and a track mod, and clicks through Copy with Specific Track and All Tracks, would show the update check, the folders it reads and the copies, and settle the run limit on `cards/setup-duper-0.1.8674.29660.yaml` (P4, P7, D1, D6, D8, C5).

## Removed

Cards taken off the site, with the date and the reason, so a removal stays visible.

None yet.
- **Suspension Tuner 1.4.1: its installer wasn't unpacked or run.** `SuspensionTuner_Setup.exe` is Inno Setup 6.7, which innoextract 1.9 (the newest release) can't read. A tool that reads Inno Setup 6.7, or a run of the installer and its uninstaller on the throwaway Windows machine with a dummy game folder, would show what it installs, any licence page, its shortcuts and what uninstalling leaves, and settle the installer limit on `cards/suspension-tuner-1.4.1.yaml` (P6, P8, G9, T7). A run that clicks Start listening with a dummy `proxy_udp.ini` would show the rewrite the card reads from the app's constants (P4, G6).
