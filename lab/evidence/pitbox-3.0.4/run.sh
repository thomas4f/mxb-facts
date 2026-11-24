#!/usr/bin/env bash
# Pitbox 3.0.4 (GitHub release v3.0.4, https://github.com/cristianboni22/pitbox/releases/tag/v3.0.4; the repository holds
# only a README, so the commands run on the release files). The folder holds Pitbox-Windows-3.0.4.zip,
# Pitbox-Linux-3.0.4.tar.gz, actualizacion.json and actualizacion.json.sig from that release page, and README.md from the
# repository at the tag's commit (https://raw.githubusercontent.com/cristianboni22/pitbox/dc05ea0caf9d89b36ea6b23bb50c9ae2b33f5ac3/README.md).
# This script unpacks the zip into win/ and the tarball into lin/, and copies the two plugins beside them. The app is Python source (win/Pitbox/gpbmods_app.py and win/Pitbox/gpbmods/),
# read as it ships; the two game plugins are prebuilt (.dlo) without names in them.
. "$(dirname "$0")/../ev.sh"
export H="$(cd "$(dirname "$0")" && pwd)"
(cd "$R" && rm -rf win lin && mkdir win lin && unzip -q Pitbox-Windows-3.0.4.zip -d win && tar xzf Pitbox-Linux-3.0.4.tar.gz -C lin \
  && cp win/Pitbox/hud/gpbmods_hud64.dlo win/Pitbox/asistente/asistente_reglaje64.dlo .)
P=win/Pitbox; G=win/Pitbox/gpbmods
HUD=gpbmods_hud64.dlo; AS=asistente_reglaje64.dlo
ev files "sha256sum Pitbox-Windows-3.0.4.zip Pitbox-Linux-3.0.4.tar.gz actualizacion.json actualizacion.json.sig $HUD $AS $P/gpbmods_app.py $P/Instalar.bat $P/integridad.json $P/vendor/7z/7z.exe $P/python/python.exe lin/Pitbox/requirements.txt lin/Pitbox/hud/gpbmods_hud64.dlo lin/Pitbox/asistente/asistente_reglaje64.dlo"
# Every program file in both packages (T1), and the top of the Windows package.
ev file "find win lin -type f \\( -iname '*.dlo' -o -iname '*.dll' -o -iname '*.exe' -o -iname '*.pyd' -o -iname '*.so' \\) | sort | xargs -d '\\n' file; echo; ls -la $P $P/vendor/7z; echo; ls lin/Pitbox"
# Bundled libraries and their versions (the dist-info folders) and licence files (C4, T6), and what the Linux package installs.
ev thirdparty "ls -d $P/lib/*.dist-info; ls $P/python/LICENSE.txt $P/vendor/7z/License.txt $P/hud/datos/OFL-*.txt $P/gpbmods/web/fonts/OFL-*.txt; strings -el $P/vendor/7z/7z.exe | grep -m1 -E '^[0-9]+\\.[0-9]+\$'; head -3 $P/python/LICENSE.txt; echo '== lin/Pitbox/requirements.txt'; cat lin/Pitbox/requirements.txt; echo '== lin/Pitbox/instalar.sh'; cat lin/Pitbox/instalar.sh"
# Code signing: where the Security (certificate) directory of each program file starts (0 = no certificate, not signed).
ev signature "find $P -type f \\( -iname '*.dlo' -o -iname '*.dll' -o -iname '*.exe' -o -iname '*.pyd' \\) | sort | while read -r f; do printf '%s  ' \"\$f\"; objdump -p \"\$f\" | awk '/Security Directory/ {print \$3}'; done"
# The update notice and the file list are signed (Ed25519) with the key built into actualizar.py (P3).
ev ed25519 "grep -n '^CLAVE_PUBLICA' $G/actualizar.py; k=\$(sed -n 's/^CLAVE_PUBLICA = \"\\([0-9a-f]*\\)\"/\\1/p' $G/actualizar.py); python3 -I \$H/../ed25519_sig.py \$k actualizacion.json actualizacion.json.sig; python3 -I \$H/../ed25519_sig.py \$k $P/integridad.json $P/integridad.json.sig; cat actualizacion.json; grep -A2 -E '\"(asistente/asistente_reglaje64.dlo|hud/gpbmods_hud64.dlo)\"' $P/integridad.json"
# The updater: how it checks (manifest signature, SHA-256), and that the page installs only after a click (P2, P3, T2).
ev updater "sed -n '1,60p;93,104p' $G/actualizar.py; echo '== actualizar.py: after an update'; sed -n '738,775p' $G/actualizar.py; echo '== webapp.py'; sed -n '1209,1262p' $G/webapp.py; echo '== web/index.html'; sed -n '6508,6549p' $P/gpbmods/web/index.html"
ev readme-claims "grep -nE 'actualiza solo|updates itself|firmad|signed|no oficial|Unofficial|No hay|no source|Ko-fi|Discord|tal cual|as is|Instalar|acceso directo|shortcut' README.md"
# Every web address in the app's code (D1).
ev urls "grep -rnoE 'https?://[A-Za-z0-9._/{}%?=-]+' $P/gpbmods_app.py $G/*.py $G/hosts/*.py"
# The app's run dropped 9 connections to 5 addresses; which names they are (DNS lookup on the day of the analysis).
ev hosts "for h in gpbmods-ranking.secundariac2003.workers.dev gpb-mods.com stats.gp-bikes.com api.github.com github.com; do printf '%s: ' \$h; getent ahostsv4 \$h | awk '{print \$1}' | sort -u | tr '\\n' ' '; echo; done; date -u +%F"
# Access screen: Steam sign-in, linked Discord, public ranking and shared telemetry are required (D2, D3, D7, D8, D9).
ev access "sed -n '1,61p' $G/acceso.py"
# What the app sends to its server: every POST, PUT and DELETE, and the bodies of the lap and telemetry uploads.
ev sends "grep -n '_peticion(\"\\(POST\\|PUT\\|DELETE\\)\"\\|requests\\.\\(put\\|post\\)' $G/*.py; echo '== ranking_mundial.py'; sed -n '1,45p;239,253p;261,267p;511,556p;601,620p;814,852p' $G/ranking_mundial.py"
ev presence "sed -n '1,24p;174,181p' $G/amigos.py; echo '== webapp.py'; sed -n '2736,2771p' $G/webapp.py"
ev limits "sed -n '1,12p;39,44p;120,123p;202,230p' $G/compartidos.py; echo '== web/index.html'; sed -n '6293,6302p;11814,11822p' $P/gpbmods/web/index.html"
ev report "sed -n '1,22p;614,625p' $G/informe.py"
ev probe "sed -n '1,10p;30,31p;47,54p' $G/conectividad.py; echo '== servers.py'; sed -n '17p' $G/servers.py; echo '== catalog.py'; sed -n '15p' $G/catalog.py"
# Local servers: pywebview's page server, the background-image server and the sign-in callback, all on 127.0.0.1 (D5).
ev servers "sed -n '1,13p;54,57p;112,113p;125,133p' $G/servidor_fondo.py; echo '== ranking_mundial.py'; sed -n '28,33p;916,925p;981,998p' $G/ranking_mundial.py; echo '== webapp.py'; sed -n '5052,5062p' $G/webapp.py"
# Installing into the game (on request), the desktop shortcut on first start, and what the app does at start (P4, P7, P8).
ev install "sed -n '1,2p;54,90p;114,121p;137,154p;248,296p;350,372p;468,484p;598,636p;661,708p' $G/instalacion.py; echo '== gpbmods_app.py'; sed -n '103,125p;236,261p' $P/gpbmods_app.py; echo '== Instalar.bat'; cat $P/Instalar.bat"
ev deletes "grep -nE 'rmtree|\\.unlink\\(|os\\.remove|send2trash' $G/*.py; echo '== mis_mods.py'; sed -n '1,22p;49p;488,500p' $G/mis_mods.py; echo '== mods_al_dia.py'; sed -n '1,30p' $G/mods_al_dia.py"
ev graphics "sed -n '1,13p' $G/graficos.py"
# Windows registry, processes and other programs' data (P6, G9, G10, D6).
ev registry "grep -nE 'winreg|HKEY|CurrentVersion.Run|Startup|schtasks|RegSetValue|SetValueEx' $P/gpbmods_app.py $G/*.py $G/hosts/*.py; sed -n '157,175p' $G/steam_cliente.py; sed -n '238,250p' $G/plataforma.py"
ev processes "grep -nE 'subprocess\\.(Popen|run)\\(|popen=subprocess|OpenProcess\\(|SendInput|keybd_event|WriteProcessMemory|ReadProcessMemory|CreateRemoteThread|SetWindowsHookEx|GetAsyncKeyState|RegisterHotKey' $P/gpbmods_app.py $G/*.py $G/hosts/*.py"
ev content "grep -niE 'cifrad|descifr|decrypt|iNLock' $G/*.py | grep -v '^$G/i18n'; echo '== inventory.py'; sed -n '80,90p' $G/inventory.py; echo '== fisicas_moto.py'; sed -n '14,19p' $G/fisicas_moto.py; echo '== modders.py'; sed -n '1,8p' $G/modders.py"
ev money "grep -nE 'ko-fi|Ko-fi|donar|premium|comprar|precio|patreon|paypal' $G/comunidad.py $G/mods_pitbox.py $G/webapp.py $P/GUIDE.html README.md"
# The plugins: headers, imports, sections (T1, G1, G2, G4, D1).
pe $HUD
pe $AS
ev imports-absent "for f in $HUD $AS; do iat.py \$f; done | grep -iE 'ws2_32|wsock|wininet|winhttp|urlmon|SendInput|keybd_event|mouse_event|SetWindowsHookEx|CreateProcess|ShellExecute|WinExec|RegSetValue|RegCreateKey|RegOpenKey|WriteProcessMemory|ReadProcessMemory|OpenProcess|CreateRemoteThread|LoadLibrary|GetProcAddress|AddVectoredExceptionHandler|SetUnhandledExceptionFilter'"
# Their memory-protection calls sit in the MinGW runtime routine that prints the pseudo-relocation messages (G2).
ev vp-hud "\$H/imports_at.sh $HUD VirtualProtect VirtualQuery DeleteFileA MoveFileExA CopyFileA"
ev vp-assistant "\$H/imports_at.sh $AS VirtualProtect VirtualQuery DeleteFileA MoveFileExA RemoveDirectoryA remove"
# Keys: each GetAsyncKeyState read follows a check that the window in front belongs to the game's own process (G7).
ev keys "\$H/imports_at.sh $HUD GetForegroundWindow GetWindowThreadProcessId GetCurrentProcessId GetAsyncKeyState; \$H/imports_at.sh $AS GetForegroundWindow GetWindowThreadProcessId GetCurrentProcessId GetAsyncKeyState"
dis $AS 180003776 1800037d6
dis $HUD 180002900 180002a24
# Files the plugins name: their own folders and logs, the game's profiles, setups, bikes and tyres (P7, D6, C5).
ev strings-plugins "for f in $HUD $AS; do echo \"== \$f\"; strings -n 6 \$f | grep -E '%s|\\.(stp|csv|ini|log|txt|tlm|cfg|fnt|tga)' | grep -vE '^[^A-Za-z]*\$|\\[_\\^' | sort -u; done"
ev strings-urls "for f in $HUD $AS; do { strings -n 5 \$f; strings -el -n 5 \$f; } | grep -niE 'https?://|www\\.|\\.(com|net|org|io)\\b|ws2_32|wininet|winhttp|socket'; done"
# «Mi sala» (your own online room, on request): the router is asked through UPnP to forward the room's port.
ev upnp "grep -n -i 'upnp' $G/sala_propia.py | head -20"
