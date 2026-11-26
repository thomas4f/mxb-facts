#!/usr/bin/env bash
# MXRP Ragdoll v3.2 (Beta 3.2, plugin 1.8.177; closed source: commands on the release files only).
# The folder holds the four files of https://github.com/avare795/MXRP-ragdoll/releases/tag/v3.2: MXRP_Beta_3.2.zip,
# MXRP_Beta_3.2_manual.zip, MXRP_Ragdoll_1.8.177.dlo and MXRP_Ragdoll_Installer.exe. This script unpacks both zips into the
# same folder and links the two program files under short names at the top of the folder, so the outputs are named after them.
. "$(dirname "$0")/../ev.sh"
(cd "$R" && unzip -o -q MXRP_Beta_3.2.zip && unzip -o -q MXRP_Beta_3.2_manual.zip \
  && ln -sf "MXRP_Ragdoll/plugins/MXRP_Ragdoll.dlo" MXRP_Ragdoll.dlo \
  && ln -sf "MXRP Beta 3.2.exe" installer.exe)
ev files "sha256sum MXRP_Beta_3.2.zip MXRP_Beta_3.2_manual.zip MXRP_Ragdoll_1.8.177.dlo MXRP_Ragdoll_Installer.exe 'MXRP Beta 3.2.exe'; find MXRP_Ragdoll -type f | LC_ALL=C sort | xargs -d '\n' sha256sum"
ev file "unzip -l MXRP_Beta_3.2.zip; unzip -l MXRP_Beta_3.2_manual.zip; file MXRP_Ragdoll_1.8.177.dlo MXRP_Ragdoll_Installer.exe 'MXRP Beta 3.2.exe'; find MXRP_Ragdoll -type f | LC_ALL=C sort | xargs -d '\n' file; cmp MXRP_Ragdoll_1.8.177.dlo MXRP_Ragdoll/plugins/MXRP_Ragdoll.dlo && cmp MXRP_Ragdoll_Installer.exe 'MXRP Beta 3.2.exe' && echo 'the two single downloads are byte for byte the plugin and the installer in the zips'"
pe MXRP_Ragdoll.dlo
pe installer.exe
# Code signing: the Security (certificate) directory of each program file.
ev signature "objdump -p MXRP_Ragdoll.dlo installer.exe | grep -E 'file format|Security Directory'"
# Compiler and third-party names in the programs' text.
ev strings-thirdparty "for f in MXRP_Ragdoll.dlo installer.exe; do echo \"== \$f\"; { strings -n 6 \$f; strings -el -n 6 \$f; } | grep -iE 'copyright|licen[cs]e|zlib|miniz|stb_|lodepng|nlohmann|imgui|lz4|zstd|GCC:|mingw|cmu|procworks|fluffygecko|mocap' | sort | uniq -c; done"
# Imports a program would need to connect, listen, press keys, hook input system-wide, start programs, write the registry or memory.
ev imports-present "for f in MXRP_Ragdoll.dlo installer.exe; do echo \"== \$f\"; iat.py \$f | grep -E 'WinHttp(Open|Connect|SendRequest|ReadData)\$|!(socket|bind|sendto|recvfrom|setsockopt|WSAIoctl)\$|GetAdaptersAddresses|SendInput|SetWindowsHookExA|CallNextHookEx|GetAsyncKeyState|GetForegroundWindow|WriteProcessMemory|ReadProcessMemory|VirtualProtect\$|FlushInstructionCache|HeapWalk|CreateToolhelp32Snapshot|Module32First|ShellExecuteA|DeleteFileA|MoveFileExA|CopyFileA|BCryptCreateHash|RegOpenKeyExA|RegQueryValueExA|SHBrowseForFolderA|FindFirstFileA'; done"
ev imports-absent "for f in MXRP_Ragdoll.dlo installer.exe; do echo \"== \$f\"; iat.py \$f | grep -E '!(listen|accept)\$|RegSetValue|RegCreateKey|RegDeleteKey|CreateProcess|WinExec|CreateRemoteThread|AddVectoredExceptionHandler|SetUnhandledExceptionFilter|CreateFileMapping|wininet|urlmon'; done"
# Automatic updates: the GitHub address, the asset digest, the hash and file checks, the question asked, the installer it opens.
ev strings-update "{ strings -n 6 MXRP_Ragdoll.dlo; strings -el -n 6 MXRP_Ragdoll.dlo; } | grep -nE 'api\\.github|/repos/|vnd\\.github|updater|browser_download_url|digest|sha256|SHA256|^https://\$|mise a jour|%s\\.(old|new)|Installer|Update available|Automatic updates|Ask before installing|installer will open|installateur|installe : actif|Enter / A|Entree / A'"
# The plugin's settings table: each entry is the setting's name, its type, its offset in the settings and its group.
ev settings-table "ptrtable.py MXRP_Ragdoll.dlo 2e3fa8ba0 96 32"
# The function that sets the defaults (called on the settings at 0x2e3fe2800 before any file is read), and the constants it copies.
dis MXRP_Ragdoll.dlo 2e3acf4e0 2e3acf709
ev defaults-rdata "objdump -s -j .rdata --start-address=0x2e3fa9be0 --stop-address=0x2e3fa9c30 MXRP_Ragdoll.dlo"
ev defaults-call "objdump -d MXRP_Ragdoll.dlo | grep -E '2e3a73de6:|2e3a73e10:|2e3a73e25:'"
# Where the automatic-updates setting (settings+0x108 = 0x2e3fe2908) and the network setting (settings+0xa8 = 0x2e3fe28a8) are read.
ev settings-reads "objdump -d MXRP_Ragdoll.dlo | grep -E '# 0x2e3fe2908\$|# 0x2e3fe28a8\$'"
dis MXRP_Ragdoll.dlo 2e3a73f04 2e3a73f12
dis MXRP_Ragdoll.dlo 2e3a750ee 2e3a7510f
# The shipped settings file: network part and the keys that block and press the respawn.
ev ini-defaults "grep -nE '^(reseau|reseau_hote|reseau_ip|reseau_port|marche_forcee|respawn_appui_long|clavier_prio|manette_prio) *=' MXRP_Ragdoll/plugins/MXRP_Ragdoll.ini; grep -nE 'Seules les touches|Radmin|reseau_hote = 1' MXRP_Ragdoll/plugins/MXRP_Ragdoll.ini"
# Network: the local-network exchange, the game's own server connection (its sendto/recvfrom) and Steam networking.
ev strings-network "{ strings -n 6 MXRP_Ragdoll.dlo; strings -el -n 6 MXRP_Ragdoll.dlo; } | grep -nE '^reseau :|^\\?reseau|steam_api64|SteamNetworking|ISteamNetworking|SteamAPI_|est a pied'"
# Servers: the server name, the plugin turning itself on, and the automatic kick of players without the plugin.
ev strings-online "{ strings -n 6 MXRP_Ragdoll.dlo; strings -el -n 6 MXRP_Ragdoll.dlo; } | grep -nE 'expuls|Kick|ID_KICK|RAGDOLL - |serveur RAGDOLL|plugin active pour cette session|hostsetup_name|Official servers|Players collide|joueurs ont le plugin|cone d.un autre joueur'"
# Changes to the game: code patches, the game's file reads redirected to its menus copy, the track's meshes, the game's image.
ev strings-game "{ strings -n 6 MXRP_Ragdoll.dlo; strings -el -n 6 MXRP_Ragdoll.dlo; } | grep -nE 'impossible de modifier le code du jeu|le CALL vise|menus : |dossier ui du jeu|maillages de la piste|surfaces sous les roues interceptees|imports ws2_32 du jeu|image du jeu copiee|squelette|ODE world|monde ODE' | head -40"
# Keyboard: the low-level keyboard hook (SetWindowsHookExA type 13) and its hook procedure; SendInput key presses; the respawn.
dis MXRP_Ragdoll.dlo 2e3aa6790 2e3aa67b8
dis MXRP_Ragdoll.dlo 2e3aa6860 2e3aa6990
dis MXRP_Ragdoll.dlo 2e3a9ab50 2e3a9abed
ev strings-keys "{ strings -n 6 MXRP_Ragdoll.dlo; strings -el -n 6 MXRP_Ragdoll.dlo; } | grep -nE '^clavier : crochet|Clavier prioritaire|^respawn :|moto : respawn|Respawn (non|pas) fait|manette simulee|installe \\(touches'"
# Files: its folders and old names, the profile copies and their readme, the settings file of the old name.
ev strings-files "{ strings -n 6 MXRP_Ragdoll.dlo; strings -el -n 6 MXRP_Ragdoll.dlo; } | grep -nE 'mxb_ragdoll|MXRP_Ragdoll_(sauvegarde|menus|relief|replay|gfx)|sauvegarde_profils|profils : |COPIES your profile|never writes|gfx\\.cfg|controls\\.txt|profile\\.ini|misc\\.pkz|autre\\(s\\) copie'"
# Bike and rider files it opens (models, gfx.cfg in a bike's .pkz).
ev strings-content "{ strings -n 6 MXRP_Ragdoll.dlo; strings -el -n 6 MXRP_Ragdoll.dlo; } | grep -nE '\\.hrc\$|\\.edf\$|^bikes\\\\|\\\\bikes\\\\|gfx\\.cfg lu|poignees prises|modele du pilote \"|crypt|chiffr'"
# The installer: Steam lookups, the four name patterns it removes from plugins, and its texts.
ev strings-installer "strings -n 6 installer.exe | sed -n '1,200p' | grep -nE 'Steam|steamapps|libraryfolders|655500|plugins|MXRP_Ragdoll|mxb_ragdoll|Old versions|misc|installed|settings|Yes:|No:'"
ev installer-patterns "ptrtable.py installer.exe 14000b660 4 8"
# The removal loop: for each pattern, FindFirstFileA/FindNextFileA in plugins, then DeleteFileA on each match.
dis installer.exe 140001f69 140002016
dis installer.exe 140002148 1400021f0
ev installer-iat-names "iat.py installer.exe | grep -E '0x1400103(b8|d0|d8|f0) |0x140010528 '"
# Money: shop, payment and donation words and web addresses.
ev strings-money "for f in MXRP_Ragdoll.dlo installer.exe MXRP_Ragdoll/MXRP_Ragdoll_LISEZ-MOI_README.txt MXRP_Ragdoll/plugins/MXRP_Ragdoll.ini; do echo \"== \$f\"; { strings -n 6 \"\$f\"; strings -el -n 6 \"\$f\"; } | grep -nE 'https?://|www\\.|[Ss]hop|[Bb]uy |[Pp]rice|[Pp]remium|[Pp]atreon|[Pp]ay[Pp]al|[Kk]o-?fi|[Dd]onat|[Cc]offee'; done"
# The guide's text the card quotes.
ev guide "sed -n '1,90p' MXRP_Ragdoll/MXRP_Ragdoll_LISEZ-MOI_README.txt | grep -nE 'removes old|Automatic:|UPDATES|downloads it|Ask before|kicked|ON/OFF button is not enough|plugin is still loaded|talk through|Every player needs|send Documents|Walking animation|FMX ramps:|RAGDOLL is added'"
# The installer's payload: the plugin, the guide and the settings file of the manual zip are inside it, byte for byte (offsets).
ev payload "python3 -I -c 'import sys; f=open(sys.argv[1],\"rb\").read(); [print(p, \"found at offset\", f.find(open(p,\"rb\").read())) for p in sys.argv[2:]]' installer.exe MXRP_Ragdoll/plugins/MXRP_Ragdoll.dlo MXRP_Ragdoll/MXRP_Ragdoll_LISEZ-MOI_README.txt MXRP_Ragdoll/plugins/MXRP_Ragdoll.ini"
