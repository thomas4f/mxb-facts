#!/bin/bash
# Sets up the plugin test host: installs Wine, MinGW, Xvfb and strace when missing, builds mxbikes.exe,
# gpbikes.exe and victim.dlo into build/ (src/build.sh), makes the
# Wine prefix, and runs a smoke test with the bystander plugin only. Safe to run again: it skips what is done.
# Run as root (cloud sessions are), or with sudo available.
set -euo pipefail
H="$(cd "$(dirname "$0")" && pwd)"
B="$H/build"
SUDO=""; [ "$(id -u)" = 0 ] || SUDO="sudo"

# 1. Packages, only those that are missing.
need=()
command -v wine >/dev/null || need+=(wine64 wine)
command -v x86_64-w64-mingw32-g++ >/dev/null || need+=(g++-mingw-w64-x86-64)
command -v xvfb-run >/dev/null || need+=(xvfb xauth)
command -v strace >/dev/null || need+=(strace)
command -v unshare >/dev/null || need+=(util-linux)
if [ ${#need[@]} -gt 0 ]; then
  $SUDO apt-get update -q
  DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y -q --no-install-recommends "${need[@]}"
fi

# Wine 9.0 (Ubuntu 24.04) aborts with "free(): invalid pointer" when the runtime dir is missing.
mkdir -p "/run/user/$(id -u)" 2>/dev/null || $SUDO mkdir -p "/run/user/$(id -u)"
chmod 700 "/run/user/$(id -u)" 2>/dev/null || true

# 2. Build, only when the sources or this script changed since the last good build.
mkdir -p "$B"
hashes="$B/.setup.sha256"
if ! sha256sum --check --status "$hashes" 2>/dev/null; then
  rm -f "$hashes"
  "$H/src/build.sh" "$B"
  rm -rf "$B/wpfx"
  WINEPREFIX="$B/wpfx" WINEDEBUG=-all timeout 300 xvfb-run -a wine wineboot -i >/dev/null 2>&1
  # Smoke test: the host with the bystander plugin only, offline. It must end cleanly.
  rm -rf "$B/run/smoke"; mkdir -p "$B/run/smoke"
  S="$B" bash "$H/src/runcase.sh" smoke --frames 60 victim.dlo
  grep -q '^host: clean exit' "$B/run/smoke/host.log" || { echo "plugin test host: smoke test failed, see $B/run/smoke/host.log" >&2; tail -n 20 "$B/run/smoke/host.log" "$B/run/smoke/wine.log" >&2; exit 1; }
  rm -rf "$B/run/smoke-gpb"; mkdir -p "$B/run/smoke-gpb"
  GAME=gpbikes S="$B" bash "$H/src/runcase.sh" smoke-gpb --frames 60 victim.dlo
  grep -q '^host: clean exit' "$B/run/smoke-gpb/host.log" || { echo "plugin test host: GP Bikes smoke test failed, see $B/run/smoke-gpb/host.log" >&2; exit 1; }
  sha256sum "$H/setup.sh" "$H/src/build.sh" "$H/src/host.cpp" "$H/src/victim.cpp" "$H/src/runcase.sh" > "$hashes"
fi
echo "plugin test host ready: $B (run a case with: S=$B $H/src/runcase.sh <case> <host args>)"
