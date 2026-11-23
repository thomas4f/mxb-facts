#!/usr/bin/env bash
# MXB Discord RPC, the mxb-mods.com download of 6 Oct 2024 (open source: the release files and the source).
# The folder holds "MXB Discord RPC.zip", the file the MediaFire link on
# https://mxb-mods.com/improved-discord-rich-presence-discord-rpc/ gives
# (https://www.mediafire.com/file/303b4vaofhtvt3y/MXB_Discord_RPC.zip/file), and discord_game_sdk.zip, Discord's Game SDK
# 3.2.1 (https://dl-game-sdk.discordapp.net/3.2.1/discord_game_sdk.zip, the address the plugin's includes.h names).
# The second argument is a checkout of https://github.com/starsssy/mxb-discord-rpc at
# 92fbd333129d47e96d0aaed10d11e89931824b8a. This script unpacks the release zip into the same folder, flat
# (discord-rpc.dlo, discord_game_sdk.dll, "READ ME IMPORTANT.txt"), and the SDK into sdk/.
. "$(dirname "$0")/../ev.sh"
(cd "$R" && unzip -o -q -j 'MXB Discord RPC.zip' && mkdir -p sdk && unzip -o -q discord_game_sdk.zip -d sdk)
ev files "sha256sum 'MXB Discord RPC.zip' discord-rpc.dlo discord_game_sdk.dll 'READ ME IMPORTANT.txt' discord_game_sdk.zip"
ev file "file discord-rpc.dlo discord_game_sdk.dll 'READ ME IMPORTANT.txt'; unzip -l 'MXB Discord RPC.zip'"
ev readme "cat -A 'READ ME IMPORTANT.txt' | sed 's/\\^M\\\$\$//'"
# The Discord DLL is Discord's own: the same file as in Discord's SDK 3.2.1 download, and the copy in the repository.
# Nothing inside it is examined; only its hash and its code signature.
ev sdk-dll "sha256sum discord_game_sdk.dll sdk/lib/x86_64/discord_game_sdk.dll sdk/lib/x86_64/discord_game_sdk.dll.lib; cd \"\$SRC\" && sha256sum discord_game_sdk.dll mxb-plugin/discord/lib/discord_game_sdk.dll.lib"
# The SDK's C++ wrapper in the repository is Discord's, unchanged.
ev sdk-src "for f in sdk/cpp/*; do b=\$(basename \"\$f\"); cmp \"\$f\" \"\$SRC/mxb-plugin/discord/src/\$b\" && echo \"same \$b\"; done; ls \"\$SRC/mxb-plugin/discord/src\" | wc -l"
pe discord-rpc.dlo
# Code signing: the Security (certificate) directory of each program file, and the signer of the Discord DLL.
ev signature "for f in discord-rpc.dlo discord_game_sdk.dll; do objdump -p \$f | grep -E 'file format|Security Directory'; done"
ev signature-sdk "python3 -I -c 'import struct,sys; d=open(sys.argv[1],\"rb\").read(); pe=struct.unpack_from(\"<I\",d,0x3C)[0]; o,n=struct.unpack_from(\"<II\",d,pe+24+112+4*8); sys.stdout.buffer.write(d[o+8:o+n])' discord_game_sdk.dll | openssl pkcs7 -inform DER -print_certs -noout | grep -E '^subject='"
# Everything the plugin imports beyond the C/C++ runtime: only DiscordCreate from the SDK and a few KERNEL32 functions.
ev imports-dlls "iat.py discord-rpc.dlo | grep -vE 'MSVCP140|VCRUNTIME140|api-ms-win-crt'"
# Imports a plugin would need to go online, press keys, read keys, hook input, start other programs, write the registry
# or another process, read another process, share memory, open a console or catch every crash (none).
ev imports-absent "iat.py discord-rpc.dlo | grep -iE 'ws2_32|wsock|wininet|winhttp|urlmon|SendInput|keybd_event|mouse_event|GetAsyncKeyState|GetKeyState|SetWindowsHookEx|CreateProcess|ShellExecute|WinExec|RegSetValue|RegCreateKey|WriteProcessMemory|ReadProcessMemory|OpenProcess|CreateRemoteThread|VirtualProtect|VirtualQuery|CreateFileMapping|CreateFile|AddVectoredExceptionHandler|AllocConsole'"
# Crash handler: the only SetUnhandledExceptionFilter (0x180022068) call passes 0, the C runtime's fatal-error path.
ev crash-filter "objdump -d discord-rpc.dlo | grep -B3 -A3 '# 0x180022068'"
# The plugin's text: what it puts in your Discord status (the same words as rpc.cpp at the commit; "Paused" came in that commit).
ev strings-status "strings -n 3 discord-rpc.dlo | grep -nE '^(MX Bikes|rpc-icon|Spectating|Watching Replay|%s on %s|In Menus|Paused|%s \\(Lap %i\\)|Testing|Racing|mxbikes)\$'"
# Web addresses in the plugin (none) and the DLL names it may load by name.
ev strings-urls "{ strings -n 5 discord-rpc.dlo; strings -el -n 5 discord-rpc.dlo; } | grep -niE 'https?://|www\\.|\\.(com|net|org|io)\\b'"
# The source defines CONSOLE (debug console and "[FN]"/"[ERR]" messages); the release has none of those messages.
ev console "(cd \"\$SRC\" && grep -n 'CONSOLE' mxb-plugin/includes.h mxb-plugin/main.cpp); echo '--- in the release plugin:'; strings -n 3 discord-rpc.dlo | grep -cE '\\[FN\\]|\\[ERR\\]|\\[DSC\\]|\\[\\+\\]|CONOUT|AllocConsole|SetConsoleTitle'"
# Third-party code and credits: tinyformat's licence header in the source; credits in the release (none).
ev thirdparty "(cd \"\$SRC\" && head -n 40 mxb-plugin/tinyformat.h | grep -nE 'Boost Software License|^// Tinyformat'; grep -nE 'tinyformat|discord' mxb-plugin/includes.h); grep -inE 'credit|tinyformat|licen|copyright|discord' 'READ ME IMPORTANT.txt'"
# Licence files (none) and every prebuilt program file in the repository.
ev repo-files "cd \"\$SRC\" && git ls-files | grep -iE 'licen|copying|\\.(dll|lib|exe|dlo|so|dylib)\$'; git log --format='%H %ad %s' --date=iso"
# Pinned versions: the SDK version the source names, and the project's dependencies (no package manager).
ev deps "cd \"\$SRC\" && grep -n 'game-sdk' mxb-plugin/includes.h; grep -nE 'AdditionalDependencies|PlatformToolset' mxb-plugin/mxb-plugin.vcxproj"
money discord-rpc.dlo "'READ ME IMPORTANT.txt'"
# The Windows runs (lab/results/mxb-discord-rpc-2024-10-06/): the game mapped discord-rpc.dlo, then looked for
# discord_game_sdk.dll beside mxbikes.exe, in Windows' folders and on the PATH, found it nowhere (the zip's layout put it
# in plugins\), and the plugin didn't load; no event of the run succeeded on discord_game_sdk.dll.
export RES="$OUT/../../results/mxb-discord-rpc-2024-10-06"
ev sdk-not-found "for r in ride bystander; do echo \"== \$r\"; zcat \"\$RES/\$r-windows/raw/procmon.csv.gz\" | grep -E 'Load Image.*discord|discord_game_sdk' | cut -d, -f2,4- | sed -E 's/\"//g; s/D:.a._temp.[a-z]+.run-[a-z]+.//' | head -n 4; echo \"lookups of discord_game_sdk.dll: \$(zcat \"\$RES/\$r-windows/raw/procmon.csv.gz\" | grep -c discord_game_sdk), succeeded: \$(zcat \"\$RES/\$r-windows/raw/procmon.csv.gz\" | grep discord_game_sdk | grep -c SUCCESS)\"; done; grep -n 'discord' \"\$RES/bystander-windows/host.log\""
# The MEGA mirror on the mxb-mods.com page gives the same zip as the MediaFire link (needs the network).
export TOOLS="$OUT/../../../tools"
ev mirror "python3 -I \"\$TOOLS/fetch_release.py\" get 'https://mega.nz/file/dBQyVZwQ#03Ulu8DFr9K4OLXU3jWlD9_oFeviupIKLOGlEmv7V-0' \"\$W\" 2>&1 | tail -n 1; sha256sum 'MXB Discord RPC.zip'"
