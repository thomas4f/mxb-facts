# Evidence from a release's files, for the card lines that name a command (rule 1: a test anyone can repeat).
# Each card's folder here holds a run.sh that sources this file and runs its commands with ev; the outputs sit beside it
# and the card links them. Run it with the folder that holds the release's files, each by the name the card's "Files
# checked" table gives it (run.sh says how to get and unpack them), and for a card that reads the source, a checkout
# of the source at the card's commit: lab/evidence/<card>/run.sh <folder> [<source checkout>]
# Commands name the checkout $SRC and a scratch folder $W, so they read the same on any machine.
set -eu
OUT="$(cd "$(dirname "$0")" && pwd)"
PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd):$PATH"  # iat.py
R="$(cd "${1:?usage: run.sh <folder with the release files> [<source checkout>]}" && pwd)"
SRC="${2:+$(cd "$2" && pwd)}"; W="$(mktemp -d)"; export SRC W; trap 'rm -rf "$W"' EXIT
export LC_ALL=C
# ev <name> <command>: runs the command in the release folder and writes "$ <command>", its output and its exit code
# to <name>.txt (a search that finds nothing ends with exit 1 and no lines).
# dis <file> <from> <to>: the instructions from address <from> to <to> (hex, without 0x), cut from the whole
# disassembly so the first one is a real instruction.
dis() {
  ev "$1.$2-$3" "objdump -d '$1' | awk -v a=$2 -v b=$3 '\$1 ~ /^[0-9a-f]+:\$/ { x = substr(\$1, 1, length(\$1) - 1); p = length(x) == length(a) && x >= a && x <= b } p'"
}
# money <files...>: shop, payment and donation words and web addresses in the files' text (M2, M3).
money() { ev strings-money "{ strings -n 6 $*; strings -el -n 6 $*; } | grep -nE 'https?://|www\\.|[Ss]hop|[Bb]uy |[Pp]rice|[Pp]remium|[Pp]atreon|[Pp]ay[Pp]al|[Kk]o-?fi|[Dd]onat'"; }
# pe <file>: the usual three for a program file: its headers, imports and exports (objdump -p, up to the long function
# and relocation tables), its sections (objdump -h), and its import address table (iat.py), which names the function behind
# each "call *...(%rip) # 0x..." line of objdump -d.
ev() {
  local n=$1; shift
  { printf '$ %s\n' "$*"; set +e; (cd "$R" && bash -c "$*" 2>&1); printf '(exit %s)\n' "$?"; set -e; } > "$OUT/$n.txt"
}
pe() {
  ev "$1.objdump-p" "objdump -p '$1' | awk '/^The Function Table|^PE File Base Relocations/{exit} 1'"
  ev "$1.objdump-h" "objdump -h '$1'"
  ev "$1.iat" "iat.py '$1'"
}
