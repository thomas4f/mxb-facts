#!/usr/bin/env bash
# ProjectGPB2 v2 (README "build 4.2"; closed source: commands on the release files only).
# The folder holds 1794501261-projectgpb2-v2.zip, the download on https://gpb-mods.com/projectgpb2-2/
# (https://gpb-mods.com/wp-content/uploads/2026/11/1794501261-projectgpb2-v2.zip). This script unpacks the zip into the same
# folder, flat (every file name in it is unique).
# The plugins carry a symbol table, so objdump -d names the function each address is in; "fn" below lists, for each call of
# the named imports, the function it sits in. Addresses in .gpb2tx, an extra code section with no names, show as
# "<.gpb2tx+0x...>" (or, past its first symbol, "<.debug_rnglists+0x...>": objdump's nearest name, not a debug section).
. "$(dirname "$0")/../ev.sh"
(cd "$R" && unzip -o -q -j 1794501261-projectgpb2-v2.zip)
P="ProjectGPB2_core64.dlo ProjectGPB2_cam64.dlo ProjectGPB2_fx64.dlo"
ev files "sha256sum 1794501261-projectgpb2-v2.zip $P README.txt CREDITS.txt 'GPB 1 Performance.ini' 'GPB 2 Balanced.ini' 'GPB 3 Quality.ini' rain_heavy.wav rain_light.wav *.frag *.vert *.glsl"
ev file "file $P README.txt CREDITS.txt rain_heavy.wav rain_light.wav *.ini *.frag *.vert *.glsl; unzip -l 1794501261-projectgpb2-v2.zip"
pe ProjectGPB2_core64.dlo
pe ProjectGPB2_cam64.dlo
pe ProjectGPB2_fx64.dlo
# Code signing: the Security (certificate) directory of each plugin.
ev signature "for f in $P; do objdump -p \$f | grep -E 'file format|Security Directory'; done"
# The compiler and runtime built in (GCC / MinGW-w64), and names of third-party libraries (none found).
ev compiler "for f in $P; do echo \"== \$f\"; strings -n 6 \$f | grep -E '^GCC: |winpthreads/src' | sort -u; done"
ev strings-thirdparty "for f in $P; do { strings -n 5 \$f; strings -el -n 5 \$f; } | grep -iE 'copyright|licen[cs]e|stb_|zlib|miniz|lodepng|imgui|glew|glad|nlohmann|Mark Adler|Sean Barrett'; done"
# The README (the only document) and the sound credits: what they say on the points the card checks.
ev readme-claims "grep -nE 'Copy the|plugins\\\\|F6|F9|Ctrl\\+F9|default F8|Settings are saved|off by default|read from the game|gfx.cfg|exhaustsmoke|ReShade|VR|UNINSTALL|Delete the three|ProjGPB2.log|free|link to the download|CC BY|Wikimedia' README.txt; echo '== CREDITS.txt'; cat CREDITS.txt"
# Web addresses in the plugins (none) and the network libraries they could load.
ev strings-urls "{ strings -n 5 $P; strings -el -n 5 $P; } | grep -niE 'https?://|www\\.|\\.(com|net|org|io)\\b|ws2_32|wininet|winhttp|urlmon|socket'"
# Imports a plugin would need to go online, press keys, hook input, start programs, write the registry or another process,
# or start with Windows: none of them.
ev imports-absent "for f in $P; do iat.py \$f; done | grep -iE 'ws2_32|wsock|wininet|winhttp|urlmon|SendInput|keybd_event|mouse_event|SetWindowsHookEx|CreateProcess|ShellExecute|WinExec|RegSetValue|RegCreateKey|RegDeleteKey|RegOpenKey|WriteProcessMemory|CreateRemoteThread|DeleteFile|SHFileOperation'"
# Imports that change memory protection, read memory, look at threads and modules, catch exceptions or move files.
ev imports-notable "for f in $P; do echo \"== \$f\"; iat.py \$f | grep -E 'VirtualProtect|ReadProcessMemory|OpenProcess|OpenThread|SuspendThread|GetThreadContext|SetThreadContext|CreateToolhelp32Snapshot|K32EnumProcessModules|K32GetModuleInformation|AddVectoredExceptionHandler|SetUnhandledExceptionFilter|MoveFileExA|RemoveDirectoryA|CopyFileA|GetAsyncKeyState|GetForegroundWindow|GetClipboardData|LoadLibraryA|waveOutOpen|PlaySoundA'; done"
# The extra code section .gpb2tx: where it is (after the debug sections, with no function names) ...
ev sections "for f in $P; do echo \"== \$f\"; objdump -h \$f | grep -A1 -E ' \\.text|gpb2'; done"
# ... the names of Windows and OpenGL functions it looks up by name at run time, and its texts.
ev gpb2tx-strings "for f in $P; do echo \"== \$f\"; objcopy -O binary --only-section=.gpb2tx \$f \$W/s.bin; strings -n 5 \$W/s.bin | grep -E '[A-Za-z]{3}' | grep -vE '^(f+\\.|[A-Z]{2,4}[A-Z\\\\]*H)\$'; done"
# Every call of the imports above, with the function it is in.
ev callsites "for f in $P; do echo \"== \$f\"; objdump -d -C \$f | awk '/^[0-9a-f]+ <.*>:\$/{fn=\$0} /__imp_(VirtualProtect|ReadProcessMemory|OpenProcess|OpenThread|SuspendThread|GetThreadContext|SetThreadContext|K32EnumProcessModules|AddVectoredExceptionHandler|MoveFileExA|RemoveDirectoryA|CopyFileA|GetAsyncKeyState|GetForegroundWindow|GetClipboardData|SetClipboardData|LoadLibraryA)>/{match(\$0,/__imp_[A-Za-z0-9]+/); print \$1, substr(\$0,RSTART+6,RLENGTH-6), \"in\", fn}'; done"
# Exported plugin functions that jump into .gpb2tx (GetInterfaceVersion, RunTelemetry, EventInit).
ev exports-jump "objdump -d ProjectGPB2_core64.dlo | grep -A1 -E '^[0-9a-f]+ <(GetInterfaceVersion|RunTelemetry|EventInit)>:'"
# GetInterfaceVersion's code in .gpb2tx: GetProcAddress of GetCommandLineA in kernel32.dll, then a search for "-vr".
dis ProjectGPB2_core64.dlo 38c623910 38c623999
# RunTelemetry's code in .gpb2tx: on its first call it adds a vectored exception handler (at 38c623820) for the whole
# process. The handler compares the exception code with four codes, logs "CRASH 0x%08x at %s+0x%llx" up to 8 times with the
# module name, and returns 0 (EXCEPTION_CONTINUE_SEARCH): it handles nothing.
dis ProjectGPB2_core64.dlo 38c6233e0 38c623421
dis ProjectGPB2_core64.dlo 38c623820 38c623905
ev crash-codes "objdump -s --start-address=0x38c637bc0 --stop-address=0x38c637bd0 ProjectGPB2_core64.dlo; objdump -s --start-address=0x38c638736 --stop-address=0x38c638762 ProjectGPB2_core64.dlo"
# The screenshot key: every frame, the SwapBuffers hook calls .gpb2tx+0x1b80, which reads the key set as [menu] shot_key
# (default "119", F8) with GetAsyncKeyState, with no check of the window in front.
dis ProjectGPB2_core64.dlo 38c623b80 38c623c31
dis ProjectGPB2_core64.dlo 38c624a90 38c624af3
ev shot-key "objdump -s --start-address=0x38c6380c9 --stop-address=0x38c6380ce ProjectGPB2_core64.dlo; objdump -s --start-address=0x38c6381cb --stop-address=0x38c6381d4 ProjectGPB2_core64.dlo; objdump -s --start-address=0x38c638300 --stop-address=0x38c638306 ProjectGPB2_core64.dlo; objdump -d ProjectGPB2_core64.dlo | grep -E 'call   38c623b80'"
# The menu's keys: panel::on_swap first checks that the window in front belongs to the game's process.
dis ProjectGPB2_core64.dlo 38c54ca90 38c54cabd
# The game's graphics module: fx looks among the loaded modules for one that exports FolderName, ServerName and
# SetSystemProcAddress, and reads the exhaust tables in it only when its image size is 0x673000.
dis ProjectGPB2_fx64.dlo 1f1262910 1f12629a5
ev strings-exhaust "{ strings -n 6 ProjectGPB2_fx64.dlo; } | grep -E '^ProjectGPB2 fx: |gfx.cfg|exhaustsmoke'"
# OpenGL pointers swapped and the game's shader programs replaced (the texts the runs' logs show).
ev strings-hooks "for f in $P; do echo \"== \$f\"; strings -n 6 \$f | grep -E 'pointer\\(s\\) swapped|after another overhaul|OverhaulHookFor|materials: |shaders patched|sibling'; done"
# Another plugin's exports it calls when one is loaded (rutlink: RutsDrive, RutsGetMap) and the ruts settings' comments.
ev strings-rutlink "strings -n 5 ProjectGPB2_core64.dlo | grep -nE '^Ruts|ruts|physical'"
# Files it names: its folder, settings, logs, presets, screenshots, the bikes' gfx.cfg and the game's exhaustsmoke.cfg.
ev strings-files "for f in $P; do echo \"== \$f\"; { strings -n 5 \$f; strings -el -n 5 \$f; } | grep -E 'ProjGPB2|\\.ini|\\.log|\\.txt|\\.bin|\\.png|screenshots|presets|gfx\\.cfg|exhaustsmoke|\\.pkz|\\.wav' | grep -vE '^_Z|^\\.|^__' | sort -u; done"
money $P README.txt
# The rider ragdoll: it looks for the player's rider among the vertex buffers the game draws.
ev strings-ragdoll "strings -n 6 ProjectGPB2_core64.dlo | grep -E '^ragdoll: |rider rig|riders found'"
# P10: what the release asks of Windows in rights: each program's manifest, the service and driver calls, and every place a file asks
# for administrator rights or checks for them (privileges.py unpacks the release files itself, into a scratch folder).
ev privileges "privileges.py 1794501261-projectgpb2-v2.zip"
