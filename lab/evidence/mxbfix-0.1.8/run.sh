#!/usr/bin/env bash
# mxbfix v0.1.8 (open source, MIT): the release files and the source.
# The folder holds the two files of https://github.com/xAmped/mxbfix/releases/tag/v0.1.8: mxbfix.dlo and mxbfix.sig.
# The second argument is a checkout of https://github.com/xAmped/mxbfix at 90740b49b5486f64e2b48abccc86dd61d1ace200
# (the commit tag v0.1.8 points at). The rebuild downloads Zig 0.13.0 (the version build.sh names) from ziglang.org,
# checked by its SHA-256, into a scratch folder; it needs the network.
. "$(dirname "$0")/../ev.sh"
ev files "sha256sum mxbfix.dlo mxbfix.sig"
ev file "file mxbfix.dlo mxbfix.sig"
pe mxbfix.dlo
# Code signing: the Security (certificate) directory (empty: not signed).
ev signature "objdump -p mxbfix.dlo | grep -E 'file format|Security Directory'"
# The commit the tag points at, the repository's history up to it, and every file in the repository that `file` calls
# a program (executable, library, object or archive): none. The .h font data and the PNGs are data.
ev repo "cd \"\$SRC\" && git rev-parse HEAD && git tag --points-at HEAD && git log --format='%h %ad %s' --date=short && git ls-files | wc -l && git ls-files -z | xargs -0 file | grep -iE 'executable|PE32|ELF|object|archive|library' ; ls .github .github/* 2>&1"
# Rebuild with Zig 0.13.0 as build.sh does, in a copy of the checkout, and compare with the release byte for byte.
ev rebuild "curl -sSLo \"\$W/zig.tar.xz\" https://ziglang.org/download/0.13.0/zig-linux-x86_64-0.13.0.tar.xz && echo 'd45312e61ebcc48032b77bc4cf7fd6915c11fa16e4aad116b66c9468211230ea  '\"\$W/zig.tar.xz\" | sha256sum -c && tar -xf \"\$W/zig.tar.xz\" -C \"\$W\" && cp -r \"\$SRC\" \"\$W/src\" && (cd \"\$W/src\" && ZIG=\"\$W/zig-linux-x86_64-0.13.0/zig\" ./build.sh) && sha256sum mxbfix.dlo \"\$W/src/dist/mxbfix.dlo\" | sed \"s|\$W|\\\$W|\" && pecmp.py mxbfix.dlo \"\$W/src/dist/mxbfix.dlo\" | sed \"s|\$W|\\\$W|\""
# The update signature: the public key in src/update_key.h sits in the plugin, and mxbfix.sig is its signature of
# "mxbfix-update|0.1.8|<SHA-256 of mxbfix.dlo>", the message the plugin checks (src/update.c).
ev key-find "p256.py find c5a5101755b6081e mxbfix.dlo"
ev sig-verify "p256.py verify-der c5a5101755b6081ec547ad64cbd6f3338505a8459220c548eab881dc5e48494f8a3d406841118205e52be4f127828cb7bd30e60f215e4a5ad63e24bc7fc76455 mxbfix.sig \"mxbfix-update|0.1.8|\$(sha256sum mxbfix.dlo | cut -c1-64)\""
# Web addresses and host names in the plugin: GitHub (update check and download, links on its page) and the report server.
ev strings-urls "{ strings -n 6 mxbfix.dlo; strings -el -n 6 mxbfix.dlo; } | grep -nE 'https?://|github\\.com|workers\\.dev'"
# Imports that would press keys or click, hook input, start a program, write the registry, write into or open another
# process, inject a thread or share memory (none).
ev imports-absent "iat.py mxbfix.dlo | grep -iE 'SendInput|keybd_event|mouse_event|SetWindowsHookEx|CreateProcess|WinExec|RegSetValue|RegCreateKey|RegDeleteKey|RegDeleteValue|WriteProcessMemory|OpenProcess|CreateRemoteThread|CreateFileMapping|MapViewOfFile|CreateNamedPipe|socket|bind|listen'"
# Imports it does use for the network, the registry, input, the game's code, crashes and opening links.
ev imports-used "iat.py mxbfix.dlo | grep -E 'WinHttp|RegGetValue|GetAsyncKeyState|GetCursorPos|GetForegroundWindow|VirtualProtect|FlushInstructionCache|ReadProcessMemory|SetUnhandledExceptionFilter|AddVectoredExceptionHandler|ShellExecute|LoadLibrary|IsHungAppWindow|K32EnumProcessModules'"
# Source searches at the commit.
# Every place the source starts a connection: three WinHttpConnect calls, to api.github.com, github.com and the report server.
ev src-connections "cd \"\$SRC\" && grep -rn 'WinHttpConnect\\|#define API_HOST\\|#define DL_HOST\\|#define RELAY_HOST' src"
# Every write to the game's code: fix_apply_patch and fix_apply_patches (src/fixes.c), called by the fixes listed in ALL[];
# each fix's build check. suspension-nan-guard is compiled but not in ALL[], so it never installs.
ev src-patches "cd \"\$SRC\" && grep -rn 'VirtualProtect\\|fix_apply_patch' src; sed -n '17,24p' src/fixes.c; grep -rn 'define [A-Z]*_BUILD' src"
# Registry: one read (the CPU name), no write. Processes: no process started; ShellExecuteW only on its page's buttons.
ev src-registry "cd \"\$SRC\" && grep -rn 'Reg[A-Z][A-Za-z]*(\\|ShellExecute\\|CreateProcess' src"
# Files outside its own folders that it opens: trainer files, mxbmrp3's crash folder, Windows' Application event log.
ev src-others "cd \"\$SRC\" && grep -rn 'profiles\\\\\\\\\\|mxbmrp3\\\\\\\\\\|EvtQuery(' src"
# What the uploader leaves out of a report (path members and raw CPU values) before it goes.
ev src-payload "cd \"\$SRC\" && grep -n 'RAW\\[\\]\\|\"\\\\\"path\\\\\"\"\\|install_id\\|has_path(payload' src/upload.c"
# Third-party code and credits: the MinGW-w64 runtime Zig builds in, and the README's credits.
ev thirdparty "strings -n 6 mxbfix.dlo | grep -n 'Mingw-w64'; cd \"\$SRC\" && grep -n -A5 '^## Credits' README.md"
money mxbfix.dlo
# The real-game runs (lab/results/mxbfix-0.1.8/): the demo's mxbikes.exe build, from the DirectInput key the game wrote
# (name, then the program's time stamp and size); the plugin's fixes are written for build 6A21833D.
export RES="$OUT/../../results/mxbfix-0.1.8"
ev demo-build "grep -o 'MXBIKES.EXE[0-9A-F]*' \"\$RES/baseline-windows/registry.txt\" | sort -u"
# What the plugin wrote in the real game, and the update check it tried (blocked by the firewall).
ev run-writes "for r in ride-pause ride-long; do echo \"== \$r\"; grep -E 'mxbfix' \"\$RES/\$r-windows/procmon.txt\" | grep -E 'WriteFile|SetRename|CreateFile.*(SUCCESS)' | awk '{\$1=\"\"; print}' | sed -E 's/D:.a._temp.realgame.run-[a-z-]+.//' | grep -v 'plugins.mxbfix.dlo ' | sort -u; cat \"\$RES/\$r-windows/network.txt\" | tail -n 2; done"
# The one write on mxbfix.dlo itself in each run is Windows' paging I/O as it maps the plugin, just before "Load Image";
# the plugin's hash after the runs is the release's (plugins.sha256).
ev dlo-load "for r in ride-pause ride-long; do echo \"== \$r\"; zcat \"\$RES/\$r-windows/raw/procmon.csv.gz\" | grep -E '(WriteFile|Load Image)\",\"[^\"]*plugins.mxbfix.dlo' | cut -d, -f1,4,6- | sed -E 's/D:.a._temp.realgame.run-[a-z-]+.//'; grep mxbfix \"\$RES/\$r-windows/plugins.sha256\"; done"
