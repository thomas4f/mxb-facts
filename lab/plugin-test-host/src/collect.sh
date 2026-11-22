#!/bin/bash
# usage: collect.sh <case> <card-slug>
# Copies the evidence of a run into lab/results/<card-slug>/<case>/, where a card can link it:
# host.log (what the host saw), files.diff (files the run added or removed), network.txt (internet sockets the run's
# processes opened, from strace), loaded.txt (the DLLs Wine loaded), and the screenshots as PNG
# when Python's PIL is there. raw/ holds the originals those are read from, compressed: strace.log.gz (the whole trace) and
# wine.log.gz (everything Wine printed), so a line on a card can be checked against what the run recorded.
set -euo pipefail
H="$(cd "$(dirname "$0")/.." && pwd)"
S="${S:-$H/build}"
c=$1; slug=$2
R="$S/run/$c"; O="$H/../results/$slug/$c"
mkdir -p "$O"
cp "$R/host.log" "$O/"
mkdir -p "$O/raw"; for f in strace.log wine.log; do gzip -9 -n -c "$R/$f" > "$O/raw/$f.gz"; done
diff "$R/before.lst" "$R/after.lst" | grep '^[<>]' | grep -v -E '\./(before|after)\.lst|\./(host|wine|strace)\.log|\./shot_[0-9]+\.bmp' > "$O/files.diff" || true
grep -E 'AF_INET6?' "$R/strace.log" > "$O/network.txt" || echo "No internet sockets (AF_INET or AF_INET6) in the trace. The run had no network (unshare -n), so this shows attempts, not traffic." > "$O/network.txt"
cat "$R/host.log" "$R/wine.log" | grep -o 'Loaded L"[^"]*"' | sed 's/\\\\/\\/g' | sort -u > "$O/loaded.txt" || true
python3 -I - "$R" "$O" <<'PY' 2>/dev/null || true
import sys,glob,os
from PIL import Image
for f in sorted(glob.glob(os.path.join(sys.argv[1],'*.bmp'))):
    Image.open(f).save(os.path.join(sys.argv[2],os.path.basename(f)[:-4]+'.png'),optimize=True)
PY
sha256sum "$R"/*.dlo "$R"/plugins/*.dlo 2>/dev/null | sed "s|$R/||" > "$O/plugins.sha256" || true
echo "evidence in $O"
