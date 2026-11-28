"""Each tool's thread in the repository's Discussions ("Tools" category), found by its title, with how many comments and replies
it has, for the tool's page and its card in the tools list. Nobody records a thread by hand: "Start a discussion" fills in the
tool's name as the title, and the oldest thread with that title is the tool's.

GitHub lets only a signed-in request read discussions, so this runs where a token is set (GITHUB_TOKEN in the Pages workflow,
with `discussions: read`). Without one, or when GitHub doesn't answer, every tool has no thread and its page offers to start
one; the build goes on either way, because a missing count is never worth a missing site.
"""
import json, os, urllib.request

QUERY = '''query($o:String!,$n:String!,$after:String){repository(owner:$o,name:$n){
  discussions(first:100,after:$after,orderBy:{field:CREATED_AT,direction:ASC}){pageInfo{hasNextPage endCursor}
    nodes{title url category{slug} comments(first:100){totalCount nodes{replies{totalCount}}}}}}}'''


def _post(token, variables):
    req = urllib.request.Request('https://api.github.com/graphql', json.dumps({'query': QUERY, 'variables': variables}).encode(),
                                 {'Authorization': 'bearer ' + token, 'Content-Type': 'application/json', 'User-Agent': 'mxb-facts-build'})
    with urllib.request.urlopen(req, timeout=30) as r:
        out = json.load(r)
    if out.get('errors'): raise RuntimeError(out['errors'][0].get('message', 'GraphQL error'))
    return out['data']['repository']


def tool_threads(repo_url, names):
    """{tool name: {'url', 'comments'}} for the tools in `names` that have a thread; empty without a token."""
    token = os.environ.get('GITHUB_TOKEN')
    if not token: return {}
    owner, name = repo_url.rstrip('/').split('/')[-2:]
    want = {n.strip().lower(): n for n in names}
    found, after = {}, None
    try:
        while True:
            r = _post(token, {'o': owner, 'n': name, 'after': after})
            for d in r['discussions']['nodes']:
                t = want.get(d['title'].strip().lower())
                if t and d['category']['slug'] == 'tools' and t not in found:  # oldest first: a later duplicate is ignored
                    c = d['comments']
                    found[t] = {'url': d['url'], 'comments': c['totalCount'] + sum(x['replies']['totalCount'] for x in c['nodes'])}
            if not r['discussions']['pageInfo']['hasNextPage']: break
            after = r['discussions']['pageInfo']['endCursor']
    except Exception as e:  # noqa: BLE001 - a failed lookup leaves the threads out, never the site
        print(f'discussions: not read ({e}); tools show "Start a discussion"')
        return {}
    return found
