#!/usr/bin/env bash
# imports_at.sh <plugin> <function>...: every call through the import table to each named function, by address, and
# for the memory-protection calls the address of the code that loads the MinGW runtime's "pseudo relocation" message
# (the runtime routine that fixes up the plugin's own addresses at load time).
set -eu
f=$1; shift
iat="$(dirname "$0")/../iat.py"
t=$(mktemp); objdump -d "$f" > "$t"
for fn in "$@"; do
  a=$(python3 -I "$iat" "$f" | awk -v n="$fn" '{split($2, p, "!"); if (p[2] == n) print $1}')
  printf '%s (import slot %s): ' "$fn" "$a"
  grep -E "# $a\$" "$t" | awk '{print $1}' | tr '\n' ' '; echo
done
read -r vma off < <(objdump -h "$f" | awk '$2 == ".rdata" {print $4, $6}')
for s in 'Unknown pseudo relocation protocol' 'Unknown pseudo relocation bit size' 'bit pseudo relocation at'; do
  o=$(strings -t x -n 6 "$f" | grep -m1 "$s" | awk '{print $1}')
  m=$(strings -n 6 "$f" | grep -m1 "$s" | sed 's/^ *//')
  v=$(printf '%x' $((0x$vma + 0x$o - 0x$off)))
  printf '"%s" at 0x%s, loaded by: ' "$m" "$v"
  grep -E "# 0x$v\$" "$t" | awk '{print $1}' | tr '\n' ' '; echo
done
rm -f "$t"
