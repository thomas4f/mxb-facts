"""Build the site: check every card and write _site/ (the data feed, the pages made from it, badges, api/cards.json, the card
files and the authors' check).

Usage: python3 -I site/build.py
The rules live in rules.py, card checks in cards.py, the feed in feed.py, the pages in render.py and templates/, the badges in
badges.py. This file lists the cards, runs the checks that need all of them (registry, links between cards), writes the site and,
unless SET_OUT is set, prints what the change does to each card compared with CHANGES_BASE (default HEAD).
"""
import datetime, glob, json, os, re, shutil, subprocess, sys, yaml
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))  # rules.py, cards.py, feed.py, render.py and badges.py sit beside this file
from rules import AREAN, CATS, CONCERN, D, RUBRICV, OUT, ROOT, SC, charges, scored, gtext, load_yaml, sround, stale_refs, tagsof, verdict
from cards import check_card, games, glance, JUDGE, MM, pending_versions, REG, SITES, SLUG, strings, VT
from cards import COMMIT, GAMESPY
from badges import BADGES, PENDING, badge_json, btitle, ptitle
from feed import SITEURL
CARDS=[  # (card file, tool in registry/tools.json), alphabetical
    ('dirt-gear-1.1.1.yaml', 'dirt-gear'),
    ('dirt-gear-1.2.0.yaml', 'dirt-gear'),
    ('dirt-gear-1.2.1.yaml', 'dirt-gear'),
    ('fixxers-rumble-1.0.yaml', 'fixxers-rumble'),
    ('heightmap-studio-26.11.7.yaml', 'heightmap-studio'),
    ('holeshot-0.24.0.yaml', 'holeshot'),
    ('holeshot-0.24.2.yaml', 'holeshot'),
    ('knee-down-0.1.8.yaml', 'knee-down'),
    ('maxhud-2.2.7.yaml', 'maxhud'),
    ('mx-dirt-mod-1.7.1.yaml', 'mx-dirt-mod'),
    ('mx-dirt-mod-alt-1.7.1-alt.1.yaml', 'mx-dirt-mod-alt'),
    ('mxb-damage-1.3.0.yaml', 'mxb-damage'),
    ('mxb-discord-rpc-2024-10-06.yaml', 'mxb-discord-rpc'),
    ('mxb-dualsense-1.1.0.yaml', 'mxb-dualsense'),
    ('mxb-fps-booster-v1.yaml', 'mxb-fps-booster'),
    ('mxb-ragdoll-1.0.yaml', 'mxb-ragdoll'),
    ('mxb-studio-1.0.1.yaml', 'mxb-studio'),
    ('mxbfix-0.1.8.yaml', 'mxbfix'),
    ('mxbmrp3-1.36.0.yaml', 'mxbmrp3'),
    ('mxrp-ragdoll-3.2.yaml', 'mxrp-ragdoll'),
    ('pitbox-3.0.4.yaml', 'pitbox'),
    ('projectgpb2-v2.yaml', 'projectgpb2'),
    ('setup-duper-0.1.8674.29660.yaml', 'setup-duper'),
    ('suspension-tuner-1.4.1.yaml', 'suspension-tuner'),
    ('trackrelief-1.2.2.yaml', 'trackrelief'),
]
# The dropdowns of the hand-started workflows (GitHub can only offer a fixed list), written like the rules tables. Both offer
# the tools in registry/tools.json, never the cards: a new card then never changes a workflow file, which the "Analyse a
# tool" run couldn't push.
_TOOLS=sorted(json.load(open(ROOT+'registry/tools.json')))
for _wf,_key,_opts in (('virustotal.yml','tools',['all']+_TOOLS),('analyse.yml','tools',_TOOLS)):
    _p=ROOT+'.github/workflows/'+_wf; _old=open(_p).read()
    assert f'# {_key}:start' in _old and f'# {_key}:end' in _old, '.github/workflows/'+_wf+f': the dropdown lost its "# {_key}:start" and "# {_key}:end" lines'
    _new=re.sub(rf'(          # {_key}:start\n).*?(          # {_key}:end\n)',lambda m:m.group(1)+''.join(f'          - {o}\n' for o in _opts)+m.group(2),_old,flags=re.S)  # noqa: B023 (used at once, inside this loop)
    if _new!=_old:
        assert not os.environ.get('CI'), '.github/workflows/'+_wf+': its dropdown differs from registry/tools.json; run python3 -I site/build.py and commit the result'
        open(_p,'w').write(_new); print('wrote the dropdown in .github/workflows/'+_wf)
# Docs, the prompt, the forms, the site's own text and every card except its history name only questions that exist.
for _f in sorted(set(glob.glob(ROOT+'*.md')+glob.glob(ROOT+'docs/*.md')+glob.glob(ROOT+'prompts/*.md')+glob.glob(ROOT+'rules/*.md')+glob.glob(ROOT+'authors/*/*.md')+glob.glob(ROOT+'.github/ISSUE_TEMPLATE/*.yml')+glob.glob(ROOT+'site/templates/*.html')+[ROOT+'site/content.yaml'])):
    _bad=stale_refs(open(_f).read()); assert not _bad, _f[len(ROOT):]+': names questions that rules/scoring.yaml no longer has: '+', '.join(_bad)
for _c,_a in CARDS:
    _y=load_yaml(D+_c); _y.pop('history',None)
    _bad=stale_refs(yaml.safe_dump(_y,allow_unicode=True,width=10**6)); assert not _bad, 'cards/'+_c+': names questions that rules/scoring.yaml no longer has: '+', '.join(_bad)
assert len(SLUG)==sum(len(e['cards']) for e in REG.values()), 'registry/tools.json: a card is listed under two tools'
assert set(SLUG)=={f for f,_ in CARDS}, 'registry/tools.json: cards must match CARDS ('+', '.join(sorted(set(SLUG)^{f for f,_ in CARDS}))+')'
assert all(SLUG[f]==t for f,t in CARDS), 'CARDS: each card names its tool in registry/tools.json'
# The maintainer's own tools (README, "Conflict of interest"): each of their cards shows the notice, and no other card does, so it
# can't be left off.
MAINTAINER_TOOLS={'mxbmrp3'}
for f,t in CARDS: assert bool(load_yaml(D+f).get('by_maintainer'))==(t in MAINTAINER_TOOLS), 'cards/'+f+': by_maintainer: true goes on the cards of '+', '.join(sorted(MAINTAINER_TOOLS))+' and nowhere else'
for s,e in REG.items():
    assert all(c.startswith(s+'-') for c in e['cards']), 'registry/tools.json: '+s+' lists a card of another tool'
    if e['github']: assert all('github.com/'+e['github']+')' in yaml.safe_load(open(D+c))['header']['GitHub'] for c in e['cards']), 'registry/tools.json: '+s+' GitHub differs from its card'
    # A pinned demo (lab/real-game/README.md, "Which demo"): one games.json lists, with what the tool shows that needs it.
    for g,pin in e.get('game_version',{}).items():
        assert g in GAMESPY.GAMES and set(pin)=={'version','why'} and pin['why'] and pin['version'] in GAMESPY.versions(g), 'registry/tools.json: '+s+' game_version names a game of lab/real-game/games.json and, for it, {"version": <one it lists>, "why": <what the tool shows>}'
    # Each game a tool's cards name brings its mods site's entry ("mxb-mods" for MX Bikes, "gpb-mods" for GP Bikes), and no other.
    ks=[k for k,_ in SITES.values() if k in e]
    want={SITES[g][0] for c in e['cards'] for g in games(yaml.safe_load(open(D+c))['header'])}
    assert set(ks)==want if e['cards'] else ks, 'registry/tools.json: '+s+' needs '+(', '.join(sorted(want)) or 'one of '+', '.join(k for k,_ in SITES.values()))+(', for the games its cards name,' if want else '')+' and has '+(', '.join(ks) or 'none')
    for k in ks:
        m=e[k]; pid=m['post']
        assert pid or m.get('note'), 'registry/tools.json: '+s+' needs a '+k+' post or a note why not'
        if pid:
            assert bool(m.get('tied_by'))!=bool(m.get('confirmed')), 'registry/tools.json: '+s+' must say what ties post '+str(pid)+' to the tool ("tied_by"), or who confirmed it ("confirmed")'
            assert s in MM[k]['tools'] and MM[k]['tools'][s]['post']==pid, 'registry/'+k+'.json: '+s+' not fetched, run tools/mxbmods_fetch.py'
            assert MM[k]['tools'][s]['still_tied'] or m.get('confirmed'), 'registry/'+k+'.json: post '+str(pid)+' no longer holds "'+m['tied_by']+'"; check it and update registry/tools.json'
for k,_ in SITES.values():
    assert set(MM[k]['tools'])<={s for s,e in REG.items() if k in e and e[k]['post']}, 'registry/'+k+'.json: tools not in the registry, run tools/mxbmods_fetch.py'
GR={}
# What the rules set on each card (the score, each area's score or Money label, what each answer costs, key marks, tags), to compare one scoring.yaml with another.
SET={}
for f,slug in CARDS:
    # A tool's newest card (the last in its registry list) is the tool's page, <site>/<tool>/, in the tools list. An earlier card
    # (rule 2: it stays) keeps a page of its own, <site>/<tool>/<version>/, which the newer cards link under "Earlier reports" and
    # every card of the tool lists under History, and its badges; Compare offers it beside the newest.
    older=REG[slug]['cards']; latest=older[-1]==f; older=older[:older.index(f)]
    a=slug if latest else f[:-len('.yaml')]
    CARD=load_yaml(D+f); C=check_card(f,CARD)
    name,ver,h,rows,V,HELDQ=C['name'],C['ver'],C['h'],C['rows'],C['A'],C['held']
    for label in ('In one line','Category','Author','Game',*(SITES[g][1] for g in games(h)),'Homepage','GitHub','Version analysed'): assert h.get(label), f+': no "'+label+'" row'
    one=h['In one line']; assert len(one)<=90, f+': "In one line" is longer than 90 characters'
    _miss=[o for o in older if '('+SITEURL+slug+'/'+load_yaml(D+o)['version']+'/)' not in h.get('Earlier reports','')]
    assert not _miss, f+': "Earlier reports" must link each earlier card of the tool, newest first, as [<version>]('+SITEURL+'<tool>/<version>/): '+', '.join(_miss)
    text='\n'.join(strings(C['d']))
    assert 'mxb-facts/actions/runs/' not in text, f+': link each file\'s VirusTotal entry, not our lookup run (readers can\'t open it)'
    cat=h['Category']; assert cat in CATS, f+': category must be one of '+'; '.join(CATS)
    hb=h.get('Held back')
    # Rule 6: "Not allowed" answers, and so "Not scored", need the licence clause that forbids the analysis, quoted on the card.
    assert any(v=='NA' for _m,v in V.values())==bool(h.get('Licence clause')), f+': a card with "Not allowed" answers needs the "Licence clause" row, and only such a card has it'
    G=scored(V,HELDQ)
    gl=glance(V,G,HELDQ)
    # The P5 mark depends on whether the release can be traced to public source (T3 or T4).
    traced=any(rows[q].startswith('{+} Yes') for q in ('T3','T4'))
    if rows['P5'].startswith(('{!} No','{~} No')): assert rows['P5'].startswith('{~}' if traced else '{!}'), f+': P5 No is a Note only when T3 or T4 is Yes'
    # Rule 8: every card names the model and effort in the Method row.
    assert re.search(r'claude-[a-z0-9-]+',CARD['header']['Method']) and re.search(r'\b(low|medium|high|xhigh|max) effort\b',CARD['header']['Method']), f+': the Method row must name the model ID (claude-…) and the effort ("… effort")'
    # Rule 7: no words that judge, outside quotes, code and links.
    plain=re.sub(r'"[^"\n]*"|“[^”]*”|`[^`]*`|\]\([^)]*\)|https?://\S+|safe mode','',text)
    jw=re.search(JUDGE,plain,re.I)
    assert not jw, f+': "'+jw.group(0)+'" judges; say what the tool does instead (CLAUDE.md, rule 7), or quote the words it uses'
    vt=VT.get(f)
    if vt:
        # P1 follows the latest VirusTotal lookup (vt/results.json): if a new lookup crosses a threshold, the build stops until the card is updated.
        found=[r for r in vt.values() if r.get('found')]
        worst=max((r['flagged']/r['engines'] for r in found if r['engines']),default=None)
        v=verdict(rows['P1'])[1]
        failed=[h for h,r in vt.items() if r.get('error')]
        # While a lookup failed (rate limit), P1 may stay "Not checked"; any other answer must still match the files that were found.
        ok=v==('No' if not worst else 'Yes' if worst>=SC['virustotal']['flagged_share'] else 'Partly') or (v=='NC' and bool(failed))
        assert ok, f+': P1 is "'+v+'", but the latest VirusTotal lookup (vt/results.json) puts it '+('nowhere on VirusTotal' if worst is None else f'at {worst:.1%} of engines at most')+'; update P1 and its history row'
    if rows['P1'].startswith('{+} No'):
        assert vt and all(vt.get(x['sha256'],{}).get('found') for x in CARD['files'] if 'inside' not in x), f+': P1 No is a Note while a file players download isn\'t on VirusTotal'
    ka=C['key']
    _crit,_opt,_pos=tagsof(CARD)
    GR[a]=(name,ver,G,h.get('Analysed on') or '',slug,latest)
    MW={'+':'Good','~':'Note','!':'Concern',None:''}
    SET[f]={'score':{'score':gtext(G)},'areas':{ar:f'{x}' for ar,x in gl.items()},
            'answers':{q:f'costs {x[0]}'+(' (open)' if x[2] else '')+(f', counted with {x[1]}' if x[1] else '') for q,x in charges(V,HELDQ).items()},
            'keys':{k:MW[x[0]] or 'no mark' for k,x in ka.items()},
            'tags':sorted(l for l,_q in _crit)+sorted(l+' (off by default)' for l,_q in _opt)+sorted(l for l,_q in _pos)}
# For authors: made from the rules, so it can't drift from them. The drop-in check is authors/mxb-facts-check/SKILL.md, pinned to this commit.
SKILLP='authors/mxb-facts-check/SKILL.md'
skill=open(ROOT+SKILLP).read()
assert skill.startswith('---\nname: mxb-facts-check\n') and '{{COMMIT}}' in skill, SKILLP+': the skill starts with its frontmatter and points at {{COMMIT}}'
skill=skill.replace('{{COMMIT}}',COMMIT)
AGENTSLINE='Before tagging a release, run the MXB Facts check in .claude/skills/mxb-facts-check/SKILL.md.'
# The files the page offers to download sit next to it: each card as it is in cards/ (rule 9: a card holds no held-back details,
# only its "Held back" row), and the For authors check with its commit filled in.
SITE=os.path.dirname(OUT)+'/'
if os.path.isdir(SITE): shutil.rmtree(SITE)
os.makedirs(SITE,exist_ok=True)
# One badge per card (rules/scores.md, "Badge"), at badge/<tool>/<version>.svg and .json.
for _a,(_name,_ver,_G,_date,_t,_l) in GR.items():
    os.makedirs(SITE+'badge/'+_t,exist_ok=True)
    for _suf,_lab,_draw in BADGES: open(SITE+f'badge/{_t}/{_ver}{_suf}.svg','w').write(_draw(_G,btitle(_name,_ver,_G,_date),'')+'\n')
    open(SITE+f'badge/{_t}/{_ver}.json','w').write(badge_json(_ver,_G)+'\n')
# A release the weekly inventory has seen (registry/releases.json) that has no card yet gets the same badges, saying "Not analysed
# yet", so an author who moves a badge to the new version before its card is published shows that, not a broken image. Under the
# version as published (v1.2.0) and without its leading v (1.2.0), the two ways a badge address is written.
# Only a release dated after the tool's newest card (cards.pending_versions).
_seen={}
for _a,(_name,_ver,_G,_date,_t,_l) in GR.items():
    _s=_seen.setdefault(_t,{'name':_name,'cards':set(),'newest':''}); _s['cards'].add(_ver)
    _s['newest']=max(_s['newest'],datetime.datetime.strptime(_date,'%d %b %Y').date().isoformat())
_rel=json.load(open(ROOT+'registry/releases.json'))['tools']
for _t,_s in _seen.items():
    for _pv in pending_versions(_s['cards'],_s['newest'],_rel.get(_t,{})):
        for _suf,_lab,_draw in BADGES: open(SITE+f'badge/{_t}/{_pv}{_suf}.svg','w').write(_draw(PENDING,ptitle(_s['name'],_pv),'')+'\n')
        open(SITE+f'badge/{_t}/{_pv}.json','w').write(badge_json(_pv,PENDING)+'\n')
# Every card's score and badges in one file, for a site that lists tools (such as a mods site) to show them by version.
os.makedirs(SITE+'api',exist_ok=True)
json.dump({'rubric':RUBRICV,'cards':[{'tool':_t,'name':_n,'version':_v,'page':f'{SITEURL}{_t}/' if _l else f'{SITEURL}#{_a}','score':gtext(_G),
           'number':None if _G['kind'] in ('notscored','malware') else sround(_G['score']),'open_answers':len(_G['open']),
           'areas':None if _G['kind'] in ('notscored','malware') else {ar:_G['areas'][ar][0] for ar in AREAN if ar in CONCERN},
           'analysed':_d,'badges':{(_suf or '-flat').lstrip('-'):f'{SITEURL}badge/{_t}/{_v}{_suf}.svg' for _suf,_x,_y in BADGES},
           'card_image':f'{SITEURL}badge/{_t}/{_v}-card.png'}
          for _a,(_n,_v,_G,_d,_t,_l) in GR.items()]},open(SITE+'api/cards.json','w'),indent=1,ensure_ascii=False)
# The versioned data feed, api/v1/ (site/feed.py, docs/FEED.md), checked against rules/feed.schema.json.
from feed import write_feed, write_site
write_feed(SITE,CARDS); write_site(SITE,skill,AGENTSLINE)
# The pages, from the feed alone (site/render.py, site/templates/).
from render import write_pages
write_pages(SITE)
os.makedirs(SITE+'cards',exist_ok=True)
for f,_a in CARDS: shutil.copyfile(D+f,SITE+'cards/'+f)
os.makedirs(os.path.dirname(SITE+SKILLP),exist_ok=True)
open(SITE+SKILLP,'w').write(skill)
print(f'wrote {os.path.relpath(SITE,ROOT)}/: {sum(len(fs) for _d,_s,fs in os.walk(SITE))} files')
# What a change does to the cards: the build at the base commit (CHANGES_BASE, default HEAD; CI on a pull request uses its base branch)
# runs in a temporary worktree and reports the same results; every difference is printed. It only reports; nothing is refused for it.
if os.environ.get('SET_OUT'): json.dump(SET,open(os.environ['SET_OUT'],'w'))
else:
    import tempfile
    _base=os.environ.get('CHANGES_BASE','HEAD'); _out=[]
    _diff=subprocess.run(['git','-C',ROOT,'diff','--quiet',_base,'--','rules','cards','site','vt'],capture_output=True,text=True)
    if _diff.returncode>1: _out.append(f'Can\'t compare the cards with {_base}: '+(_diff.stderr.strip().splitlines() or ['?'])[-1])
    elif _diff.returncode==1:
        with tempfile.TemporaryDirectory() as _tmp:
            _wt=_tmp+'/base'
            _add=subprocess.run(['git','-C',ROOT,'worktree','add','--detach','-q',_wt,_base],capture_output=True,text=True)
            try:
                if _add.returncode: _out.append(f'Can\'t check out {_base} to compare the cards: '+(_add.stderr.strip().splitlines() or ['?'])[-1])
                else:
                    _run=subprocess.run([sys.executable,'-I',_wt+'/site/build.py'],cwd=_wt,capture_output=True,text=True,
                                        env={**os.environ,'SET_OUT':_tmp+'/set.json','OUT':_tmp+'/site/index.html','CI':''})
                    if _run.returncode or not os.path.exists(_tmp+'/set.json'):
                        _out.append(f'The build at {_base} '+('fails' if _run.returncode else 'doesn\'t report card results yet')+', so there is nothing to compare the cards with.')
                    else:
                        _old=json.load(open(_tmp+'/set.json')); _cnt=0
                        _out.append(f'What this changes on the cards, compared with {_base}:')
                        for f in sorted(set(_old)|set(SET)):
                            if f not in SET or f not in _old: _out.append(f'  {f}: card '+('added' if f in SET else 'removed')); continue
                            for part in ('score','areas','answers','keys'):
                                for x in sorted(set(_old[f].get(part,{}))|set(SET[f][part]),key=str):
                                    o,n=_old[f].get(part,{}).get(x,'-'),SET[f][part].get(x,'-')
                                    if o!=n: _out.append(f'  {f}: {x}: {o} -> {n}'); _cnt+=1
                            for l in sorted(set(_old[f]['tags'])-set(SET[f]['tags'])): _out.append(f'  {f}: tag removed: {l}'); _cnt+=1
                            for l in sorted(set(SET[f]['tags'])-set(_old[f]['tags'])): _out.append(f'  {f}: tag added: {l}'); _cnt+=1
                        if not _cnt: _out.append('  nothing: every score, Money label, mark and tag stays the same')
            finally: subprocess.run(['git','-C',ROOT,'worktree','remove','--force',_wt],capture_output=True)
    for _l in _out: print(_l)
    if _out and os.environ.get('GITHUB_STEP_SUMMARY'): open(os.environ['GITHUB_STEP_SUMMARY'],'a').write('\n'.join(['### Card changes','','```']+_out+['```',''])+'\n')
