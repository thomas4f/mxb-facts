#!/usr/bin/env bash
# MXB FPS Booster V1 (closed source: commands on the release file only).
# The folder holds MXB_FPS_Booster_V1.zip, the download on its mxb-mods.com page (https://mxb-mods.com/mxb_fps_booster_v1-2/,
# through MediaFire: https://www.mediafire.com/file/6cas28gcg5u2v56/MXB_FPS_Booster_V1.zip/file). This script unzips it into
# the same folder, flat, and unpacks the program's PyInstaller archive into pkg/ with tools/carchive.py, without running it.
# pyinst.py reads the bundled Python code with marshal and dis, so it needs the Python version the program bundles (3.15,
# python315.dll): set PY315 to that interpreter if python3.15 isn't on PATH.
. "$(dirname "$0")/../ev.sh"
TOOLS="$(cd "$OUT/../../../tools" && pwd)"; export TOOLS
if [ -n "${PY315:-}" ]; then mkdir -p "$W/bin"; ln -s "$PY315" "$W/bin/python3.15"; export PATH="$W/bin:$PATH"; fi
(cd "$R" && unzip -o -q -j MXB_FPS_Booster_V1.zip)
ev files "sha256sum MXB_FPS_Booster_V1.zip 'MXB FPS Booster.exe'"
ev file "unzip -l MXB_FPS_Booster_V1.zip; file 'MXB FPS Booster.exe'"
# The PyInstaller archive at the end of the program: every entry (type, name, size). s = a script it runs, m = a module,
# z = the PYZ archive of bundled Python modules, b = a program file or data, o = an option.
ev carchive "rm -rf pkg; python3 -I \"\$TOOLS/carchive.py\" 'MXB FPS Booster.exe' pkg"
# Every program file in it: type and SHA-256, and the versions of Python, Tcl/Tk, OpenSSL and psutil they are built from.
ev bundled "cd pkg; find . -type f ! -name '*.pyc_raw' ! -name PYZ.pyz ! -name base_library.zip | sort | while read f; do sha256sum \"\$f\"; file -b \"\$f\"; done"
# Code signing: the Security (certificate) directory of the program and of every program file bundled in it.
ev signature "for f in 'MXB FPS Booster.exe' pkg/*.dll pkg/*.pyd pkg/psutil/*.pyd; do objdump -p \"\$f\" | grep -E 'file format|Security Directory'; done"
ev versions "strings -el pkg/python315.dll | grep -A1 -xE 'FileVersion|ProductName'; strings -n 5 pkg/tcl90.dll | grep -xE '9\\.[0-9]+\\.[0-9]+'; strings -n 5 pkg/libcrypto-3.dll | grep -E '^OpenSSL [0-9]' | head -1; pyinst.py consts pkg/PYZ.pyz psutil | grep -xE \"'[0-9]+\\.[0-9]+\\.[0-9]+'\""
# The Python modules bundled in the PYZ archive: Python's standard library, tkinter and psutil.
ev pyz "pyinst.py pyz pkg/PYZ.pyz"
# The tool's own code, main.py (compiled), every function, one line per source line.
ev main "pyinst.py code pkg/main.pyc_raw"
# What main.py imports.
ev main-imports "pyinst.py code pkg/main.pyc_raw | grep -nE 'IMPORT_NAME'"
# Network, registry, memory and process functions main.py would need to go online, write the registry, change another
# program or press keys: none of them.
ev main-absent "pyinst.py code pkg/main.pyc_raw | grep -nE 'IMPORT_NAME (socket|ssl|urllib|http|requests|winreg|ctypes|win32[a-z]*|ftplib|smtplib)\\b|ATTR (urlopen|connect|sendall|OpenKey|SetValue|SetValueEx|CreateKey|kill|terminate|suspend|WriteProcessMemory|keybd_event|SendInput)\\b'"
# Every program it starts and every file it copies, creates, unpacks or opens.
ev main-process "pyinst.py code pkg/main.pyc_raw | grep -nE 'subprocess|Popen|startfile|powercfg|tasklist|psutil'"
ev main-files "pyinst.py code pkg/main.pyc_raw | grep -nE 'copy2|copytree|mkdir|extractall|unlink|remove|rmtree|rename|write_|read_text|BACKUP_ROOT|Documents|libraryfolders|plugins'"
# Web addresses, shop and donation words in its code (none).
ev main-money "pyinst.py code pkg/main.pyc_raw | grep -niE 'https?://|www\\.|shop|donat|paypal|ko-?fi|patreon|buy |price|premium'"
# The functions behind each button, and the texts its window shows.
ev power-plan "pyinst.py code pkg/main.pyc_raw get_active_power_plan set_power_plan App.toggle_gaming_mode App.disable_gaming_mode App.on_close"
ev plugin-install "pyinst.py code pkg/main.pyc_raw App.plugins_dir App.open_plugins App.backup_plugins App.safe_install_files 'App.safe_install_files.<locals>.<genexpr>' App.install_from_file"
ev launch "pyinst.py code pkg/main.pyc_raw App.launch App.is_game_running 'App.is_game_running.<locals>.<genexpr>' App.refresh App.__init__"
ev game-find "pyinst.py code pkg/main.pyc_raw candidate_game_dirs find_game App.scan App.choose_game"
ev ui-text "pyinst.py code pkg/main.pyc_raw App._ui | grep -E 'LOAD_CONST .[A-Z][A-Za-z ]'"

