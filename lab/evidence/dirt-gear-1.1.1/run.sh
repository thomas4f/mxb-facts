#!/usr/bin/env bash
# Dirt Gear 1.1.1 (no licence found; source public at e407acd9e39393d7a7d1ddc295fe00056f9df7d5, tag v1.1.1).
# Usage: run.sh <release folder> <source checkout at e407acd>
# The release folder holds the three files of the GitHub release v1.1.1
# (https://github.com/Dirt-Graphic-Studios/Dirt-Gear/releases/tag/v1.1.1): Dirt-Gear-Setup-1.1.1.exe, update.json and
# update.json.sig. This script unpacks the installer's PyInstaller archive into setup/ with tools/carchive.py, unzips its
# payload.zip (the installed program folder) into payload/, and unpacks the program's archive into app/, without running
# anything. pycmp.py and pyinst.py read the packed Python code with marshal, so they need the Python version the program
# bundles (3.12, python312.dll): set PY312 to that interpreter if python3.12 isn't on PATH. bootloader and pywebview-lib
# download two wheels from PyPI (pinned by SHA-256), so they need the network, and so does release-page.
. "$(dirname "$0")/../ev.sh"
: "${SRC:?give the source checkout as the second argument}"
TOOLS="$(cd "$OUT/../../../tools" && pwd)"; export TOOLS OUT R
if [ -n "${PY312:-}" ]; then mkdir -p "$W/bin"; ln -s "$PY312" "$W/bin/python3.12"; export PATH="$W/bin:$PATH"; fi
S=Dirt-Gear-Setup-1.1.1.exe
A='payload/Dirt Gear.exe'
ev carchive-setup "rm -rf setup; python3 -I \"\$TOOLS/carchive.py\" $S setup"
(cd "$R" && rm -rf payload && mkdir payload && cd payload && unzip -o -q ../setup/payload.zip)
ev carchive-app "rm -rf app; python3 -I \"\$TOOLS/carchive.py\" '$A' app"
ev files "sha256sum $S update.json update.json.sig setup/payload.zip '$A'"
ev file "file $S '$A' setup/payload.zip; unzip -l setup/payload.zip | tail -1"
# Every program file in the installed folder: SHA-256 and type (data files such as Python sources, fonts and images left out).
ev bundled "cd payload; find . -type f \\( -iname '*.dll' -o -iname '*.pyd' -o -iname '*.exe' \\) | sort | while read f; do sha256sum \"\$f\"; file -b \"\$f\"; done"
# Code signing: the Security (certificate) directory of the installer and the program.
ev signature "for f in $S '$A'; do echo \"\$f\"; objdump -p \"\$f\" | grep -E 'file format|Security Directory'; done"
# Versions of what is packed: Python, the packages with a dist-info folder, Pillow, psd-tools, OpenSSL, pythonnet, aggdraw
# and Microsoft's WebView2 SDK files (from pywebview).
ev versions "echo '- python312.dll:'; strings -el payload/_internal/python312.dll | grep -A1 -xE 'FileVersion'; echo '- dist-info folders:'; ls -d payload/_internal/*.dist-info; echo '- PIL._version, psd_tools.version:'; python3.12 -I \"\$OUT/../pyinst.py\" consts app/PYZ.pyz PIL._version; python3.12 -I \"\$OUT/../pyinst.py\" consts app/PYZ.pyz psd_tools.version; echo '- cffi (its __version__, first number):'; python3.12 -I \"\$OUT/../pyinst.py\" consts app/PYZ.pyz cffi | grep -m1 -E \"^'[0-9]+\\.[0-9]+\\.[0-9]+'\$\"; echo '- libcrypto-3.dll:'; strings -n 5 payload/_internal/libcrypto-3.dll | grep -m1 -E '^OpenSSL [0-9]'; echo '- Python.Runtime.dll (pythonnet):'; strings -el payload/_internal/pythonnet/runtime/Python.Runtime.dll | grep -A1 -xE 'FileVersion'; echo '- aggdraw:'; strings payload/_internal/aggdraw.cp312-win_amd64.pyd | grep -m1 -xE '[0-9]+\\.[0-9]+\\.[0-9]+'; echo '- Microsoft.Web.WebView2.Core.dll:'; strings -el payload/_internal/webview/lib/Microsoft.Web.WebView2.Core.dll | grep -A1 -xE 'ProductVersion'"
# The bootloader: the code (.text, .data, .pdata) of the installer and the program is the same as PyInstaller 6.22.3's
# runw.exe; .rdata and the resources (icon, version) differ, as they do for every PyInstaller build.
ev bootloader "cd \"\$W\" && curl -sSLO https://files.pythonhosted.org/packages/24/83/c5422204772a27aef643280fdc887b7ef55679989096b21dceb1b9625fc4/pyinstaller-6.22.3-py3-none-win_amd64.whl && echo '500bd58c7bf7e584a8435adccbd763a0b918d5c12b08d74ff50fd79b2915458b  pyinstaller-6.22.3-py3-none-win_amd64.whl' | sha256sum -c && unzip -q -o pyinstaller-6.22.3-py3-none-win_amd64.whl PyInstaller/bootloader/Windows-64bit-intel/runw.exe && cd \"\$R\" && python3 -I \"\$OUT/../pesect.py\" \"\$W/PyInstaller/bootloader/Windows-64bit-intel/runw.exe\" $S '$A'"
# pywebview's webview/lib folder (Microsoft's WebView2 SDK files and pywebview's WebBrowserInterop) is the one in pywebview 6.2.1.
ev pywebview-lib "cd \"\$W\" && curl -sSLO https://files.pythonhosted.org/packages/3d/25/9491695c22c4842c5b3903b4dc172e0eecf67a27c0af34a71512c9b76a0a/pywebview-6.2.1-py3-none-any.whl && echo '9d07275f53894ab4d5e2e0e996227193e7187dec276d9b624dccbce029216b46  pywebview-6.2.1-py3-none-any.whl' | sha256sum -c && unzip -q -o pywebview-6.2.1-py3-none-any.whl 'webview/lib/*' && (cd webview/lib && find . -type f | sort | xargs sha256sum) > wheel.txt && (cd \"\$R/payload/_internal/webview/lib\" && find . -type f | sort | xargs sha256sum) > release.txt && cat release.txt && diff wheel.txt release.txt && echo 'same files, same SHA-256 as pywebview 6.2.1'"
# The release against the source at the commit: the tool's five Python files compiled with Python 3.12 and compared with
# the code packed in the release (pycmp.py: every function and constant, all but the file path), then the data files
# (byte for byte, or the same once Windows line ends, CRLF, are turned back into LF: the build ran on a Windows checkout).
ev same-as-source "echo '- installer.py (in the installer):'; python3.12 -I \"\$OUT/../pycmp.py\" raw setup/installer.pyc_raw \"\$SRC/build/installer.py\"; echo '- app.py (in the program):'; python3.12 -I \"\$OUT/../pycmp.py\" raw app/app.pyc_raw \"\$SRC/source/app.py\"; for m in updater packing fastpreview; do echo \"- \$m.py (PYZ):\"; python3.12 -I \"\$OUT/../pycmp.py\" pyz app/PYZ.pyz \$m \"\$SRC/source/\$m.py\"; done; echo '- data files:'; same() { if cmp -s \"\$1\" \"\$2\"; then echo \"same: \$1\"; elif [ \"\$(tr -d '\\r' < \"\$1\" | sha256sum)\" = \"\$(tr -d '\\r' < \"\$2\" | sha256sum)\" ]; then echo \"same but CRLF: \$1\"; else echo \"DIFFERENT: \$1\"; fi; }; for f in \$(cd \"\$SRC/source/static\" && ls); do same payload/_internal/static/\$f \"\$SRC/source/static/\$f\"; done; ls payload/_internal/static | wc -l; diff -rq payload/_internal/fonts \"\$SRC/source/fonts\" && echo \"same: all \$(ls payload/_internal/fonts | wc -l) fonts\"; same payload/_internal/update_public_key.pem \"\$SRC/source/update_public_key.pem\"; same payload/_internal/icon.ico \"\$SRC/source/icon.ico\"; same payload/_internal/VERSION.txt \"\$SRC/VERSION.txt\"; same setup/VERSION.txt \"\$SRC/VERSION.txt\"; for f in README.md CHANGELOG.md VERSION.txt; do same payload/\$f \"\$SRC/\$f\"; done; echo '- update_repo.txt (written by the release workflow):'; cat payload/_internal/update_repo.txt; echo"
# The signed update feed of the release: update.json names the installer's size and SHA-256, and update.json.sig is an
# Ed25519 signature of it that the public key in the source verifies.
ev update-manifest "cat update.json; echo; base64 -d update.json.sig > \"\$W/sig.bin\" && openssl pkeyutl -verify -pubin -inkey \"\$SRC/source/update_public_key.pem\" -rawin -in update.json -sigfile \"\$W/sig.bin\""
# Every file in the repository at the commit, with its type: no prebuilt program file (only scripts, fonts, images, texts).
ev repo-files "cd \"\$SRC\" && git ls-files | wc -l && git ls-files -z | xargs -0 file | grep -vE 'Python script|ASCII text|UTF-8 text|JSON|PNG image|SVG|font|Font|MS Windows icon|empty|HTML|JavaScript|public key' ; git ls-files -z | xargs -0 file | grep -E 'PE32|ELF|Mach-O|archive|compiled|executable,' | grep -v 'Python script'"
# The source's internet, network and browser code: urllib only in updater.py (GitHub's API and the release files), the
# local server on 127.0.0.1 in app.py, webbrowser only for the release page; the page itself has no outside address.
ev src-network "cd \"\$SRC\" && grep -nE 'urllib|urlopen|socket|requests\\.|https?://|webbrowser|make_server|127\\.0\\.0\\.1|localhost|connect-src' source/*.py build/installer.py; grep -noE 'https?://[^\"'\\'' )]+' source/static/*.js source/static/*.html source/static/*.css | sort | uniq -c"
# The local server's checks: every request must name 127.0.0.1 or localhost as its host, and every /api/ request must come
# from the app's own page (or name no Origin) and carry the random token made at each start.
ev src-server "cd \"\$SRC\" && sed -n '36p;78,97p;1521,1524p' source/app.py"
# When the update check runs: 4 s after the page loads, unless "Check for updates when Dirt Gear starts" is unticked;
# clicking the version button opens the About box and checks at once.
ev src-update-ui "cd \"\$SRC\" && grep -noE 'setTimeout\\(\\(\\)=>checkUpdates\\(false\\),4000\\)|versionBtn.\\)\\.onclick=[^;]*;[^;]*;|checkNow.\\)\\.onclick=[^;]*;|checkOnStart.\\)\\.onchange=[^}]*}' source/static/app.js; grep -nE 'checkOnStart|Download and install|Skip this version' source/static/index.html | cut -c1-220; grep -nE \"check_on_start|skip_version\" source/app.py"
# Every place the source writes, moves or deletes a file, and where.
ev src-files "cd \"\$SRC\" && grep -nE 'write_bytes|write_text|\\.save\\(|open\\(.wb|copytree|copyfileobj|rmtree|unlink|\\.rename\\(|\\.replace\\(destination|\\.replace\\(path|\\.replace\\(target|mkdir|TemporaryDirectory' source/app.py source/updater.py build/installer.py"
# MX Bikes: it reads global.ini in Documents\\PiBoSo\\MX Bikes for the mods folder, lists rider models with a paints folder,
# and Pack & install writes <name>.pnt there, replacing a file of the same name only after you confirm.
ev src-game "cd \"\$SRC\" && sed -n '1365,1413p' source/app.py; grep -noE '.{0,60}already exists for .{0,60}' source/static/app.js"
# Other programs' files it reads: Windows' fonts, Moto Gear's library (copied once), the clipboard (Ctrl+V or Paste).
ev src-reads "cd \"\$SRC\" && grep -nE 'WINDIR|Microsoft/Windows/Fonts|LEGACY_DATA_NAME|Moto Gear|grabclipboard|GetClipboardData|OpenClipboard|global\\.ini' source/app.py"
# What it would need to change the registry, start with Windows, open other processes, press or read keys outside its
# window, or change the game: none, except the installer's OpenProcess with SYNCHRONIZE (0x00100000), which waits for the
# old Dirt Gear to close before an update, and its calls to PowerShell (shortcuts), ie4uinit.exe and SHChangeNotify (icons).
ev src-absent "cd \"\$SRC\" && grep -nE 'winreg|HKEY|RegSetValue|CurrentVersion.Run|schtasks|Startup|OpenProcess|WriteProcessMemory|ReadProcessMemory|VirtualProtect|CreateRemoteThread|SetWindowsHookEx|GetAsyncKeyState|keybd_event|SendInput|mxbikes\\.exe|subprocess|Popen|ie4uinit|SHChangeNotify|powershell' source/*.py build/installer.py"
# Shop, payment and donation words in the source and the page.
ev strings-money "cd \"\$SRC\" && grep -niE 'gumroad|donat|paypal|ko-?fi|patreon|premium|price|lemon|buy|licen[cs]e key|unlock|subscri|discord\\.gg' source/*.py source/static/*.html source/static/*.js README.md"
# Credits and licence texts: the repository has no licence file; the installed folder has the licence files PyInstaller
# copies from the packages' dist-info folders, the brand font's OFL, and no THIRD_PARTY_NOTICES.txt.
ev thirdparty "cd \"\$SRC\" && echo '- repository:'; git ls-files | grep -iE 'licen|copying|notice|credit|third' ; cd \"\$R\" && echo '- installed folder:'; find payload -iname '*licen*' -o -iname '*copying*' -o -iname '*notice*' -o -iname '*OFL*' | sort; ls payload"
# The fonts it ships, with the maker and copyright line each one names.
ev fonts "cd payload/_internal/fonts && ls | wc -l && for f in *; do printf '%s: %s\\n' \"\$f\" \"\$(file -b \"\$f\" | grep -oE '(Copyright|\\(c\\)|©)[^,]{0,90}' | head -1)\"; done"
# Dependencies: source/requirements.txt (cryptography without a version) and what the workflow installs (pip, PyInstaller,
# scipy, scikit-image and aggdraw without versions; actions by version tag).
ev deps "cd \"\$SRC\" && cat source/requirements.txt; grep -nE 'pip install|uses:|python-version' .github/workflows/release.yml build/build.ps1"
# The release page: published by github-actions from the commit.
ev release-page "curl -sSL https://github.com/Dirt-Graphic-Studios/Dirt-Gear/releases/tag/v1.1.1 | python3 -I -c 'import re,sys; d=sys.stdin.read(); t=re.sub(r\"<[^>]+>|\\s+\", \" \", d); i=t.find(\"released this\"); print(t[i-60:i+40].strip()); print(sorted(set(re.findall(r\"/commit/[0-9a-f]{40}\", d)))); '; curl -sSL https://github.com/Dirt-Graphic-Studios/Dirt-Gear/releases/expanded_assets/v1.1.1 | grep -oE 'releases/download/v1\\.1\\.1/[^\"]+' | sort -u"
# The public history up to the commit.
ev history "cd \"\$SRC\" && git log --format='%h %ad %s' --date=short e407acd9e39393d7a7d1ddc295fe00056f9df7d5 | cat; git log --format=%ad --date=short e407acd9e39393d7a7d1ddc295fe00056f9df7d5 | sort -u | wc -l"
