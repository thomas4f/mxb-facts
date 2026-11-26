#!/bin/bash
# usage: run.sh <game> <case> <card-slug> [--game-version <version>] [--ride <seconds>] [--key <second> <key>]... <plugin file or folder>...
# Runs the real game (the public demo of mxbikes or gpbikes, games.json: the --game-version named, else the newest) with the plugins under test in its plugins folder:
# offline (unshare -n), on a virtual screen (Xvfb), traced by strace and WINEDEBUG=+loaddll. It clicks through the menus to
# Testing on the demo's first track (each step waits for the screen to settle), rides for --ride seconds (default 30) holding the throttle, presses each --key (an
# xdotool key name, such as F8 or ctrl+r) that many seconds after reaching the track, and quits. The evidence goes to
# lab/results/<card-slug>/<case>/, in the layout of the test host's collect.sh.
# The demo is downloaded once into cache/ and checked against its SHA-256; nothing of the game goes into the repository.
set -euo pipefail
H="$(cd "$(dirname "$0")" && pwd)"; ROOT="$(cd "$H/../.." && pwd)"; PT="$ROOT/lab/plugin-test-host"
game=$1 case=$2 slug=$3; shift 3
ride=30; keys=(); plugins=(); gver=
while [ $# -gt 0 ]; do
  case $1 in
    --game-version) gver=$2; shift 2;;
    --ride) ride=$2; shift 2;;
    --key) keys+=("$2 $3"); shift 3;;
    *) plugins+=("$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"); shift;;
  esac
done
# The demo: its name, version, URL, SHA-256, exe and menu steps (games.py).
demo=$(python3 -I "$H/games.py" pick "$game" $gver)
cfg() { printf '%s' "$demo" | python3 -I -c "import json,sys; print(json.load(sys.stdin)$1)"; }
url=$(cfg "['url']"); sha=$(cfg "['sha256']"); exe=$(cfg "['exe']"); ver=$(cfg "['version']")

# 1. The Wine prefix and tools come from the test host's setup.
[ -d "$PT/build/wpfx" ] || bash "$PT/setup.sh"
command -v xdotool >/dev/null && command -v import >/dev/null || DEBIAN_FRONTEND=noninteractive apt-get install -y -q --no-install-recommends xdotool imagemagick >/dev/null

# 2. The demo, downloaded and unpacked once, checked by SHA-256 (the installer is a self-extracting zip).
C="$H/cache/$game/$ver"; mkdir -p "$C"; inst="$C/$(basename "$url")"
if [ ! -f "$C/game/.ok" ]; then
  [ -f "$inst" ] && echo "$sha  $inst" | sha256sum -c --status || curl -fsSL --retry 3 -o "$inst" "$url"
  echo "$sha  $inst" | sha256sum -c --status || { echo "real game: $inst doesn't match its SHA-256 in games.json" >&2; exit 1; }
  rm -rf "$C/game"; 7z x -y -o"$C/game" "$inst" >/dev/null || true
  [ -f "$C/game/$exe" ] || { echo "real game: unpacking $inst gave no $exe" >&2; exit 1; }
  (cd "$C/game" && find . -type f -name '*.pkz' -print0 | sort -z | xargs -0 sha256sum) > "$C/pkz.sha256"
  touch "$C/game/.ok"
fi

# 3. A fresh run folder: the game's small files copied, its large data files (.pkz) linked, the plugins under test added,
# and a fresh Wine prefix, so what the run writes (in the game folder or in Documents) is all new.
R="$H/build/$case"; rm -rf "$R"; mkdir -p "$R"
G="$R/game"; mkdir -p "$G"
(cd "$C/game" && find . -type d -exec mkdir -p "$G/{}" \; && find . -type f ! -name '*.pkz' ! -name .ok -exec cp {} "$G/{}" \; && find . -type f -name '*.pkz' -exec ln -s "$C/game/{}" "$G/{}" \;)
for p in "${plugins[@]}"; do cp -r "$p" "$G/plugins/"; done
cp -a "$PT/build/wpfx" "$R/wpfx"
lists() { (cd "$G" && find . -type f | sort; cd "$R/wpfx/drive_c/users" && find . -type f | sed 's|^\.|users|' | sort); }
lists > "$R/before.lst"

# 4. The run, inside one network namespace with no network: the screen, the game and the clicks.
cat > "$R/drive.sh" <<EOF
#!/bin/bash
export DISPLAY=:77
Xvfb :77 -screen 0 1280x720x24 -nolisten tcp >/dev/null 2>&1 & sleep 2
export WINEPREFIX="$R/wpfx" WINEDEBUG=+loaddll,err+all WINEDLLOVERRIDES="mscoree,mshtml="
unset ANTHROPIC_API_KEY GH_TOKEN GITHUB_TOKEN VT_API_KEY
cd "$G"
strace -f -qq -o "$R/strace.log" -e trace=socket,connect,sendto,bind,openat,unlinkat,renameat,renameat2,mkdirat,execve wine "$exe" > "$R/game.log" 2> "$R/wine.log" &
shot() { import -window root "$R/shot_\$1.png"; echo "\$(date +%s) \$1" >> "$R/steps.log"; }
click() { xdotool mousemove \$1 \$2; sleep 0.5; xdotool mousedown 1; sleep 0.2; xdotool mouseup 1; }
# The screen, small and coarse, so a still screen hashes the same; and whether it shows anything at all.
look() { import -window root -resize 64x36 -colorspace gray -depth 4 gray:- 2>/dev/null | md5sum | cut -c1-12; }
lit() { [ "\$(import -window root -resize 64x36 -colorspace gray -format '%[fx:mean>0.03]' info: 2>/dev/null)" = 1 ]; }
# Wait (at most \$1 seconds) until the screen shows something and differs from \$2 (the screen before a click), then until it
# holds still, or 10 seconds more for a screen that keeps moving (a turning bike in a menu).
settle() { local end=\$((SECONDS + \$1)) prev= h t0=; while [ \$SECONDS -lt \$end ]; do h=\$(look); if lit && [ "\$h" != "\$2" ]; then t0=\${t0:-\$SECONDS}; { [ "\$h" = "\$prev" ] || [ \$((SECONDS - t0)) -ge 10 ]; } && return 0; fi; prev=\$h; sleep 3; done; return 1; }
# Point at a button, let its hover show, then click until the screen moves on (a slow game can miss a click), 3 tries at most.
press() { local b i; xdotool mousemove \$1 \$2; sleep 2; b=\$(look); for i in 1 2 3; do click \$1 \$2; settle \$3 \$b && return 0; echo "\$(date +%s) no change after clicking \$1,\$2 (try \$i)" >> "$R/steps.log"; done; }
# The average colour of a 24 by 10 patch at x,y, as "r g b".
patch() { import -window root -crop 24x10+\$((\$1 - 12))+\$((\$2 - 5)) +repage -resize 1x1 -format '%[fx:int(255*r)] %[fx:int(255*g)] %[fx:int(255*b)]' info: 2>/dev/null; }
# Wait (at most \$1 seconds) until the patch at \$2,\$3 is within 40 of the colour \$4 \$5 \$6: a button that shows only on the right screen.
until_colour() { local end=\$((SECONDS + \$1)) c; while [ \$SECONDS -lt \$end ]; do c=(\$(patch \$2 \$3)); [ \${#c[@]} = 3 ] && [ \$(( (c[0]-\$4)*(c[0]-\$4) + (c[1]-\$5)*(c[1]-\$5) + (c[2]-\$6)*(c[2]-\$6) )) -lt 1600 ] && return 0; sleep 3; done; echo "\$(date +%s) timed out waiting for the colour at \$2,\$3" >> "$R/steps.log"; }
EOF
printf '%s' "$demo" > "$R/demo.json"
python3 -I - "$R/demo.json" "$R" >> "$R/drive.sh" <<'PY'
import json, sys
# Each step first waits for its button's colour (when it names one, "until": x, y, r, g, b), clicks (when it has a place to
# click), then waits at most "wait" seconds for the next screen to settle.
for s in json.load(open(sys.argv[1]))['steps']:
    if 'until' in s: print(f"until_colour {s['wait']} {' '.join(map(str, s['until']))}")
    if 'click' in s: print(f"press {s['click'][0]} {s['click'][1]} {s['wait']}")
    else: print(f"settle {s['wait']} none || echo \"$(date +%s) timed out\" >> {sys.argv[2]}/steps.log")
    print(f"shot {s['name']}")
PY
{
  echo "xdotool keydown Up"
  t=0
  for k in $(printf '%s\n' "${keys[@]}" | sort -n | tr ' ' ':'); do
    s=${k%%:*}; n=${k#*:}; [ "$s" -gt "$t" ] && echo "sleep $((s - t))" && t=$s
    echo "xdotool key $n; sleep 2; shot key-$n"; t=$((t + 2))
  done
  [ "$ride" -gt "$t" ] && echo "sleep $((ride - t))"
  echo "xdotool keyup Up; shot ride"
  echo "WINEPREFIX=\"$R/wpfx\" wineserver -k; sleep 3"
} >> "$R/drive.sh"
chmod +x "$R/drive.sh"
U="unshare -n"; [ "$(id -u)" = 0 ] || U="unshare -c -n"
timeout 900 $U "$R/drive.sh" || true
lists > "$R/after.lst"

# 5. The evidence, as the test host's collect.sh lays it out, plus the screenshots after each step. raw/ holds the originals,
# compressed: the whole trace, everything Wine printed and everything the game printed.
O="$ROOT/lab/results/$slug/$case"; rm -rf "$O"; mkdir -p "$O"
{ echo "game: $(cfg "['name']"), $exe, installer SHA-256 $sha"; echo "steps (unix time, step):"; cat "$R/steps.log"; } > "$O/host.log"
mkdir -p "$O/raw"; for f in strace.log wine.log game.log; do gzip -9 -n -c "$R/$f" > "$O/raw/$f.gz"; done
diff "$R/before.lst" "$R/after.lst" | grep '^[<>]' > "$O/files.diff" || true
grep -E 'AF_INET6?' "$R/strace.log" > "$O/network.txt" || echo "No internet sockets (AF_INET or AF_INET6) in the trace. The run had no network (unshare -n), so this shows attempts, not traffic." > "$O/network.txt"
grep -o 'Loaded L"[^"]*"' "$R/wine.log" | sed 's/\\\\/\\/g' | sort -u > "$O/loaded.txt" || true
(cd "$G" && sha256sum plugins/* 2>/dev/null | grep -v ': Is a directory') > "$O/plugins.sha256" || true
cp "$R"/shot_*.png "$O/" 2>/dev/null || true
# The game's data must be untouched: a run that wrote into a linked .pkz spoils the cache, so it is unpacked again next time.
(cd "$C/game" && sha256sum -c --status "$C/pkz.sha256") || { rm -f "$C/game/.ok"; echo "a .pkz changed during the run: see files.diff" >> "$O/host.log"; }
echo "evidence in $O"
