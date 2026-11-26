#!/usr/bin/env bash
# MXB Ragdoll 1.0 (closed source: commands on the release files only).
# The folder holds MXB-Ragdoll-v1.0.zip, from https://www.mediafire.com/file/k34umlk5ta5n39g/MXB-Ragdoll-v1.0.zip/file (the
# download of https://mxb-mods.com/mx-bikes-ragdoll-v1-0-2/). This script unpacks it into the same folder and links the two
# program files under their own names at the top of the folder, so the outputs are named after them.
. "$(dirname "$0")/../ev.sh"
(cd "$R" && unzip -o -q MXB-Ragdoll-v1.0.zip \
  && ln -sf "MXB-Ragdoll-v1.0/Manual Install/plugins/mxb_ragdoll.dlo" mxb_ragdoll.dlo \
  && ln -sf "MXB-Ragdoll-v1.0/Auto Install/MXB-Ragdoll-Setup.exe" MXB-Ragdoll-Setup.exe)
ev files "sha256sum MXB-Ragdoll-v1.0.zip; cd MXB-Ragdoll-v1.0 && find . -type f | LC_ALL=C sort | xargs -d '\n' sha256sum"
ev file "unzip -l MXB-Ragdoll-v1.0.zip; cd MXB-Ragdoll-v1.0 && find . -type f | LC_ALL=C sort | xargs -d '\n' file"
pe mxb_ragdoll.dlo
pe MXB-Ragdoll-Setup.exe
# Code signing: the Security (certificate) directory of each program file.
ev signature "objdump -p mxb_ragdoll.dlo MXB-Ragdoll-Setup.exe | grep -E 'file format|Security Directory'"
# The setup's payload (its RT_RCDATA resource): every file in it, by SHA-256, against the files of the Manual Install folder.
ev payload "rsrc.py MXB-Ragdoll-Setup.exe; mxbp.py MXB-Ragdoll-Setup.exe > \$W/p.txt; cat \$W/p.txt; grep -E '^[0-9a-f]{64}' \$W/p.txt | awk '{print \$1\"  \"\$2}' | sort > \$W/a; (cd 'MXB-Ragdoll-v1.0/Manual Install/plugins' && find . -type f | sed 's|^\./||' | LC_ALL=C sort | xargs -d '\n' sha256sum) | sort > \$W/b; diff \$W/a \$W/b && echo 'the payload holds the same 15 files as Manual Install\\plugins, byte for byte'"
# The manual installer's scripts.
ev scripts "cd 'MXB-Ragdoll-v1.0/Manual Install' && cat INSTALL.bat UNINSTALL.bat && grep -nE 'Copy-Item|Remove-Item|New-Item|ExtractToFile|HKCU|libraryfolders|Get-Process|foreach \\(\\\$name' tools/install.ps1 tools/uninstall.ps1"
# Every web address in the two programs.
ev strings-urls "for f in mxb_ragdoll.dlo MXB-Ragdoll-Setup.exe; do echo \"== \$f\"; { strings -n 6 \$f; strings -el -n 6 \$f; } | grep -nE 'https?://|www\\.|steam://' | grep -v 'clang version'; done"
# What the plugin changes in the game: its log lines about hooks, patches and the trainer guard.
ev strings-hooks "{ strings -n 6 mxb_ragdoll.dlo; strings -el -n 6 mxb_ragdoll.dlo; } | grep -nE 'import-table|scene hook|call site|bone override|bone_hook|trainer guard|trainer_guard|DirectInput hooked|xinput64.dli hooked|held back|OpenAL|muffled|EFX|VirtualProtect|stub|kicking off|detached|ODE world|discovery'"
# Online: the setting, its menu text and the log lines for a server.
ev strings-online "{ strings -n 6 mxb_ragdoll.dlo; strings -el -n 6 mxb_ragdoll.dlo; } | grep -niE 'online|server|offline'"
# Files of the game the plugin reads (the save folder, the profile, the respawn binding).
ev strings-profile "{ strings -n 6 mxb_ragdoll.dlo; strings -el -n 6 mxb_ragdoll.dlo; } | grep -nE 'PiBoSo|profile|global.ini|controls.txt|respawn (is|binding)|save folder'"
# What the setup reads and writes, and the texts it shows.
ev strings-setup "{ strings -n 6 MXB-Ragdoll-Setup.exe; strings -el -n 6 MXB-Ragdoll-Setup.exe; } | grep -nE 'pkz|\\.fnt|Valve|Steam App|libraryfolders|appmanifest|CI\\\\Policy|VerifiedAndReputable|Smart App|MXB-Ragdoll-Setup.log|\\.setup-tmp|Nothing outside|Nothing else|Keep my settings|removed|Remove|administrator|--install-now|is encrypted|Launch MX Bikes|tga|\\.log'"
ev strings-thirdparty "for f in mxb_ragdoll.dlo MXB-Ragdoll-Setup.exe; do { strings -n 6 \$f; strings -el -n 6 \$f; } | grep -iE 'copyright|licen[cs]e|zlib|stb_|lodepng|nlohmann|imgui|miniz|lz4|zstd|mxbmrp|clang version|llvm-mingw/llvm-mingw\$'; done | sort | uniq -c"
ev strings-money "for f in mxb_ragdoll.dlo MXB-Ragdoll-Setup.exe MXB-Ragdoll-v1.0/README.txt 'MXB-Ragdoll-v1.0/Manual Install/plugins/mxb_ragdoll.ini'; do echo \"== \$f\"; { strings -n 6 \"\$f\"; strings -el -n 6 \"\$f\"; } | grep -nE 'https?://|www\\.|[Ss]hop|[Bb]uy |[Pp]rice|[Pp]remium|[Pp]atreon|[Pp]ay[Pp]al|[Kk]o-?fi|[Dd]onat|[Cc]offee|It.s free' | grep -v 'clang version'; done"
# Imports a program would need to connect, listen, press keys, hook input system-wide, start programs, write the registry or another process, or share memory.
ev imports-absent "{ iat.py mxb_ragdoll.dlo; iat.py MXB-Ragdoll-Setup.exe; objdump -p mxb_ragdoll.dlo MXB-Ragdoll-Setup.exe | grep 'DLL Name'; } | grep -iE 'ws2_32|wsock|wininet|winhttp|urlmon|SendInput|keybd_event|mouse_event|SetWindowsHookEx|WriteProcessMemory|CreateRemoteThread|CreateProcess|WinExec|RegSetValue|RegCreateKey|RegDeleteKey|CreateFileMapping|SetUnhandledExceptionFilter.*dlo'"
ev imports-present "iat.py mxb_ragdoll.dlo | grep -E 'VirtualProtect|FlushInstructionCache|ReadProcessMemory|AddVectoredExceptionHandler|GetAsyncKeyState|GetForegroundWindow|ShellExecuteA|LoadLibraryA|SHGetFolderPathA'; iat.py MXB-Ragdoll-Setup.exe | grep -E 'RegGetValueW|ShellExecute|DeleteFileW|MoveFileExW|RemoveDirectoryW|CreateToolhelp32Snapshot|OpenProcess|SetUnhandledExceptionFilter|GetTempPathW'"
# The plugin keeps its function names: the ones that hook, patch, write into the game's physics or handle crashes.
ev symbols "objdump -d mxb_ragdoll.dlo | grep -E '^[0-9a-f]+ <' | sed 's/^[0-9a-f]* <\\(.*\\)>:/\\1/' | c++filt | grep -E '^(camera::(Install|RedirectCall|Uninstall|.*Patch)|input::(Install|Uninstall|Replay|TakePress|.*Hook|.*H_|.*KeyState)|audio::Muffle|trainerfix::(Start|Stop|.*H_Compare|.*LiveClear)|game::(Write|Set|SafeRead|Discover|ReadBikeObstacles|TerrainHeight)|ragdoll::(OverrideBones|H_Skeleton|KickRider|ApplyToGame|Startup|EventInit|OnTelemetry|GameFocused)|crashlog::)' | sed 's/(.*//' | sort -u"
# What Startup installs (always, before any event) and where the online setting (g_offline) is read.
ev startup-installs "objdump -d mxb_ragdoll.dlo | awk '/^[0-9a-f]+ <.*>:\$/{fn=\$2} /call.*<_ZN6camera7InstallE|call.*<_ZN5input7InstallE|call.*<_ZN10trainerfix5StartE|call.*<_ZN8crashlog7InstallE/{print fn, \$1, \$NF}' | c++filt; echo '-- reads of g_offline, by function:'; objdump -d mxb_ragdoll.dlo | awk '/^[0-9a-f]+ <.*>:\$/{fn=\$2} /<_ZN7ragdoll9g_offlineE>/{print fn}' | c++filt | sort | uniq -c"
# Keyboard: every GetAsyncKeyState use, the check that the window in front is the game's, and the reads behind it.
ev keys-callsites "objdump -d mxb_ragdoll.dlo | awk '/^[0-9a-f]+ <.*>:\$/{fn=\$2} /<__imp_GetAsyncKeyState>|<__imp_GetForegroundWindow>|call   18000eca0|call   18005f910/{print fn, \$0}' | c++filt"
dis mxb_ragdoll.dlo 18000eca0 18000ecd5
dis mxb_ragdoll.dlo 1800109ba 180010a25
dis mxb_ragdoll.dlo 18002bca0 18002bcf3
# Respawn: Replay sets the press the hooked DirectInput and XInput reads hand to the game (g_inject), and who reads it.
dis mxb_ragdoll.dlo 180078c50 180078c62
ev inject "objdump -d mxb_ragdoll.dlo | awk '/^[0-9a-f]+ <.*>:\$/{fn=\$2} /g_injectE>|call.*<_ZN5input6ReplayEv>/{print fn}' | c++filt | sort | uniq -c"
# Crash handler: installed with AddVectoredExceptionHandler; it logs access violations and similar faults (at most 8) and returns 0.
dis mxb_ragdoll.dlo 18007b9aa 18007b9b8
dis mxb_ragdoll.dlo 18007b9f0 18007ba54
dis mxb_ragdoll.dlo 18007c0f7 18007c10c
# The shipped settings' defaults that G3 and G5 name: online use off, get back on (the respawn hold-back) on.
ev ini-defaults "grep -nE '^(online|get_back_on) =' 'MXB-Ragdoll-v1.0/Manual Install/plugins/mxb_ragdoll.ini'"
