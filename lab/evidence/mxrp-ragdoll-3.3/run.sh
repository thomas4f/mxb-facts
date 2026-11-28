#!/usr/bin/env bash
# MXRP Ragdoll v3.3 (Beta 3.3, plugin 1.8.203). The plugin is closed source; the source of the installer and of the
# automatic updates is published at the tag's commit (source/, read-only licence that allows reading and building to
# compare). Run as: run.sh <folder> <checkout of avare795/MXRP-ragdoll at abafb8cd42af04b2c79460fecd5f757305e55166>.
# The folder holds the six files of https://github.com/avare795/MXRP-ragdoll/releases/tag/v3.3 by their names:
# MXRP_Beta_3.3.zip, MXRP_Beta_3.3_manual.zip, MXRP_Ragdoll_1.8.203.dlo, MXRP_Ragdoll_1.8.203.dlo.sig,
# MXRP_Ragdoll_Installer.exe and MXRP_Ragdoll_Installer.exe.sig; and, for the test of the installer's check on
# mxb_ragdoll*.dlo, mxb_ragdoll.dlo of MXB Ragdoll 1.0 (Manual Install/plugins/ in MXB-Ragdoll-v1.0.zip, SHA-256
# 82592eff97a2836635930f8d513c875b7d1dbaf17fd4196e3df686a4057fd3c9, the file on the MXB Ragdoll 1.0 card).
# This script unpacks both zips into the same folder and links the two program files under short names.
# The rebuild of the installer (T4) needs MinGW-w64 (Ubuntu 24.04: apt install gcc-mingw-w64-x86-64, GCC 13-win32).
. "$(dirname "$0")/../ev.sh"
(cd "$R" && unzip -o -q MXRP_Beta_3.3.zip && unzip -o -q MXRP_Beta_3.3_manual.zip \
  && ln -sf "MXRP_Ragdoll/plugins/MXRP_Ragdoll.dlo" MXRP_Ragdoll.dlo \
  && ln -sf "MXRP Beta 3.3.exe" installer.exe)
K=60d78dbe2397fb631031918a963511c25c8ffebc610375e997dc7ad5253a07b573487181449ddc3e317e473abad3b151b6801187abf70544d60203fc17468524
ev files "sha256sum MXRP_Beta_3.3.zip MXRP_Beta_3.3_manual.zip MXRP_Ragdoll_1.8.203.dlo MXRP_Ragdoll_1.8.203.dlo.sig MXRP_Ragdoll_Installer.exe MXRP_Ragdoll_Installer.exe.sig 'MXRP Beta 3.3.exe' mxb_ragdoll.dlo; find MXRP_Ragdoll -type f | LC_ALL=C sort | xargs -d '\n' sha256sum"
ev file "unzip -l MXRP_Beta_3.3.zip; unzip -l MXRP_Beta_3.3_manual.zip; file MXRP_Ragdoll_1.8.203.dlo MXRP_Ragdoll_Installer.exe 'MXRP Beta 3.3.exe' MXRP_Ragdoll_1.8.203.dlo.sig MXRP_Ragdoll_Installer.exe.sig; find MXRP_Ragdoll -type f | LC_ALL=C sort | xargs -d '\n' file; cmp MXRP_Ragdoll_1.8.203.dlo MXRP_Ragdoll/plugins/MXRP_Ragdoll.dlo && cmp MXRP_Ragdoll_Installer.exe 'MXRP Beta 3.3.exe' && echo 'the two single downloads are byte for byte the plugin and the installer in the zips'; echo '== source files at the commit'; cd \"\$SRC\" && git ls-files | xargs file"
pe MXRP_Ragdoll.dlo
pe installer.exe
ev signature "objdump -p MXRP_Ragdoll.dlo installer.exe | grep -E 'file format|Security Directory'"
ev strings-thirdparty "for f in MXRP_Ragdoll.dlo installer.exe; do echo \"== \$f\"; { strings -n 6 \$f; strings -el -n 6 \$f; } | grep -iE 'copyright|licen[cs]e|zlib|miniz|stb_|lodepng|nlohmann|imgui|lz4|zstd|GCC:|mingw|cmu|procworks|fluffygecko|mocap|lpfeffer|innerscene' | sort | uniq -c; done; echo '== credits at the commit'; grep -nE 'MinGW|puff|Adler|CMU|lpfeffer|Innerscene' \"\$SRC/README.md\" \"\$SRC/source/README.md\" \"\$SRC/source/src/inflate.c\""
ev imports-present "for f in MXRP_Ragdoll.dlo installer.exe; do echo \"== \$f\"; iat.py \$f | grep -E 'WinHttp(Open|Connect|SendRequest|ReadData)\$|!(socket|bind|sendto|recvfrom|setsockopt|WSAIoctl)\$|GetAdaptersAddresses|SendInput|SetWindowsHookExA|CallNextHookEx|GetAsyncKeyState|GetForegroundWindow|WriteProcessMemory|ReadProcessMemory|VirtualProtect\$|FlushInstructionCache|HeapWalk|CreateToolhelp32Snapshot|Module32First|ShellExecuteA|DeleteFileA|MoveFileExA|CopyFileA|BCrypt(CreateHash|ImportKeyPair|VerifySignature)|RegOpenKeyExA|RegQueryValueExA|SHBrowseForFolderA|FindFirstFileA'; done"
ev imports-absent "for f in MXRP_Ragdoll.dlo installer.exe; do echo \"== \$f\"; iat.py \$f | grep -E '!(listen|accept)\$|RegSetValue|RegCreateKey|RegDeleteKey|CreateProcess|WinExec|CreateRemoteThread|AddVectoredExceptionHandler|SetUnhandledExceptionFilter|CreateFileMapping|wininet|urlmon'; done"
# Automatic updates: texts in the plugin, and the published source of the check (update.c).
ev strings-update "{ strings -n 6 MXRP_Ragdoll.dlo; strings -el -n 6 MXRP_Ragdoll.dlo; } | grep -nE 'api\\.github|/repos/|vnd\\.github|updater|browser_download_url|digest|sha256|SHA256|%s\\.sig|signature|mise a jour : |%s\\.(old|new)|Installer|Automatic updates|Ask before installing|installateur'"
ev src-update "cd \"\$SRC\" && grep -nE 'UPD_PATH|k_pub_[xy]\\[32\\]|BCRYPT_ECDSA|BCryptVerifySignature|static unsigned char \\*download_checked|sig_ok\\(d|_stricmp\\(got, sha\\)|pas de signature|g_ask = 1|d && g_ask|write_all\\(tmp|MoveFileExA|ShellExecuteA|download_checked\\(\\(const' source/src/update.c"
# The author's signatures on the two files the update downloads, checked with the public key written in update.c.
ev sig-verify "grep -A1 -E 'k_pub_[xy]\\[32\\]' \"\$SRC/source/src/update.c\" | head -4; echo \"key: $K\"; p256.py verify $K MXRP_Ragdoll_1.8.203.dlo.sig MXRP_Ragdoll_1.8.203.dlo; p256.py verify $K MXRP_Ragdoll_Installer.exe.sig MXRP_Ragdoll_Installer.exe"
# The same key in the compiled plugin: written as eight 8-byte constants, then the key is imported and the signature
# checked (the calls go through the thunks below to BCryptOpenAlgorithmProvider, BCryptImportKeyPair, BCryptVerifySignature).
dis MXRP_Ragdoll.dlo 2e3ace283 2e3ace3ef
ev bcrypt-thunks "objdump -d MXRP_Ragdoll.dlo | grep -E '^ +2e3ad35(30|38|40|58|70):'; iat.py MXRP_Ragdoll.dlo | grep -E '0x2e5fcb(800|7f8|7f0|7d8|7c0) '"
# Settings: the menu entries for updates and the kick (label, name, offset in the settings), the function that sets the
# defaults (called on the settings at 0x2e427b840 before the settings file is read), and the constants it copies.
ev settings-table "ptrtable.py MXRP_Ragdoll.dlo 2e3af17a8 9 16; ptrtable.py MXRP_Ragdoll.dlo 2e423dae0 3 32"
dis MXRP_Ragdoll.dlo 2e3a75356 2e3a75395
dis MXRP_Ragdoll.dlo 2e3ad2eb0 2e3ad2fc7
ev defaults-rdata "objdump -s -j .rdata --start-address=0x2e423e7a0 --stop-address=0x2e423e7b0 MXRP_Ragdoll.dlo"
# At start: the test-mode, ask and automatic-updates settings (+0x118, +0x10c, +0x108) are read; with the last at 0 it logs
# "automatique desactivee" (0x2e3ae8de0) and skips the check.
dis MXRP_Ragdoll.dlo 2e3a7545e 2e3a7547c
ev settings-reads "objdump -d MXRP_Ragdoll.dlo | grep -E '# 0x2e3ae8de0\$'"
ev ini-defaults "grep -nE '^(reseau|reseau_hote|reseau_ip|reseau_port|expulsion_auto|marche_forcee|respawn_appui_long|clavier_prio|manette_prio) *=' MXRP_Ragdoll/plugins/MXRP_Ragdoll.ini"
ev strings-network "{ strings -n 6 MXRP_Ragdoll.dlo; strings -el -n 6 MXRP_Ragdoll.dlo; } | grep -nE '^reseau :|^\\?reseau|steam_api64|SteamNetworking|ISteamNetworking|SteamAPI_|est a pied|serveur RAGDOLL'"
ev strings-online "{ strings -n 6 MXRP_Ragdoll.dlo; strings -el -n 6 MXRP_Ragdoll.dlo; } | grep -nE 'expuls|Kick|ID_KICK|RAGDOLL - |plugin active pour cette session|hostsetup_name|Official servers|Players collide|joueurs ont le plugin|cone d.un autre joueur'"
ev strings-game "{ strings -n 6 MXRP_Ragdoll.dlo; strings -el -n 6 MXRP_Ragdoll.dlo; } | grep -nE 'impossible de modifier le code du jeu|le CALL vise|menus : |dossier ui du jeu|maillages de la piste|surfaces sous les roues interceptees|imports ws2_32 du jeu|image du jeu copiee|squelette|ODE world|monde ODE' | head -40"
ev strings-keys "{ strings -n 6 MXRP_Ragdoll.dlo; strings -el -n 6 MXRP_Ragdoll.dlo; } | grep -nE '^clavier : crochet|Clavier prioritaire|^respawn :|moto : respawn|Respawn (non|pas) fait|manette simulee|installe \\(touches|DirectInput'"
# Keyboard: the low-level keyboard hook (SetWindowsHookExA type 13) and its hook procedure, which writes every key's
# state to a table before it looks at the foreground window; SendInput (keyboard, by scan code).
dis MXRP_Ragdoll.dlo 2e3aa94f0 2e3aa9518
dis MXRP_Ragdoll.dlo 2e3aa95c0 2e3aa96f0
dis MXRP_Ragdoll.dlo 2e3a9d2c0 2e3a9d330
ev user32-names "iat.py MXRP_Ragdoll.dlo | grep -E '0x2e5fcb(d70|cb0|d00|d28|d48|8c0|8e8) '"
ev strings-files "{ strings -n 6 MXRP_Ragdoll.dlo; strings -el -n 6 MXRP_Ragdoll.dlo; } | grep -nE 'mxb_ragdoll|MXRP_Ragdoll_(sauvegarde|menus|relief|replay|gfx)|sauvegarde_profils|profils : |COPIES your profile|never writes|gfx\\.cfg|controls\\.txt|profile\\.ini|misc\\.pkz|autre\\(s\\) copie'"
ev strings-content "{ strings -n 6 MXRP_Ragdoll.dlo; strings -el -n 6 MXRP_Ragdoll.dlo; } | grep -nE '\\.hrc\$|\\.edf\$|^bikes\\\\|\\\\bikes\\\\|gfx\\.cfg lu|poignees prises|modele du pilote \"|crypt|chiffr'"
# The installer: its source at the commit (removal patterns, the check on mxb_ragdoll*.dlo, what it writes and reads).
ev src-installer "cd \"\$SRC\" && grep -nE 'static const char \\*pat\\[\\]|old_dlo_is_ours|mem_has\\(buf|DeleteFileA\\(from\\)|_stricmp\\(fd.cFileName|res_write\\([123]|install_font\\(dir|RegOpenKeyExA|reg_str\\(HKEY|misc/misc.fnt|requireAdministrator' source/installer/installer.c source/installer/installer.manifest"
ev strings-installer "strings -n 6 installer.exe | sed -n '1,420p' | grep -nE 'Steam|steamapps|libraryfolders|655500|plugins|MXRP_Ragdoll|mxb_ragdoll|Old versions|misc|installed|settings|Yes:|No:'"
ev installer-patterns "ptrtable.py installer.exe 14000b680 4 8"
# The compiled installer: the loop over the patterns (FindFirstFileA, DeleteFileA), then the check on a mxb_ragdoll*.dlo
# match: its two names (0x14000b35b mxb_ragdoll.fnt, 0x14000b36b plugins\mxb_ragdoll.ini) searched in the file read.
dis installer.exe 140002040 1400021f0
dis installer.exe 140002547 140002596
ev installer-iat-names "iat.py installer.exe | grep -E '0x1400103(b8|d0|e8|f0) |0x140010410 |0x140010470 '"
# Test: MXB Ragdoll 1.0's plugin (another author's mxb_ragdoll.dlo) holds the first name but not the second, so the
# installer's check leaves it alone.
ev mxb-ragdoll-check "sha256sum mxb_ragdoll.dlo; for s in 'mxb_ragdoll.fnt' 'plugins\\mxb_ragdoll.ini'; do printf '%s: ' \"\$s\"; grep -c -a -F \"\$s\" mxb_ragdoll.dlo; done"
# The rebuild of the installer from the source at the commit (T4), with the release's own plugin, guide and settings
# file as its payload, as source/README.md says; then the two files compared, section by section.
ev rebuild "cp -r \"\$SRC/source\" \$W/s && mkdir -p \$W/s/build \$W/s/config && cp MXRP_Ragdoll/plugins/MXRP_Ragdoll.dlo \$W/s/build/ && cp MXRP_Ragdoll/plugins/MXRP_Ragdoll.ini \$W/s/config/ && cp MXRP_Ragdoll/MXRP_Ragdoll_LISEZ-MOI_README.txt \$W/s/ && H=\$PWD && cd \$W/s/installer && x86_64-w64-mingw32-gcc --version | head -1 && x86_64-w64-mingw32-windres -DRC_PLUGIN='\\\"1.8.203\\\"' -DRC_NAME='\\\"MXRP Beta 3.3\\\"' installer.rc -O coff -o ../build/installer.res && cd .. && x86_64-w64-mingw32-gcc -O2 -Wall -s -mwindows -static -DVER='\"1.8.203\"' -DTITLE_NAME='\"MXRP Beta 3.3 (1.8.203)\"' installer/installer.c src/inflate.c build/installer.res -o build/MXRP_Ragdoll_Installer.exe -lshell32 -lole32 -ladvapi32 && cd \"\$H\" && sha256sum MXRP_Ragdoll_Installer.exe \$W/s/build/MXRP_Ragdoll_Installer.exe && stat -c '%s %n' MXRP_Ragdoll_Installer.exe \$W/s/build/MXRP_Ragdoll_Installer.exe; echo '== sections (name, size): release, then rebuild'; objdump -h MXRP_Ragdoll_Installer.exe | awk '/^ +[0-9]/{print \$2,\$3}'; objdump -h \$W/s/build/MXRP_Ragdoll_Installer.exe | awk '/^ +[0-9]/{print \$2,\$3}'; echo '== resources: release, then rebuild'; rsrc.py MXRP_Ragdoll_Installer.exe | grep -v RT_VERSION; rsrc.py \$W/s/build/MXRP_Ragdoll_Installer.exe | grep -v RT_VERSION; echo '== the payload of each: the plugin, guide and settings file of the manual zip'; for f in MXRP_Ragdoll/plugins/MXRP_Ragdoll.dlo MXRP_Ragdoll/MXRP_Ragdoll_LISEZ-MOI_README.txt MXRP_Ragdoll/plugins/MXRP_Ragdoll.ini; do sha256sum \"\$f\"; done"
ev strings-money "for f in MXRP_Ragdoll.dlo installer.exe MXRP_Ragdoll/MXRP_Ragdoll_LISEZ-MOI_README.txt MXRP_Ragdoll/plugins/MXRP_Ragdoll.ini \"\$SRC/README.md\"; do echo \"== \$f\"; { strings -n 6 \"\$f\"; strings -el -n 6 \"\$f\"; } | grep -nE 'https?://|www\\.|[Ss]hop|[Bb]uy |[Pp]rice|[Pp]remium|[Pp]atreon|[Pp]ay[Pp]al|[Kk]o-?fi|[Dd]onat|[Cc]offee'; done"
ev guide "sed -n '1,100p' MXRP_Ragdoll/MXRP_Ragdoll_LISEZ-MOI_README.txt | grep -nE 'removes old|old versions|UPDATES|downloads it|Ask before|kick|ON/OFF button is not enough|plugin is still loaded|talk through|Every player needs|send Documents|Walking animation|FMX ramps:|Furniture:|RAGDOLL is added'"
ev readme "grep -nE '^- \\*\\*(Internet|Local network|Online|Steam ID|Auto-kick|Game|Keys|Files|Uninstall):' \"\$SRC/README.md\""
ev payload "python3 -I -c 'import sys; f=open(sys.argv[1],\"rb\").read(); [print(p, \"found at offset\", f.find(open(p,\"rb\").read())) for p in sys.argv[2:]]' installer.exe MXRP_Ragdoll/plugins/MXRP_Ragdoll.dlo MXRP_Ragdoll/MXRP_Ragdoll_LISEZ-MOI_README.txt MXRP_Ragdoll/plugins/MXRP_Ragdoll.ini"
# The game channel: with reseau (settings+0xa8 = 0x2e427b8e8) at 0 it is logged "non utilise" (0x2e3ae9173) and not used.
dis MXRP_Ragdoll.dlo 2e3a76678 2e3a766b9
# The plugin's renaming of its own old names in a folder: for each suffix of the table below, "<folder>\mxb_ragdoll<suffix>"
# (0x2e3ae8d34) is renamed "<folder>\MXRP_Ragdoll<suffix>" (0x2e3ae8d46) when it exists (GetFileAttributesA).
ev rename-old-names "ptrtable.py MXRP_Ragdoll.dlo 2e3ae9e00 5 8; iat.py MXRP_Ragdoll.dlo | grep -E '0x2e5fcb(8d0|990) '"
dis MXRP_Ragdoll.dlo 2e3a752b0 2e3a75332
