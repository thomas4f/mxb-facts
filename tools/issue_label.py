#!/usr/bin/env python3
"""Find which form an issue came from and which tool it is about, for its labels.

Reads the issue from the GitHub event file, takes the form's "Card" (correction)
or "Tool name" (request) field and matches it against registry/tools.json.
Prints "<kind> <slug>": kind is "correction", "analyse" or "-", slug is the tool's
slug or "-" when no tool matches. The issue text is only compared with the registry,
never run or passed on: both words come from fixed lists, so only a known label
ever reaches the shell.
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def field(body, label):
    m = re.search(r'^### ' + re.escape(label) + r'\s*\n+(.+?)(?:\n### |\Z)', body, re.M | re.S)
    return m.group(1).strip() if m else ''

def norm(s):
    return re.sub(r'[^a-z0-9]+', '', s.lower())

def find(body, reg):
    card, tool = field(body, 'Card'), field(body, 'Tool name')
    kind = 'correction' if card else 'analyse' if tool else '-'
    text = norm(card or tool)
    # A tool matches by its name anywhere in the text, or by its slug at the start ("mxb-damage 1.3.0" for "MXB Damage").
    # The longest match wins, so "MXB App" doesn't take an issue about a tool whose name contains it.
    best = max(((max(len(norm(t['name'])) if norm(t['name']) in text else 0, len(norm(slug)) if text.startswith(norm(slug)) else 0), slug)
                for slug, t in reg.items() if norm(t['name'])), default=(0, '-')) if text else (0, '-')
    return kind, best[1] if best[0] else '-'

def main():
    event = json.load(open(sys.argv[1] if len(sys.argv) > 1 else os.environ['GITHUB_EVENT_PATH']))
    body = (event.get('issue') or {}).get('body') or ''
    reg = json.load(open(os.path.join(ROOT, 'registry', 'tools.json')))
    print(*find(body, reg))

if __name__ == '__main__':
    main()
