#!/usr/bin/env python3
"""Check that every open correction issue is on its card, and every open correction on a card is an open issue.

Usage: python3 -I tools/check_corrections.py   (exit 1 on any mismatch)

Reads the open issues labelled "correction" through the GitHub API (GH_TOKEN or GITHUB_TOKEN, and
GITHUB_REPOSITORY), finds each one's tool by its "tool:<slug>" label (tools/issue_label.py sets it)
and looks for it in the "corrections" list of that tool's cards. Without a token it says so and stops,
so a local run doesn't fail. The issue text is never read here: only numbers and labels.
"""
import json
import os
import sys
import urllib.request

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def open_issues(repo, token):
    """Numbers and tool slugs of the open issues labelled "correction"."""
    out, page = {}, 1
    while True:
        req = urllib.request.Request(f'https://api.github.com/repos/{repo}/issues?state=open&labels=correction&per_page=100&page={page}',
                                     headers={'Authorization': 'Bearer ' + token, 'Accept': 'application/vnd.github+json'})
        batch = json.load(urllib.request.urlopen(req, timeout=30))
        for i in batch:
            if 'pull_request' in i:
                continue
            slugs = [l['name'][5:] for l in i.get('labels', []) if l['name'].startswith('tool:')]
            out[i['number']] = slugs[0] if len(slugs) == 1 else None
        if len(batch) < 100:
            return out
        page += 1


def check(issues, reg, cards):
    """issues: {number: slug or None}; reg: registry/tools.json; cards: {card file: card data}. Returns (errors, warnings)."""
    errors, warnings = [], []
    listed = {}
    for slug, e in reg.items():
        for f in e['cards']:
            for c in cards[f].get('corrections', []):
                if c['status'] == 'open':
                    listed[c['issue']] = (slug, f)
    for n, slug in sorted(issues.items()):
        if slug is None:
            warnings.append(f'correction #{n} has no single "tool:<slug>" label, so it can\'t be matched to a card; label it')
        elif slug not in reg or not reg[slug]['cards']:
            warnings.append(f'correction #{n} is about {slug}, which has no card')
        elif n not in listed:
            errors.append(f'correction #{n} is open, but no card of {slug} lists it under "corrections" with status open; add it to {reg[slug]["cards"][-1]}')
        elif listed[n][0] != slug:
            errors.append(f'correction #{n} is labelled tool:{slug}, but {listed[n][1]} lists it')
    for n, (slug, f) in sorted(listed.items()):
        if n not in issues:
            errors.append(f'{f} lists correction #{n} as open, but it isn\'t an open correction issue; set its status (fixed or declined), "closed" and "reason"')
    return errors, warnings


def main():
    token = os.environ.get('GH_TOKEN') or os.environ.get('GITHUB_TOKEN')
    if not token:
        print('No GH_TOKEN or GITHUB_TOKEN: corrections not compared with GitHub issues (CI does this).')
        return 0
    repo = os.environ.get('GITHUB_REPOSITORY', 'thomas4f/mxb-facts')
    reg = json.load(open(os.path.join(ROOT, 'registry', 'tools.json')))
    cards = {f: yaml.safe_load(open(os.path.join(ROOT, 'cards', f))) for e in reg.values() for f in e['cards']}
    errors, warnings = check(open_issues(repo, token), reg, cards)
    gh = os.environ.get('GITHUB_ACTIONS')
    for w in warnings:
        print(('::warning::' if gh else 'WARNING: ') + w)
    for e in errors:
        print(('::error::' if gh else 'ERROR: ') + e)
    print(f'{len(errors)} mismatches' if errors else 'every open correction is on its card')
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
