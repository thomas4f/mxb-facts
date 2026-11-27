#!/usr/bin/env bash
# MX Dirt Mod Alt 1.7.1-alt.1 for MX Bikes (open source, GPL-3.0: the release files and the source).
# The folder holds MX-Dirt-Mod-Alt-1.7.1-alt.1.zip and MX-Dirt-Mod-Alt-1.7.1-alt.1.sha256.txt from
# https://github.com/FMilesi-Cloud/mx-dirt-mod-alt/releases/tag/v1.7.1-alt.1. The second argument is a checkout of
# https://github.com/FMilesi-Cloud/mx-dirt-mod-alt at c5ed04c72bdbab7b00fd594ce7525e7a1914f797 (the tag's commit).
# This script unpacks the zip into the same folder, keeping its folders (the zip stores them with backslashes, which
# unzip turns into folders with a warning, exit 1). The rebuild downloads Zig 0.13.0 (pinned by SHA-256) into $W.
. "$(dirname "$0")/../ev.sh"
(cd "$R" && { unzip -o -q MX-Dirt-Mod-Alt-1.7.1-alt.1.zip 2>/dev/null || [ $? -eq 1 ]; })
ev files "sha256sum MX-Dirt-Mod-Alt-1.7.1-alt.1.zip MX-Dirt-Mod-Alt-1.7.1-alt.1.sha256.txt plugins/mx_dirt.dlo plugins/mx_dirt_render.dlo plugins/mx_dirt.ini plugins/mx_dirt_render.ini plugins/mx_dirt_data/white.tga Install.cmd Uninstall.cmd install/Install.ps1 install/Uninstall.ps1 launcher/MXDirtLauncher.ps1 'launcher/MX Dirt Mod.cmd' README.txt NOTICE.txt LICENSE SUPPORTED_EXE.txt; cat MX-Dirt-Mod-Alt-1.7.1-alt.1.sha256.txt"
ev file "unzip -l MX-Dirt-Mod-Alt-1.7.1-alt.1.zip; find . -type f ! -name '*.zip' ! -name '*.sha256.txt' | sort | while read -r f; do file \"\$f\"; done"
# Every file in the repository at the commit, and the program files among them (none: the .dlo files are built, see .gitignore).
ev repo-files "cd \"\$SRC\" && git rev-parse HEAD && git tag --points-at HEAD && git ls-files && echo '-- program files:' && git ls-files -z | xargs -0 file | grep -iE 'PE32|ELF|executable|DLL' ; echo '-- .gitignore:'; cat .gitignore"
ev history "cd \"\$SRC\" && git log --date=short --format='%h %ad %an: %s' HEAD"
# Each non-program file in the zip is the repository's file at the commit (package.ps1 copies them; LICENSE,
# SUPPORTED_EXE.txt and Install.ps1 differ only in line endings).
ev zip-vs-source "for p in README.md:README.txt NOTICE.md:NOTICE.txt LICENSE:LICENSE SUPPORTED_EXE.txt:SUPPORTED_EXE.txt install/Install.cmd:Install.cmd install/Uninstall.cmd:Uninstall.cmd install/Install.ps1:install/Install.ps1 install/Uninstall.ps1:install/Uninstall.ps1 launcher/MXDirtLauncher.ps1:launcher/MXDirtLauncher.ps1 'launcher/MX Dirt Mod.cmd:launcher/MX Dirt Mod.cmd' src/core/mx_dirt.ini:plugins/mx_dirt.ini src/render/mx_dirt_render.ini:plugins/mx_dirt_render.ini data/mx_dirt_data/white.tga:plugins/mx_dirt_data/white.tga; do a=\"\${p%%:*}\"; b=\"\${p##*:}\"; if cmp -s \"\$SRC/\$a\" \"\$b\"; then echo \"same: \$b\"; elif cmp -s <(tr -d '\\r' < \"\$SRC/\$a\") <(tr -d '\\r' < \"\$b\"); then echo \"same apart from line endings: \$b\"; else echo \"DIFFERENT: \$b\"; fi; done; cat \"\$SRC/package.ps1\""
# The rebuild (T4): rebuild.sh, beside this script.
export EVD="$OUT"
ev rebuild "bash \"\$EVD/rebuild.sh\""
(cd "$R" && cp plugins/mx_dirt.dlo plugins/mx_dirt_render.dlo .)  # pe names its outputs after the file
pe mx_dirt.dlo
pe mx_dirt_render.dlo
# Code signing: the Security (certificate) directory of each plugin.
ev signature "for f in plugins/mx_dirt.dlo plugins/mx_dirt_render.dlo; do objdump -p \$f | grep -E 'file format|Security Directory'; done"
# Imports a plugin would need to go online, press keys, hook input, write the registry or another process, open another
# process, share memory, load another library by name or catch every crash (none of these).
ev imports-absent "for f in plugins/mx_dirt.dlo plugins/mx_dirt_render.dlo; do iat.py \$f; done | grep -iE 'ws2_32|wsock|wininet|winhttp|urlmon|SendInput|keybd_event|mouse_event|SetWindowsHookEx|ShellExecute|WinExec|RegSetValue|RegCreateKey|RegOpenKey|WriteProcessMemory|OpenProcess|CreateRemoteThread|CreateFileMapping|LoadLibrary|SetUnhandledExceptionFilter|AddVectoredExceptionHandler'"
# The imports that do change or read code and memory, start a program, or read keys, in each plugin.
ev imports-notable "for f in plugins/mx_dirt.dlo plugins/mx_dirt_render.dlo; do echo \"-- \$f\"; iat.py \$f | grep -E 'VirtualProtect|VirtualAlloc|VirtualQuery|FlushInstructionCache|ReadProcessMemory|CreateProcess|GetAsyncKeyState|GetForegroundWindow|GetCursorPos|FindWindow|SetForegroundWindow|GetProcAddress|DeleteFile|MoveFileEx|WritePrivateProfileString|CreateDirectory|Crypt|BCrypt'; done"
# Every web address and every DLL name in the plugins' text (only their imports' DLLs).
ev strings-urls "for f in plugins/mx_dirt.dlo plugins/mx_dirt_render.dlo; do { strings -n 5 \$f; strings -el -n 5 \$f; } | grep -niE 'https?://|www\\.|\\.(com|net|org|io)\\b|\\.dll'; done"
# The functions the plugins look up by name (GetProcAddress, wglGetProcAddress) and the module names they ask for.
ev src-getprocaddress "cd \"\$SRC\" && grep -rnE 'GetProcAddress|GetModuleHandle[AW]?\\(\"|LoadLibrary' src"
# No network code anywhere in the source or the scripts; the launcher's only address is Steam's own steam:// link.
ev src-network "cd \"\$SRC\" && grep -rniE 'socket|winsock|wininet|winhttp|urlmon|https?://|Invoke-WebRequest|Invoke-RestMethod|WebClient|Net\\.Http|steam://' src install launcher"
money plugins/mx_dirt.dlo plugins/mx_dirt_render.dlo README.txt NOTICE.txt install/Install.ps1 launcher/MXDirtLauncher.ps1
# Code changes in the game: every place the source changes memory protection or writes code (VirtualProtect).
ev src-codewrites "cd \"\$SRC\" && grep -rnE 'VirtualProtect|InterlockedCompareExchangePointer\\(slot' src"
# The one supported mxbikes.exe: the SHA-256 both plugins check at Startup, and what the Windows runs logged.
ev src-exehash "cd \"\$SRC\" && grep -rn '9e792d7aed1dc40df11eea51d1a6d0519daec7be2b65609905df8c9de804a291' src SUPPORTED_EXE.txt; grep -n 'executable_hash\\|verified_image' src/render/mxdirt_render_host.c | head -8"
# Every file the plugins open, create, move or delete.
ev src-files "cd \"\$SRC\" && grep -rnoE '(fopen|_wfopen|CreateFileW|CreateDirectoryA|DeleteFileA|MoveFileExA|WritePrivateProfileStringA|FindFirstFileA)\\([^;]{0,100}' src; grep -rnE 'RA_TERRAIN_DIR|RA_LAPS_DIR|mx_dirt_soft|mx_dirt_laps|mxb_reflex_ghosts|mx_dirt_presets|mx_dirt_tracks|overhaul.ini|mxbmrp3_data|bikes\\\\\\\\|tyres\\\\\\\\' src | grep -v '^\\s*//' | cut -c1-220"
# Keys: every GetAsyncKeyState in the source, and the check that the game's window is in front before any key counts.
ev src-keys "cd \"\$SRC\" && grep -rnE 'GetAsyncKeyState|GetForegroundWindow' src | cut -c1-240"
# Crash handling: no handler for the whole game in the source.
ev src-crash "cd \"\$SRC\" && grep -rnE 'SetUnhandledExceptionFilter|AddVectoredExceptionHandler|__try' src"
# What the installer, the uninstaller and the launcher do with files and Windows (registry reads, shortcut, moves).
ev scripts "cd \"\$SRC\" && grep -nE 'Retire|Backup|Copy-Item|Move-Item|Remove-Item|Unblock-File|CreateShortcut|HKCU|HKLM|Set-ItemProperty|New-ItemProperty|Startup|Run\\b|steam://|testing.dfm' install/Install.ps1 install/Uninstall.ps1 launcher/MXDirtLauncher.ps1 | cut -c1-260"
# The shipped settings that decide the defaults.
ev settings "grep -nE '^(enabled|use_telemetry|use_bike_tyres|record_ghosts|ghost_riders|prewear_riders|online_wear|dump_terrain|online_echo|launcher_key|content_log|dirt_material|raised_dirt_surface)=|^\\[' plugins/mx_dirt.ini plugins/mx_dirt_render.ini"
# Third-party code and credits.
ev thirdparty "cd \"\$SRC\" && grep -rniE 'copyright|licen[cs]e|public domain|kadenball' NOTICE.md src tests | cut -c1-200; grep -niE 'kadenball|GPL' README.md | head -8 | cut -c1-200"
# What the README says on the points the card checks.
ev readme-claims "grep -nE 'SUPPORTED_EXE|se apaga solo|stays inactive|switch|memoria del juego|game.s memory|reverse engineering|Online|online|launcher|Install.cmd|backup|Nothing is ever deleted|Zig' README.txt SUPPORTED_EXE.txt | cut -c1-260"
# P10: what the release asks of Windows in rights: each program's manifest, the service and driver calls, and every place a file asks
# for administrator rights or checks for them (privileges.py unpacks the release files itself, into a scratch folder).
ev privileges "privileges.py MX-Dirt-Mod-Alt-1.7.1-alt.1.zip"
