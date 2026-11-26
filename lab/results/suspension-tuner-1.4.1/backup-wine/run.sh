#!/usr/bin/env bash
# Suspension Tuner 1.4.1: what its proxy_udp.ini.bak keeps across runs (P4, G6).
# Runs the app from the release zip under Wine 9 + Xvfb, with no network (the whole script runs under `unshare -n`),
# in a fresh Wine prefix that holds a test MX Bikes folder (C:\MX Bikes, one of the folders the app looks in) with a
# stub mxbikes.exe and the game's stock proxy_udp.ini, and an empty setups folder (the app won't start listening
# without one). Each run starts the app, waits, clicks "Start listening" (where the app enables the game's UDP plugin
# with "Configure MX Bikes automatically" on, the default), waits, takes a screenshot and closes it. Between runs the
# script lists the SHA-256 and the time of every file in the test folder, and prints the two .ini files.
#   Run 1: the stock file.  Run 2: no change in between.  Then the file is edited by hand to point the plugin at
#   another app (ip = 127.0.0.1:40000), as a player would for another telemetry tool.  Run 3.
#   Run 4: the .bak is deleted and the same hand edit made again, to see when the app writes its .bak.
# Needs wine, Xvfb, xdotool, ImageMagick (import) and unzip. Usage, as root or in a user namespace that may
# unshare the network: unshare -n lab/results/suspension-tuner-1.4.1/backup-wine/run.sh <SuspensionTuner.zip> > log.txt
# (the zip from https://github.com/Lilian1134/Suspension-Tuner/releases/tag/1.4.1, fetched beforehand: no network here).
set -eu
USER="${USER:-$(id -un)}"
ZIP="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
OUT="$(cd "$(dirname "$0")" && pwd)"
W="$(mktemp -d)"; trap 'wineserver -k 2>/dev/null || true; rm -rf "$W"' EXIT
export WINEPREFIX="$W/prefix" WINEDEBUG=-all DISPLAY=:77 LC_ALL=C
echo "== zip"; sha256sum "$ZIP" | sed "s#  .*/#  #"
(cd "$W" && unzip -q "$ZIP")
APP="$W/SuspensionTuner/app"
Xvfb :77 -screen 0 1280x720x24 -nolisten tcp >/dev/null 2>&1 & XP=$!
sleep 2
wineboot -i >/dev/null 2>&1
G="$WINEPREFIX/drive_c/MX Bikes"
mkdir -p "$G" "$WINEPREFIX/drive_c/users/$USER/Documents/PiBoSo/MX Bikes/profiles/unnamedProfile/setups/common"
echo stub > "$G/mxbikes.exe"
stock() { printf '[params]\r\nenable = 0\r\nport = 30000\r\nip = 127.0.0.1:30001\r\ndelay = 1\r\n'; }
edited() { printf '[params]\r\nenable = 1\r\nport = 30000\r\nip = 127.0.0.1:40000\r\ndelay = 1\r\n'; }
stock > "$G/proxy_udp.ini"
state() {
  echo "== test folder $1"
  (cd "$G" && for f in $(ls); do printf '%s  %s  %s\n' "$(sha256sum "$f" | cut -c1-64)" "$(date -u -r "$f" +%H:%M:%S.%N | cut -c1-12)" "$f"; done)
  for f in proxy_udp.ini proxy_udp.ini.bak; do [ -e "$G/$f" ] && { echo "-- $f"; tr -d '\r' < "$G/$f"; } || echo "-- $f: none"; done
}
click() { xdotool mousemove "$1" "$2"; sleep 0.5; xdotool mousedown 1; sleep 0.3; xdotool mouseup 1; }
run() {
  echo "== run $1: start the app"
  (cd "$APP" && wine start /unix "$APP/SuspensionTuner.exe")
  until xdotool search --name "Suspension Tuner" >/dev/null 2>&1; do sleep 2; done
  sleep 25
  echo "== run $1: click Start listening"
  click 157 480
  sleep 15
  import -window root "$OUT/run$1.png"
  wineserver -k; sleep 2
}
echo "SHA-256 of the stock file: $(stock | sha256sum | cut -c1-64)"
echo "SHA-256 of the hand-edited file: $(edited | sha256sum | cut -c1-64)"
state "before run 1"
run 1; state "after run 1"
run 2; state "after run 2 (no change in between)"
sleep 1; edited > "$G/proxy_udp.ini"; state "after the hand edit (ip = 127.0.0.1:40000)"
run 3; state "after run 3"
rm "$G/proxy_udp.ini.bak"; sleep 1; edited > "$G/proxy_udp.ini"; state "after deleting the .bak and the same hand edit"
run 4; state "after run 4"
kill $XP 2>/dev/null || true
