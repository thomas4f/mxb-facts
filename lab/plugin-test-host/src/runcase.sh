#!/bin/bash
# usage: [GAME=gpbikes] runcase.sh <case> <host args...>
# Runs mxbikes.exe (or gpbikes.exe with GAME=gpbikes, for GP Bikes plugins) in $S/run/<case>/ (put the plugins under test there first, in plugins/ as in the game;
# the host and victim.dlo are copied in when missing)
# with no network (unshare -n), on a virtual screen (Xvfb), traced by strace and WINEDEBUG=+loaddll.
# $S is the build folder from setup.sh (it holds the Wine prefix wpfx/).
S="${S:-$(cd "$(dirname "$0")/.." && pwd)/build}"
c=$1; shift
G="${GAME:-mxbikes}.exe"
cd "$S/run/$c" || exit 1
[ -f "$G" ] || cp "$S/$G" .
[ -f victim.dlo ] || cp "$S/victim.dlo" .
mkdir -p "/run/user/$(id -u)" 2>/dev/null; chmod 700 "/run/user/$(id -u)" 2>/dev/null
# The program under test gets none of the runner's keys (the analysis workflow's API key, GitHub tokens).
unset ANTHROPIC_API_KEY GH_TOKEN GITHUB_TOKEN
export WINEPREFIX=$S/wpfx WINEDEBUG=+loaddll,err+all${WINEDEBUG_EXTRA:+,$WINEDEBUG_EXTRA} WINEDLLOVERRIDES="mscoree,mshtml="
find . -type f | sort > before.lst
# A regular user (a GitHub runner) gets its network namespace through a user namespace that maps it to itself (-c).
U="unshare -n"; [ "$(id -u)" = 0 ] || U="unshare -c -n"
timeout 600 $U xvfb-run -a -s "-screen 0 1280x720x24" \
  strace -f -qq -o strace.log -e trace=socket,connect,sendto,bind,openat,unlinkat,renameat,renameat2,mkdirat,execve \
  wine "$G" "$@" > host.log 2> wine.log
echo "exit=$?" >> host.log
find . -type f | sort > after.lst
