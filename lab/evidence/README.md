# Evidence from release files

The output of the commands a card names on its lines (`objdump`, `strings`, `file`, searches of the source), so each
line links what it rests on. One folder per card, named like the card file. Its `run.sh` lists every command; each
output file starts with the command, then its output and exit code (a search that finds nothing shows `(exit 1)`).

To repeat it, put the release's files in one folder, each by the name in the card's "Files checked" table (`run.sh`
says where they come from and how to unpack them), and run `lab/evidence/<card>/run.sh <that folder>`. `files.txt`
gives each file's SHA-256, to match with the card. The tools are GNU binutils (`objdump`, `strings`) and `file`.

Runs (what a plugin or app did when it ran, in the real game or the test host) are in `lab/results/`.
