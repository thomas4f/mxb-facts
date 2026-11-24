#!/usr/bin/env bash
# Heightmap Studio 26.11.7. Its Terms of Use (https://heightmapstudio.com/terms, section 4) forbid reverse engineering,
# decompiling and disassembling the app, so this covers public facts only (rule 6): the release files' hashes, whether
# the Windows installer carries a code signature, the update feed, the release page and the tool's public pages. Nothing
# is run, unpacked or disassembled.
# The folder holds the seven files of https://github.com/bradenmackey/hms-public/releases/tag/v26.11.7, by their names.
# The public-page commands fetch the pages as they are when run; the committed output is from the date of the card.
. "$(dirname "$0")/../ev.sh"
ev files "sha256sum Heightmap-Studio-setup.exe Heightmap-Studio-setup.exe.sig Heightmap-Studio.AppImage Heightmap-Studio.AppImage.sig Heightmap-Studio.deb Heightmap-Studio.rpm latest.json"
ev file "file Heightmap-Studio-setup.exe Heightmap-Studio-setup.exe.sig Heightmap-Studio.AppImage Heightmap-Studio.AppImage.sig Heightmap-Studio.deb Heightmap-Studio.rpm latest.json"
# Code signing: only the Security (certificate) directory entry of the installer's header; nothing else of it is read.
ev signature "objdump -p Heightmap-Studio-setup.exe | grep -E 'file format|Security Directory'"
# The Linux packages' signatures: the AppImage's signature sections (.sha256_sig, .sig_key), the .deb's members (a signed
# .deb has a _gpg member), and the .rpm's signature header (rpm -K names a signature it finds). Nothing is unpacked.
ev signature-linux "objdump -h Heightmap-Studio.AppImage | grep -E 'file format|sig'; ar t Heightmap-Studio.deb; rpm -Kv Heightmap-Studio.rpm"
# Whether the AppImage's two signature sections hold anything: the count of non-zero bytes in each (0 = empty, unsigned).
ev signature-appimage "for s in .sha256_sig .sig_key; do printf '%s non-zero bytes: ' \$s; objdump -s -j \$s Heightmap-Studio.AppImage | awk 'NR>4{for(i=2;i<=5;i++)print \$i}' | grep -o .. | grep -vc 00; done"
# The update feed published with the release (the file is public): its version, date, and for each platform the file it
# points to and whether a signature comes with it. The signature text is decoded only to its first (comment) line.
ev feed "python3 -I -c 'import json,base64;d=json.load(open(\"latest.json\"));print(\"version:\",d[\"version\"],\"pub_date:\",d[\"pub_date\"]);[print(p,v[\"url\"],\"signature:\",base64.b64decode(v[\"signature\"]).decode().splitlines()[0]) for p,v in d[\"platforms\"].items()]'"
ev sig-files "for f in *.sig; do echo \"\$f:\"; base64 -d \"\$f\" | head -1; echo; done"
# The release page and the public repository (GitHub API): assets with their published digests, the tag's commit,
# every file of the repository at that commit, and its history.
ev release "curl -sS https://api.github.com/repos/bradenmackey/hms-public/releases/tags/v26.11.7 | python3 -I -c 'import json,sys;r=json.load(sys.stdin);print(r[\"tag_name\"],r[\"published_at\"],\"target:\",r[\"target_commitish\"]);[print(a[\"name\"],a[\"size\"],a[\"digest\"]) for a in r[\"assets\"]]'"
ev repo "curl -sS https://api.github.com/repos/bradenmackey/hms-public/git/refs/tags/v26.11.7 | python3 -I -c 'import json,sys;print(\"tag v26.11.7 ->\",json.load(sys.stdin)[\"object\"][\"sha\"])'; curl -sS 'https://api.github.com/repos/bradenmackey/hms-public/git/trees/dcafa91992d4e556abc9fcf1c7d28af32e69bec8?recursive=1' | python3 -I -c 'import json,sys;[print(t[\"type\"],t[\"path\"]) for t in json.load(sys.stdin)[\"tree\"]]'; curl -sS https://api.github.com/repos/bradenmackey/hms-public | python3 -I -c 'import json,sys;r=json.load(sys.stdin);print(\"license:\",r[\"license\"])'; curl -sS https://api.github.com/repos/bradenmackey/hms-public/commits | python3 -I -c 'import json,sys;[print(c[\"sha\"],c[\"commit\"][\"committer\"][\"date\"],c[\"commit\"][\"message\"].splitlines()[0]) for c in json.load(sys.stdin)]'"
# Text of the public pages, tags removed, then the lines the card quotes.
PAGE='python3 -I -c "import html,re,sys;t=sys.stdin.read();t=re.sub(r\"(?s)<(script|style).*?</\\1>\",\"\",t);t=re.sub(r\"<br\\s*/?>|</p>|</li>|</h[0-9]>|</div>\",\"\\n\",t);t=re.sub(r\"<[^>]+>\",\"\",t);[print(l.strip()) for l in html.unescape(t).splitlines() if l.strip()]"'
ev terms "curl -sSL https://heightmapstudio.com/terms | $PAGE | grep -nE 'Effective|reverse engineer|^Personal license|^You may use every|^Commercial license|You need an active Commercial|currently \\\$|checks heightmapstudio.com for updates|Third-Party Notices|^5\\. Plugins|can install game plugins'"
ev privacy "curl -sSL https://heightmapstudio.com/privacy | $PAGE | grep -nE 'Effective|We do not track you|license server|checks heightmapstudio.com for a newer version|Place searches send|token is sent only'"
ev pricing "curl -sSL https://heightmapstudio.com/pricing | $PAGE | grep -nE 'Free to build|per user, per year|For hobby|For anything you sell|Unsigned for now|Version 2[0-9]\\.'"
ev readme "curl -sS https://raw.githubusercontent.com/bradenmackey/hms-public/dcafa91992d4e556abc9fcf1c7d28af32e69bec8/README.md"
ev notices "curl -sS https://heightmapstudio.com/third-party-notices.txt | sed -n 1,8p"
# Shop, payment and donation words on the release page and the tool's pages (M2, M3).
ev money "for p in '' pricing terms; do echo \"== heightmapstudio.com/\$p\"; curl -sSL https://heightmapstudio.com/\$p | $PAGE | grep -niE 'donat|ko-?fi|patreon|paypal|buymeacoffee|buy a license|stripe'; done"
