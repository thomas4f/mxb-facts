#!/usr/bin/env bash
# MXB Studio 1.0.1. Its Software License Terms (https://mxbstudio.com/software-license.html, "Restrictions and third-party
# rights") forbid reverse engineering and decompiling the software, so this covers public facts only (rule 6): the release
# files' hashes and types, the installer's code signature, whether the update packages carry a package signature, the update
# feed, the release page, the GitHub repository and the tool's public pages. Nothing is run, unpacked or disassembled.
# The folder holds the three files of https://github.com/smithtan91-netizen/mxb-studio-downloads/releases/tag/v1.0.1, by
# their names. The public-page commands fetch the pages as they are when run; the committed output is from the card's date.
# Needs osslsigncode (apt install osslsigncode).
. "$(dirname "$0")/../ev.sh"
ev files "sha256sum MXBStudio-win-Setup.exe MXBStudio-1.0.1-full.nupkg MXBStudio-1.0.1-delta.nupkg"
ev file "file MXBStudio-win-Setup.exe MXBStudio-1.0.1-full.nupkg MXBStudio-1.0.1-delta.nupkg"
# Code signing: the Security (certificate) directory entry of the installer's header, then an Authenticode check of it
# against Microsoft's "Identity Verification Root Certificate Authority 2020" (Windows trusts it; Linux's CA bundle doesn't
# hold it), fetched from Microsoft's PKI page. Only the common name of each certificate subject is kept (rule 10).
ev signature "objdump -p MXBStudio-win-Setup.exe | grep -E 'file format|Security Directory'; curl -sSL -o \$W/root.crt 'http://www.microsoft.com/pkiops/certs/Microsoft%20Identity%20Verification%20Root%20Certificate%20Authority%202020.crt' && openssl x509 -inform DER -in \$W/root.crt -out \$W/root.pem && openssl x509 -in \$W/root.pem -noout -subject -fingerprint -sha256; osslsigncode verify -CAfile \$W/root.pem -TSA-CAfile \$W/root.pem -in MXBStudio-win-Setup.exe 2>&1 | sed -E 's/^(\\s*Subject: ).*(CN=[^,]*).*/\\1\\2/' | grep -vE '^\\s*$'"
# Whether the two update packages (zip files) carry a NuGet package signature: the count of .signature.p7s entries in each
# one's file list. Nothing is extracted.
ev nupkg-signature "for f in MXBStudio-1.0.1-full.nupkg MXBStudio-1.0.1-delta.nupkg; do printf '%s: ' \$f; unzip -Z1 \$f | grep -cE '(^|/)\\.signature\\.p7s\$'; done"
# The release page and the public repository (GitHub API): assets with their published digests, the tag's commit, every
# file of the repository at that commit, its licence and its history.
ev release "curl -sS https://api.github.com/repos/smithtan91-netizen/mxb-studio-downloads/releases/tags/v1.0.1 | python3 -I -c 'import json,sys;r=json.load(sys.stdin);print(r[\"tag_name\"],r[\"name\"],r[\"published_at\"],\"target:\",r[\"target_commitish\"]);[print(a[\"name\"],a[\"size\"],a[\"digest\"]) for a in r[\"assets\"]];print(r[\"body\"])'"
ev repo "curl -sS https://api.github.com/repos/smithtan91-netizen/mxb-studio-downloads/git/refs/tags/v1.0.1 | python3 -I -c 'import json,sys;print(\"tag v1.0.1 ->\",json.load(sys.stdin)[\"object\"][\"sha\"])'; curl -sS 'https://api.github.com/repos/smithtan91-netizen/mxb-studio-downloads/git/trees/9518e331eff3d27984be476363881ee65019d451?recursive=1' | python3 -I -c 'import json,sys;[print(t[\"type\"],t[\"path\"]) for t in json.load(sys.stdin)[\"tree\"]]'; curl -sS https://api.github.com/repos/smithtan91-netizen/mxb-studio-downloads | python3 -I -c 'import json,sys;r=json.load(sys.stdin);print(\"description:\",r[\"description\"]);print(\"license:\",r[\"license\"])'; curl -sS https://api.github.com/repos/smithtan91-netizen/mxb-studio-downloads/commits | python3 -I -c 'import json,sys;[print(c[\"sha\"],c[\"commit\"][\"committer\"][\"date\"],c[\"commit\"][\"message\"].splitlines()[0]) for c in json.load(sys.stdin)]'"
ev readme "curl -sS https://raw.githubusercontent.com/smithtan91-netizen/mxb-studio-downloads/9518e331eff3d27984be476363881ee65019d451/README.md"
# Where the homepage's download button leads (the form's action, then the redirect it answers with).
ev download "curl -sSL https://mxbstudio.com/download.html | grep -oE '<form[^>]*>'; curl -sS -I https://mxbstudio.com/updates/MXBStudio-win-Setup.exe | grep -iE '^(HTTP|location)'"
# The update feed on the tool's site (public): its SHA-256 (the release text names it as "feed"), and each package it lists.
ev feed "curl -sS -o \$W/feed.json https://mxbstudio.com/updates/releases.win.json && sha256sum \$W/feed.json | cut -c1-64 && python3 -I -c 'import json,sys;[print(a[\"PackageId\"],a[\"Version\"],a[\"Type\"],a[\"FileName\"],\"SHA256:\",a[\"SHA256\"],a[\"Size\"]) for a in json.load(open(sys.argv[1]))[\"Assets\"]]' \$W/feed.json"
# Text of the public pages, tags removed, then the lines the card quotes.
PAGE='python3 -I -c "import html,re,sys;t=sys.stdin.read();t=re.sub(r\"(?s)<(script|style).*?</\\1>\",\"\",t);t=re.sub(r\"<br\\s*/?>|</p>|</li>|</h[0-9]>|</div>\",\"\\n\",t);t=re.sub(r\"<[^>]+>\",\"\",t);[print(l.strip()) for l in html.unescape(t).splitlines() if l.strip()]"'
ev licence "curl -sSL https://mxbstudio.com/software-license.html | $PAGE | grep -nE 'Effective date|^We grant|reverse engineer/decompile|Vendor checks|Pro allows two'"
ev privacy "curl -sSL https://mxbstudio.com/privacy.html | $PAGE | grep -nE 'Effective date|^Free needs no account|Windows Credential Manager|LimeLM|Update requests'"
ev terms "curl -sSL https://mxbstudio.com/terms.html | $PAGE | grep -nE 'Effective date|^Free requires no account|^Pro is|7-day trial'"
ev plans "curl -sSL https://mxbstudio.com/plans.html | $PAGE | grep -nE '^\\\$0|month|Free and Pro both|Exports without the Studio watermark|Track-menu image without|^Erosion|^Multi-ruts, bumps|^Cameras and marshals|^Multiple editable layouts'"
ev help "curl -sSL https://mxbstudio.com/help.html | $PAGE | grep -nE 'Check for updates'; curl -sSL https://mxbstudio.com/export-help.html | $PAGE | grep -nE 'includes its own compiler|^Install in MX Bikes installs'"
ev home "curl -sSL https://mxbstudio.com/ | $PAGE | grep -nE 'Free download|Windows x64'"
# Shop, payment and donation words on the release page, README and the tool's pages (M2, M3).
ev money "for p in '' download.html plans.html help.html changelog.html software-license.html terms.html; do echo \"== mxbstudio.com/\$p\"; curl -sSL https://mxbstudio.com/\$p | $PAGE | grep -niE 'donat|ko-?fi|patreon|paypal|buymeacoffee|stripe'; done; echo '== README and release text'; { curl -sS https://raw.githubusercontent.com/smithtan91-netizen/mxb-studio-downloads/9518e331eff3d27984be476363881ee65019d451/README.md; curl -sS https://api.github.com/repos/smithtan91-netizen/mxb-studio-downloads/releases/tags/v1.0.1; } | grep -ciE 'donat|ko-?fi|patreon|paypal|buymeacoffee'"
