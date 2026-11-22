#!/usr/bin/env bash
# MXB Damage 1.3.0 (closed source: commands on the release files only).
# The folder holds the five files of https://github.com/FroxyMXB/MXB-Damage-Plugin/releases/tag/v1.3.0, by their names:
# MXB-Damage-Setup.exe, mxb_damage_1.3.0.zip, mxb_damage_1.3.0.pkg, mxb_damage_manifest.txt, mxb_damage_manifest.sig.
# This script unpacks the zip into the same folder (mxb_damage.dlo and the mxb_damage folder).
. "$(dirname "$0")/../ev.sh"
(cd "$R" && unzip -o -q mxb_damage_1.3.0.zip)
ev files "sha256sum MXB-Damage-Setup.exe mxb_damage_1.3.0.zip mxb_damage_1.3.0.pkg mxb_damage_manifest.txt mxb_damage_manifest.sig mxb_damage.dlo mxb_damage/mxb_damage_updater.exe mxb_damage/README.txt mxb_damage/settings.ini"
ev file "file MXB-Damage-Setup.exe mxb_damage.dlo mxb_damage/mxb_damage_updater.exe mxb_damage_1.3.0.pkg; unzip -l mxb_damage_1.3.0.zip"
pe mxb_damage.dlo
pe MXB-Damage-Setup.exe
ev updater.objdump-p "objdump -p mxb_damage/mxb_damage_updater.exe | awk '/^The Function Table|^PE File Base Relocations/{exit} 1'"
ev updater.iat "iat.py mxb_damage/mxb_damage_updater.exe"
# Code signing: the Security (certificate) directory of each program file.
ev signature "objdump -p MXB-Damage-Setup.exe mxb_damage.dlo mxb_damage/mxb_damage_updater.exe | grep -E 'file format|Security Directory'"
# Update check: the release manifest, the package's contents against it, and the signature with the key in the programs.
ev manifest "cat mxb_damage_manifest.txt; echo; cat mxb_damage_manifest.sig"
ev pkg "mxbd_pkg.py mxb_damage_1.3.0.pkg > \$W/pkg.txt; grep '^file=' mxb_damage_manifest.txt | sed 's/^file=//' | sort | diff - <(sort \$W/pkg.txt) && echo 'every file in the package is the one the manifest names (path, size, SHA-256), and none is missing'; sha256sum mxb_damage_1.3.0.pkg; grep package_sha256 mxb_damage_manifest.txt"
ev key-find "p256.py find d00fd1e3eebd002a mxb_damage.dlo mxb_damage/mxb_damage_updater.exe MXB-Damage-Setup.exe"
ev key-verify "p256.py verify d00fd1e3eebd002a2b11983fb6ddf61a8a80f3e59d521c9eb6ea16afd9db31a8711a5cfb882cbfb9dd538abf6887a9d4b6e600c51a05d4d8709bda58548f1bee mxb_damage_manifest.sig mxb_damage_manifest.txt"
ev strings-update "{ strings -n 6 mxb_damage.dlo; strings -el -n 6 mxb_damage.dlo; } | grep -nE 'github|update:|updater|manifest|signature|refused'"
ev strings-updater "{ strings -n 6 mxb_damage/mxb_damage_updater.exe; strings -el -n 6 mxb_damage/mxb_damage_updater.exe; } | grep -nE 'signature|staged|rollback|ROLLBACK|waiting for MX Bikes|gamefx|GameFX|disabled-by|renamed|deleted|--analyze|--plugins|--data|--pid|usage:|part finder|works together'"
# Every web address in the three programs.
ev strings-urls "for f in mxb_damage.dlo mxb_damage/mxb_damage_updater.exe MXB-Damage-Setup.exe; do echo \"== \$f\"; { strings -n 6 \$f; strings -el -n 6 \$f; } | grep -nE 'https?://|www\\.'; done"
# Pointers in the game redirected to the plugin, and the search of the game's code.
ev strings-hooks "{ strings -n 6 mxb_damage.dlo; strings -el -n 6 mxb_damage.dlo; } | grep -nE '^hooks:|OverhaulHookFor|compatibility:'"
ev strings-capture "{ strings -n 6 mxb_damage.dlo; strings -el -n 6 mxb_damage.dlo; } | grep -nE 'capture|recorder|draw_capture|dumped|profiles.rec|texture_|buffer_|read from the GPU|cache'"
ev strings-multiplayer "{ strings -n 6 mxb_damage.dlo; strings -el -n 6 mxb_damage.dlo; } | grep -niE 'multiplayer|other riders|others:|online|server'"
ev strings-plugins "{ strings -n 6 mxb_damage.dlo; strings -el -n 6 mxb_damage.dlo; } | grep -nE 'gamefx|camera64|overhaul64|whiteout|conflicts:|plugins:|second copy|--gamefx-off'"
ev strings-setup "{ strings -n 6 MXB-Damage-Setup.exe; strings -el -n 6 MXB-Damage-Setup.exe; } | grep -nE 'conflicts|Recycle Bin|Remove|remove|Steam|libraryfolders|disabled-by|GameFX|Camera64|Overhaul|Whiteout|works together|left as it is|--gamefx-off|signed|signature|Verifying|\\.log'"
ev strings-thirdparty "for f in mxb_damage.dlo mxb_damage/mxb_damage_updater.exe MXB-Damage-Setup.exe; do { strings -n 6 \$f; strings -el -n 6 \$f; } | grep -iE 'copyright|licen[cs]e|zlib|stb_|lodepng|nlohmann|imgui|miniz|lz4|zstd|crts|ucrt|Microsoft'; done | sort | uniq -c"
money mxb_damage.dlo mxb_damage/mxb_damage_updater.exe MXB-Damage-Setup.exe mxb_damage/README.txt
# Imports a program would need to press keys, hook input, start with Windows, write the registry or another process, or listen for connections.
ev imports-absent "{ iat.py mxb_damage.dlo; iat.py mxb_damage/mxb_damage_updater.exe; iat.py MXB-Damage-Setup.exe; } | grep -E 'SendInput|keybd_event|mouse_event|WriteProcessMemory|CreateRemoteThread|RegSetValue|RegCreateKey|ws2_32|WS2_32|WSOCK|CreateFileMapping|AddVectoredExceptionHandler|WinHttpWebSocket'"
ev imports-setup-hook "iat.py MXB-Damage-Setup.exe | grep -E 'SetWindowsHookExW|RegGetValueW|ShellExecuteW|SHFileOperationW'"
# Keyboard: every GetAsyncKeyState call site, the check that the window in front is the game's, and the key-field snapshot.
ev keys-callsites "objdump -d mxb_damage.dlo | grep -E '# 0x180110628|# 0x180110638|call   0x180090b60'"
dis mxb_damage.dlo 18008fd38 18008fdc1
dis mxb_damage.dlo 18008ffb8 180090011
dis mxb_damage.dlo 1800900b0 1800900c7
dis mxb_damage.dlo 180090260 1800903cb
dis mxb_damage.dlo 1800925d0 180092658
dis mxb_damage.dlo 180090b60 180090bf4
# Crash handler: every call of SetUnhandledExceptionFilter (0x180110208) passes 0, right before UnhandledExceptionFilter.
ev crash-filter "objdump -d mxb_damage.dlo | grep -B3 '# 0x180110208'"
