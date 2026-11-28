#!/usr/bin/env bash
# Graphics Overhaul 2.4.0 (closed source: commands on the release files only).
# The folder holds 1794860747-graphics-overhaul.zip, the download of https://mxb-mods.com/graphics-overhaul-2/ (from
# https://mxb-mods.com/wp-content/uploads/2026/11/1794860747-graphics-overhaul.zip). This script unpacks it into the same
# folder (README.txt and plugins\) and links the plugin at the top of the folder, so the outputs are named after it.
# For the rig comparison the folder also holds mxbikes-beta21f.exe, the MX Bikes demo installer named in lab/real-game/games.json
# (SHA-256 76feb83746e785310e8858938dd50b5e0685d1b0004480d5d1c2d4fc21f11949); no game file is committed, only the output.
. "$(dirname "$0")/../ev.sh"
(cd "$R" && unzip -o -q 1794860747-graphics-overhaul.zip && ln -sf plugins/overhaul64.dlo overhaul64.dlo)
# fn <import>: the functions of the plugin that call or load that import (it ships with its function names).
fns() { echo "objdump -d overhaul64.dlo | awk '/^[0-9a-f]+ <.*>:\$/{fn=\$2} /<__imp_$1>/{print fn}' | c++filt | sort | uniq -c"; }
ev files "sha256sum 1794860747-graphics-overhaul.zip; find README.txt plugins -type f | LC_ALL=C sort | xargs -d '\n' sha256sum"
ev file "unzip -l 1794860747-graphics-overhaul.zip; find README.txt plugins -type f | LC_ALL=C sort | xargs -d '\n' file"
pe overhaul64.dlo
# Code signing: the Security (certificate) directory.
ev signature "objdump -p overhaul64.dlo | grep -E 'file format|Security Directory'"
# Every web address in the plugin and the text files.
ev strings-urls "for f in overhaul64.dlo README.txt plugins/overhaul/sounds/CREDITS.txt plugins/presets/Low-end.ini; do echo \"== \$f\"; { strings -n 6 \$f; strings -el -n 6 \$f; } | grep -nE 'https?://|www\\.' | grep -v 'gcc.gnu.org'; done"
# Imports a program would need to connect, listen, start programs, write the registry or another process, hook input system-wide or send input.
ev imports-absent "{ iat.py overhaul64.dlo; objdump -p overhaul64.dlo | grep 'DLL Name'; } | grep -iE 'ws2_32|wsock|wininet|winhttp|urlmon|dnsapi|SendInput|SetWindowsHookEx|WriteProcessMemory|CreateRemoteThread|CreateProcess|WinExec|RegSetValue|RegCreateKey|RegDeleteKey|RegOpenKey|advapi32'"
ev imports-present "iat.py overhaul64.dlo | grep -E 'VirtualProtect|K32EnumProcessModules|ReadProcessMemory|SuspendThread|GetThreadContext|AddVectoredExceptionHandler|keybd_event|SetWindowLongPtrA|GetAsyncKeyState|GetForegroundWindow|ShellExecuteA|CreateFileMappingA|MapViewOfFile|MoveFileExA|DeleteFileA|CopyFileA|RemoveDirectoryA|CreateDirectoryA|GetLogicalDrives|GetClipboardData|SetClipboardData|LoadLibraryA|GetEnvironmentVariableA'"
# Which of its functions use each of those imports.
ev callers "for i in VirtualProtect K32EnumProcessModules ReadProcessMemory SuspendThread GetThreadContext AddVectoredExceptionHandler keybd_event SetWindowLongPtrA GetAsyncKeyState GetForegroundWindow ShellExecuteA CreateFileMappingA MoveFileExA DeleteFileA CopyFileA RemoveDirectoryA CreateDirectoryA GetLogicalDrives GetClipboardData SetClipboardData; do echo \"== \$i\"; objdump -d overhaul64.dlo | awk -v i=\"<__imp_\$i>\" '/^[0-9a-f]+ <.*>:\$/{fn=\$2} index(\$0, i){print fn}' | c++filt | sort | uniq -c; done"
# Its own function names, by part (hooks, the menu, the ragdoll, the crash and freeze watch, the ruts link).
ev symbols "objdump -d overhaul64.dlo | grep -E '^[0-9a-f]+ <' | sed 's/^[0-9a-f]* <\\(.*\\)>:/\\1/' | c++filt | grep -E '^((\\(anonymous namespace\\)::)?(swap_pointers|scan_ranges|sibling_hooks|hk_[A-Za-z]+)|hooks_|OverhaulHookFor|rutlink::|ragdoll::(load_rig|before_draw|after_draw|active|set_telemetry)|materials::on_use_program|panel::\\(anonymous namespace\\)::(bus|panel_proc|share_preset|export_preset|import_clipboard|fb_list|browse_start|user_dir|rename_commit|list_presets)|panel::on_swap|crash_catcher|hang_watch|make_presets_dir|presets_dir|Startup|Shutdown)' | sort -u"
# Pointer hooks: scan_ranges lists, for every loaded module but itself, the writable sections (and the import table) of the
# game's program and of every other .dlo that doesn't export OverhaulHookFor; swap_pointers rewrites the pointers it finds there.
dis overhaul64.dlo 38c5824a0 38c5829d0
ev hook-strings "objdump -s -j .rdata --start-address=0x38c5e5bd0 --stop-address=0x38c5e5c30 overhaul64.dlo | tail -n +5"
dis overhaul64.dlo 38c582330 38c5823d0
# The ruts link: if another loaded module exports RutsDrive and RutsGetMap, it calls them.
dis overhaul64.dlo 38c54df40 38c54e14a
ev ruts-strings "objdump -s -j .rdata --start-address=0x38c5dbb00 --stop-address=0x38c5dbb58 overhaul64.dlo | tail -n +5"
# Keys: the focus checks in front of the key reads (the frame hook, and the menu's on_swap).
dis overhaul64.dlo 38c519bb9 38c519c0e
dis overhaul64.dlo 38c56bf0b 38c56bf3d
ev keys-callsites "objdump -d overhaul64.dlo | awk '/^[0-9a-f]+ <.*>:\$/{fn=\$2} /<__imp_GetAsyncKeyState>|<__imp_GetForegroundWindow>|L7pressedEib>/{print fn}' | c++filt | sort | uniq -c"
# The menu's window hook: it handles messages only while the menu is open (s_open), else hands them on.
dis overhaul64.dlo 38c560330 38c56034a
# keybd_event: media keys (0xB0 next track, 0xB1 previous track, 0xB3 play/pause), pressed and released, in the menu's draw.
dis overhaul64.dlo 38c569838 38c56986c
dis overhaul64.dlo 38c56b350 38c56b3b8
# The shared memory: a 32-byte block named Local\OverhaulPanels_<process id>.
dis overhaul64.dlo 38c54e3f0 38c54e46f
ev bus-uses "objdump -d overhaul64.dlo | grep -A10 'call.*L3busEv>' | grep -E 'call.*L3busEv>|\\(%r[a-z0-9]+\\)|0x[0-9a-f]+\\(%r(ax|bx|si)\\)' | head -40; strings -n 6 overhaul64.dlo | grep -n 'OverhaulPanels'"
# Crash handler: for an access violation it logs, then returns 0 so the crash goes on.
dis overhaul64.dlo 38c51b120 38c51b14b
# Files: what it writes and moves (its folder, the old shaders folder, presets, screenshots).
ev strings-files "{ strings -n 4 overhaul64.dlo; strings -el -n 4 overhaul64.dlo; } | grep -nE '^(overhaul\\\\|shaders|shaders\\.pak|shaders_old_unused|overhaul\\.log|overhaul\\.ini|keybinds\\.ini|race_offset\\.txt|presets\\\\|\\*\\.ini|shot\\.req|shot\\.bmp|compare\\\\|_vanilla\\.bmp|_overhaul\\.bmp|shader_dump_%02d\\.txt|rig_default_mx\\.bin|Documents|OneDrive|USERPROFILE|::drives|Deleted \"|Renamed to \"|Imported |Export failed.*)\$'"
# presets_dir: the data folder (plugins\overhaul\) with its last 9 characters cut and presets\ added: plugins\presets\.
dis overhaul64.dlo 38c585ee0 38c585fd0
ev startup-calls "objdump -d overhaul64.dlo | awk '/^000000038c516340 <Startup>:/{p=1} p&&/^\$/{exit} p' | grep -E 'call' | grep -oE '<[^>]+>' | c++filt | grep -vE 'basic_string|operator|chkstk' | uniq"
# The menu's texts on the store, Discord, Spotify and lyrics (money, links, what it offers).
ev strings-money "{ strings -n 6 overhaul64.dlo; strings -el -n 6 overhaul64.dlo; } | grep -nE 'https?://|[Ss]tore|Advanced|ADVANCED|[Ss]hop|[Bb]uy |[Pp]rice|[Pp]remium|[Pp]atreon|[Pp]ay[Pp]al|[Kk]o-?fi|[Dd]onat|Coming soon|Spotify|lyrics|Discord|#presets' | grep -v 'gcc.gnu.org'"
# The settings file it writes on first start: its defaults and the sections for its sibling plugins.
ev strings-ini "strings -n 4 overhaul64.dlo | awk '/^; MX Bikes Overhaul - ragdoll/{p=1} p{print} /^max_fit_error=/{exit}' | grep -nE '^(; MX Bikes|; Hotkeys|graphics=|ragdoll=|hotkeys=|materials=|ruts=|physical=|physical_probe=|terrain_log=|camera=|exhaust=|sound=|injuries=|rain=|snow=|\\[)|camera64|exhaust64|soundplus64|injuries64|EXPERIMENTAL|digs the ruts'"
# Online: any text about servers, online or multiplayer.
ev strings-online "{ strings -n 6 overhaul64.dlo; strings -el -n 6 overhaul64.dlo; } | grep -niE 'online|server|multiplayer|offline'"
# The ragdoll and the rider mesh: its log texts.
ev strings-ragdoll "{ strings -n 6 overhaul64.dlo; } | grep -nE '^ragdoll: |rider rig|rig file'"
# The rig file it ships: its header, bone names and mesh names.
ev rig "head -c 8 plugins/overhaul/rig_default_mx.bin | od -c | head -1; strings -n 4 plugins/overhaul/rig_default_mx.bin | grep -nE '^(OVRIG01|riderRIG_[A-Za-z0-9]+|gopro|lod[0-9]|cockpit|shadow)\$' | head -90"
# The shader pack: OVP1, XORed with an xorshift32 stream (its decode loop in pak_lookup), listed entry by entry.
dis overhaul64.dlo 38c5833b8 38c583420
ev shaders-pak "ovpak.py plugins/overhaul/shaders.pak"
# Third-party code: the compiler and runtime names, and any licence or library name.
ev strings-thirdparty "{ strings -n 6 overhaul64.dlo; } | grep -iE 'GCC: |mingw-w64-libraries|winpthreads|libgcc|copyright|licen[cs]e|zlib|stb_|imgui|miniz|lodepng|nlohmann|Jimenez|FXAA' | sort | uniq -c"
# The rig file against the game's own default rider: the demo's rider.pkz (is any entry encrypted?), then each mesh's vertices
# looked up in the default rider's model files.
ev rig-vs-game "sha256sum mxbikes-beta21f.exe; 7z x -y -o\$W mxbikes-beta21f.exe rider.pkz > /dev/null; (cd \$W && sha256sum rider.pkz); echo \"encrypted entries: \$(7z l -slt \$W/rider.pkz | grep -c 'Encrypted = +')\"; 7z x -y -o\$W/r \$W/rider.pkz 'rider/riders/default_mx/*.edf' > /dev/null; (cd \$W/r && sha256sum rider/riders/default_mx/*.edf && rigcmp.py \"\$OLDPWD/plugins/overhaul/rig_default_mx.bin\" rider/riders/default_mx/rider.edf rider/riders/default_mx/c_rider.edf rider/riders/default_mx/rider_s.edf)"
