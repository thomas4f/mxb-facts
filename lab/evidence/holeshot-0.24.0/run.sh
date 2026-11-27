#!/usr/bin/env bash
# HoleShot HUD 0.24.0 (source public on GitHub, no licence file: the release files and the source).
# The folder holds the two files of https://github.com/LeadingTrendTechnologies/HoleshotHUD/releases/tag/v0.24.0, by
# their names: Holeshot-HUD-0.24.0-windows-x64.zip and HoleshotHUD-Setup.exe. This script unpacks the zip into zip/.
# The second argument is a checkout of https://github.com/LeadingTrendTechnologies/HoleshotHUD at
# 3ffdbf366023c19e1741178e39b5704a91728819 (tag v0.24.0), with its history.
# Needs GNU binutils, file, unzip, python3, innoextract (1.9) and, for release-api, the network.
. "$(dirname "$0")/../ev.sh"
(cd "$R" && rm -rf zip && mkdir zip && unzip -q -d zip Holeshot-HUD-0.24.0-windows-x64.zip)
ev files "sha256sum Holeshot-HUD-0.24.0-windows-x64.zip HoleshotHUD-Setup.exe zip/*"
ev file "unzip -l Holeshot-HUD-0.24.0-windows-x64.zip; file HoleshotHUD-Setup.exe zip/*"
# The installer is Inno Setup 6.7.0; innoextract 1.9 can't unpack that version (so its files weren't read from it).
ev setup "strings -n 8 HoleshotHUD-Setup.exe | grep -m3 'Inno Setup'; innoextract -l HoleshotHUD-Setup.exe"
# The scripts and README in the zip are the files of installer/ at the commit, apart from line endings (CRLF).
ev same-as-source "for p in 'Install.ps1:installer/install.ps1' 'Install.bat:installer/install.bat' 'Install-Plugin.ps1:installer/install-plugin.ps1' 'Uninstall.ps1:installer/uninstall.ps1' 'Uninstall.bat:installer/uninstall.bat' 'README.txt:installer/README.txt'; do a=\"\${p%%:*}\"; b=\"\${p##*:}\"; cmp -s <(tr -d '\\r' < \"zip/\$a\") <(tr -d '\\r' < \"\$SRC/\$b\") && echo \"same apart from line endings: zip/\$a = \$b at the commit\"; done"
# The overlay carries the plugin inside it, byte for byte, and writes it into the game (overlay/src/plugin.rs line 14).
ev embedded-dlo "python3 -I -c 'import sys; d=open(sys.argv[1],\"rb\").read(); p=open(sys.argv[2],\"rb\").read(); i=d.find(p); print(\"Holeshot-HUD.dlo (\", len(p), \"bytes) found whole inside Holeshot-HUD.exe at offset\", hex(i) if i >= 0 else None)' zip/Holeshot-HUD.exe zip/Holeshot-HUD.dlo"
for f in Holeshot-HUD.dlo Holeshot-HUD.exe; do
  ev $f.objdump-p "objdump -p zip/$f | awk '/^The Function Table|^PE File Base Relocations/{exit} 1'"
  ev $f.objdump-h "objdump -h zip/$f"
  ev $f.iat "iat.py zip/$f"
done
ev signature "objdump -p zip/Holeshot-HUD.exe zip/Holeshot-HUD.dlo HoleshotHUD-Setup.exe | grep -E 'file format|Security Directory'"
# What the plugin imports: the registry write, the crash handler, the shared memory, the key reads; and what it
# doesn't (network, code patching, other processes, starting programs).
ev imports-dlo "objdump -p zip/Holeshot-HUD.dlo | grep 'DLL Name'; iat.py zip/Holeshot-HUD.dlo | grep -E 'RegCreateKeyExW|RegSetValueExW|SetUnhandledExceptionFilter|CreateFileMappingW|MapViewOfFile|LoadLibraryW|GetProcAddress|VirtualProtect'; echo '--- absent:'; iat.py zip/Holeshot-HUD.dlo | grep -iE 'ws2_32|wsock|wininet|winhttp|urlmon|user32|WriteProcessMemory|ReadProcessMemory|OpenProcess|CreateRemoteThread|CreateProcess|ShellExecute|WinExec|AddVectoredExceptionHandler' || echo 'none of: network, user32 (no key reads), Read/WriteProcessMemory, OpenProcess, CreateRemoteThread, CreateProcess, ShellExecute, WinExec, AddVectoredExceptionHandler'"
# The plugin's three VirtualProtect calls (IAT slot 0x18003e2c0) all take the plugin's own .fptable section
# (0x18005e000, 0x100 bytes), a table of the statically linked MSVC C runtime, not the game's code.
ev virtualprotect "objdump -h zip/Holeshot-HUD.dlo | grep -E 'fptable'; objdump -d zip/Holeshot-HUD.dlo | grep -E '# 0x18003e2c0|# 0x18005e000'"
# The plugin's in-game HUD, layout editor and key reads (src/hud, src/layout.cpp) are built only with MXBO_INGAME_HUD=1.
ev plugin-build "grep -nE 'ClCompile Include|AdditionalDependencies' \"\$SRC/mxbo.vcxproj\""
ev imports-exe "iat.py zip/Holeshot-HUD.exe | grep -E 'RegSetValueExW|RegDeleteValueW|GetAsyncKeyState|ClipCursor|SetWindowPos|OpenProcess|TerminateProcess|CreateToolhelp32Snapshot|Module32FirstW|IcmpSendEcho|GetExtendedTcpTable|WSAStartup|OpenFileMappingW|XInputGetState|CreateProcessW|ShellExecuteW'; echo '--- absent:'; iat.py zip/Holeshot-HUD.exe | grep -E 'WriteProcessMemory|ReadProcessMemory|VirtualAllocEx|CreateRemoteThread|SetWindowsHookEx|SendInput|keybd_event|mouse_event' || echo 'none of: WriteProcessMemory, ReadProcessMemory, VirtualAllocEx, CreateRemoteThread, SetWindowsHookEx, SendInput, keybd_event, mouse_event'"
# Web addresses in the two program files.
ev strings-urls "for f in zip/Holeshot-HUD.exe zip/Holeshot-HUD.dlo; do echo \"== \$f\"; strings -n 6 \$f | grep -oE 'https?://[A-Za-z0-9./{}_?=-]+' | sort -u; done"
# The presence service in the source (overlay/src/presence.rs) isn't built: main.rs declares no presence module and
# the overlay holds no workers.dev address.
ev presence-absent "grep -n '^mod ' \"\$SRC/overlay/src/main.rs\"; grep -c 'mod presence' \"\$SRC/overlay/src/main.rs\"; strings -n 6 zip/Holeshot-HUD.exe | grep -c -iE 'workers\\.dev|holeshot-presence'"
# The settings and their defaults (HudConfig::new): all widgets off, no auto-update, no start-up entries, no stream server.
ev src-defaults "cd \"\$SRC\" && grep -nE '^ +show: false,|^ +(game_ui|start_with_windows|open_with_game|close_with_game|stream_enabled|auto_update_on_launch): false,' overlay/hud/src/config.rs; grep -nE '\"(Update automatically on launch|Open when Windows starts|Open when MX Bikes opens|MX Bikes menus|Browser Source)\"' overlay/src/settings/app.rs"
# The updater: when it runs, where it looks, what it checks before it replaces the overlay and the plugin.
ev src-update "cd \"\$SRC\" && grep -nE 'auto_update_on_launch|update::check|apply_on_launch' overlay/src/main.rs; grep -nE 'releases/latest|browser_download_url|\"digest\"|sha256:|starts_with\\(\"https://github.com|got != rel.digest|fs::copy\\(&src_exe|join\\(PLUGIN_DLO\\)|const UA' overlay/src/update.rs"
# Every connection in the overlay's source: the update check, feedback, ICMP ping, web pages it shows, the local server.
ev src-network "cd \"\$SRC\" && grep -rnE 'ureq::|\\.post\\(|IcmpSendEcho\\(|FALLBACK: u32|TcpListener::bind|Access-Control-Allow-Origin|HOME_URL: &str|mxb-ranked.com/Rider|cbrservers.com/player|holeshot-hud.vercel.app' overlay/src --include=*.rs | grep -v '/tests/'"
# What a feedback report carries, and when replies are fetched.
ev src-feedback "cd \"\$SRC\" && grep -nE 'attach_log: true|fn send\\(|\\\\\"kind\\\\\":|log_name|fn tick\\(settings_open|tickets_lock\\(\\).is_empty|fn fetch_tickets' overlay/src/feedback.rs; grep -nE '\\\\\"v\\\\\":1,\\\\\"file\\\\\"|\\\\\"evt\\\\\":\\\\\"place\\\\\"|\\\\\"n\\\\\":\\{race_num\\}' overlay/src/record.rs; grep -n 'public: false' api/feedback.js"
# Registry writes: the AppCompatFlags value for mxbikes.exe (plugin and overlay), the Run values (overlay), and what
# the uninstallers remove.
ev src-registry "cd \"\$SRC\" && grep -nE 'AppCompatFlags|DISABLEDXMAXIMIZEDWINDOWEDMODE|ensureOverlayCompat\\(\\)' src/plugin.cpp; grep -nE 'AppCompatFlags|const FLAG|fn ensure_disable_fullscreen_optimizations' overlay/src/compat.rs; grep -nE 'ensure_disable_fullscreen_optimizations' overlay/src/main.rs; grep -nE 'RUN_KEY|RUN_GAME|wait-for-game' overlay/src/startup.rs | head -8; echo '--- in the uninstallers:'; grep -nE 'HKCU|AppCompat' installer/uninstall.ps1 overlay/src/uninstall.rs"
# Files written into the game's folder: the plugin, the pitboard override, the menu pack; and what is deleted.
ev src-gamefiles "cd \"\$SRC\" && grep -nE 'fs::write\\(&dest|remove_legacy_plugin|LEGACY_PLUGIN_FILE: &str|PLUGIN_FILE: &str' overlay/src/plugin.rs; grep -nE 'misc|pitboard.cfg|MARKER_FILE: &str|fs::write\\(&cfg_path|pitboard_shown_anywhere' overlay/src/stock_pitboard.rs; grep -nE 'BAK_DIR: &str|MANIFEST: &str' overlay/src/game_ui/mod.rs; grep -nE 'write_english_labels\\(ui|backup_if_needed\\(ui|copy_dir\\(bak, ui\\)|ui.pkz' overlay/src/game_ui/pack.rs; grep -nE 'english.str\\\"\\)|patch_str_pair\\(&raw' overlay/src/game_ui/io.rs; grep -nE 'Copy-Item|Remove-Item' installer/install-plugin.ps1 installer/install.ps1"
# Keys and input: the plugin's Ctrl and mouse reads, the overlay's settings key, F9, mouse, and the cursor clip.
ev src-keys "cd \"\$SRC\" && grep -nE 'GetAsyncKeyState|keyDown\\(VK_|GetForegroundWindow' src/layout.cpp; grep -nE 'GetAsyncKeyState\\(' overlay/src/main.rs overlay/src/stance.rs; grep -nE 'ClipCursor\\(Some' overlay/src/compat.rs"
# Crash handler in the plugin.
ev src-crash "cd \"\$SRC\" && grep -nE 'SetUnhandledExceptionFilter|MiniDumpWriteDump\"|crash-|EXCEPTION_CONTINUE_SEARCH' src/crash_log.cpp"
# Shared memory: the names, made with default security in the Local session namespace, and the rider data in it.
ev src-shm "cd \"\$SRC\" && grep -nE 'define MXBO_(SHM|CMD)_NAME |char name\\[MXBO_NAME\\]|serverName|eventGuid' src/shm/mxbo_shm.h; grep -nE 'CreateFileMappingW|nullptr,\$' src/shm_writer.cpp"
# Steam files the overlay reads: the registry, libraryfolders.vdf (game folder), loginusers.vdf (signed-in account).
ev src-steam "cd \"\$SRC\" && grep -nE 'libraryfolders.vdf|loginusers.vdf|ActiveUser|fn local_steam_id64|fn ranked_url_from_steam_id64|fn cbr_url_from_steam_id64' overlay/src/plugin.rs; grep -nE 'libraryfolders|Valve' installer/install-plugin.ps1"
# The MyMXB page: the script the overlay adds to that site hides and removes its ad slots.
ev src-mymxb "cd \"\$SRC\" && grep -nE 'adsbygoogle|mymxb-ad-hide|node.remove\\(\\)|with_initialization_script|open-browser' overlay/src/settings/mymxb.rs | head -12"
# The release on GitHub: who uploaded the files, and the Release workflow run for the tag at the commit (network).
ev release-api "curl -sS https://api.github.com/repos/LeadingTrendTechnologies/HoleshotHUD/releases/tags/v0.24.0 | python3 -I -c 'import json,sys; d=json.load(sys.stdin); print(\"release\", d[\"tag_name\"], \"author\", d[\"author\"][\"login\"], \"published\", d[\"published_at\"]); [print(a[\"name\"], \"uploaded by\", a[\"uploader\"][\"login\"], a[\"digest\"], a[\"updated_at\"]) for a in d[\"assets\"]]'; curl -sS 'https://api.github.com/repos/LeadingTrendTechnologies/HoleshotHUD/actions/runs?head_sha=3ffdbf366023c19e1741178e39b5704a91728819' | python3 -I -c 'import json,sys; [print(r[\"name\"], r[\"event\"], r[\"head_branch\"], r[\"head_sha\"], r[\"conclusion\"], r[\"created_at\"], r[\"updated_at\"], r[\"html_url\"]) for r in json.load(sys.stdin)[\"workflow_runs\"]]'"
# The build: the Release workflow, the toolchain and the lock file.
ev deps "cd \"\$SRC\" && grep -nE 'tags:|uses:|cargo build|choco install|msbuild mxbo|files:' .github/workflows/release.yml; ls rust-toolchain rust-toolchain.toml overlay/rust-toolchain.toml 2>&1; git ls-files | grep -E 'Cargo.lock\$'; grep -nE '^(ureq|wry|zip|sha2|rusqlite) =' overlay/Cargo.toml"
# The repository: licence (none), prebuilt program files, and the history up to the commit.
ev repo-files "cd \"\$SRC\" && git ls-files | grep -iE 'licen|copying' || echo 'no licence file'; echo '--- prebuilt program files:'; git ls-files | grep -E '\\.(dll|lib|exe|dlo|so|wasm|pyc|o|obj)\$' | while read f; do file \"\$f\"; done; echo '--- the .pyc header (magic, flags, source mtime, source size) and the size of the script it is named for, in every commit that has them:'; python3 -I -c 'import struct,sys; print(struct.unpack(\"<IIII\", open(sys.argv[1],\"rb\").read(16)))' overlay/hud/assets/__pycache__/gen_gamepad_xbox.cpython-313.pyc; for c in \$(git log --format=%h -- overlay/hud/assets/gen_gamepad_xbox.py); do echo \"\$c: gen_gamepad_xbox.py \$(git show \$c:overlay/hud/assets/gen_gamepad_xbox.py | wc -c) bytes\"; done; echo '--- names in the .pyc:'; strings -n 8 overlay/hud/assets/__pycache__/gen_gamepad_xbox.cpython-313.pyc | head -12; echo '--- the wasm and the last commits that changed it and its source:'; git log -1 --format='%h %ad %s' --date=short -- web/pkg/mxbo_web_preview_bg.wasm; git log -1 --format='%h %ad %s' --date=short -- web-preview overlay/hud/src; echo '--- history:'; git log --oneline 3ffdbf366023c19e1741178e39b5704a91728819 | wc -l; git log --format='%ad' --date=short 3ffdbf366023c19e1741178e39b5704a91728819 | sed -n '1p;\$p'"
# Third-party code and credits.
ev strings-thirdparty "echo '== credits in the release README'; grep -niE 'font awesome|licen|credit|thanks' zip/README.txt; echo '== crates in the lock file'; grep -c '^name = ' \"\$SRC/overlay/Cargo.lock\"; echo '== font licence in the repository'; cd \"\$SRC\" && git ls-files | grep -iE 'OFL|licen'"
money zip/Holeshot-HUD.exe zip/Holeshot-HUD.dlo zip/README.txt
# The Windows runs (lab/results/holeshot-0.24.0/): the ride against the bare demo, and the overlay and setup runs.
export RES="$OUT/../../results/holeshot-0.24.0"
ev runs "cd \"\$RES\" && echo '== ride: steps (the bare demo reached the track; with the plugin, To Track was clicked three times)'; grep -E 'no change|to-track|ride' \"baseline-windows/host.log\" \"ride-windows/host.log\"; echo '== ride: files written outside the game folder, against the baseline (texture cache names are random)'; diff <(sed -E 's/textures\\\\[a-z0-9]{8}/textures\\\\<random>/' \"baseline-windows/outside.txt\" | sort -u) <(sed -E 's/textures\\\\[a-z0-9]{8}/textures\\\\<random>/' \"ride-windows/outside.txt\" | sort -u); echo '== ride: registry writes not in the baseline'; diff <(sort -u \"baseline-windows/registry.txt\") <(sort -u \"ride-windows/registry.txt\") | grep '^>'; echo '== network'; for r in ride overlay overlay-wait setup; do echo \"-- \$r\"; cat \"\$r-windows/network.txt\"; done; echo '== overlay: registry'; cat \"overlay-windows/registry.txt\"; echo '== setup: processes started'; zcat \"setup-windows/raw/procmon.csv.gz\" | grep 'Process Create' | cut -d, -f2,5; echo '== bystander'; grep -E 'Startup\\(|untouched|changed|clean exit' \"bystander-windows/host.log\" | sort | uniq -c"
# P10: what the release asks of Windows in rights: each program's manifest, the service and driver calls, and every place a file asks
# for administrator rights or checks for them (privileges.py unpacks the release files itself, into a scratch folder).
ev privileges "privileges.py Holeshot-HUD-0.24.0-windows-x64.zip HoleshotHUD-Setup.exe"
# The installer's own setup header (Inno Setup 6.7, which innoextract can't read): its default folder and the rights it asks for.
ev setup-rights "innosetup.py HoleshotHUD-Setup.exe"
