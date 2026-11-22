#!/usr/bin/env python3
"""Open a re-check issue for each release newer than its tool's card, unless one is already open.

Usage: python3 -I tools/recheck_issues.py <newer.json>   (written by tools/releases_fetch.py with NEWER_OUT set)

Each issue is titled "Re-check: <tool name> <version>" and labelled "analyse" and "tool:<slug>", like a request from the
"Analyse a tool" form, so it joins the queue the same way (CLAUDE.md, "Requests and corrections"). An open issue with the
same title means it was opened before, so nothing is opened twice. Needs GH_TOKEN and GITHUB_REPOSITORY (the workflow sets
them). Release names and versions come from the places a tool publishes: they are passed to gh as arguments and a body
file, never through a shell.
"""
import json
import os
import subprocess
import sys
import tempfile


def gh(*args):
    return subprocess.run(['gh', *args, '--repo', os.environ['GITHUB_REPOSITORY']], capture_output=True, text=True, check=True).stdout


def main(path):
    newer = json.load(open(path))
    if not newer:
        print('No release is newer than its card.')
        return 0
    titles = {i['title'] for i in json.loads(gh('issue', 'list', '--state', 'open', '--label', 'analyse', '--limit', '500', '--json', 'title'))}
    for slug in sorted({n['tool'] for n in newer}):
        gh('label', 'create', 'tool:' + slug, '--color', 'ededed', '--description', 'Issues about this tool', '--force')
    gh('label', 'create', 'analyse', '--color', 'd4c5f9', '--force')
    for n in newer:
        title = f'Re-check: {n["name"]} {n["version"]}'.strip()
        if title in titles:
            print('already open: ' + title)
            continue
        body = (f'The weekly "Update inventory" run found a release of **{n["name"]}** that none of the files on its newest card '
                f'(`cards/{n["card"]}`, version {n["card_version"]}) match.\n\n'
                f'- Where: {n["place"]}\n- Version or file: {n["version"]}\n' + (f'- Date: {n["date"]}\n' if n['date'] else '')
                + (f'- Link: {n["url"]}\n' if n['url'] else '')
                + '\nA newer release gets a new card; the old one stays. Opened automatically; the release details above are what '
                  'the release page says, not a finding.\n')
        with tempfile.NamedTemporaryFile('w', suffix='.md', delete=False) as f:
            f.write(body)
        try:
            print(gh('issue', 'create', '--title', title, '--body-file', f.name, '--label', 'analyse', '--label', 'tool:' + n['tool']).strip())
        finally:
            os.unlink(f.name)
        titles.add(title)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1]))
