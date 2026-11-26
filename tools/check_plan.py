"""Checks the plan for a Windows run (lab/plugin-test-host/windows/README.md) before the Windows job runs it.

usage: python3 -I tools/check_plan.py <plan.json>

The plan comes from Claude's first pass, which has read untrusted release files, so only what the Windows run needs is
let through: https release files with a SHA-256 each, plain names, host arguments without paths that leave the run
folder, apps inside the release, real-game runs with known key names in a demo games.json lists, and the licence read (allows, forbids or unclear),
which decides whether the run may upload release files to VirusTotal (only "allows") and run anything (not "forbids"). Prints the plan as Markdown (for the run's summary) and exits 1 when it isn't valid.
"""
import json, os, re, sys

NAME = re.compile(r'^[a-z0-9][a-z0-9-]{0,39}$')
SHA = re.compile(r'^[0-9a-f]{64}$')
# Text a run may pass: paths inside the run folder, and the words a --click looks for ("Tool: click to set up").
SAFE = re.compile(r'^[A-Za-z0-9 _.,:!+()\[\]\\/-]{1,200}$')
# A Windows switch an installer takes (/VERYSILENT, /S): a slash and a word, no value, so it can't name a path.
SWITCH = re.compile(r'^/[A-Za-z][A-Za-z0-9_-]{0,39}$')
# The keys lab/real-game/windows/run.ps1 can press (xdotool's names; its $scan table), alone (ctrl too) or joined with + (ctrl+r).
KEY = re.compile(r'^((ctrl|shift|alt)\+){0,2}(Up|Down|Left|Right|Escape|Return|space|Tab|BackSpace|Caps_Lock|Insert|Delete|Home|End|Prior|Next|F([1-9]|1[0-2])|[a-z0-9]|ctrl|shift|alt)$')
KEYS = {'game', 'game_version', 'licence', 'files', 'realgame', 'cases', 'apps', 'note'}
LICENCE = ('allows', 'forbids', 'unclear')
# The demos each game can run in (lab/real-game/games.json); the workflow writes the plan's game_version (games.py plan).
GAMES = json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'lab', 'real-game', 'games.json')))


def check(plan):
    assert set(plan) <= KEYS, 'unknown keys: %s' % sorted(set(plan) - KEYS)
    assert plan.get('game') in ('mxbikes', 'gpbikes'), 'game must be mxbikes or gpbikes'
    vs = [v['version'] for v in GAMES[plan['game']]['versions']]
    assert plan.get('game_version', vs[0]) in vs, 'game_version must be a demo of %s in lab/real-game/games.json: %s' % (plan['game'], ', '.join(vs))
    assert plan.get('licence') in LICENCE, 'licence must be allows, forbids or unclear'
    files, games, cases, apps = (plan.get(k, []) for k in ('files', 'realgame', 'cases', 'apps'))
    assert plan['licence'] != 'forbids' or not (games or cases or apps), 'nothing runs when the licence forbids analysis (rule 6)'
    assert len(files) <= 5 and len(games) <= 4 and len(cases) <= 6 and len(apps) <= 3, 'at most 5 files, 4 real-game runs, 6 cases and 3 apps'
    for f in files:
        assert set(f) == {'url', 'sha256'}, 'a file has url and sha256'
        assert re.match(r'^https://[^\s"\'`$]+$', f['url']) and len(f['url']) < 500, 'file url: ' + f['url']
        assert SHA.match(f['sha256']), 'sha256 of ' + f['url']
    names = ['baseline'] + [r.get('name') for r in games + cases + apps]
    twice = sorted({n for n in names if names.count(n) > 1}, key=str)
    assert not twice, 'run names must differ across real-game runs, cases and apps, and "baseline" is the bare demo\'s; used more than once: %s' % ', '.join(map(str, twice))
    for r in games:
        assert set(r) <= {'name', 'ride', 'keys'} and NAME.match(str(r.get('name'))), 'real-game run: name, ride, keys'
        ride = r.get('ride', 30)
        assert isinstance(ride, int) and 10 <= ride <= 300, 'real-game run %s: ride 10 to 300 seconds' % r['name']
        for k in r.get('keys', []):
            assert isinstance(k, list) and len(k) == 2 and isinstance(k[0], int) and 0 <= k[0] <= ride and isinstance(k[1], str) and KEY.match(k[1]), 'real-game run %s key: %r' % (r['name'], k)
    for c in cases:
        assert set(c) == {'name', 'args'} and NAME.match(c['name']), 'case: name and args'
        for a in c['args']:
            assert isinstance(a, str) and SAFE.match(a) and '..' not in a and not re.match(r'^([A-Za-z]:|[\\/])', a), 'case %s argument: %r' % (c['name'], a)
    for a in apps:
        assert set(a) <= {'name', 'exe', 'args', 'seconds'} and NAME.match(a['name']), 'app: name, exe, args, seconds'
        assert SAFE.match(a['exe']) and a['exe'].lower().endswith('.exe') and '..' not in a['exe'] and not re.match(r'^([A-Za-z]:|[\\/])', a['exe']), 'app exe: ' + a['exe']
        # Each release file sits in a folder of its own name, so even a bare .exe is "<file>\\<file>" (seen 24 Nov 2026).
        assert '\\' in a['exe'], 'app %s exe: %s is the release file\'s folder; name the file inside it, e.g. %s\\%s' % (a['name'], a['exe'], a['exe'], a['exe'].split('\\')[-1])
        for x in a.get('args', []):
            assert isinstance(x, str) and (SWITCH.match(x) or SAFE.match(x) and '..' not in x and not re.match(r'^([A-Za-z]:|[\\/])', x)), 'app %s argument: %r' % (a['name'], x)
        assert 10 <= int(a.get('seconds', 60)) <= 300, 'app seconds: 10 to 300'
    assert not (games or cases or apps) or files, 'runs need release files'


def main(path):
    plan = json.load(open(path))
    try:
        check(plan)
    except AssertionError as e:
        print('The plan for the Windows run is not valid: %s' % e)
        return 1
    out = ['### Windows run plan', '', 'Game: %s %s. Licence: %s.' % (plan['game'], plan.get('game_version', 'newest demo'), plan['licence']), '']
    out += ['- file: %s (`%s`)' % (f['url'], f['sha256']) for f in plan.get('files', [])]
    out += ['- real game `%s`: ride %ss%s' % (r['name'], r.get('ride', 30), ''.join(', %s at %ss' % (k[1], k[0]) for k in r.get('keys', []))) for r in plan.get('realgame', [])]
    out += ['- case `%s`: `%s`' % (c['name'], ' '.join(c['args'])) for c in plan.get('cases', [])]
    out += ['- app `%s`: `%s %s`, %ss' % (a['name'], a['exe'], ' '.join(a.get('args', [])), a.get('seconds', 60)) for a in plan.get('apps', [])]
    if not (plan.get('realgame') or plan.get('cases') or plan.get('apps')):
        out.append('Nothing to run' + (': ' + str(plan.get('note', ''))[:300] if plan.get('note') else '.'))
    print('\n'.join(out))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1]))
