"""The game demos the real-game runs use (games.json), and which one a run takes.

usage:
  python3 -I lab/real-game/games.py pick <game> [<version>]
      Prints the demo as JSON (name, version, url, sha256, exe, steps): the version asked for, else the newest.
  python3 -I lab/real-game/games.py plan <plan.json> <tool> [<version>]
      Writes "game_version" into a Windows run plan: the version asked for, else the tool's pin in registry/tools.json
      ("game_version": {"<game>": {"version": ..., "why": ...}}, for a tool that needs an older demo), else the newest.
      Prints the choice.

games.json lists each game's demos newest first, as {"version", "name", "url", "sha256"}, with the exe and the menu
steps at the game's level; a demo whose buttons moved has "steps" of its own.
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
GAMES = json.load(open(os.path.join(HERE, 'games.json')))


def versions(game):
    assert game in GAMES, 'games.json has no game %r (%s)' % (game, ', '.join(GAMES))
    return [v['version'] for v in GAMES[game]['versions']]


def pick(game, version=None):
    # The demo of one game, with its exe and steps: the version named, else the newest (the first listed).
    vs = versions(game)
    assert not version or version in vs, '%s has no demo %r in games.json (%s)' % (game, version, ', '.join(vs))
    g = GAMES[game]; v = g['versions'][vs.index(version) if version else 0]
    return {'game': game, 'exe': g['exe'], 'steps': g['steps'], **v}


def by_sha(sha):
    # The demo an installer SHA-256 belongs to, or None.
    return next((pick(k, v['version']) for k, g in GAMES.items() for v in g['versions'] if v['sha256'] == sha), None)


def choose(game, tool, version=None):
    # A run's demo and why: the version asked for, else the tool's pin, else the newest.
    if version: return pick(game, version)['version'], 'asked for'
    pin = json.load(open(os.path.join(ROOT, 'registry', 'tools.json'))).get(tool, {}).get('game_version', {}).get(game)
    if pin: return pick(game, pin['version'])['version'], 'pinned in registry/tools.json: ' + pin['why']
    return versions(game)[0], 'the newest'


def main(a):
    if a[:1] == ['pick'] and len(a) in (2, 3):
        print(json.dumps(pick(a[1], a[2] if len(a) > 2 else None), indent=1))
    elif a[:1] == ['plan'] and len(a) in (3, 4):
        plan = json.load(open(a[1])); game = plan.get('game', 'mxbikes')
        v, why = choose(game, a[2], a[3] if len(a) > 3 else None)
        plan['game_version'] = v
        json.dump(plan, open(a[1], 'w'), indent=1)
        print('Demo: %s (%s).' % (pick(game, v)['name'], why))
    else:
        print(__doc__.strip()); return 2
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main(sys.argv[1:]))
    except AssertionError as e:
        print('games.py: %s' % e, file=sys.stderr); sys.exit(1)
