"""Look up release files on VirusTotal by SHA-256. This script never uploads anything.

A hash lookup only reads results that already exist; a file VirusTotal has never seen comes
back as "not found". Uploading such a file is done by hand by the maintainer, and only for a
publicly released file of a tool whose licence allows analysis (CLAUDE.md, "VirusTotal").

The API key is read from the VT_API_KEY environment variable (a GitHub Actions secret, or
your shell). It is never written to the repository or to the output.

Usage:
  python3 -I tools/vt_lookup.py <sha256> [<sha256> ...]
  python3 -I tools/vt_lookup.py --card cards/<card>.yaml [cards/<card>.yaml ...]
  python3 -I tools/vt_lookup.py --all                  (every card in cards/)

Options for --card and --all:
  --json vt/results.json   merge the results into this file, one entry per card and hash
                           (--all also drops cards that no longer exist)
  --markdown <file>        also write the results as a Markdown table (for a PR comment)

A card's hashes are the sha256 values of its files list.
Prints one line per hash: detections / engines, scan date, and the names of the engines
that flagged it, plus the permalink to quote as evidence on the card. The public API
allows 4 requests a minute and 500 a day, so it waits 15 s between hashes, waits a minute
and retries when VirusTotal answers "too many requests", and stops after MAX_LOOKUPS.
Exits 1 if any lookup failed, after writing the outputs.
"""
import glob
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

API = 'https://www.virustotal.com/api/v3/files/'
GUI = 'https://www.virustotal.com/gui/file/'
WAIT = 15
MAX_LOOKUPS = 400
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def lookup(key, h):
    """One hash. Returns a result dict; 'error' is set when the lookup failed."""
    req = urllib.request.Request(API + h, headers={'x-apikey': key, 'accept': 'application/json'})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                data = json.load(r)['data']['attributes']
            break
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return {'found': False}
            if e.code == 429 and attempt < 3:
                time.sleep(60)
                continue
            return {'error': f'HTTP {e.code}'}
        except (urllib.error.URLError, TimeoutError) as e:
            return {'error': str(getattr(e, 'reason', e))}
    stats = data.get('last_analysis_stats', {})
    flagged = sorted(k for k, v in data.get('last_analysis_results', {}).items()
                     if v.get('category') in ('malicious', 'suspicious'))
    return {
        'found': True,
        'flagged': stats.get('malicious', 0) + stats.get('suspicious', 0),
        'engines': sum(stats.get(k, 0) for k in ('malicious', 'suspicious', 'undetected', 'harmless')),
        'flagged_by': flagged,
        'last_scanned': time.strftime('%Y-%m-%d', time.gmtime(data.get('last_analysis_date', 0))),
    }


def describe(r):
    if 'error' in r:
        return f'lookup failed ({r["error"]})'
    if not r['found']:
        return 'not found on VirusTotal'
    names = (': ' + ', '.join(r['flagged_by'])) if r['flagged_by'] else ''
    return f'{r["flagged"]} of {r["engines"]} engines flagged it, last scanned {r["last_scanned"]}{names}'


def card_hashes(path):
    with open(path, encoding='utf-8') as f:
        text = f.read()
    return list(dict.fromkeys(x.lower() for x in re.findall(r'^\s*sha256: ([0-9a-fA-F]{64})$', text, re.M)))


def run_url():
    run = os.environ.get('GITHUB_RUN_ID')
    if not run:
        return None
    return f'{os.environ.get("GITHUB_SERVER_URL", "https://github.com")}/{os.environ.get("GITHUB_REPOSITORY")}/actions/runs/{run}'


def lookup_all(key, hashes):
    """Looks up each distinct hash once, throttled. Returns {hash: result}."""
    results = {}
    for i, h in enumerate(dict.fromkeys(hashes)):
        if i >= MAX_LOOKUPS:
            results[h] = {'error': f'skipped, over {MAX_LOOKUPS} lookups in one run'}
            continue
        if i:
            time.sleep(WAIT)
        results[h] = lookup(key, h)
    return results


def write_json(path, cards, results, today, url, prune):
    try:
        with open(path, encoding='utf-8') as f:
            old = json.load(f).get('cards', {})
    except FileNotFoundError:
        old = {}
    new = {} if prune else dict(old)
    for name, hashes in cards.items():
        entry = {}
        for h in hashes:
            r = results[h]
            prev = old.get(name, {}).get(h)
            if 'error' in r and prev:
                entry[h] = prev  # keep the last good result rather than an error
                continue
            entry[h] = dict(r, looked_up=today, run=url, permalink=GUI + h)
        new[name] = entry
    out = {
        'about': 'VirusTotal hash lookups (no uploads) for the files listed in each card, '
                 'written by tools/vt_lookup.py. How a card quotes them (P1) is in rules/questions.md.',
        'cards': dict(sorted(new.items())),
    }
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, indent=2, sort_keys=False)
        f.write('\n')


def write_markdown(path, cards, results, today, url):
    lines = ['<!-- vt-lookup -->', '### VirusTotal hash lookup', '',
             f'Looked up on {today}' + (f' in [this run]({url})' if url else '') +
             '. Hash lookups only; nothing was uploaded.', '',
             '| Card | File hash | Result | Permalink |', '|---|---|---|---|']
    for name, hashes in cards.items():
        if not hashes:
            lines.append(f'| `{name}` | (no SHA-256 in the header) | | |')
        for h in hashes:
            lines.append(f'| `{name}` | `{h}` | {describe(results[h])} | [VirusTotal]({GUI + h}) |')
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(lines) + '\n')


def take(argv, flag):
    """Removes '--flag value' from argv and returns the value (or None)."""
    if flag in argv:
        i = argv.index(flag)
        value = argv[i + 1]
        del argv[i:i + 2]
        return value
    return None


def main(argv):
    key = os.environ.get('VT_API_KEY')
    if not key:
        print('Set VT_API_KEY first.', file=sys.stderr)
        return 2
    argv = list(argv)
    json_path = take(argv, '--json')
    md_path = take(argv, '--markdown')
    prune = False
    if argv[:1] == ['--all']:
        paths = sorted(glob.glob(os.path.join(ROOT, 'cards', '*.yaml')))
        prune = True
    elif argv[:1] == ['--card']:
        paths = argv[1:]
    else:
        results = lookup_all(key, [x.lower() for x in argv])
        for h, r in results.items():
            print(f'{h}  {describe(r)}' + ('' if 'error' in r else f'  {GUI + h}'))
        return 1 if any('error' in r for r in results.values()) else 0

    cards = {os.path.basename(p): card_hashes(p) for p in paths}
    results = lookup_all(key, [h for hs in cards.values() for h in hs])
    today = time.strftime('%Y-%m-%d', time.gmtime())
    url = run_url()
    for name, hashes in cards.items():
        print(name if hashes else f'{name}  (no SHA-256 in the header)')
        for h in hashes:
            r = results[h]
            print(f'  {h}  {describe(r)}' + ('' if 'error' in r else f'  {GUI + h}'))
    if json_path:
        write_json(json_path, cards, results, today, url, prune)
    if md_path:
        write_markdown(md_path, cards, results, today, url)
    return 1 if any('error' in r for r in results.values()) else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
