#!/usr/bin/env bash
# MaXHUD v2.2.7 (closed source: commands on the release files only).
# The folder holds "MaXHUD - v2.2.7.zip", the file in the author's MEGA folder linked from the PiBoSo forum topic
# https://forum.piboso.com/index.php?topic=79.0 (tools/fetch_release.py downloads and decrypts it:
# https://mega.nz/folder/dRsyARjI#ceFbX0UW01KgB93KY83hZA/file/QYlnVZwS). This script unpacks the zip into the same
# folder, flat (every file name in it is unique). pdftotext is from poppler-utils.
. "$(dirname "$0")/../ev.sh"
(cd "$R" && unzip -o -q -j 'MaXHUD - v2.2.7.zip')
ev files "sha256sum 'MaXHUD - v2.2.7.zip' MaxHUD_MXB64.dlo MaxHUD_GPB64.dlo MaxHUD_KRP64.dlo MaxHUD_WRS64.dlo MaxStopRumble.exe MaxHUD.pdf *.tga *.fnt"
ev file "file MaxHUD_MXB64.dlo MaxHUD_GPB64.dlo MaxHUD_KRP64.dlo MaxHUD_WRS64.dlo MaxStopRumble.exe MaxHUD.pdf *.tga *.fnt; unzip -l 'MaXHUD - v2.2.7.zip'"
pe MaxHUD_MXB64.dlo
pe MaxStopRumble.exe
# Code signing: the Security (certificate) directory of every program file.
ev signature "for f in MaxHUD_MXB64.dlo MaxHUD_GPB64.dlo MaxHUD_KRP64.dlo MaxHUD_WRS64.dlo MaxStopRumble.exe; do objdump -p \$f | grep -E 'file format|Security Directory'; done"
# The manual (the only document in the release): its text, then what it says on the points the card checks.
ev pdf-text "pdftotext -layout MaxHUD.pdf - "
ev readme-claims "pdftotext -layout MaxHUD.pdf - | grep -nE 'credit|thanks|CAPS-LOCK|MaxHUD.ini|renamed|Documents|XInput|rumble_crashed|xinput_device|Logging|log was never|MX Bikes|vc_redist|MaxStopRumble|licen|Licen|donat|Donat'"
# Web addresses in the plugin and the app (none) and the DLL names they may load by name.
ev strings-urls "{ strings -n 5 MaxHUD_MXB64.dlo MaxStopRumble.exe; strings -el -n 5 MaxHUD_MXB64.dlo MaxStopRumble.exe; } | grep -niE 'https?://|www\\.|\\.(com|net|org|io)\\b'"
ev strings-dlls "{ strings -n 5 MaxHUD_MXB64.dlo; strings -el -n 5 MaxHUD_MXB64.dlo; } | grep -niE '\\.dll|^api-ms-|^ext-ms-'"
# The files and folders it names (its data folder, its settings and log, fonts and images).
ev strings-files "{ strings -n 5 MaxHUD_MXB64.dlo; strings -el -n 5 MaxHUD_MXB64.dlo; } | grep -nE 'MaxHUD|\\.tga|\\.fnt|\\.ini|\\.log|path|%Y'"
# Third-party code: the joystick texts match SFML's Windows joystick code (src/SFML/Window/Win32/JoystickImpl.cpp).
ev strings-thirdparty "{ strings -n 5 MaxHUD_MXB64.dlo; strings -el -n 5 MaxHUD_MXB64.dlo; } | grep -iE 'copyright|licen[cs]e|SFML|joystick|DirectInput|zlib|imgui|nlohmann|Microsoft'"
money MaxHUD_MXB64.dlo MaxStopRumble.exe MaxHUD.pdf
# Imports a plugin would need to go online, press keys, hook input, start other programs, write the registry or another
# process, read another process, change memory protection, share memory or catch every crash: none of them.
ev imports-absent "iat.py MaxHUD_MXB64.dlo MaxStopRumble.exe | grep -iE 'ws2_32|wsock|wininet|winhttp|urlmon|SendInput|keybd_event|mouse_event|SetWindowsHookEx|CreateProcess|ShellExecute|WinExec|RegSetValue|RegCreateKey|RegDeleteKey|WriteProcessMemory|ReadProcessMemory|OpenProcess|CreateRemoteThread|VirtualProtect|VirtualAlloc|VirtualQuery|CreateFileMapping|AddVectoredExceptionHandler|CreateThread'"
# The code takes no fixed address in the game's program (mxbikes.exe loads at 0x140000000).
ev fixed-addresses "objdump -d MaxHUD_MXB64.dlo | grep -E '0x14[0-9a-f]{7}\\b'"
# Keys and mouse: every GetKeyState (0x180035368), GetAsyncKeyState (0x180035350), GetCursorPos (0x180035358),
# FindWindowA (0x180035370), ScreenToClient (0x180035360) and GetClientRect (0x180035378) call site.
ev keys-callsites "objdump -d MaxHUD_MXB64.dlo | grep -E '# 0x180035368|# 0x180035350|# 0x180035358|# 0x180035370|# 0x180035360|# 0x180035378|call   0x1800139a0'"
# Draw (export at 0x18002afd0) calls the menu function at 0x1800139a0, which reads Caps Lock's toggle with GetKeyState(0x14):
# on shows the menu, off hides it. Only while the menu shows does it ask the "MX Bikes" window for the cursor position and
# read the left (0x01) and right (0x02) mouse buttons and Left Shift (0xa0) with GetAsyncKeyState.
dis MaxHUD_MXB64.dlo 18002b0e2 18002b0f3
dis MaxHUD_MXB64.dlo 1800139a0 180013bca
ev window-name "objdump -s --start-address=0x1800390a0 --stop-address=0x1800390b0 MaxHUD_MXB64.dlo"
# Controller: every XInputGetState (0x180035410) and XInputSetState (0x180035408) call site, and the joystick reads
# through winmm (joyGetPosEx 0x1800353f0, joyGetDevCapsW 0x1800353f8).
ev xinput-callsites "objdump -d MaxHUD_MXB64.dlo | grep -E '# 0x180035410|# 0x180035408|# 0x1800353f0|# 0x1800353f8'"
# Registry: every RegOpenKeyExW (0x180035000) and RegQueryValueExW (0x180035010) call site; the keys are Windows' joystick
# settings, read to name the joystick (as SFML does). It imports no function that writes the registry (imports-absent).
ev registry-callsites "objdump -d MaxHUD_MXB64.dlo | grep -E '# 0x180035000|# 0x180035010'"
# DirectInput: LoadLibraryA (0x180035120) of the name at 0x180035c70, GetProcAddress (0x180035088) of the name at
# 0x180035c80, GetModuleHandleW(NULL) (0x180035080), as in SFML's JoystickImpl::initialize.
dis MaxHUD_MXB64.dlo 18002ebf0 18002ec4b
ev dinput-names "objdump -s --start-address=0x180035c30 --stop-address=0x180035ca0 MaxHUD_MXB64.dlo"
# File delete and rename: the only remove (0x180035420) and rename (0x180035428) call sites. remove takes the save path
# joined with "MaxHUD.log" (0x18003ab60); rename moves the MaxHUD.ini path to the same path with a date added
# (strftime 0x1800355a8, format at 0x180039080).
ev file-ops "objdump -d MaxHUD_MXB64.dlo | grep -E '# 0x180035420|# 0x180035428|# 0x1800355a8'"
dis MaxHUD_MXB64.dlo 180029e1e 180029ea0
dis MaxHUD_MXB64.dlo 1800118d7 1800119c7
ev file-names "objdump -s --start-address=0x18003ab60 --stop-address=0x18003ab70 MaxHUD_MXB64.dlo; objdump -s --start-address=0x180039070 --stop-address=0x180039090 MaxHUD_MXB64.dlo"
# Crash handler: both SetUnhandledExceptionFilter (0x180035108) calls pass 0, right before UnhandledExceptionFilter.
ev crash-filter "objdump -d MaxHUD_MXB64.dlo | grep -B3 -A3 '# 0x180035108'"
# MaxStopRumble.exe: all its text.
ev stoprumble-strings "strings -n 6 MaxStopRumble.exe | grep -E '[a-z]{3}'"
