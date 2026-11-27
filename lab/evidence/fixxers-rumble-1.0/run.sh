#!/usr/bin/env bash
# FIXXER's Controller Rumble V1.0 for GP Bikes (closed source: commands on the release files only).
# The folder holds FIXXER_s_Rumble.zip, the file the MEGA link on https://gpb-mods.com/fixxers-controller-vibration-rumble/
# gives (tools/fetch_release.py downloads and decrypts it). This script unpacks the zip into the same folder, flat
# (FIXXER_RUMBLE_GPB64.dlo, READ ME.md, settings.txt, rumble.fnt, Pointer.tga).
. "$(dirname "$0")/../ev.sh"
(cd "$R" && unzip -o -q -j FIXXER_s_Rumble.zip)
ev files "sha256sum FIXXER_s_Rumble.zip FIXXER_RUMBLE_GPB64.dlo 'READ ME.md' settings.txt rumble.fnt Pointer.tga"
ev file "file FIXXER_RUMBLE_GPB64.dlo 'READ ME.md' settings.txt rumble.fnt Pointer.tga; unzip -l FIXXER_s_Rumble.zip"
pe FIXXER_RUMBLE_GPB64.dlo
# Code signing: the Security (certificate) directory.
ev signature "objdump -p FIXXER_RUMBLE_GPB64.dlo | grep -E 'file format|Security Directory'"
# Every web address in the plugin (none) and the DLL names its C runtime may load by name.
ev strings-urls "{ strings -n 5 FIXXER_RUMBLE_GPB64.dlo; strings -el -n 5 FIXXER_RUMBLE_GPB64.dlo; } | grep -niE 'https?://|www\\.|\\.(com|net|org|io)\\b'"
ev strings-dlls "{ strings -n 5 FIXXER_RUMBLE_GPB64.dlo; strings -el -n 5 FIXXER_RUMBLE_GPB64.dlo; } | grep -niE '\\.dll|^api-ms-|^ext-ms-'"
# The files it names, its log lines and its panel's text.
ev strings-files "{ strings -n 5 FIXXER_RUMBLE_GPB64.dlo; strings -el -n 5 FIXXER_RUMBLE_GPB64.dlo; } | grep -nE '%s|FIXXER_Rumble|Settings|settings|_enabled|_intensity|invert_motors'"
ev strings-panel "{ strings -n 4 FIXXER_RUMBLE_GPB64.dlo; strings -el -n 4 FIXXER_RUMBLE_GPB64.dlo; } | grep -nE '^(Rumble|FIXXER Rumble Settings|Front Lockup|Rear Spin|Rear Lock|Suspension|Rev Limiter|Ground Effects|Engine Effects|Invert L/R motors|RESET|SAVE|Material.*|Ctrl\\+R to close|FIXXER 1001|V[0-9].*)\$'"
ev strings-thirdparty "{ strings -n 5 FIXXER_RUMBLE_GPB64.dlo; strings -el -n 5 FIXXER_RUMBLE_GPB64.dlo; } | grep -iE 'copyright|licen[cs]e|zlib|stb_|lodepng|imgui|miniz|nlohmann|Microsoft|SDK' | sort | uniq -c"
money FIXXER_RUMBLE_GPB64.dlo "'READ ME.md'" settings.txt
# Imports a plugin would need to go online, press keys, hook input, start other programs, write the registry or another
# process, read another process, share memory or catch every crash.
ev imports-absent "iat.py FIXXER_RUMBLE_GPB64.dlo | grep -iE 'ws2_32|wsock|wininet|winhttp|urlmon|SendInput|keybd_event|mouse_event|SetWindowsHookEx|CreateProcess|ShellExecute|WinExec|RegSetValue|RegCreateKey|WriteProcessMemory|ReadProcessMemory|OpenProcess|CreateRemoteThread|VirtualQuery|CreateFileMapping|AddVectoredExceptionHandler'"
# The code takes no fixed address in the game's program (gpbikes.exe loads at 0x140000000).
ev fixed-addresses "objdump -d FIXXER_RUMBLE_GPB64.dlo | grep -E '0x14[0-9a-f]{7}\\b'"
# Its only module handle is its own: GetModuleHandleExA (0x180020018) with flags 6 (from an address, refcount unchanged)
# and an address inside the plugin, then GetModuleFileNameA (0x180020000) for its folder.
dis FIXXER_RUMBLE_GPB64.dlo 18000112f 180001164
# Keyboard: every GetAsyncKeyState (0x1800202b0) and GetForegroundWindow (0x1800202b8) call site; RunTelemetry (export at
# 0x180001e10) calls the function at 0x180002840, which reads Ctrl (0x11) and R (0x52) with no focus check, and only
# while the panel is open asks the window in front for the cursor position and reads the left mouse button (0x01).
ev keys-callsites "objdump -d FIXXER_RUMBLE_GPB64.dlo | grep -E '# 0x1800202b0|# 0x1800202b8|call   0x180002840'"
dis FIXXER_RUMBLE_GPB64.dlo 180001e10 180001e39
dis FIXXER_RUMBLE_GPB64.dlo 180002840 180002975
# Controller: every XInputGetState (ordinal 2, 0x1800202d0) and XInputSetState (ordinal 3, 0x1800202c8) call site.
ev xinput-callsites "objdump -d FIXXER_RUMBLE_GPB64.dlo | grep -E '# 0x1800202d0|# 0x1800202c8'"
# Log at start-up: when rumble.log is over 256 KB (0x40000), it deletes rumble.log.old and renames rumble.log to it.
ev log-rotate "objdump -d FIXXER_RUMBLE_GPB64.dlo | grep -E '# 0x180020008|# 0x180020030|# 0x180020020'"
dis FIXXER_RUMBLE_GPB64.dlo 180001c29 180001cce
# VirtualProtect (0x180020248): every call site; each changes only the plugin's own .fptable section (0x180035000, 0x100
# bytes; see FIXXER_RUMBLE_GPB64.dlo.objdump-h.txt), the C runtime's table of the functions it loads by name.
ev virtualprotect "objdump -d FIXXER_RUMBLE_GPB64.dlo | grep -B6 '# 0x180020248'"
# Crash handler: the only SetUnhandledExceptionFilter (0x1800200c8) call passes 0, right before UnhandledExceptionFilter.
ev crash-filter "objdump -d FIXXER_RUMBLE_GPB64.dlo | grep -B3 -A3 '# 0x1800200c8'"
# What the READ ME says, and the settings it ships.
ev readme-claims "grep -nE 'Version|Ctrl|SAVE|Settings live|falls back|crash|XInput|Credits|SDK' 'READ ME.md'"
ev settings "cat settings.txt"
# P10: what the release asks of Windows in rights: each program's manifest, the service and driver calls, and every place a file asks
# for administrator rights or checks for them (privileges.py unpacks the release files itself, into a scratch folder).
ev privileges "privileges.py FIXXER_s_Rumble.zip"
