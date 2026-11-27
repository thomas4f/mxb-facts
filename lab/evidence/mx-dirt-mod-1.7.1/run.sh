#!/usr/bin/env bash
# MX Dirt Mod 1.7.1 (open source, GPL-3.0: the release files and the source).
# The folder holds the two files of https://github.com/kadenball/mx-dirt-mod/releases/tag/v1.7.1, by their names:
# MX-Dirt-Mod-1.7.1.zip and MX-Dirt-Mod-1.7.1.sha256.txt.
# The second argument is a checkout of https://github.com/kadenball/mx-dirt-mod at
# 5c300cccd92f533e415b7258ee084feb2d35fc97 (tag v1.7.1).
# The zip names its files with backslashes (plugins\mx_dirt.dlo); this script unpacks them into folders
# (plugins/mx_dirt.dlo) in the same folder.
. "$(dirname "$0")/../ev.sh"
(cd "$R" && python3 -I -c '
import os, zipfile, sys
z = zipfile.ZipFile(sys.argv[1])
for i in z.infolist():
    n = i.filename.replace("\\", "/")
    assert not n.startswith("/") and ".." not in n.split("/")
    os.makedirs(os.path.dirname(n) or ".", exist_ok=True)
    open(n, "wb").write(z.read(i))
' MX-Dirt-Mod-1.7.1.zip)
ev files "sha256sum MX-Dirt-Mod-1.7.1.zip MX-Dirt-Mod-1.7.1.sha256.txt plugins/mx_dirt.dlo plugins/mx_dirt_render.dlo plugins/mx_dirt.ini plugins/mx_dirt_render.ini install/Install.ps1 install/Uninstall.ps1 'launcher/MX Dirt Mod.cmd' launcher/MXDirtLauncher.ps1 Install.cmd Uninstall.cmd LICENSE README.txt SUPPORTED_EXE.txt; echo '--- the author-published hash list:'; cat MX-Dirt-Mod-1.7.1.sha256.txt"
ev file "unzip -l MX-Dirt-Mod-1.7.1.zip; file plugins/mx_dirt.dlo plugins/mx_dirt_render.dlo install/*.ps1 launcher/*.ps1 *.cmd launcher/*.cmd"
# Every file in the release other than the two plugins is the same file as in the source at the commit.
ev same-as-source "for p in 'install/Install.ps1:install/Install.ps1' 'install/Uninstall.ps1:install/Uninstall.ps1' 'launcher/MX Dirt Mod.cmd:launcher/MX Dirt Mod.cmd' 'launcher/MXDirtLauncher.ps1:launcher/MXDirtLauncher.ps1' 'plugins/mx_dirt.ini:src/core/mx_dirt.ini' 'plugins/mx_dirt_render.ini:src/render/mx_dirt_render.ini' 'Install.cmd:install/Install.cmd' 'Uninstall.cmd:install/Uninstall.cmd' 'LICENSE:LICENSE' 'README.txt:README.md' 'SUPPORTED_EXE.txt:SUPPORTED_EXE.txt'; do a=\"\${p%%:*}\"; b=\"\${p##*:}\"; cmp \"\$a\" \"\$SRC/\$b\" && echo \"same: \$a = \$b at the commit\"; done"
# The usual three for each plugin (ev.sh's pe, with the file in plugins/): headers, imports and exports; sections; import table.
for n in mx_dirt mx_dirt_render; do
  ev $n.dlo.objdump-p "objdump -p plugins/$n.dlo | awk '/^The Function Table|^PE File Base Relocations/{exit} 1'"
  ev $n.dlo.objdump-h "objdump -h plugins/$n.dlo"
  ev $n.dlo.iat "iat.py plugins/$n.dlo"
done
# Code signing: the Security (certificate) directory of each program file.
ev signature "objdump -p plugins/mx_dirt.dlo plugins/mx_dirt_render.dlo | grep -E 'file format|Security Directory'"
# Imports a plugin would need to go online, press keys, hook input, write the registry or another process, start
# with Windows, share memory or catch every crash (none in either plugin).
ev imports-absent "{ iat.py plugins/mx_dirt.dlo; iat.py plugins/mx_dirt_render.dlo; } | grep -iE 'ws2_32|wsock|wininet|winhttp|urlmon|SendInput|keybd_event|mouse_event|SetWindowsHookEx|RegSetValue|RegCreateKey|WriteProcessMemory|OpenProcess|CreateRemoteThread|CreateFileMapping|SetUnhandledExceptionFilter|AddVectoredExceptionHandler|ShellExecute|WinExec'"
# What the plugins import to change code in memory, read the game's memory, read a key and start a program.
ev imports-core "iat.py plugins/mx_dirt.dlo | grep -E 'VirtualProtect|VirtualAlloc|VirtualQuery|FlushInstructionCache|CreateThread|DeleteFileA|MoveFileExA|CreateDirectoryA|Crypt'"
ev imports-render "iat.py plugins/mx_dirt_render.dlo | grep -E 'VirtualProtect|VirtualAlloc|VirtualQuery|FlushInstructionCache|ReadProcessMemory|CreateProcessW|GetAsyncKeyState|GetForegroundWindow|SetForegroundWindow|FindWindowW|CreateFileW|BCrypt'"
# Web addresses in the plugins, and any web request in the scripts (none).
ev strings-urls "for f in plugins/mx_dirt.dlo plugins/mx_dirt_render.dlo; do echo \"== \$f\"; { strings -n 6 \$f; strings -el -n 6 \$f; } | grep -niE 'https?://|www\\.'; done; echo '== scripts'; grep -niE 'https?://|Invoke-WebRequest|Invoke-RestMethod|WebClient|Net\\.Http|DownloadFile|BitsTransfer|curl|wget' install/*.ps1 launcher/*.ps1 *.cmd launcher/*.cmd"
# What the installer, uninstaller and launcher do to files, the registry, shortcuts and programs.
ev scripts-actions "grep -nE 'Move-Item|Copy-Item|Remove-Item|Start-Process|HKCU|HKLM|Set-ItemProperty|New-ItemProperty|CreateShortcut|Unblock-File|libraryfolders|testing\\.dfm|Retire|living_dirt' install/Install.ps1 install/Uninstall.ps1 launcher/MXDirtLauncher.ps1 Install.cmd Uninstall.cmd 'launcher/MX Dirt Mod.cmd' | cut -c1-260"
# The supported game build: the hash both plugins compare mxbikes.exe with, in their text and in SUPPORTED_EXE.txt.
ev supported-exe "cat SUPPORTED_EXE.txt; strings -n 64 plugins/mx_dirt.dlo | grep -n 9e792d7aed1dc40df11eea51d1a6d0519daec7be2b65609905df8c9de804a291"
# Rebuild (T4): Zig 0.16.0 for Linux, from ziglang.org (needs the network), with the flags of build.ps1 and
# build_render.ps1 at the commit, then a byte comparison with the release's plugins.
ev rebuild "H=\$PWD && cd \$W && curl -sSfLO https://ziglang.org/download/0.16.0/zig-x86_64-linux-0.16.0.tar.xz && echo '70e49664a74374b48b51e6f3fdfbf437f6395d42509050588bd49abe52ba3d00  zig-x86_64-linux-0.16.0.tar.xz' | sha256sum -c && tar xf zig-x86_64-linux-0.16.0.tar.xz && Z=\$W/zig-x86_64-linux-0.16.0/zig && \$Z version && export ZIG_GLOBAL_CACHE_DIR=\$W/gc ZIG_LOCAL_CACHE_DIR=\$W/lc && F='-shared -target x86_64-windows-gnu -std=c11 -O2 -msse2 -Wall -Wextra -Werror -ffp-contract=off -fno-fast-math -fms-extensions' && (cd \"\$SRC\" && grep -nE \"'-shared'|-luser32|-lopengl32\" build.ps1 build_render.ps1 && \$Z cc \$F -I src/core -I src/shared src/core/mx_dirt.c src/core/mxdirt_session.c src/core/mxdirt_contact.c src/core/mxdirt_wheel_sample.c src/core/mxdirt_frame_snapshot.c src/core/mxdirt_height_field.c src/core/mxdirt_height_publication.c src/core/mxdirt_publication_hooks.c src/core/mxdirt_transport.c src/core/mxdirt_native_height.c src/core/mxdirt_patches.c -luser32 -ladvapi32 -o \$W/mx_dirt.dll && \$Z cc \$F -I src/shared -I src/render src/render/mxdirt_render_host.c src/render/mxdirt_render_content.c src/render/mxdirt_terrain_scope.c src/render/mxdirt_dirt.c src/render/mxdirt_dirt_gl.c -lopengl32 -lgdi32 -luser32 -lbcrypt -o \$W/mx_dirt_render.dll) && cd \"\$H\" && sha256sum \$W/mx_dirt.dll \$W/mx_dirt_render.dll plugins/mx_dirt.dlo plugins/mx_dirt_render.dlo && for p in mx_dirt mx_dirt_render; do echo \"== \$p: sizes, then every differing byte (offset, release, rebuild; octal)\"; stat -c '%s %n' plugins/\$p.dlo \$W/\$p.dll; cmp -l plugins/\$p.dlo \$W/\$p.dll; echo \"== \$p: sections (name, size) release, then rebuild\"; objdump -h plugins/\$p.dlo | awk '/^ +[0-9]/{print \$2,\$3,\$6}'; objdump -h \$W/\$p.dll | awk '/^ +[0-9]/{print \$2,\$3,\$6}'; echo \"== \$p: the .text section (code) compared\"; objcopy -O binary -j .text plugins/\$p.dlo \$W/a.bin; objcopy -O binary -j .text \$W/\$p.dll \$W/b.bin; cmp \$W/a.bin \$W/b.bin && echo '.text identical'; done; echo '== the two differing constants in mx_dirt.dlo (file offset 0x5f3a0 and 0x5f3c0), release then rebuild'; xxd -s 0x5f3a0 -l 48 plugins/mx_dirt.dlo; xxd -s 0x5f3a0 -l 48 \$W/mx_dirt.dll; echo '== the code that loads them: 80-bit x87 loads (fldt), in runtime code the source has no long double for'; objdump -d plugins/mx_dirt.dlo | grep -E 'fldt .*# 0x180060b[a-c]0'; grep -rc 'long double' \"\$SRC/src\" | grep -v ':0\$' || echo 'no long double in src/'"
# The repository: licence, prebuilt program files (none) and the history up to the commit.
ev repo-files "cd \"\$SRC\" && git ls-files | grep -iE 'licen|copying|\\.(dll|lib|exe|dlo|so|dylib|a|o|obj)\$'; echo '--- every file:'; git ls-files | wc -l; ls -a .github 2>&1; echo '--- history:'; git log --format='%H %ad %s' --date=short 5c300cccd92f533e415b7258ee084feb2d35fc97"
# The build tool and its version (the only dependency; no package manager, no third-party code in src/).
ev deps "cd \"\$SRC\" && grep -nE 'Zig|zig' README.md build.ps1 build_render.ps1 | cut -c1-200; grep -rliE 'copyright|licensed under|SPDX' src || echo 'no copyright or licence header in src/'"
# Third-party code built into the plugins (Zig's MinGW-w64 C runtime) and credits in the release.
ev strings-thirdparty "for f in plugins/mx_dirt.dlo plugins/mx_dirt_render.dlo; do echo \"== \$f\"; strings -n 8 \$f | grep -iE 'mingw|zig|copyright|licen'; done; echo '== README.txt'; grep -niE 'credit|thanks|mingw|zig|copyright|licen|PiBoSo' README.txt"
money plugins/mx_dirt.dlo plugins/mx_dirt_render.dlo README.txt launcher/MXDirtLauncher.ps1
# The Windows runs (lab/results/mx-dirt-mod-1.7.1/): the demo's mxbikes.exe isn't the supported build, so the
# simulation plugin's Startup returned before writing its log, and the look plugin logged the mismatch and stopped.
export RES="$OUT/../../results/mx-dirt-mod-1.7.1"
ev runs "for r in ride ride-launcher-key default launcher-key crash; do echo \"== \$r\"; grep -h 'mxbikes.exe\$' \"\$RES/\$r-windows/plugins.sha256\"; grep -E 'exe_hash_mismatch|gate_fail|launcher_key|core_export' \"\$RES/\$r-windows/mx_dirt_render.log\"; echo \"files: \$(tr '\\n' ' ' < \"\$RES/\$r-windows/files.diff\")\"; echo \"mx_dirt.jsonl written: \$(zcat \"\$RES/\$r-windows/raw/procmon.csv.gz\" | grep -c 'mx_dirt.jsonl')\"; echo \"processes started: \$(zcat \"\$RES/\$r-windows/raw/procmon.csv.gz\" | grep 'Process Create' | cut -d, -f2,5 | tr '\\n' ' ')\"; head -n 1 \"\$RES/\$r-windows/network.txt\"; done; grep -h 'Startup(plugins' \"\$RES/default-windows/host.log\""
# Files written outside the game folder: the ride runs against the bare demo (only the game's own texture cache
# names, which are random, and the screenshots the game saves when F10 is pressed differ).
ev outside "for r in ride ride-launcher-key; do echo \"== \$r against the baseline\"; diff <(sed -E 's/textures\\\\[a-z0-9]{8}/textures\\\\<random>/' \"\$RES/baseline-windows/outside.txt\" | sort -u) <(sed -E 's/textures\\\\[a-z0-9]{8}/textures\\\\<random>/' \"\$RES/\$r-windows/outside.txt\" | sort -u); done"
# P10: what the release asks of Windows in rights: each program's manifest, the service and driver calls, and every place a file asks
# for administrator rights or checks for them (privileges.py unpacks the release files itself, into a scratch folder).
ev privileges "privileges.py MX-Dirt-Mod-1.7.1.zip"
