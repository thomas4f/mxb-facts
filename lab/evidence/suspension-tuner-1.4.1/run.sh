#!/usr/bin/env bash
# Suspension Tuner 1.4.1 (no licence found; no public source: commands on the release files only).
# The folder holds the two files of the GitHub release 1.4.1 (https://github.com/Lilian1134/Suspension-Tuner/releases/tag/1.4.1):
# SuspensionTuner.zip and SuspensionTuner_Setup.exe. This script unzips the zip into zip/, without running anything.
# The launcher (zip/SuspensionTuner/SuspensionTuner.exe) is a .NET program: ilspycmd (ILSpy's command line,
# `dotnet tool install --tool-path <dir> ilspycmd --version 9.1.0.7988`, on .NET 8 with DOTNET_ROLL_FORWARD=Major) decompiles it; set ILSPYCMD to it if it isn't on PATH.
# The app (zip/SuspensionTuner/app/SuspensionTuner.exe) is a Nuitka program: its Python modules are compiled to machine
# code, so nuitka.py lists the constants each module keeps (names it uses, its texts), which is what the searches read.
. "$(dirname "$0")/../ev.sh"
ILSPYCMD="${ILSPYCMD:-ilspycmd}"; export ILSPYCMD
(cd "$R" && rm -rf zip && mkdir zip && cd zip && unzip -o -q ../SuspensionTuner.zip)
A=zip/SuspensionTuner/app/SuspensionTuner.exe
L=zip/SuspensionTuner/SuspensionTuner.exe
ev files "sha256sum SuspensionTuner.zip SuspensionTuner_Setup.exe $L $A zip/SuspensionTuner/app/PIL/_imagingtk.pyd"
ev file "file SuspensionTuner.zip SuspensionTuner_Setup.exe $L $A; unzip -l SuspensionTuner.zip | tail -1"
# Every program file in the zip: SHA-256 and type (data files such as Tcl scripts, fonts and images left out).
ev bundled "cd zip; find . -type f \\( -iname '*.dll' -o -iname '*.pyd' -o -iname '*.exe' \\) | sort | while read f; do sha256sum \"\$f\"; file -b \"\$f\"; done"
# Code signing: the Security (certificate) directory of the installer, the launcher and the app.
ev signature "for f in SuspensionTuner_Setup.exe $L $A; do echo \"\$f\"; objdump -p \"\$f\" | grep -E 'file format|Security Directory'; done"
# Versions of what is packed: Python, OpenSSL, Tcl/Tk, Pillow, customtkinter, darkdetect, and the Nuitka runtime.
ev versions "echo '- python313.dll:'; strings -el zip/SuspensionTuner/app/python313.dll | grep -A1 -xE 'FileVersion|ProductName'; echo '- libcrypto-3.dll:'; strings -n 5 zip/SuspensionTuner/app/libcrypto-3.dll | grep -E '^OpenSSL [0-9]' | head -1; echo '- tcl86t.dll:'; strings zip/SuspensionTuner/app/tcl86t.dll | grep -xE '8\\.6\\.[0-9]+' | head -1; echo '- Pillow (PIL._version):'; nuitka.py consts $A PIL._version | grep -xE 'u[0-9.]+'; echo '- customtkinter:'; nuitka.py consts $A customtkinter | grep -xE 'u[0-9]+\\.[0-9]+\\.[0-9]+'; echo '- darkdetect:'; nuitka.py consts $A darkdetect | grep -xE 'u[0-9.]+'; echo '- Nuitka (lines naming it in the app):'; strings -n 8 $A | grep -cE 'Nuitka'; strings -n 8 $A | grep -m3 -E 'nuitka\\.net|__nuitka_version__|__compiled__'"
# Licence and credit files in the zip (only Tk's).
ev thirdparty "unzip -l SuspensionTuner.zip | grep -iE 'licen|copying|credit|notice|readme'"
# The installer: Inno Setup, its data version 6.7.0; innoextract 1.9 (the newest release) can't read it.
ev setup "strings -n 6 SuspensionTuner_Setup.exe | grep -m3 -E 'Inno Setup'; innoextract --version | head -1; innoextract -l SuspensionTuner_Setup.exe"
# The launcher, decompiled: it starts app\\SuspensionTuner.exe with the same arguments and exits.
ev launcher "objdump -p $L | grep -E 'DLL Name|CorExeMain'; \"\$ILSPYCMD\" $L"
# The app's module blocks (offset, name, size): Python's own and its packages' modules, and the tool's own nine modules
# (__main__, calibration, gameplay_analysis, proof, stp_setup, suspension_rules, suspension_settings, suspension_tuner,
# suspension_update).
ev blocks "nuitka.py blocks $A"
OWN="__main__ calibration gameplay_analysis proof stp_setup suspension_rules suspension_settings suspension_tuner suspension_update"
for m in $OWN; do ev "consts-$m" "nuitka.py consts $A $m"; done
# Shorthand for the searches below: every constant of the tool's own modules, each line prefixed with its module.
ALL="for m in $OWN; do nuitka.py consts $A \$m | sed \"s/^/\$m: /\"; done"
# The DLLs the app loads by its import table.
ev imports "objdump -p $A | grep 'DLL Name'"
# Its internet and network code: urllib only in suspension_update (the GitHub release list), a UDP socket bound to 0.0.0.0
# in suspension_tuner (the game's proxy_udp data), and webbrowser in __main__ (Discord, Gumroad).
ev network "$ALL | grep -nE ': (a|u)(urllib|urlopen|socket|AF_INET|SOCK_DGRAM|SOCK_STREAM|bind|recvfrom|sendto|connect|webbrowser|http|ssl|0\\.0\\.0\\.0|127\\.0\\.0\\.1:?)\$|https?://'"
# The update check, in full: GET https://api.github.com/repos/Lilian1134/Suspension-Tuner/releases?per_page=20 with the
# User-Agent SuspensionTuner/1.4.1; it keeps the newest release's tag, notes and page (html_url).
ev update "nuitka.py consts $A suspension_update; nuitka.py raw $A suspension_update aok 60"
# What the window does with it: a notice with a Download button; settings show "Checked automatically at startup".
ev update-ui "nuitka.py consts $A __main__ | grep -nE -A3 'Checked automatically|Update available|_install_update|Could not check'"
# Finding the game and enabling its proxy_udp plugin (enable_plugin, auto_setup): Steam's registry entry and
# libraryfolders.vdf, four fixed folders, then proxy_udp.ini rewritten after a copy to proxy_udp.ini.bak.
ev proxy-ini "nuitka.py consts $A suspension_tuner | awk '/^afind_game_dirs\$/{p=1} p; /set enable = 1 by hand/{exit}'"
# The switch for it and the --no-setup argument the window passes when it is off.
ev auto-plugin "nuitka.py consts $A __main__ | grep -nE -B1 -A2 'auto_plugin|Configure MX Bikes|--no-setup'; nuitka.py consts $A suspension_tuner | grep -nE -A1 -- '--no-setup|aauto_setup'"
# The defaults: DEFAULTS in suspension_settings, a dict of ten keys and then their values: '' (stp_dir), 30001 (port: 'l'
# and 0xb1 0xea 0x01, 7 bits a byte, low first), True (auto_plugin), False (apply_extras), '' (track), [] (track_history),
# 'motocross' (discipline), '' (bike_folder), False (hide_discord), [] (known_bikes); settings.json under %APPDATA%.
ev defaults "nuitka.py consts $A suspension_settings; nuitka.py raw $A suspension_settings aDict 150"
# The UDP listener: bound to 0.0.0.0 (every network interface) on the port from settings (30001 by default).
ev udp "nuitka.py consts $A suspension_tuner | grep -nE -B2 -A6 '^asocket\$'"
# Registry: only read (winreg OpenKey and QueryValueEx: Steam's folder); the window's ctypes calls set its DPI and taskbar id.
ev registry "$ALL | grep -nE 'winreg|HKEY|OpenKey|QueryValueEx|SetValue|CreateKey|DeleteKey|Valve|windll|shell32|user32|shcore|ole32|SetCurrentProcess|SetProcessDpi|SHGetKnownFolderPath'"
# Functions it would need to start programs, change other processes, press keys, read keys outside its window, download a
# file or write the registry: none in its own modules.
ev absent "$ALL | grep -nE ': a(subprocess|Popen|system|OpenProcess|ReadProcessMemory|WriteProcessMemory|VirtualProtect|CreateRemoteThread|SendInput|keybd_event|SetWindowsHookExW|SetWindowsHookExA|GetAsyncKeyState|GetKeyState|urlretrieve|SetValueEx|CreateKey|DeleteKey|rmtree|unlink|kill|terminate)\$'"
# Every file it writes or copies, and where: settings and session files under %APPDATA%\\SuspensionTuner, .stp setups in the
# setups folder (ST_<track>_<bike>.stp), test and calibration .stp files, proxy_udp.ini and its .bak.
ev file-writes "$ALL | grep -nE ': (a|u)(write|write_text|write_bytes|copyfile|shutil|mkdir|makedirs|remove|replace|move|rename|.*\\.json|.*\\.bak|.*\\.stp|ST_|suspension_tuner_calib_|APPDATA|Documents|setups|profiles|unnamedProfile)\$'"
# What it reads from the game's data (the proxy_udp packet channels) and how its .stp files are named.
ev telemetry "nuitka.py consts $A suspension_tuner | grep -nE '^a(steer|throttle|brake_f|brake_r|susp_front|susp_rear|speed|rpm|gear|parse_channels|parse_event|recvfrom)\$|ST_|default.stp'"
# Shop, payment and donation words and links in its own modules.
ev strings-money "$ALL | grep -niE 'gumroad|donat|support|paypal|ko-?fi|patreon|buy|price|premium|free|licen[cs]e key|unlock|discord\\.gg'"
# Its own texts that the card quotes (settings, reset, support).
ev ui-claims "nuitka.py consts $A __main__ | grep -nE 'untouched|100% free|nothing to unlock|Entirely optional|first launch|Join the Discord|15 seconds|Open the setups folder'"
# P10: what the release asks of Windows in rights: each program's manifest, the service and driver calls, and every place a file asks
# for administrator rights or checks for them (privileges.py unpacks the release files itself, into a scratch folder).
ev privileges "privileges.py SuspensionTuner.zip SuspensionTuner_Setup.exe"
# The installer's own setup header (Inno Setup 6.7, which innoextract can't read): its default folder and the rights it asks for.
ev setup-rights "innosetup.py SuspensionTuner_Setup.exe"
