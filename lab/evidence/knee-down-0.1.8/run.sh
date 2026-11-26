#!/usr/bin/env bash
# Knee Down 0.1.8 (no licence found; no public source: commands on the release files only).
# The folder holds KneeDown-preset.exe and latest.yml from the GitHub release v0.1.8
# (https://github.com/gsv-r/knee-down/releases/tag/v0.1.8). This script unpacks, without running anything: the NSIS installer
# with 7-Zip into nsis/, the app archive inside it (app-64.7z) into app/, and the app's own code (app/resources/app.asar, an
# Electron archive) with asar.py into asar/. The app's code is JavaScript as built (not minified in out/main and out/preload;
# minified in out/renderer), so the searches read it directly; line numbers are those of the unpacked files.
# Needs 7-Zip (7z), GNU binutils (objdump, strings) and file. The public-page commands fetch the pages as they are when run;
# the committed output is from the card's date.
. "$(dirname "$0")/../ev.sh"
(cd "$R" && rm -rf nsis app asar && 7z x -y -onsis KneeDown-preset.exe >/dev/null && 7z x -y -oapp 'nsis/$PLUGINSDIR/app-64.7z' >/dev/null \
  && python3 -I "$OUT/../asar.py" app/resources/app.asar asar)
M=asar/out/main/index.js
ev files "sha256sum KneeDown-preset.exe latest.yml 'nsis/\$PLUGINSDIR/app-64.7z' 'nsis/\$R0/Uninstall KneeDown.exe' app/KneeDown.exe app/resources/app.asar app/resources/elevate.exe app/resources/app-update.yml"
ev file "file KneeDown-preset.exe 'nsis/\$R0/Uninstall KneeDown.exe' app/KneeDown.exe app/resources/elevate.exe; 7z l KneeDown-preset.exe | grep -E 'SubType|app-64|Uninstall'"
# Every program file in the release: SHA-256 and type (data files such as .pak, locales and images left out), and the
# native modules (.node) in the app archive (none).
ev bundled "find nsis app -type f \\( -iname '*.dll' -o -iname '*.exe' -o -iname '*.node' \\) | sort | while read f; do sha256sum \"\$f\"; file -b \"\$f\"; done; echo '.node files in app.asar:'; find asar -name '*.node' | wc -l"
# Code signing: the Security (certificate) directory of the installer, the uninstaller, the app and elevate.exe.
ev signature "for f in KneeDown-preset.exe 'nsis/\$R0/Uninstall KneeDown.exe' app/KneeDown.exe app/resources/elevate.exe; do echo \"\$f\"; objdump -p \"\$f\" | grep -E 'file format|Security Directory'; done"
# What is packed: the Electron and Chromium versions in KneeDown.exe, the app's package.json, and the versions of the
# packages it ships.
ev versions "strings app/KneeDown.exe | grep -m1 -oE 'Chrome/[0-9.]+ Electron/[0-9.]+'; cat asar/package.json; echo; for p in asar/node_modules/*/package.json asar/node_modules/@*/*/package.json; do printf '%s ' \"\${p#asar/node_modules/}\"; grep -m1 -oE '\"version\": *\"[^\"]+\"' \"\$p\"; done"
# The updater: its settings, the update feed it reads, the file check, and the install ID it sends.
ev update "cat app/resources/app-update.yml; echo; echo '== latest.yml'; cat latest.yml; echo '== the app (out/main/index.js)'; grep -nE 'autoUpdater\\.(autoDownload|autoInstallOnAppQuit|checkForUpdates|downloadUpdate|quitAndInstall)|CHECK_INTERVAL_MS =|did-finish-load|startPeriodicChecks\\(\\);|if \\(!app.isPackaged\\) return' $M; echo '== electron-updater: NsisUpdater.js (signature check only with a publisherName)'; sed -n '50,57p;84,100p' asar/node_modules/electron-updater/out/NsisUpdater.js; echo '== electron-updater: AppUpdater.js (install ID header, .updaterId)'; sed -n '386,387p;501,519p' asar/node_modules/electron-updater/out/AppUpdater.js; echo '== electron-updater: sha512 check of the download'; grep -n 'sha512' asar/node_modules/electron-updater/out/AppUpdater.js asar/node_modules/electron-updater/out/providers/GitHubProvider.js | head -5"
# The update button in the window: it appears when a version is available; a click downloads, then installs and restarts.
ev update-ui "grep -oE '.{0,40}function b2\\(n,r,o\\).{0,200}' asar/out/renderer/assets/index-*.js; grep -oE 'g\\?k.jsx\\(za,\\{variant:\"ghost\",className:z2,onClick:c,title:.{0,140}' asar/out/renderer/assets/index-*.js; grep -oE 'const h=_.useCallback\\(\\(\\)=>\\{c\\(!0\\),s.current=!0.{0,90}' asar/out/renderer/assets/index-*.js"
# Every web address in the app's own code (main, preload, renderer), with counts.
ev urls "grep -ohE 'https?://[a-zA-Z0-9._/-]+' asar/out/main/index.js asar/out/preload/*.js asar/out/renderer/*.html asar/out/renderer/assets/*.js | sort | uniq -c | sort -rn"
# Network calls in the app's own code: Electron's net, fetch, XMLHttpRequest, WebSocket, sockets, servers; the window's
# content policy; links opened in the browser.
ev network "grep -nE 'net\\.(fetch|request)|fetch\\(|XMLHttpRequest|WebSocket|createServer|listen\\(|require\\(\"(http|https|net|dgram)\"\\)|from \"(http|https|net|dgram)\"' asar/out/main/index.js asar/out/preload/*.js; echo '== renderer'; grep -cE 'XMLHttpRequest|new WebSocket|sendBeacon' asar/out/renderer/assets/*.js; echo '== content policy'; grep -h -A1 'Content-Security-Policy' asar/out/renderer/*.html; echo '== links opened in the browser'; grep -nE 'shell\\.openExternal|setWindowOpenHandler' $M; grep -oE 'const dE=\"[^\"]+\"|onClick:\\(\\)=>window.open\\(dE,\"_blank\"\\)' asar/out/renderer/assets/index-*.js"
# Where it reads: Steam's registry value and library files, the game's profiles and mods folders, global.ini.
ev reads "grep -nE 'STEAM_REGISTRY_QUERY =|LIBRARY_FOLDERS_FILE =|appmanifest_|MODS_PATH =|PROFILES_PATH =|GLOBAL_INI_FILENAME =|GAME_APP_ID =|readFileSync\\(|function findSteamPath|function findGameInLibraries|function parseProfileInfo' $M"
# Every place its main code writes, renames or deletes a file or folder.
ev writes "grep -nE 'writeFile(Sync)?\\(|mkdir(Sync)?\\(|rename(Sync)?\\(|\\.rm\\(|rmSync|unlink|copyFile|fs\\\$1\\.link' $M"
# What it writes into the game's mods folder at each start: a folder per .pkz mod, folders per paint, metadata.json, a
# track preview.png, and a rendered preview.png per bike paint; and when a paint preview counts as fresh.
ev mods-writes "sed -n '2111,2124p;2143,2163p;2236,2257p;2329,2368p;4141,4165p;4228,4236p;4278,4284p' $M; echo '== at start'; sed -n '4928,4945p' $M"
# practice.ini in the game folder, and the game launch through Steam.
ev launch "grep -nE 'PRACTICE_LAUNCH_ARGS =|GAME_PROCESS_NAME =|PRACTICE_INI_FILENAME =' $M; sed -n '1258,1275p;1540,1563p;4583,4587p' $M; grep -nE 'persistPracticeIni\\(\\);' $M | head -3"
# The profile page: renaming the profile folder, profile.ini's name and race number, global.ini's lastprofile and nickname,
# and the reset that clears them.
ev profile "sed -n '558,574p;575,612p;647,657p;1565,1573p' $M; grep -nE 'ipcMain.handle\\(\"(profiles:save|launcher:reset)\"' $M"
# Mod archives (.pkz): it reads plain ZIP entries only and stops at encrypted ones; which entries it reads.
ev pkz "grep -nE 'Encrypted PKZ|plain ZIP only|function isWantedName|bn.endsWith\\(\".edf\"\\) \\|\\||function looksLikeEdf|function readPackedLayer|function readPaint|function gatherTyreFiles|PREVIEW_WIDTH =|PREVIEW_HEIGHT =' $M"
# Things not in its main code: Windows start-up, global shortcuts, the registry beyond the one reg query, other processes,
# crash reporting, native modules, code from the internet.
ev absent "grep -nE 'globalShortcut|setLoginItemSettings|openAtLogin|crashReporter|uncaughtException|WriteProcessMemory|OpenProcess|robotjs|sendInputEvent|reg add|reg delete|HKEY_LOCAL_MACHINE|eval\\(|new Function\\(|ffi|\\.node\"' $M asar/out/preload/*.js; echo '== child processes started (all)'; grep -nE 'execSync\\(|execAsync\\(|exec\\(|spawn\\(|execFile\\(' $M"
# Shop, payment and donation words in the app's own code and window.
ev money "grep -oiE '.{0,30}(donat|ko-?fi|patreon|paypal|buymeacoffee|premium|purchase|subscription|licen[cs]e key).{0,30}' asar/out/main/index.js asar/out/preload/*.js asar/out/renderer/assets/*.js"
# Licence and credit files shipped: Electron's and Chromium's, and each package in app.asar; licence comments in the
# window's bundled code (React and its other packages are bundled there).
ev thirdparty "ls app | grep -iE 'licen'; echo '== packages in app.asar with a licence file'; find asar/node_modules -maxdepth 3 -iname 'licen[cs]e*' | wc -l; echo '== packages in app.asar'; find asar/node_modules -maxdepth 2 -name package.json | wc -l; echo '== React in app.asar'; ls asar/node_modules | grep -xE 'react|react-dom' ; echo '== licence comments in the window code'; grep -lE '@license|Copyright' asar/out/renderer/assets/*.js; echo '== React in the window code'; grep -oE 'react.dev/errors' asar/out/renderer/assets/*.js | sort | uniq -c"
# The release page and the public repository (GitHub API): assets with their published digests, the tag's commit, every
# file of the repository at that commit, its licence and its history.
ev release "curl -sS https://api.github.com/repos/gsv-r/knee-down/releases/tags/v0.1.8 | python3 -I -c 'import json,sys;r=json.load(sys.stdin);print(r[\"tag_name\"],r[\"name\"],r[\"published_at\"],\"target:\",r[\"target_commitish\"]);[print(a[\"name\"],a[\"size\"],a[\"digest\"]) for a in r[\"assets\"]];print(r[\"body\"])'"
ev repo "curl -sS https://api.github.com/repos/gsv-r/knee-down/git/refs/tags/v0.1.8 | python3 -I -c 'import json,sys;print(\"tag v0.1.8 ->\",json.load(sys.stdin)[\"object\"][\"sha\"])'; curl -sS 'https://api.github.com/repos/gsv-r/knee-down/git/trees/27abfcc757fcbc726678b50ea8c6240fa6863203?recursive=1' | python3 -I -c 'import json,sys;[print(t[\"type\"],t[\"path\"]) for t in json.load(sys.stdin)[\"tree\"]]'; curl -sS https://api.github.com/repos/gsv-r/knee-down | python3 -I -c 'import json,sys;r=json.load(sys.stdin);print(\"description:\",r[\"description\"]);print(\"license:\",r[\"license\"])'; curl -sS 'https://api.github.com/repos/gsv-r/knee-down/commits?per_page=100' | python3 -I -c 'import json,sys;[print(c[\"sha\"],c[\"commit\"][\"committer\"][\"date\"],c[\"commit\"][\"message\"].splitlines()[0]) for c in json.load(sys.stdin)]'; curl -sS 'https://api.github.com/repos/gsv-r/knee-down/releases?per_page=100' | python3 -I -c 'import json,sys;[print(r[\"tag_name\"],r[\"published_at\"]) for r in json.load(sys.stdin)]'"
ev readme "curl -sS https://raw.githubusercontent.com/gsv-r/knee-down/27abfcc757fcbc726678b50ea8c6240fa6863203/README.md"
# Its gpb-mods.com page, tags removed, the lines the card quotes.
ev gpb-mods "curl -sSL https://gpb-mods.com/knee-down-launcher/ | python3 -I -c \"import html,re,sys;t=sys.stdin.read();t=re.sub(r'(?s)<(script|style).*?</\\\\1>','',t);t=re.sub(r'<br\\\\s*/?>|</p>|</li>|</h[0-9]>|</div>','\\\\n',t);t=re.sub(r'<[^>]+>','',t);[print(l.strip()) for l in html.unescape(t).splitlines() if l.strip()]\" | sed -n '/^Installation Guide/,/^Mod Rating/p'"
