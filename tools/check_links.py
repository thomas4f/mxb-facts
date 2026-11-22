"""Check every pinned GitHub code link in the cards.

For each https://github.com/<owner>/<repo>/(blob|tree)/<ref>/<path>[#L<a>[-L<b>]] link it
fetches the repository once (a blobless partial clone under .cache/repos/), and checks
that <path> exists at <ref> and that the line range fits the file at that ref.

Why not a generic link checker (lychee, markdown-link-check): they only check that a
URL answers, not that line 120 exists in that file at that commit, and GitHub answers
200 for a blob URL with any line anchor.

Usage: python3 -I tools/check_links.py   (exit 1 on any bad link)
"""
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARDS = os.path.join(ROOT, 'cards')
CACHE = os.environ.get('LINK_CACHE', os.path.join(ROOT, '.cache', 'repos'))
LINK = re.compile(r'https://github\.com/([^/\s)]+/[^/\s)]+)/(blob|tree)/([0-9a-fA-F]{7,40}|v?[\w.\-]+)/([^)\s#]*)(?:#L(\d+)(?:-L(\d+))?)?')


def git(repo_dir, *args):
    return subprocess.run(['git', '-C', repo_dir, *args], capture_output=True, text=True)


def repo_dir(repo):
    d = os.path.join(CACHE, repo.replace('/', '__'))
    if not os.path.isdir(d):
        os.makedirs(CACHE, exist_ok=True)
        r = subprocess.run(['git', 'clone', '--quiet', '--filter=blob:none', '--no-checkout',
                            f'https://github.com/{repo}.git', d], capture_output=True, text=True)
        if r.returncode:
            return None
    return d


def main():
    bad = n = 0
    for f in sorted(os.listdir(CARDS) if os.path.isdir(CARDS) else []):
        if not f.endswith('.yaml'):
            continue
        text = open(os.path.join(CARDS, f), encoding='utf-8').read()
        for m in LINK.finditer(text):
            repo, kind, ref, path, a, b = m.groups()
            if not re.fullmatch(r'[0-9a-f]{40}', ref):
                print(f'{f}: {repo} links by "{ref}"; use the full commit hash, since a tag or branch can move')
                bad += 1
                continue
            path = path.rstrip('/')
            n += 1
            d = repo_dir(repo)
            if d is None:
                print(f'{f}: cannot clone {repo}')
                bad += 1
                continue
            if git(d, 'cat-file', '-e', f'{ref}^{{commit}}').returncode:
                git(d, 'fetch', '--quiet', '--filter=blob:none', 'origin', ref)
            spec = f'{ref}:{path}' if path else f'{ref}^{{tree}}'
            kind_r = git(d, 'cat-file', '-t', spec)
            if kind_r.returncode:
                print(f'{f}: MISSING {repo} {ref} {path}')
                bad += 1
                continue
            if a and kind_r.stdout.strip() == 'blob':
                lines = git(d, 'show', spec).stdout.count('\n') + 1
                if int(b or a) > lines:
                    print(f'{f}: RANGE {repo} {path} L{a}-L{b or a} > {lines} lines')
                    bad += 1
    print(f'{n} links, {bad} bad')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
