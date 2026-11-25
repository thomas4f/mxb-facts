"""Build the site: check every card and write _site/ (the page, badges, api/cards.json, the card files and the
authors' check).

Usage: python3 -I site/build.py
The rules live in rules.py, card checks and Markdown in cards.py, HTML in page.py. This file lists the cards, runs the
checks that need all of them (registry, links between parts of the page), assembles the page and, unless SET_OUT is set,
prints what the change does to each card compared with CHANGES_BASE (default HEAD).
"""
import datetime, glob, json, os, re, shutil, subprocess, sys, yaml
from urllib.parse import quote
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))  # rules.py, cards.py and page.py sit beside this file
from rules import (
    AREAK, AREAN, CATS, CONCERN, D, GCOST, RUBRICV, GSC, GT, STATES, OUT, QS, ROOT, SC, TAGICON, charges, concern_span, goodwhen,
    scored, gtext, load_yaml, sround, stale_refs, state_html, tagcls, tagsof, verdict)
from icons import LICENCE as ICON_LICENCE, LUCIDE, STROKE, logo, mask_url
from cards import CORRFORM, JUDGE, MM, REG, REPO, SITES, SLUG, VT, check_card, esc, glance, strings
from page import (
    BADGES, COMMIT, GNOTE, MW, SITEURL, TAGCAP, badge_json, btitle, byline, history, score_html, score_section, inline,
    money_html, prm, share_page, tagrow, tool, tpl)
CARDS=[  # (card file, tool in registry/tools.json), alphabetical
    ('dirt-gear-1.1.1.yaml', 'dirt-gear'),
    ('dirt-gear-1.2.0.yaml', 'dirt-gear'),
    ('dirt-gear-1.2.1.yaml', 'dirt-gear'),
    ('fixxers-rumble-1.0.yaml', 'fixxers-rumble'),
    ('heightmap-studio-26.11.7.yaml', 'heightmap-studio'),
    ('holeshot-0.24.0.yaml', 'holeshot'),
    ('holeshot-0.24.2.yaml', 'holeshot'),
    ('maxhud-2.2.7.yaml', 'maxhud'),
    ('mx-dirt-mod-1.7.1.yaml', 'mx-dirt-mod'),
    ('mx-dirt-mod-alt-1.7.1-alt.1.yaml', 'mx-dirt-mod-alt'),
    ('mxb-damage-1.3.0.yaml', 'mxb-damage'),
    ('mxb-discord-rpc-2024-10-06.yaml', 'mxb-discord-rpc'),
    ('mxb-dualsense-1.1.0.yaml', 'mxb-dualsense'),
    ('mxb-fps-booster-v1.yaml', 'mxb-fps-booster'),
    ('mxb-ragdoll-1.0.yaml', 'mxb-ragdoll'),
    ('mxbfix-0.1.8.yaml', 'mxbfix'),
    ('pitbox-3.0.4.yaml', 'pitbox'),
    ('projectgpb2-v2.yaml', 'projectgpb2'),
    ('setup-duper-0.1.8674.29660.yaml', 'setup-duper'),
    ('suspension-tuner-1.4.1.yaml', 'suspension-tuner'),
]
# The dropdowns of the hand-started workflows (GitHub can only offer a fixed list), written like the rules tables. Both offer
# the tools in registry/tools.json, never the cards: a new card then never changes a workflow file, which the "Analyse a
# tool" run couldn't push.
_TOOLS=sorted(json.load(open(ROOT+'registry/tools.json')))
for _wf,_key,_opts in (('virustotal.yml','tools',['all']+_TOOLS),('analyse.yml','tools',_TOOLS)):
    _p=ROOT+'.github/workflows/'+_wf; _old=open(_p).read()
    assert f'# {_key}:start' in _old and f'# {_key}:end' in _old, '.github/workflows/'+_wf+f': the dropdown lost its "# {_key}:start" and "# {_key}:end" lines'
    _new=re.sub(rf'(          # {_key}:start\n).*?(          # {_key}:end\n)',lambda m:m.group(1)+''.join(f'          - {o}\n' for o in _opts)+m.group(2),_old,flags=re.S)
    if _new!=_old:
        assert not os.environ.get('CI'), '.github/workflows/'+_wf+': its dropdown differs from registry/tools.json; run python3 -I site/build.py and commit the result'
        open(_p,'w').write(_new); print('wrote the dropdown in .github/workflows/'+_wf)
# Docs, the prompt, the forms, the site's own text and every card except its history name only questions that exist.
for _f in sorted(set(glob.glob(ROOT+'*.md')+glob.glob(ROOT+'docs/*.md')+glob.glob(ROOT+'prompts/*.md')+glob.glob(ROOT+'rules/*.md')+glob.glob(ROOT+'authors/*/*.md')+glob.glob(ROOT+'.github/ISSUE_TEMPLATE/*.yml')+[ROOT+'site/shell.html'])):
    _bad=stale_refs(open(_f).read()); assert not _bad, _f[len(ROOT):]+': names questions that rules/scoring.yaml no longer has: '+', '.join(_bad)
for _c,_a in CARDS:
    _y=load_yaml(D+_c); _y.pop('history',None)
    _bad=stale_refs(yaml.safe_dump(_y,allow_unicode=True,width=10**6)); assert not _bad, 'cards/'+_c+': names questions that rules/scoring.yaml no longer has: '+', '.join(_bad)
assert len(SLUG)==sum(len(e['cards']) for e in REG.values()), 'registry/tools.json: a card is listed under two tools'
assert set(SLUG)=={f for f,_ in CARDS}, 'registry/tools.json: cards must match CARDS ('+', '.join(sorted(set(SLUG)^{f for f,_ in CARDS}))+')'
assert all(SLUG[f]==t for f,t in CARDS), 'CARDS: each card names its tool in registry/tools.json'
for s,e in REG.items():
    assert all(c.startswith(s+'-') for c in e['cards']), 'registry/tools.json: '+s+' lists a card of another tool'
    if e['github']: assert all('github.com/'+e['github']+')' in yaml.safe_load(open(D+c))['header']['GitHub'] for c in e['cards']), 'registry/tools.json: '+s+' GitHub differs from its card'
    # An MX Bikes tool has an "mxb-mods" entry, a GP Bikes tool a "gpb-mods" entry, never both.
    ks=[k for k,_ in SITES.values() if k in e]; assert len(ks)==1, 'registry/tools.json: '+s+' needs one of '+', '.join(k for k,_ in SITES.values())
    k=ks[0]; m=e[k]; pid=m['post']
    assert all(yaml.safe_load(open(D+c))['header']['Game']==next(g for g,v in SITES.items() if v[0]==k) for c in e['cards']), 'registry/tools.json: '+s+' has "'+k+'", but its card is for another game'
    assert pid or m.get('note'), 'registry/tools.json: '+s+' needs a '+k+' post or a note why not'
    if pid:
        assert bool(m.get('tied_by'))!=bool(m.get('confirmed')), 'registry/tools.json: '+s+' must say what ties post '+str(pid)+' to the tool ("tied_by"), or who confirmed it ("confirmed")'
        assert s in MM[k]['tools'] and MM[k]['tools'][s]['post']==pid, 'registry/'+k+'.json: '+s+' not fetched, run tools/mxbmods_fetch.py'
        assert MM[k]['tools'][s]['still_tied'] or m.get('confirmed'), 'registry/'+k+'.json: post '+str(pid)+' no longer holds "'+m['tied_by']+'"; check it and update registry/tools.json'
for k,_ in SITES.values():
    assert set(MM[k]['tools'])<={s for s,e in REG.items() if k in e and e[k]['post']}, 'registry/'+k+'.json: tools not in the registry, run tools/mxbmods_fetch.py'
GR={};HELDS={};rowsh=[];views=[];ALL=[];KA=[];PICK=[];PICKV=[];REG_FILE={};SHARE={};TOOLV=[]
# What the rules set on each card (the score, each area's score or Money label, what each answer costs, key marks, tags), to compare one scoring.yaml with another.
SET={}
for f,slug in CARDS:
    # A tool's newest card (the last in its registry list) is the tool's page, at #<tool> and <site>/<tool>/, in the tools list.
    # An earlier card (rule 2: it stays) keeps a page of its own at #<card file without .yaml>, which the newer cards link under
    # "Earlier reports" and every card of the tool lists under History, and its badges; it is left out of the list and the share
    # pages, and Compare offers it beside the newest, so two releases of one tool can be compared.
    older=REG[slug]['cards']; latest=older[-1]==f; older=older[:older.index(f)]
    a=slug if latest else f[:-len('.yaml')]
    CARD=load_yaml(D+f); C=check_card(f,CARD)
    name,ver,h,rows,V,HELDQ=C['name'],C['ver'],C['h'],C['rows'],C['A'],C['held']
    for label in ('In one line','Category','Author','Game',SITES[h['Game']][1],'Homepage','GitHub','Version analysed'): assert h.get(label), f+': no "'+label+'" row'
    one=h['In one line']; assert len(one)<=90, f+': "In one line" is longer than 90 characters'
    _miss=[o for o in older if '('+SITEURL+'#'+o[:-len('.yaml')]+')' not in h.get('Earlier reports','')]
    assert not _miss, f+': "Earlier reports" must link each earlier card of the tool, newest first, as [<version>]('+SITEURL+'#<card file without .yaml>): '+', '.join(_miss)
    text='\n'.join(strings(C['d']))
    assert 'mxb-facts/actions/runs/' not in text, f+': link each file\'s VirusTotal entry, not our lookup run (readers can\'t open it)'
    cat=h['Category']; assert cat in CATS, f+': category must be one of '+'; '.join(CATS)
    hb=h.get('Held back')
    # Rule 6: "Not allowed" answers, and so "Not scored", need the licence clause that forbids the analysis, quoted on the card.
    assert any(v=='NA' for _m,v in V.values())==bool(h.get('Licence clause')), f+': a card with "Not allowed" answers needs the "Licence clause" row, and only such a card has it'
    G=scored(V,HELDQ)
    gl=glance(V,G,HELDQ)
    ALL.append((name,a,rows,gl))
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
    KA.append((name,a,ka))
    _crit,_opt,_pos=tagsof(CARD)
    if latest: SHARE[a]=(name,ver,G,one,CARD)
    GR[a]=(name,ver,G,h.get('Analysed on') or '',slug,latest); HELDS[a]=HELDQ
    SET[f]={'score':{'score':gtext(G)},'areas':{ar:f'{x}' for ar,x in gl.items()},
            'answers':{q:f'costs {x[0]}'+(' (open)' if x[2] else '')+(f', counted with {x[1]}' if x[1] else '') for q,x in charges(V,HELDQ).items()},
            'keys':{k:MW[x[0]][1] or 'no mark' for k,x in ka.items()},
            'tags':sorted(l for l,_q in _crit)+sorted(l+' (off by default)' for l,_q in _opt)+sorted(l for l,_q in _pos)}
    # What the tools list sorts on: the name, the score (a tool without a number sorts last) and the analysis date. It is built
    # in the default order, by name, so the page reads the same before its script runs.
    _num=f'{G["score"]:.1f}' if G['kind']=='score' else ''
    _day=datetime.datetime.strptime(h['Analysed on'],'%d %b %Y').date().isoformat()
    if latest: rowsh.append((name.lower(),f'<li class="trow" data-cat="{cat}" data-t="{a}" data-name="{esc(name.lower())}" data-score="{_num}" data-date="{_day}">{score_html(G,a,'row').replace(f'href="#g-{a}"',f'href="#{a}"',1)}<a class="tl" href="#{a}"><span class="tn">{esc(name)}</span> <span class="tv">{esc(ver)}</span></a><span class="td">{inline(one)}</span><span class="ta">{byline(h["Author"])} · {cat}{" · "+CARD["header"]["Game"] if CARD["header"]["Game"]!="MX Bikes" else ""}</span><label class="tcmp"><input type="checkbox" data-cmp="{a}">Compare</label><div class="tfind">{tagrow(CARD,a,TAGCAP)}</div></li>'))
    if latest: PICK.append((cat,name,a))
    PICKV.append((cat,name,a,ver,len(REG[slug]['cards']),REG[slug]['cards'].index(f))); REG_FILE[a]=f
    newest='' if latest else f'<p class="maint"><strong>An earlier report.</strong> The newest card for this tool is <a href="#{slug}">{esc(name)} {esc(load_yaml(D+REG[slug]["cards"][-1])["version"])}</a>.</p>'
    TOOLV.append((C,a,slug,gl,tagrow(CARD,a),score_section(a,slug,latest,name,ver,G,GR[a][3],gl),CARD.get("by_maintainer",False),newest))
# The tool pages, once every card's score is known, since History lists every card of the tool with its score.
REL={f:(a,GR[a][1],GR[a][2],GR[a][3]) for f,_s in CARDS for a in [_s if REG[_s]['cards'][-1]==f else f[:-len('.yaml')]]}
for C,a,slug,gl,tg,gs,mt,nw in TOOLV: views.append(tool(C,a,slug,gl,history(C,a,REL),tg,gs,mt,nw))
used=[c for c in CATS if any(p[0]==c for p in PICK)]
filters='<button type="button" class="chip on" data-cat="">All <span>'+str(len(PICK))+'</span></button>'+''.join(f'<button type="button" class="chip" data-cat="{c}">{c} <span>{sum(1 for p in PICK if p[0]==c)}</span></button>' for c in used)
# One chip per tool, its newest release. A tool with several cards also has a chip for each earlier release, named with its
# version, which shows only while one of that tool's releases is ticked (or a link ticks it), so the picker stays one tool a chip.
picker=''.join(f'<div class="pkg"><span class="pkh">{c}</span><div class="pks">'+''.join(f'<label class="pk{" pkold" if i<n-1 else ""}" data-rel="{SLUG[REG_FILE[a]]}"'+(' hidden' if i<n-1 else '')+f'><input type="checkbox" id="pk-{a}" value="{a}"> {nm}'+(f' <span class="tv"{"" if i<n-1 else " hidden"}>{esc(v)}</span>' if n>1 else '')+'</label>' for _c,nm,a,v,n,i in sorted((p for p in PICKV if p[0]==c),key=lambda p:(p[1].lower(),-p[5])))+'</div></div>' for c in used) or '<p class="pending">No tool is analysed yet, so there is nothing to compare.</p>'
AREAS=[]
for i,ar,_ in QS:
    if ar not in AREAS: AREAS.append(ar)
# Each column names the tool and the release its card covers, since every card is pinned to one release.
mx=['<table class="mx"><thead><tr><th scope="col">Question</th>'+''.join(f'<th scope="col" data-t="{a}"><a href="#{a}">{n} <span class="tv">{esc(GR[a][1])}</span></a></th>' for n,a,_,_ in ALL)+'</tr></thead><tbody>']
def mxbar(sc,href,tip):
    # A score as a number and a bar, the same for the overall score and each area, so they compare at a glance.
    return f'<a class="mxbar" href="{href}" title="{esc(tip)}"><span class="av">{sc}</span><span class="at"><i style="width:{sc if isinstance(sc,int) else 0}%"></i></span></a>'
lev=[f'<tr class="mxarea"><th colspan="{len(ALL)+1}" scope="colgroup">Scores</th></tr>']
# The overall score as a bar like the areas below it; a tool without a score says why in words ("Not scored", "Signs of malware").
lev.append('<tr class="mxlev"><th scope="row">Score</th>'+''.join(f'<td data-t="{a}">'+(mxbar(sround(GR[a][2]['score']),f'#g-{a}',f'{n} · Score: {gtext(GR[a][2])}') if GR[a][2]['kind']=='score' else f'<a class="mxnone" href="#g-{a}">{gtext(GR[a][2])}</a>')+'</td>' for n,a,rows,gl in ALL)+'</tr>')
for ar in AREAN:
    cells=''
    for n,a,rows,gl in ALL:
        if ar in CONCERN:
            sc=gl[ar]; tip=f'{n} · {ar}: {sc}'
            cells+=f'<td data-t="{a}">{mxbar(sc,f"#r-{a}-{AREAK[ar]}",tip)}</td>'
        else: cells+=f'<td data-t="{a}">{money_html(gl[ar],f"#r-{a}-{AREAK[ar]}")}</td>'
    lev.append(f'<tr class="mxlev"><th scope="row">{ar}</th>{cells}</tr>')
mx.extend(lev)
# Each answer shows its verdict (Yes, No, Partly, ...) drawn as its mark: the colour and icon say Good, Note, Concern or Major,
# the tip names the mark, and a Concern keeps its cost. A question reads with its answer, as on the tool page.
VWORD={'Opt':'Yes, not by default','Req':'Yes, on request'}
for ar in AREAS:
    mx.append(f'<tr class="mxarea"><th colspan="{len(ALL)+1}" scope="colgroup">{ar}</th></tr>')
    for i,qa,qt in QS:
        if qa!=ar: continue
        cells=''
        for n,a,rows,_ in ALL:
            ans=rows[i]
            mk,v=verdict(ans)
            tip=(f'{n} · {i}: {qt}&#10;'+re.sub(r'<[^>]+>|\{.\} |`|\*\*','',ans)).replace('"','&quot;')
            if mk=='!':
                # A Concern shows as it does in the answer: "Concern", "Major", "Off by default" or "On request" (one scale on every view).
                A={q:verdict(rows[q]) for q in rows}
                ST=charges(A,HELDS[a]); sp=concern_span([i],A,ST,i[0])[1]
                m=re.match(r'<span class="mk ([^"]*)" title="[^"]*">(.*?)</span>',sp)
                # Its cost, as in the answer: "(−N)", "(±0)" when another answer of the same behaviour counts it.
                ch=ST.get(i); cost=f' ({"±0" if ch[1] else "−"+str(ch[0])})' if ch else ' (±0)' if v in ('Yes','No','Partly') and i in GCOST else ''
                cells+=f'<td data-t="{a}"><a class="mark {m.group(1)}" href="#q-{a}-{i}" title="{m.group(2)}: {tip}">{VWORD.get(v,v)}{cost}</a></td>'
                continue
            # Good or Note, as in the answer; with no mark, its grey state (Held back when a rule-9 item touches it), in words.
            st={'+':'good','~':'note'}[mk] if mk else {'NC':'held' if i in HELDS[a] else 'nc','NA':'na','DNA':'dna'}[v]
            word,cls=STATES[st][:2]
            cells+=f'<td data-t="{a}"><a class="mark {cls}" href="#q-{a}-{i}" title="{word}: {tip}">{VWORD.get(v,v) if mk else word}</a></td>'
        mx.append(f'<tr><th scope="row"><span class="qid">{i}</span> {qt}</th>{cells}</tr>')
mx.append('</tbody></table>')
# For authors: made from the rules, so it can't drift from them. The drop-in check is authors/mxb-facts-check/SKILL.md, pinned to this commit.
SKILLP='authors/mxb-facts-check/SKILL.md'
skill=open(ROOT+SKILLP).read()
assert skill.startswith('---\nname: mxb-facts-check\n') and '{{COMMIT}}' in skill, SKILLP+': the skill starts with its frontmatter and points at {{COMMIT}}'
skill=skill.replace('{{COMMIT}}',COMMIT)
AGENTSLINE='Before tagging a release, run the MXB Facts check in .claude/skills/mxb-facts-check/SKILL.md.'
# For authors, in the order an author needs it: what the site is, what earns Good, how to check before a release, and what to do once
# a card exists (the agent prompt, a re-check, a correction, the badge: all on the tool's own page, under "For the tool's author").
good=''.join(f'<details class="more"><summary>{esc(AREAN[n])} <span>{sum(qa==ar for _i,qa,_t in QS)} questions</span></summary><div class="tw"><table class="goodw"><thead><tr><th>Question</th><th>Good when</th></tr></thead><tbody>'+
             ''.join(f'<tr><td><span class="qid">{i}</span> {esc(qt)}</td><td>{esc(goodwhen(i))}</td></tr>' for i,qa,qt in QS if qa==ar)+'</tbody></table></div></details>' for n,ar in enumerate(AREAS))
authors=(f'<div class="intro"><p>MXB Facts answers the same questions about every tool, with evidence for each answer, from <a href="#prompt">a published prompt</a>. '
         f'The questions and the rules are public, so you can see what your tool would get, and change it if you want to, before anyone checks it. '
         f'Authors aren\'t told before a card is published, except about a security problem (rule 9); anyone, you included, can correct it afterwards (<a href="#rules">how a card is made</a>).</p></div>'
         f'<h3>What earns a Good answer</h3><p>The answer each question needs for a Good mark. A Note or a Concern can be the honest answer for what a tool is for: a mark says what a player should know, and what to change, if anything, is up to you. What each Concern costs is in <a href="#scores">the scores</a>.</p>{good}'
         f'<h3>Check your tool before you release</h3><ol class="flow">'
         f'<li><b>Add the check to your repository:</b> save it (unfold it below) as <code>.claude/skills/mxb-facts-check/SKILL.md</code> '
         f'(<a class="dl" download="SKILL.md" href="{SKILLP}">download it</a>). Claude Code picks it up as a skill; for other agents, add this line to <code>AGENTS.md</code> or <code>CLAUDE.md</code>:<pre><code id="agents-line">{esc(AGENTSLINE)}</code></pre></li>'
         f'<li><b>Ask your agent to run it</b> before a release. It follows our prompt, steps 1 to 5, with the rules pinned to one commit, and lists every answer that wouldn\'t be Good, with its evidence. It changes nothing on its own.</li></ol>'
         f'<details class="more"><summary>The check <span>{SKILLP.rsplit("/",2)[1]}/SKILL.md, pinned to commit {COMMIT[:12]}</span></summary><pre><code>{esc(skill)}</code></pre></details>'
         f'<p>Prefer the full run? Clone this repository, open Claude Code in it, paste <a href="#prompt">the analysis prompt</a> and stop after step 5, as the check does.</p>'
         f'<h3>Once your tool has a card</h3><p>Everything below is at the foot of your tool\'s page, under "For the tool\'s author".</p><ol class="flow">'
         f'<li><b>Go through it with your agent:</b> download the card and paste one prompt. Your agent follows each answer\'s evidence into your code; we don\'t suggest fixes.</li>'
         f'<li><b>Release, then <a href="{REPO}issues/new?template=analyse-tool.yml">request a re-check</a>.</b> The new release gets a new card; the old one stays.</li>'
         f'<li><b>Something wrong, missing, or context to add?</b> Use the comment icon beside any answer, Good ones included, or <a href="{CORRFORM}">comment on an answer</a> with its evidence; it is answered in public (<a href="#rules">how corrections work</a>).</li>'
         f'<li><b>Add the badge to your page:</b> your score in five styles, three of them drawn like shields.io badges, each pinned to the card\'s version (<a href="#scores">how scores are worked out</a>).</li></ol>')
# The icon in a tile in place of a score: a cross for signs of malware fills it, Not scored's stays small beside its words.
GICON={'malware':.42,'notscored':.3}
shell=open(ROOT+'site/shell.html').read()
# The page is a full HTML document and asks no other site for anything (fonts, scripts, images).
assert shell.startswith('<!doctype html>\n<html lang="en">\n<meta charset="utf-8">'), 'site/shell.html must start with the doctype, the language and the charset'
assert not re.search(r'<(link|script|img|iframe)\b[^>]*\b(href|src)="(https?:)?//',shell) and '@import' not in shell and 'url(http' not in shell, 'site/shell.html must not load anything from another site'
# The front page's legend: the marks, the grey states and the results in place of a score, each with its icon and meaning
# (STATES in rules.py), and the costs a Concern and a Major can have, from rules/scoring.yaml: a Concern costs less than the
# severe tier, a Major the severe tier or more (signs of malware, P9, has its own result).
_cs=sorted({c for q,x in GCOST.items() if q!=GSC['malware'] for c in (x.values() if isinstance(x,dict) else [x])})
_rng=lambda l:f'{l[0]}–{l[-1]} points' if len(l)>1 else f'{l[0]} points'
_lo=[c for c in _cs if c<GT['severe']]; _hi=[c for c in _cs if c>=GT['severe']]
assert _lo and _hi, 'rules/scoring.yaml: the legend needs costs below and at the severe tier'
def _chip(k): return state_html(k).replace('class="mk ','class="mark ',1)
# One line per mark or state, each with its meaning; a Concern and a Major also say what they cost.
_cost={'concern':f'In the default setup; costs {_rng(_lo)}','major':f'A major concern in the default setup; costs {_rng(_hi)}'}
def _rows(head,keys): return f'<li class="lgh">{head}</li>'+''.join(f'<li>{_chip(k)} <span>{_cost.get(k,STATES[k][3])}.</span></li>' for k in keys)
marks=(_rows("Each answer's mark",("good","note","concern","major"))
       +_rows('In grey: never a confirmed Concern',("off","req","dna","nc","held","na"))
       +_rows('In place of a score',("malware","notscored"))
       +'<li class="lgh">Tags and counts</li>')
# Every state's icon as a mask on its mark, so it takes the mark's colour (STATES in rules.py, drawings in site/icons.py); the
# grey "Not checked" and "Not allowed" tags of "Says vs does" and the result square use the same icons.
def _sel(cls): return '.'+'.'.join(cls.split())
iconcss=('.mark::before, .mk::before { flex: none } '
         +' '.join(f'.mark{_sel(c)}::before, .mk{_sel(c)}::before'
                   +f' {{ width: 11px; height: 11px; border-radius: 0; box-shadow: none; background: currentColor; -webkit-mask: {mask_url(ic)} center / contain no-repeat; mask: {mask_url(ic)} center / contain no-repeat }}'
                   for k,(_l,c,ic,_m) in STATES.items())
         # Then each tag's own icon (TAGICON in rules.py), after the states' so it wins over the colour's icon.
         +' '.join(f' .mark.ti.ti-{ic}::before {{ -webkit-mask: {mask_url(ic)} center / contain no-repeat; mask: {mask_url(ic)} center / contain no-repeat }}' for ic in TAGICON.values())
         +' '.join(f' .g-{k} .gicon {{ display: block; width: calc(var(--gs) * {GICON[k]}); height: calc(var(--gs) * {GICON[k]}); background: #fff; -webkit-mask: {mask_url(STATES[k][2])} center / contain no-repeat; mask: {mask_url(STATES[k][2])} center / contain no-repeat }}' for k in ('malware','notscored')))
# The icons' licence goes with them into the built page, as their licence asks.
shell=shell.replace('<meta charset="utf-8">','<meta charset="utf-8">\n<!--\n'+ICON_LICENCE+'-->',1)
# The site's icon: in the header drawn in the theme's colours (shell.html, .logo), and as the favicon in the accent and surface
# colours read from shell.html's light and dark themes, so the two can't drift apart.
_th=[dict(re.findall(r'--(accent|surface): (#[0-9a-f]{6})',x)) for x in re.findall(r'(?s)\n:root \{(.*?)\n\}|:root\[data-theme="dark"\] \{(.*?)\}',shell) for x in [x[0] or x[1]]]
assert len(_th)==2 and all(set(t)=={'accent','surface'} for t in _th), 'site/shell.html: the light and dark themes each need --accent and --surface'
shell=(shell.replace('{{FAVICON}}','data:image/svg+xml,'+quote(logo(_th[0]['accent'],_th[0]['surface'],_th[1]['accent'],_th[1]['surface']),safe=" =:/'.,-"))
       .replace('{{LOGO}}',f'<svg viewBox="-2 -2 28 28" {STROKE} stroke="currentColor">{LUCIDE["search-check"]}</svg>'))
# The footer names the commit the page was built from, linked on GitHub, so a reader can see exactly which rules and cards it shows.
shell=shell.replace('{{BUILD}}',f'<a href="{REPO}commit/{COMMIT}">{COMMIT[:12]}</a>')
# The legend's example tags show their own icons, like the tags they stand for.
shell=re.sub(r'\{\{TI:([^}]+)\}\}',lambda m:tagcls(m.group(1)),shell)
out=(shell.replace('{{ICONCSS}}',iconcss).replace('{{FILTERS}}',filters).replace('{{GNOTE}}',f'<small class="gnote">{GNOTE}</small>').replace('{{MARKS}}',marks).replace('{{PICKER}}',picker).replace('{{INDEX}}',('<ul class="tlist">'+''.join(h for _k,h in sorted(rowsh))+'</ul>') if rowsh else '<p class="pending">No tool is analysed yet. The first analyses are under way.</p>').replace('{{TOOLS}}','\n'.join(views))
     .replace('{{MATRIX}}',''.join(mx)).replace('{{TPL}}',tpl).replace('{{PROMPT}}',prm).replace('{{AUTHORS}}',authors))
assert '{{' not in out
# Every link inside the page (tags, Compare, key answers, the report's contents bar) lands on an anchor that exists, once.
_ids=re.findall(r'\bid="([^"]+)"',out)
assert len(_ids)==len(set(_ids)), 'two elements share an id: '+', '.join(sorted({i for i in _ids if _ids.count(i)>1}))
_dead=sorted({h for h in re.findall(r'href="#([^"]+)"',out)}-set(_ids))
assert not _dead, 'links to anchors that don\'t exist: '+', '.join(_dead)
os.makedirs(os.path.dirname(OUT),exist_ok=True)
open(OUT,'w').write(out)
# The files the page offers to download sit next to it: each card as it is in cards/ (rule 9: a card holds no held-back details,
# only its "Held back" row), and the For authors check with its commit filled in.
SITE=os.path.dirname(OUT)+'/'
# One badge per card (rules/scores.md, "Badge"), at badge/<tool>/<version>.svg and .json.
for _a,(_name,_ver,_G,_date,_t,_l) in GR.items():
    os.makedirs(SITE+'badge/'+_t,exist_ok=True)
    for _suf,_lab,_draw in BADGES: open(SITE+f'badge/{_t}/{_ver}{_suf}.svg','w').write(_draw(_G,btitle(_name,_ver,_G,_date),'')+'\n')
    open(SITE+f'badge/{_t}/{_ver}.json','w').write(badge_json(_ver,_G)+'\n')
# Every card's score and badges in one file, for a site that lists tools (such as a mods site) to show them by version.
os.makedirs(SITE+'api',exist_ok=True)
json.dump({'rubric':RUBRICV,'cards':[{'tool':_t,'name':_n,'version':_v,'page':f'{SITEURL}{_t}/' if _l else f'{SITEURL}#{_a}','score':gtext(_G),
           'number':None if _G['kind'] in ('notscored','malware') else sround(_G['score']),'open_answers':len(_G['open']),
           'areas':None if _G['kind'] in ('notscored','malware') else {ar:_G['areas'][ar][0] for ar in AREAN if ar in CONCERN},
           'analysed':_d,'badges':{(_suf or '-flat').lstrip('-'):f'{SITEURL}badge/{_t}/{_v}{_suf}.svg' for _suf,_x,_y in BADGES}}
          for _a,(_n,_v,_G,_d,_t,_l) in GR.items()]},open(SITE+'api/cards.json','w'),indent=1,ensure_ascii=False)
os.makedirs(SITE+'cards',exist_ok=True)
# Each tool's own address, for sharing: <site>/<tool>/ (page.share_page). A tool's anchor can't take a name the site uses for a folder.
assert not set(SHARE)&{'api','badge','cards','authors'}, 'a tool anchor is also a folder name of the site'
for _a,_x in SHARE.items():
    os.makedirs(SITE+_a,exist_ok=True)
    open(SITE+_a+'/index.html','w').write(share_page(_a,*_x))
for f,_a in CARDS: shutil.copyfile(D+f,SITE+'cards/'+f)
os.makedirs(os.path.dirname(SITE+SKILLP),exist_ok=True)
open(SITE+SKILLP,'w').write(skill)
print(f'wrote {os.path.relpath(OUT,ROOT)} ({len(out)} bytes)')
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
