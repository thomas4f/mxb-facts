#!/bin/bash
# usage: unshare -n -m runapp.sh <run folder> <app folder under drive_c> <exe> [seconds]
# Runs an app (.exe) offline under Wine and Xvfb, traced by strace, inside a network namespace that has only
# loopback. resolv.conf points at 127.0.0.1, where dnslog.py writes each host name the app looks up to
# <run folder>/dns.log and refuses it, so nothing resolves and no traffic leaves. WINEPREFIX must be set.
set -u
# The program under test gets none of the runner's keys (the analysis workflow's API key, GitHub tokens).
unset ANTHROPIC_API_KEY GH_TOKEN GITHUB_TOKEN
D=$1 APP=$2 EXE=$3 T=${4:-150}
H="$(cd "$(dirname "$0")" && pwd)"
python3 -I "$H/lo_up.py"
echo "nameserver 127.0.0.1" > /tmp/resolv.conf.test
mount --bind /tmp/resolv.conf.test /etc/resolv.conf
python3 -I "$H/dnslog.py" "$D/dns.log" &
sleep 1
cd "$WINEPREFIX/drive_c/$APP"
timeout "$T" xvfb-run -a -s "-screen 0 1280x720x24" strace -f -qq -o "$D/strace.log" -e trace=socket,connect,sendto,execve wine "$EXE" > "$D/app.log" 2>&1
echo "exit=$?" >> "$D/app.log"
