#!/usr/bin/env bash
# FIXXER's Controller Rumble V1.0 for GP Bikes (closed source: commands on the release files only).
# The folder holds the one file players download, FIXXER's_Rumble.zip, from the MEGA link on
# https://gpb-mods.com/fixxers-controller-vibration-rumble/ (MEGA encrypts it; to get it as players do:
# python3 -I tools/mega_fetch.py 'https://mega.nz/file/EPwQ2C7Y#h8ljtwB07QDbCWzQgLDRSv252Ti_6nYuzyFjnE2FiNw' <folder>).
# This script unpacks the zip into the same folder and copies the plugin and its data folder up next to it, so the commands
# name them plainly.
. "$(dirname "$0")/../ev.sh"
(cd "$R" && unzip -o -q "FIXXER's_Rumble.zip" && cp -f "FIXXER's_Rumble/plugins/FIXXER_RUMBLE_GPB64.dlo" . && rm -rf FIXXER_Rumble_Data && cp -r "FIXXER's_Rumble/plugins/FIXXER_Rumble_Data" .)
ev files "sha256sum \"FIXXER's_Rumble.zip\" FIXXER_RUMBLE_GPB64.dlo 'FIXXER_Rumble_Data/READ ME.md' FIXXER_Rumble_Data/settings.txt FIXXER_Rumble_Data/rumble.fnt FIXXER_Rumble_Data/Pointer.tga"
ev file "file FIXXER_RUMBLE_GPB64.dlo FIXXER_Rumble_Data/*; unzip -l \"FIXXER's_Rumble.zip\""
pe FIXXER_RUMBLE_GPB64.dlo
# Code signing: the Security (certificate) directory.
ev signature "objdump -p FIXXER_RUMBLE_GPB64.dlo | grep -E 'file format|Security Directory'"
# The settings file the release ships.
ev settings "cat FIXXER_Rumble_Data/settings.txt"
# The plugin's own text: its files, settings keys, log lines and panel labels.
ev strings-plugin "strings -n 5 FIXXER_RUMBLE_GPB64.dlo | grep -nE 'FIXXER|%s|_enabled|_intensity|invert_motors|Settings|Rumble|Lockup|Spin|Lock|Suspension|Limiter|Ground|Engine|RESET|SAVE|Material|Ctrl' | grep -v '\\.pdb\$'"
# Web addresses, network libraries, shop and donation words: none.
ev strings-urls "{ strings -n 5 FIXXER_RUMBLE_GPB64.dlo; strings -el -n 5 FIXXER_RUMBLE_GPB64.dlo; } | grep -inE 'https?://|www\\.|ws2_|wsock|wininet|winhttp|urlmon|socket|\\.com|\\.net'"
money FIXXER_RUMBLE_GPB64.dlo
# The library names the C runtime loads on its own (LoadLibraryExW in its Windows-version thunks): Windows' own.
ev strings-crt "strings -el -n 5 FIXXER_RUMBLE_GPB64.dlo | grep -nE '^(api|ext)-ms|^(advapi32|kernel32|kernelbase|ntdll|user32|mscoree.dll)\$'"
ev strings-thirdparty "{ strings -n 6 FIXXER_RUMBLE_GPB64.dlo; strings -el -n 6 FIXXER_RUMBLE_GPB64.dlo; } | grep -iE 'copyright|licen[cs]e|zlib|stb_|lodepng|imgui|miniz|freetype|crts|ucrt|Microsoft' | sort | uniq -c"
# Imports a plugin would need to press keys, hook input, start with Windows, write the registry or another process,
# read another process, start a program, share memory or listen for connections.
ev imports-absent "iat.py FIXXER_RUMBLE_GPB64.dlo | grep -E 'SendInput|keybd_event|mouse_event|SetWindowsHookEx|WriteProcessMemory|ReadProcessMemory|OpenProcess|CreateRemoteThread|CreateProcess|ShellExecute|WinExec|RegSetValue|RegCreateKey|ADVAPI32|ws2_32|WS2_32|WSOCK|WININET|WINHTTP|CreateFileMapping|AddVectoredExceptionHandler'"
# Call sites of the imports that touch files, memory protection, the crash filter, the keyboard and XInput (iat.py names each slot).
ev callsites "for s in KERNEL32.dll!MoveFileA KERNEL32.dll!DeleteFileA KERNEL32.dll!CreateFileA KERNEL32.dll!CreateDirectoryA KERNEL32.dll!VirtualProtect KERNEL32.dll!SetUnhandledExceptionFilter USER32.dll!GetAsyncKeyState USER32.dll!GetForegroundWindow USER32.dll!GetCursorPos 'XINPUT1_4.dll!#2' 'XINPUT1_4.dll!#3'; do a=\$(iat.py FIXXER_RUMBLE_GPB64.dlo | awk -v s=\"\$s\" '\$2 == s {print \$1}'); echo \"== \$s (\$a)\"; objdump -d FIXXER_RUMBLE_GPB64.dlo | grep \"# \$a\$\"; done"
# Ctrl (0x11) and R (0x52) read with GetAsyncKeyState, before any check of the window in front; the left mouse button (1) only
# while the panel is open. RunTelemetry (export at 0x180001e10) calls this function at 0x180001e34.
dis FIXXER_RUMBLE_GPB64.dlo 180002840 180002970
ev telemetry-calls "objdump -d FIXXER_RUMBLE_GPB64.dlo | grep -E '^   180001e[1-4][0-9a-f]:'"
# A click inside the SAVE button: creates the data folder and writes settings.txt ("Settings saved" or "Failed to write ...").
dis FIXXER_RUMBLE_GPB64.dlo 1800029c6 180002a4d
dis FIXXER_RUMBLE_GPB64.dlo 180002bf0 180002c20
# Startup (export at 0x180001ba0): opens rumble.log; over 256 KiB (0x40000) it deletes rumble.log.old and renames the log to it.
dis FIXXER_RUMBLE_GPB64.dlo 180001ba0 180001ce4
# XInputGetState (#2) and XInputSetState (#3) on controller slots 0 to 3; 0x180001b20 sets every slot's motors to 0.
dis FIXXER_RUMBLE_GPB64.dlo 1800019d0 180001b5a
# VirtualProtect: the C runtime's thunks change the protection of 0x180035000, the plugin's own .fptable section (objdump -h).
dis FIXXER_RUMBLE_GPB64.dlo 1800143e8 18001444e
dis FIXXER_RUMBLE_GPB64.dlo 1800146e0 18001470f
# Crash filter: the one call of SetUnhandledExceptionFilter passes 0 (xor ecx), right before UnhandledExceptionFilter.
dis FIXXER_RUMBLE_GPB64.dlo 18000ee07 18000ee1c
