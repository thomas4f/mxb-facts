#!/usr/bin/env bash
# MaXHUD 2.2.7 (closed source: commands on the release files only).
# The folder holds the one file of the release, "MaXHUD - v2.2.7.zip", from the MEGA folder the forum post links
# (https://forum.piboso.com/index.php?topic=79.0): https://mega.nz/folder/dRsyARjI#ceFbX0UW01KgB93KY83hZA/file/QYlnVZwS
# (tools/fetch_release.py downloads it). This script unpacks the zip into the same folder and names its folder m.
# Besides binutils and file, it needs pdftotext (poppler-utils) for the PDF.
. "$(dirname "$0")/../ev.sh"
(cd "$R" && unzip -o -q "MaXHUD - v2.2.7.zip" && ln -sfn "MaXHUD - v2.2.7" m)
# dis for a file in m/: the output is named after the file alone.
mdis() {
  ev "$(basename "$1").$2-$3" "objdump -d '$1' | awk -v a=$2 -v b=$3 '\$1 ~ /^[0-9a-f]+:\$/ { x = substr(\$1, 1, length(\$1) - 1); p = length(x) == length(a) && x >= a && x <= b } p'"
}
P="m/MaxHUD_MXB64.dlo m/MaxHUD_GPB64.dlo m/MaxHUD_KRP64.dlo m/MaxHUD_WRS64.dlo m/MaxStopRumble.exe"
ev files "sha256sum 'MaXHUD - v2.2.7.zip' $P m/MaxHUD.pdf m/MaxHUD_data/*"
ev file "file $P m/MaxHUD.pdf; unzip -l 'MaXHUD - v2.2.7.zip'"
# The plugin for MX Bikes: headers, imports and exports, sections, import address table.
ev MaxHUD_MXB64.dlo.objdump-p "objdump -p m/MaxHUD_MXB64.dlo | awk '/^The Function Table|^PE File Base Relocations/{exit} 1'"
ev MaxHUD_MXB64.dlo.objdump-h "objdump -h m/MaxHUD_MXB64.dlo"
ev MaxHUD_MXB64.dlo.iat "iat.py m/MaxHUD_MXB64.dlo"
ev MaxStopRumble.exe.objdump-p "objdump -p m/MaxStopRumble.exe | awk '/^The Function Table|^PE File Base Relocations/{exit} 1'"
ev MaxStopRumble.exe.iat "iat.py m/MaxStopRumble.exe"
# Every library each program file imports, and the import that the other three plugins have and the MX Bikes one hasn't.
ev imports-dlls "for f in $P; do echo \"== \$f\"; objdump -p \$f | grep 'DLL Name'; done"
ev imports-compare "for f in m/MaxHUD_GPB64.dlo m/MaxHUD_KRP64.dlo m/MaxHUD_WRS64.dlo; do echo \"== \$f against m/MaxHUD_MXB64.dlo\"; diff <(iat.py m/MaxHUD_MXB64.dlo | awk '{print \$2}' | sort) <(iat.py \$f | awk '{print \$2}' | sort); done"
# Imports a program would need to go online, listen for connections, write the registry or another process, press keys,
# patch code, share memory, start a program or install a crash handler of its own: none in any of the five.
ev imports-absent "for f in $P; do iat.py \$f; done | grep -iE 'ws2_32|wsock|wininet|winhttp|urlmon|iphlpapi|WriteProcessMemory|ReadProcessMemory|OpenProcess|CreateRemoteThread|VirtualProtect|VirtualAlloc|RegSetValue|RegCreateKey|RegDeleteKey|SendInput|keybd_event|mouse_event|SetWindowsHookEx|CreateFileMapping|CreateProcess|ShellExecute|WinExec|AddVectoredExceptionHandler|CoCreateInstance|EnumProcessModules|Module32|GetForegroundWindow|GetFocus'"
# Code signing: the Security (certificate) directory of each program file.
ev signature "objdump -p $P | grep -E 'file format|Security Directory'"
# The functions it loads at run time: every LoadLibraryA, GetProcAddress and GetModuleHandleW call and the names they get.
ev dynamic-calls "iat.py m/MaxHUD_MXB64.dlo | grep -E 'LoadLibraryA|GetProcAddress|GetModuleHandleW'; objdump -d m/MaxHUD_MXB64.dlo | grep -B8 -E '# 0x180035120|# 0x180035088|# 0x180035080' | grep -E 'call|lea .*# 0x1800'"
ev dynamic-names "objdump -s --start-address=0x180035c70 --stop-address=0x180035c94 m/MaxHUD_MXB64.dlo; objdump -s --start-address=0x1800360f0 --stop-address=0x1800361b0 m/MaxHUD_MXB64.dlo"
mdis m/MaxHUD_MXB64.dlo 18002ec00 18002ec68
# Keyboard and mouse: every GetKeyState, GetAsyncKeyState, GetCursorPos and FindWindowA call, the code around them,
# and the window name FindWindowA looks for.
ev keys-callsites "iat.py m/MaxHUD_MXB64.dlo | grep -E 'GetKeyState|GetAsyncKeyState|GetCursorPos|FindWindowA|ScreenToClient|GetClientRect'; objdump -d m/MaxHUD_MXB64.dlo | grep -E '# 0x180035368|# 0x180035350|# 0x180035358|# 0x180035370'"
mdis m/MaxHUD_MXB64.dlo 1800139a0 180013bc7
ev findwindow-name "objdump -s --start-address=0x1800390a0 --stop-address=0x1800390b0 m/MaxHUD_MXB64.dlo"
# Crash handler: both calls of SetUnhandledExceptionFilter (0x180035108) pass 0, right before UnhandledExceptionFilter.
ev crash-filter "objdump -d m/MaxHUD_MXB64.dlo | grep -B3 -A2 '# 0x180035108'"
# Registry: the keys it reads (Windows' joystick names) and every call of RegOpenKeyExW (0x180035000).
ev registry "{ strings -n 6 m/MaxHUD_MXB64.dlo; strings -el -n 6 m/MaxHUD_MXB64.dlo; } | grep -nE 'CurrentControlSet|OEMName|registry'; objdump -d m/MaxHUD_MXB64.dlo | grep -c '# 0x180035000'"
# Its files: settings, log, data folder, fonts and backgrounds; and the single remove and rename calls.
ev strings-files "{ strings -n 5 m/MaxHUD_MXB64.dlo; strings -el -n 5 m/MaxHUD_MXB64.dlo; } | grep -nE 'MaxHUD\\.ini|MaxHUD\\.log|MaxHUD_data|back_%s|\\.fnt|\\.tga|Save path|Data path|Ini file|Log file|mxbikes|has been reset'; objdump -d m/MaxHUD_MXB64.dlo | grep -E '# 0x180035420|# 0x180035428'"
# The rename call (the settings backup, named with "%Y%m%d-%H%M%S" from 0x180039080 after "MaxHUD" at 0x180039000) and the
# remove call (right after the name "MaxHUD.log" at 0x18003ab60), with the strings they use.
mdis m/MaxHUD_MXB64.dlo 1800118a0 1800119c7
mdis m/MaxHUD_MXB64.dlo 180029e40 180029ea0
ev rename-remove-names "objdump -s --start-address=0x180039000 --stop-address=0x180039008 m/MaxHUD_MXB64.dlo; objdump -s --start-address=0x180039080 --stop-address=0x180039090 m/MaxHUD_MXB64.dlo; objdump -s --start-address=0x18003ab50 --stop-address=0x18003ab6b m/MaxHUD_MXB64.dlo"
# Joystick code of SFML (the same messages as SFML's src/SFML/Window/Win32/JoystickImpl.cpp).
ev strings-sfml "{ strings -n 6 m/MaxHUD_MXB64.dlo; strings -el -n 6 m/MaxHUD_MXB64.dlo; } | grep -nE 'joystick at index|DirectInput|Joystick\$'"
# Every web address and credit in the five programs, and shop, payment and donation words in them and in the PDF.
ev strings-urls "for f in $P; do echo \"== \$f\"; { strings -n 6 \$f; strings -el -n 6 \$f; } | grep -niE 'https?://|www\\.|\\.com|\\.net|\\.org'; done"
ev strings-thirdparty "for f in $P; do { strings -n 6 \$f; strings -el -n 6 \$f; } | grep -iE 'copyright|licen[cs]e|sfml|zlib|stb_|imgui|\\(c\\)'; done | sort | uniq -c"
ev strings-money "{ for f in $P; do strings -n 6 \$f; strings -el -n 6 \$f; done; pdftotext -layout m/MaxHUD.pdf -; } | grep -niE '[Ss]hop|[Bb]uy |[Pp]rice|[Pp]remium|[Pp]atreon|[Pp]ay[Pp]al|[Kk]o-?fi|[Dd]onat|licen[cs]e key|serial|activat'"
# MaxStopRumble.exe: its text, and its whole main function (for each XInput pad 0-3 that answers, XInputSetState with
# both motors at 0).
ev strings-stoprumble "strings -n 6 m/MaxStopRumble.exe | grep -nE 'Rumble running|Rumble done|Stopped xinput'"
mdis m/MaxStopRumble.exe 401050 4010db
# What the PDF says, on the points the card quotes.
ev pdf "pdftotext -layout m/MaxHUD.pdf - | grep -nE 'MaXHUD v|AdvancedHUD|share his code|Unzipping|MaxHUD_[A-Z]+64.dlo :|MaxHUD_data :|MaxHUD.pdf :|Copy the MaxHUD_data|creates a MaxHUD.ini|Documents.PiBoSo.MX Bikes|compatibility mode|renamed to MaxHUD.ini|CAPS-LOCK|right clicking|left shift|Logging to MaxHUD.log|erased at startup|TheFatController|Juju|Enables rumble|XInput|vc_redist|Rumble \\(not'"
