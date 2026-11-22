#!/bin/bash
# usage: build.sh <folder>
# Builds the plugin test host into <folder>: mxbikes.exe, gpbikes.exe (the same host with GP Bikes' struct layouts) and
# victim.dlo, with MinGW. Used by setup.sh (the Wine lab) and by the "Analyse a tool" workflow's Windows run.
set -euo pipefail
H="$(cd "$(dirname "$0")/.." && pwd)"
B="$1"
mkdir -p "$B"
# PiBoSo's plugin header isn't kept here (it is PiBoSo's file). piboso.com isn't reachable from cloud
# sessions, so it comes from a public repository that carries it unchanged, pinned to a commit.
HDR_URL="https://raw.githubusercontent.com/LeadingTrendTechnologies/HoleshotHUD/3ffdbf366023c19e1741178e39b5704a91728819/src/vendor/piboso/mxb_api.h"
HDR_SHA="259195fa4bb255535c15abc0b97e2e73e331c101f140a100b737719b9957eeeb"
if ! echo "$HDR_SHA  $B/mxb_api.h" | sha256sum --check --status 2>/dev/null; then
  curl -sfL --retry 3 -o "$B/mxb_api.h" "$HDR_URL"
  echo "$HDR_SHA  $B/mxb_api.h" | sha256sum --check --quiet
fi
# GP Bikes: the struct layouts come from PiBoSo's GP Bikes plugin example (gpb_example.c), carried unchanged
# by a public repository, pinned to a commit; only its typedefs are kept, as gpb_api.h.
GPB_URL="https://raw.githubusercontent.com/JR-SRUSA/GPBikesPluginLogger/d54fac0d7f5eec5ecf869fa01ad30f627c79cd4e/gpb_example.c"
GPB_SHA="b1b49860345d6feb3d9dac9d657ab056f6d1fb0aa2e85bc841207a8cb052cab7"
if ! echo "$GPB_SHA  $B/gpb_example.c" | sha256sum --check --status 2>/dev/null; then
  curl -sfL --retry 3 -o "$B/gpb_example.c" "$GPB_URL"
  echo "$GPB_SHA  $B/gpb_example.c" | sha256sum --check --quiet
fi
awk '/^typedef struct/{p=1} p{print} /^}.*;/{p=0}' "$B/gpb_example.c" > "$B/gpb_api.h"
x86_64-w64-mingw32-g++ -O2 -static -I"$B" -o "$B/mxbikes.exe" "$H/src/host.cpp" -lopengl32 -lgdi32 -luser32
x86_64-w64-mingw32-g++ -O2 -static -DGPB -I"$B" -o "$B/gpbikes.exe" "$H/src/host.cpp" -lopengl32 -lgdi32 -luser32
x86_64-w64-mingw32-g++ -O2 -shared -static -o "$B/victim.dlo" "$H/src/victim.cpp" -lopengl32
