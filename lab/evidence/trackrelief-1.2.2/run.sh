#!/usr/bin/env bash
# TrackRelief 1.2.2 (no licence found; no public source: commands on the release files only).
# The folder holds the two files of the GitHub release 1.2.2 (https://github.com/Lilian1134/TrackRelief/releases/tag/1.2.2):
# TrackRelief.zip and TrackRelief_Setup.exe. This script unzips the zip into zip/, without running anything.
# The launcher (zip/TrackRelief/TrackRelief.exe) is a .NET program: ilspycmd (ILSpy's command line,
# `dotnet tool install --tool-path <dir> ilspycmd`, 11.2.0 here) decompiles it; set ILSPYCMD to it if it isn't on PATH.
# The app (zip/TrackRelief/app/TrackRelief.exe) is a Nuitka program: its Python modules are compiled to machine code, so
# nuitka.py lists the constants each module keeps (names it uses, its texts), which is what the searches read.
. "$(dirname "$0")/../ev.sh"
ILSPYCMD="${ILSPYCMD:-ilspycmd}"; export ILSPYCMD
(cd "$R" && rm -rf zip && mkdir zip && cd zip && unzip -o -q ../TrackRelief.zip)
A=zip/TrackRelief/app/TrackRelief.exe
L=zip/TrackRelief/TrackRelief.exe
ev files "sha256sum TrackRelief.zip TrackRelief_Setup.exe $L $A"
ev file "file TrackRelief.zip TrackRelief_Setup.exe $L $A; unzip -l TrackRelief.zip | tail -1"
# Every program file in the zip: SHA-256 and type (data files such as Tcl scripts, fonts, images and GDAL data left out).
ev bundled "cd zip; find . -type f \\( -iname '*.dll' -o -iname '*.pyd' -o -iname '*.exe' -o -iname '*.dlo' \\) | sort | while read f; do sha256sum \"\$f\"; file -b \"\$f\"; done"
# Code signing: the Security (certificate) directory of the installer, the launcher and the app.
ev signature "for f in TrackRelief_Setup.exe $L $A; do echo \"\$f\"; objdump -p \"\$f\" | grep -E 'file format|Security Directory'; done"
# Versions of what is packed: Python, OpenSSL, Tcl/Tk, and the packages whose version text the app keeps; the Nuitka runtime.
ev versions "echo '- python314.dll:'; strings -el zip/TrackRelief/app/python314.dll | grep -A1 -xE 'FileVersion|ProductName'; echo '- libcrypto-3.dll:'; strings -n 5 zip/TrackRelief/app/libcrypto-3.dll | grep -E '^OpenSSL [0-9]' | head -1; echo '- tcl86t.dll:'; strings zip/TrackRelief/app/tcl86t.dll | grep -xE '8\\.6\\.[0-9]+' | head -1; for m in PIL._version customtkinter numpy.version scipy.version rasterio pyproj tkintermapview geocoder certifi; do echo \"- \$m:\"; nuitka.py consts $A \$m | grep -m2 -xE 'u[0-9]+\\.[0-9]+(\\.[0-9]+)?'; done; echo '- Nuitka (lines naming it in the app):'; strings -n 8 $A | grep -cE 'Nuitka'; strings -n 8 $A | grep -m3 -E 'nuitka\\.net|__nuitka_version__|__compiled__'"
# Licence and credit files in the zip (Tk's and GDAL's).
ev thirdparty "unzip -l TrackRelief.zip | grep -iE 'licen|copying|credit|notice|readme|authors'"
# The installer: Inno Setup, its data version 6.7.0, which innoextract 1.9 (the newest release) can't read.
ev setup "strings -n 6 TrackRelief_Setup.exe | grep -m3 -E 'Inno Setup'"
# The launcher, decompiled: it starts app\\TrackRelief.exe and exits.
ev launcher "objdump -p $L | grep -E 'DLL Name|CorExeMain'; \"\$ILSPYCMD\" $L"
# The app's module blocks (offset, name, size): Python's own and its packages' modules, and the tool's own seven modules
# (__main__, api_fetcher, exporters, satellite, settings, terrain_processor, update; __parents_main__ is Nuitka's copy of
# __main__ for its worker processes).
ev blocks "nuitka.py blocks $A"
OWN="__main__ api_fetcher exporters satellite settings terrain_processor update"
for m in $OWN; do ev "consts-$m" "nuitka.py consts $A $m"; done
# Shorthand for the searches below: every constant of the tool's own modules, each line prefixed with its module.
ALL="for m in $OWN; do nuitka.py consts $A \$m | sed \"s/^/\$m: /\"; done"
# The DLLs the app loads by its import table.
ev imports "objdump -p $A | grep 'DLL Name'"
# Every web address in its own modules: the map tiles, place search, elevation services, roads, satellite imagery,
# GitHub's release list, Discord and Gumroad.
ev urls "$ALL | grep -nE 'https?://'"
# Its internet code: requests sessions with the User-Agent TrackRelief/1.0, urllib in update, webbrowser for the buttons.
ev network "$ALL | grep -nE ': (a|u)(urllib|urlopen|requests|Session|socket|bind|listen|webbrowser|User-Agent|TrackRelief/1\\.0.*|TrackRelief/|api_key|opentopo_api_key|http\\.server|HTTPServer)\$'"
# The update check, in full: GET https://api.github.com/repos/Lilian1134/TrackRelief/releases?per_page=20 with the
# User-Agent TrackRelief/<version>; it keeps the newest release's tag, notes and page (html_url).
ev update "nuitka.py consts $A update"
# What the window does with it: the Settings switch "Check for updates at startup", the Check for updates button.
ev update-ui "nuitka.py consts $A __main__ | grep -nE -B2 -A3 'auto_check_updates|Check for updates|check_update_startup|Update available|Download'"
# Settings: settings.json under %APPDATA%\\TrackRelief (or ~/.config/TrackRelief), its keys, and the defaults the
# constants show ('auto' elevation source, 'Heightmap only (PNG)', '1024', 'Map').
ev defaults "nuitka.py consts $A settings; nuitka.py raw $A settings aapi_key 120"
# Place search: Nominatim (OpenStreetMap) with the text you type; the search history kept in settings.
ev search "nuitka.py consts $A __main__ | grep -nE -B6 -A8 'nominatim'; nuitka.py consts $A __main__ | grep -nE 'search_history|_add_to_history|_remove_history_entry'"
# Elevation sources and the OpenTopography key (Settings, "OpenTopography API key", only for areas outside the listed ones).
ev sources "nuitka.py consts $A __main__ | grep -nE 'LiDAR|3DEP|DGM1|OpenTopography|Italy PCN|Only needed outside|My own file|Automatic'; nuitka.py consts $A api_fetcher | grep -nE 'https?://|api_key|API_Key'"
# Every file it writes, deletes or opens, and where: settings.json, its tile and download cache in the temp folder
# (TrackRelief\\tiles, cleared with rmtree), a new TrackRelief_<date>_<time> folder under the output folder for each
# generation (heightmap_16bit.png, surface_mask.png, texture_satellite.png, terrain_info.json, track.tht and the other game
# files), merged_dem.tif removed after use, and the result folder opened (startfile) when you answer yes.
ev file-writes "$ALL | grep -nE ': (a|u)(write|write_text|write_bytes|copyfile|shutil|mkdir|makedirs|remove|replace|move|rename|unlink|rmtree|clear_cache|default_cache_dir|gettempdir|tiles|sat|startfile|askyesno|out_dir|output_dir|TrackRelief_%Y%m%d_%H%M%S|.*\\.png|.*\\.json|.*\\.tht|.*\\.tif|.*\\.obj|.*\\.ini|Your track files are ready\\.|Open the folder\\?|The folder where .*)\$'"
# The game exports: MX Bikes (.tht), BeamNG (.json), Assetto Corsa (mesh); no path into a game folder.
ev exports "nuitka.py consts $A __main__ | grep -nE 'MX Bikes|BeamNG|Assetto|GAME_EXPORTS|Heightmap only'; nuitka.py consts $A exporters | grep -nE 'tht|MX Bikes|material|layer|friction|\\.json|\\.obj|levels/'; $ALL | grep -niE 'PiBoSo|mxbikes|steamapps|Steam' || true"
# Registry and Windows calls: none in its own modules.
ev registry "$ALL | grep -nE ': a(winreg|HKEY.*|OpenKey|QueryValueEx|SetValue|SetValueEx|CreateKey|DeleteKey|windll|ctypes|shell32|user32|SetCurrentProcess.*|SetProcessDpi.*)\$'"
# Functions it would need to start other programs, change other processes, press keys, read keys outside its window, read
# identifiers or write the registry: none in its own modules (startfile only opens the result folder, file-writes.txt).
ev absent "$ALL | grep -nE ': a(subprocess|Popen|system|OpenProcess|ReadProcessMemory|WriteProcessMemory|VirtualProtect|CreateRemoteThread|SendInput|keybd_event|SetWindowsHookExW|SetWindowsHookExA|GetAsyncKeyState|GetKeyState|urlretrieve|SetValueEx|CreateKey|DeleteKey|kill|terminate|getnode|gethostname|getuser|getlogin|environ|platform|MachineGuid|uuid1|uuid4|winreg|ctypes)\$'"
# Shop, payment and donation words and links in its own modules.
ev strings-money "$ALL | grep -niE 'gumroad|donat|support|paypal|ko-?fi|patreon|buy|price|premium|free|licen[cs]e key|unlock|discord\\.gg'"
# Its own texts that the card quotes.
ev ui-claims "nuitka.py consts $A __main__ | grep -nE -A6 '100% free and open|is free, with every feature|entirely optional|changes nothing in the app'"
# P10: what the release asks of Windows in rights: each program's manifest, the service and driver calls, and every place a file asks
# for administrator rights or checks for them (privileges.py unpacks the release files itself, into a scratch folder).
ev privileges "privileges.py TrackRelief.zip TrackRelief_Setup.exe"
# The installer's own setup header (Inno Setup 6.7, which innoextract can't read): its default folder and the rights it asks for.
ev setup-rights "innosetup.py TrackRelief_Setup.exe"
