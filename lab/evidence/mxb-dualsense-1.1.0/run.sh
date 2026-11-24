#!/usr/bin/env bash
# MXB DualSense Support 1.1.0 (MIT licence; no public source: commands on the release file only).
# The folder holds 1795198224-mxb-dualsense-support-1.1.0.zip, the download on its mxb-mods.com page
# (https://mxb-mods.com/mxb-dualsense-support-ps5-adaptive-triggers-2/,
# https://mxb-mods.com/wp-content/uploads/2026/11/1795198224-mxb-dualsense-support-1.1.0.zip). This script unzips it into zip/
# and unpacks the program's PyInstaller archive into pkg/ with tools/carchive.py, without running it.
# pyinst.py reads the bundled Python code with marshal and dis, so it needs the Python version the program bundles (3.15,
# python315.dll): set PY315 to that interpreter if python3.15 isn't on PATH.
. "$(dirname "$0")/../ev.sh"
TOOLS="$(cd "$OUT/../../../tools" && pwd)"; export TOOLS
if [ -n "${PY315:-}" ]; then mkdir -p "$W/bin"; ln -s "$PY315" "$W/bin/python3.15"; export PATH="$W/bin:$PATH"; fi
Z=1795198224-mxb-dualsense-support-1.1.0.zip
(cd "$R" && rm -rf zip && mkdir zip && cd zip && unzip -o -q "../$Z" 2>/dev/null || true)
ev carchive "rm -rf pkg; python3 -I \"\$TOOLS/carchive.py\" zip/MXB-DualSense-Support.exe pkg"
ev files "sha256sum $Z zip/MXB-DualSense-Support.exe pkg/hud_plugin/mxbds_hud64.dlo pkg/hud_plugin/mxbds_hud/Inter-SemiBold.fnt"
ev file "unzip -l $Z; file zip/MXB-DualSense-Support.exe pkg/hud_plugin/mxbds_hud64.dlo"
# Every program file packed in the exe: SHA-256 and type (data files such as .js, .css, fonts and texts left out).
ev bundled "cd pkg; find . -type f \\( -name '*.dll' -o -name '*.pyd' -o -name '*.dlo' -o -name '*.exe' \\) | sort | while read f; do sha256sum \"\$f\"; file -b \"\$f\"; done"
# Code signing: the Security (certificate) directory of the exe, the HUD plugin and every program file packed in the exe.
ev signature "objdump -p zip/MXB-DualSense-Support.exe | grep -E 'file format|Security Directory'; find pkg -type f \\( -name '*.dll' -o -name '*.pyd' -o -name '*.dlo' \\) | sort | while read f; do echo \"\$f\"; objdump -p \"\$f\" | grep -E 'Security Directory'; done"
# Versions of what is packed: Python, OpenSSL, and the package list the release gives (licenses/README.txt).
ev versions "strings -el pkg/python315.dll | grep -A1 -xE 'FileVersion|ProductName'; strings -n 5 pkg/libcrypto-3.dll | grep -E '^OpenSSL [0-9]' | head -1; cat 'zip/licenses/README.txt'"
# Credits and licence texts in the release.
ev thirdparty "cat zip/LICENSE.txt zip/CREDITS.txt; ls zip/licenses"
# The Python modules packed in the PYZ archive: Python's standard library, pywebview and what it needs, and the tool's own
# package mxbds.
ev pyz "pyinst.py pyz pkg/PYZ.pyz"
# The tool's own code, every function, one line per source line: the start script and each mxbds module.
ev code-mxb_dualsense "pyinst.py code pkg/mxb_dualsense.pyc_raw"
for m in mxbds mxbds.brake mxbds.core mxbds.dsx mxbds.effects mxbds.game_setup mxbds.gui mxbds.gui.api mxbds.gui.app mxbds.hotkeys \
         mxbds.hud mxbds.install mxbds.lockup mxbds.main mxbds.mode mxbds.settings mxbds.spikes mxbds.telemetry mxbds.whoops; do
  ev "code-$m" "pyinst.py pyzcode pkg/PYZ.pyz $m"
done
# Shorthand for the searches below: the whole of the tool's own code.
ALL="{ pyinst.py code pkg/mxb_dualsense.pyc_raw; for m in \$(pyinst.py pyz pkg/PYZ.pyz | grep -E '^mxbds'); do pyinst.py pyzcode pkg/PYZ.pyz \$m; done; }"
# What the tool's code imports.
ev imports "$ALL | grep -oE 'IMPORT_NAME [A-Za-z_.]+' | sort | uniq -c"
# Every socket it opens and where it sends or listens: DSX (UDP 6969), the HUD plugin (UDP 30002), the game's proxy_udp data
# (UDP 30001), all on 127.0.0.1.
ev network "$ALL | grep -nE \"socket\\.socket|ATTR (sendto|send|bind|connect|recv)\\b|'127\\.0\\.0\\.1'|DEFAULT_PORT|STORE_NAME PORT|PORT_FILE\""
# Web addresses in its code and window (only the WebView2 download page, opened when WebView2 is missing and you click Yes).
ev urls "{ $ALL; cat pkg/gui_web/index.html pkg/gui_web/app.js pkg/gui_web/style.css; } | grep -noE 'https?://[^ |\"'\\'')]+|webbrowser'"
# Functions it would need to write the registry, change another program, press keys, read the game's memory or go online
# itself: none (the registry is only read: OpenKey and QueryValueEx).
ev absent "$ALL | grep -nE 'IMPORT_NAME (urllib|http|requests|ssl|ftplib|smtplib|subprocess)\\b|ATTR (urlopen|SetValue|SetValueEx|CreateKey|DeleteKey|DeleteValue|OpenProcess|ReadProcessMemory|WriteProcessMemory|SendInput|keybd_event|SetWindowsHookExW|SetWindowsHookExA|Popen|startfile|system|kill|terminate)\\b'"
ev registry "$ALL | grep -nE 'winreg|OpenKey|QueryValueEx|WEBVIEW2_KEY|Valve'"
# Every file it writes, copies, replaces or removes, and where.
ev file-writes "$ALL | grep -nE 'ATTR (copy2|write_bytes|write_text|replace|unlink|rmdir|mkdir)\\b|backup|settings\\.ini|_base_folder|STORE_NAME FILE|PLUGIN_NAME|DATA_DIR|FONT_NAME|INI_NAME'"
# The functions behind the HUD install and uninstall, the proxy_udp.ini setup and the settings file.
ev install "pyinst.py pyzcode pkg/PYZ.pyz mxbds.install"
ev proxy-ini "pyinst.py pyzcode pkg/PYZ.pyz mxbds.game_setup"
ev api-confirm "pyinst.py pyzcode pkg/PYZ.pyz mxbds.gui.api ControlApi.install_hud ControlApi.uninstall_hud ControlApi.fix_proxy ControlApi.toggle_hud ControlApi.set_hud ControlApi._write_saved ControlApi.save_settings ControlApi.choose_game_folder ControlApi.set_game_folder"
# The window's buttons that call them: each asks first (confirmBox) and passes true only after you confirm.
ev buttons "grep -nE 'confirmBox|api\\.(install_hud|uninstall_hud|fix_proxy|choose_game_folder)' pkg/gui_web/app.js"
# The global hotkeys: GetAsyncKeyState, polled every 50 ms by the control center (Ctrl+Shift+H, Ctrl+Shift+M), and the numpad in --tune.
ev hotkeys "pyinst.py pyzcode pkg/PYZ.pyz mxbds.hotkeys; pyinst.py pyzcode pkg/PYZ.pyz mxbds.gui.app main 'main.<locals>.watch_hotkey'"
# The control center window: WebView2 (Microsoft Edge), private mode, opened on the window's own files.
ev window "pyinst.py pyzcode pkg/PYZ.pyz mxbds.gui.app"
# pywebview's local web server: bound to 127.0.0.1 on a random port, serving the window's own files; its js_api route answers
# only when a js_callback is set, which the Edge (WebView2) window code never does.
ev webview-server "pyinst.py pyzcode pkg/PYZ.pyz webview.http | grep -nE \"'localhost'|127\\.0\\.0\\.1|route|js_callback|Access-Control|root_path|_get_random_port\"; echo '--- js_callback in the Edge window code:'; pyinst.py pyzcode pkg/PYZ.pyz webview.platforms.edgechromium | grep -c js_callback"
# What it reads from the game's data (proxy_udp packet fields) and what it sends to DSX and to the HUD plugin.
ev telemetry "pyinst.py pyzcode pkg/PYZ.pyz mxbds.telemetry | head -80"
ev dsx "pyinst.py pyzcode pkg/PYZ.pyz mxbds.dsx"
ev hud-feed "pyinst.py pyzcode pkg/PYZ.pyz mxbds.hud"
# Shop, payment and donation words in its code and window (none).
ev strings-money "{ $ALL; cat pkg/gui_web/index.html pkg/gui_web/app.js; } | grep -niE 'shop|donat|paypal|ko-?fi|patreon|buy |price|premium|licen[cs]e key'"
# The README's own claims quoted on the card.
ev readme-claims "grep -nE 'changes nothing in the game|no admin rights|does not|collect|ONE program|asks first|backup|removes exactly|not digitally signed|Closing it sets' zip/README.txt"
# The optional in-game HUD plugin (packed in the exe, copied into <MX Bikes>/plugins only from the HUD page or --install-hud).
cd_pe() { ev "$2.objdump-p" "objdump -p '$1' | awk '/^The Function Table|^PE File Base Relocations/{exit} 1'"; ev "$2.objdump-h" "objdump -h '$1'"; ev "$2.iat" "iat.py '$1'"; }
cd_pe pkg/hud_plugin/mxbds_hud64.dlo mxbds_hud64.dlo
# Its socket: UDP (17), bound to 127.0.0.1 (0x7f000001) port 30002 (0x7532); WS2_32 ordinals 115 WSAStartup, 23 socket,
# 9 htons, 8 htonl, 2 bind.
ev mxbds_hud64.dlo.180001b9a-180001c12 "objdump -d pkg/hud_plugin/mxbds_hud64.dlo | awk -v a=180001b9a -v b=180001c12 '\$1 ~ /^[0-9a-f]+:\$/ { x = substr(\$1, 1, length(\$1) - 1); p = length(x) == length(a) && x >= a && x <= b } p'"
# Its VirtualProtect calls: all on its own .fptable section (0x18001e000), the C runtime's table.
ev virtualprotect "objdump -h pkg/hud_plugin/mxbds_hud64.dlo | grep fptable; objdump -d pkg/hud_plugin/mxbds_hud64.dlo | grep -B6 '# 0x1800101e8'"
ev strings-dlo "strings -n 6 pkg/hud_plugin/mxbds_hud64.dlo | grep -iE 'mxb|hud|\\.fnt|http|\\.ini|\\.log'; strings -el -n 6 pkg/hud_plugin/mxbds_hud64.dlo | grep -iE 'mxb|hud|http'"
# Its only SetUnhandledExceptionFilter call (0x180010078): the C runtime's failure report, right after IsDebuggerPresent
# (0x180010168), which clears the filter (xor ecx,ecx = NULL) and calls UnhandledExceptionFilter (0x180010000) to end the
# process; it sets no crash handler of its own.
ev crash-filter "objdump -d pkg/hud_plugin/mxbds_hud64.dlo | grep -nE '# 0x180010078|# 0x180010000'; objdump -d pkg/hud_plugin/mxbds_hud64.dlo | awk -v a=180006cf7 -v b=180006d12 '\$1 ~ /^[0-9a-f]+:\$/ { x = substr(\$1, 1, length(\$1) - 1); p = length(x) == length(a) && x >= a && x <= b } p'"
# What stopping the mod (closing the window) does: both triggers back to normal (dsx.normal), the HUD hidden.
ev core-stop "pyinst.py pyzcode pkg/PYZ.pyz mxbds.core ModCore.stop; pyinst.py pyzcode pkg/PYZ.pyz mxbds.gui.api ControlApi.shutdown ControlApi.stop"
