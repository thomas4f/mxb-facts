"""The public data feed: api/v1/ (index.json, cards/<card>.json, match.json), made from the checked card data, never from the
raw YAML, so a reader shows exactly what the site shows and works out no mark, cost or score itself. Its contract is
docs/FEED.md; its shape is rules/feed.schema.json, which every file is checked against here.

Usage: from build.py, write_feed(SITE, CARDS) and write_site(SITE, skill, agents_line) after the cards are checked.
"""
import datetime, json, jsonschema, os, re, subprocess
from rules import (AREAK, AREAN, CATS, CONCERN, GCOST, GCOVER, GSC, GT, HEADER, HELD, KEYS, MDTXT, MLAB, MLEFT, PMEANS, QCELL, QIDS, QS, RUBRICV,
    SC, SCHEMA as CARD_SCHEMA, STATES, ans_md, concern_span, goodwhen, load_yaml, maxcost, money, qcost, scored, sround, state_of, tagsof, verdict, ROOT, D)
from cards import COMMIT, CORR, CORRFORM, REQFORM, SITEURL, FOLDNAME, LIMS, MM, REG, REPO, SITES, SLUG, check_card, correction_link, files_table, games, pending_versions
from badges import BADGES


FEED_VERSION='1.2'
SCHEMA=json.load(open(ROOT+'rules/feed.schema.json'))
# "What it says vs what it does": each verdict drawn in the style of the mark it reads like (STATES in rules.py), with its own
# words and meaning, since a verdict isn't a mark and costs nothing; T2 is the answer the score counts. A verdict may add words
# after its own ("Matches, as far as checked").
SAYS={'Matches':('good','What it does matches what its docs say'),'Partly':('note','Only part of what its docs say matches what it does'),
      "Doesn't match":('concern','What it does differs from what its docs say; T2 says whether that costs points'),
      'Not checked':('nc','Not checked; the evidence says why'),'Not allowed':('na','The licence forbids checking this')}
SAYSQ='T2'  # the answer the claims back: the key answer built from it counts them
assert SAYSQ in QIDS, 'rules/scoring.yaml: '+SAYSQ+', the answer "What it says vs what it does" backs, is gone; name the new one in SAYSQ (site/feed.py)'
assert set(SAYS)==set(re.match(r'\^\((.*?)\)',CARD_SCHEMA['$defs']['block']['oneOf'][3]['properties']['rows']['items']['properties']['Verdict']['pattern']).group(1).split('|')), 'card.schema.json: the "Says vs does" verdicts changed; give each one a mark and a meaning in SAYS (site/feed.py)'
# The feed's licence (docs/FEED.md, "Using the data"): the card data under CC BY 4.0, credited as MXB Facts with a link; the code
# that builds it is MIT. What a card quotes from a tool stays with that tool's owners.
LICENCE={'data':'CC-BY-4.0','name':'Creative Commons Attribution 4.0 International','url':'https://creativecommons.org/licenses/by/4.0/',
         'attribution':'MXB Facts (https://thomas4f.github.io/mxb-facts/)','code':'MIT',
         'note':"What a card quotes from a tool (its README, strings, files) stays with that tool's owners."}

def says_word(v):
    # The verdict a "Says vs does" row starts with (SAYS); it may add words after its own ("Matches, as far as checked").
    w=next((w for w in SAYS if v==w or v.startswith(w+',')),None)
    assert w, 'a "What it says vs what it does" verdict must start with '+', '.join(SAYS)+': '+v
    return w

def answer_state(i,A,SETS,held):
    # One answer's state as every view shows it (STATES in rules.py): Good, Note, a Concern as concern_span draws it (Concern,
    # Major, Off by default, On request, Signs of malware), or a grey state. Every page shows it from the feed.
    if A[i][0]=='!': return state_of(concern_span([i],A,SETS,i[0])[1])
    if A[i][0]: return {'+':'good','~':'note'}[A[i][0]]
    return {'NC':'held' if i in held else 'nc','NA':'na','DNA':'dna'}[A[i][1]]
def answer_cost(i,A,SETS):
    # What the answer takes off its area, as its line shows it: (cost, counted with, open). 0 when another answer of the same
    # behaviour counts it, or a covered or waived cost; an open answer at its highest cost.
    ch=SETS.get(i)
    if ch: return (0 if ch[1] else ch[0]),ch[1],ch[2]
    cov=next((w for w in GCOVER.get(i,()) if A[w][0]=='!' and A[w][1] in ('Yes','No','Partly')),None)
    return 0,cov,False

AREA_ID={ar:AREAK[ar] for ar in AREAN}
QAREA={i:AREA_ID[a] for i,a,_t in QS}
VWORD={'Opt':'Yes, not by default','Req':'Yes, on request','NC':'Not checked','NA':'Not allowed','DNA':"Doesn't apply"}

def plain(md):
    # Markdown to plain text for lists and apps: links keep their words, code its text, bold goes.
    t=re.sub(r'\[([^\]]+)\]\([^)]+\)',r'\1',md or '')
    t=re.sub(r'`([^`]*)`',r'\1',t)
    return re.sub(r'\*\*|__','',t).strip()

def iso(day): return datetime.datetime.strptime(day,'%d %b %Y').date().isoformat()

# The site's own words (site/content.yaml): the lede, rule 8's AI note, the maintainer's notice, what Under review means and How a card is made.
CONTENT=load_yaml(ROOT+'site/content.yaml')
assert CONTENT['heading_accent'] in CONTENT['heading'], 'site/content.yaml: heading_accent must be a word of heading'

def ai_note(text=None):
    # Rule 8's words as plain text, for apps: the first two sentences of the site's AI note.
    return ' '.join(x.strip() for x in re.findall(r'[^.]+\.',plain(text or CONTENT['ai_note']))[:2])

def check(obj,kind):
    jsonschema.validate(obj,{**SCHEMA,'$ref':'#/$defs/'+kind})
    # Markdown with https links only: no link a consumer would resolve against its own site.
    assert not re.search(r'\]\((?!https://)',json.dumps(obj,ensure_ascii=False)), kind+': a link in the feed is not https://'
    # A reference-style link definition ("[ref]: address" on a line of its own) is refused too: its address isn't checked above.
    assert not re.search(r'(^|\\n)[\s>*+\-\d.]*\[[^\]]+\]:\s*\S',json.dumps(obj,ensure_ascii=False)), kind+': a reference-style link in the feed'

def key_state(k):
    # A key answer's state: its mark, a Concern as the site draws it (Major, Off by default, On request, Signs of malware), or a grey state.
    mk,_h,ans,span=k
    if mk=='!': return state_of(span)
    if mk: return {'+':'good','~':'note'}[mk]
    return 'held' if ans.startswith('Held back') else 'na' if ans.startswith('Not allowed') else 'nc'

def result(G,A,held,hb):
    # The score block: kind, number, every area by id, the Money label, open answers and what is held back (rule 9: the number
    # of items and the questions, as the card's "Held back" row gives them, nothing more).
    num=G['kind']=='score'; m=re.match(HELD,hb) if hb else None
    return {'kind':G['kind'],'score':sround(G['score']) if num else None,
            'label':{'malware':'Signs of malware','notscored':'Not scored'}.get(G['kind'],f'{sround(G["score"])} / 100'),
            'areas':{AREA_ID[ar]:(G['areas'][ar][0] if num else None) for ar in CONCERN},
            'money':money(A,held),'open_questions':G['open'],'why':G['why'],
            'held_back':{'items':int(m.group(1)) if m else 0,'questions':sorted(held)}}

# The header rows a tool's page shows at its top (facts()); the rest are its "Release and method" table.
TOP=('In one line','What it is','Category','Author','Game','mxb-mods.com','gpb-mods.com','Homepage','GitHub','Version analysed','Analysed on','Earlier reports')
CKINDS={'correction':'Correction','missing':'Something missing','context':"Author's context"}

def short(v):
    # A header row's first clause, without asides in brackets; the whole row stays in "Release and method".
    d=0
    for m in re.finditer(r'[()]|(?<!\w\.\w)\. |; ',v):
        t=m.group()
        if t=='(': d+=1
        elif t==')': d=max(d-1,0)
        elif d==0: v=v[:m.start()]; break
    return re.sub(r' \((?![^()]*\]\()[^()]*\)','',v).strip()

def facts(h,slug):
    # The facts at the top of a tool's page, in order, as Markdown. A mods site shows its address, never the page's own title (author text).
    gs=games(h); out=[{'label':'Games' if len(gs)>1 else 'Game','text':', '.join(gs)}]
    for label in ('Version analysed','Category','Author',*(SITES[g][1] for g in gs),'Homepage','GitHub','Analysed on'):
        v=h.get(label); k=next((k for k,ms in SITES.values() if ms==label),None)
        if k and slug in MM[k]['tools']: v=f'[{re.sub(r"^https?://(www\.)?|/$","",MM[k]["tools"][slug]["link"])}]({MM[k]["tools"][slug]["link"]})'
        if v: out.append({'label':{'Version analysed':'Version'}.get(label,label),'text':short(v)})
    return out

def rule_note(i,row,state):
    # Where a mark depends on a condition ("Concern; Note if ..."), the rule, but only when its condition set the mark: the
    # answer's mark isn't the first one the rule names (a Major is a Concern at the severe cost). Where Partly has its own
    # meaning, that. The full rule is on the How it works page either way.
    mv=re.match(r'\{.\} (Yes|No)\b',row); rule=QCELL[i].get(mv.group(1)) if mv else None
    if re.match(r'\{.\} Partly\b',row) and PMEANS.get(i): return f'Partly here means: {PMEANS[i]}.'
    if not (rule and ' if ' in rule and not rule.endswith('Note if only on request')): return None
    first=rule.split(';')[0].strip().lower()
    if state not in ('good','note','concern','major') or state==first or (state,first)==('major','concern'): return None
    return f'Marked by the rule: {rule}.'

def cost_note(i,A,SETS):
    # Why an answer's cost is what it is, in words, where the number alone doesn't say: null, or one line.
    ch=SETS.get(i)
    if ch: return f'Counted with {ch[1]}: the same behaviour' if ch[1] else 'Open: it counts at its highest cost until it is answered' if ch[2] else None
    if A[i][0]=='!' and A[i][1] in ('Yes','No','Partly') and i in GCOST:
        cov=next((w for w in GCOVER.get(i,()) if A[w][0]=='!' and A[w][1] in ('Yes','No','Partly')),None)
        return f'Counted with {cov}: the same behaviour' if cov else 'Costs nothing: the release is traced to public source'
    return None


def changes_since(f,card,A1):
    # What changed since the tool's previous card (registry order is oldest first): each answer whose verdict or mark moved,
    # each area score that moved, and the overall score. None for a tool's first card.
    lst=REG[SLUG[f]]['cards']; i=lst.index(f)
    if i==0: return None
    old=load_yaml(D+lst[i-1])
    # Each side as the answer's own mark draws it (state, verdict, cost), so a change reads like the answers on the page.
    def marks(g,c):
        C=check_card(g,c); A,S=C['A'],C['SETS']
        return {q:{'state':answer_state(q,A,S,C['held']),'verdict':VWORD.get(A[q][1],A[q][1]),'cost':answer_cost(q,A,S)[0],'cost_note':cost_note(q,A,S)} for q in QIDS if q in A}
    M0,M1=marks(lst[i-1],old),marks(f,card)
    asked={'state':'dna','verdict':'Not asked','cost':0,'cost_note':''}
    rows=[{'question':q,'from':M0.get(q,asked),'to':M1[q]} for q in QIDS if M0.get(q,asked)!=M1[q]]
    A0={q:verdict(ans_md(old['answers'][q])) for q in QIDS if q in old['answers']}
    try: G0=scored(A0)
    except (KeyError,AssertionError): G0=None
    G1=scored(A1)
    areas=[{'area':AREA_ID[ar],'from':G0['areas'][ar][0],'to':G1['areas'][ar][0]} for ar in G1['areas'] if G0 and ar in G0['areas'] and G0['areas'][ar][0]!=G1['areas'][ar][0]]
    return {'card':lst[i-1][:-len('.yaml')],'version':old['version'],'answers':rows,'areas':areas,'unchanged':len(QIDS)-len(rows)}

def author_prompt(f,name,ver):
    # The one prompt every author gets for their card: no fixes of ours, the rules pinned to the commit the page was built from.
    return (f'This is the MXB Facts card for {name} {ver} ({f}): one release of this tool, answered against the same questions as every other tool, '
            f'with evidence for each answer. Go through every answer whose mark isn\'t "Good", and those without a mark ("Not checked"). For each one, '
            f'follow its evidence to the code or file it points at in this repository and explain to me what causes that answer. Don\'t change anything yet: '
            f'we\'ll decide together what to change, if anything, because that depends on what the tool is for. The questions, the rules behind each mark and what each Concern costs '
            f'are rules/questions.md, rules/template.md and rules/scores.md in {REPO.rstrip("/")} at commit {COMMIT}.')

def legend():
    # What a Concern and a Major cost, from rules/scoring.yaml: a Concern costs less than the severe tier, a Major the severe tier or more.
    cs=sorted({c for q,x in GCOST.items() if q!=GSC['malware'] for c in (x.values() if isinstance(x,dict) else [x])})
    lo=[c for c in cs if c<GT['severe']]; hi=[c for c in cs if c>=GT['severe']]
    assert lo and hi, 'rules/scoring.yaml: the legend needs costs below and at the severe tier'
    rng=lambda l:f'{l[0]}–{l[-1]} points' if len(l)>1 else f'{l[0]} points'
    return {'concern':f'In the default setup; costs {rng(lo)}','major':f'A major concern in the default setup; costs {rng(hi)}'}

def add(d,k,v):
    if v not in d.setdefault(k,[]): d[k].append(v)

def write_feed(SITE,CARDS):
    # The commit's date, not the clock, so the same commit always writes the same files.
    when=subprocess.run(['git','-C',ROOT,'log','-1','--format=%cI'],capture_output=True,text=True).stdout.strip() or '1970-01-01T00:00:00+00:00'
    base={'feed_version':FEED_VERSION,'built_at':when,'commit':COMMIT,'rubric':RUBRICV,'licence':LICENCE}
    note=ai_note()
    out=SITE+'api/v1/'; os.makedirs(out+'cards',exist_ok=True)
    tools={}; found={'github':{},'mods_post':{},'sha256':{}}
    for f,slug in CARDS:
        raw=load_yaml(D+f); C=check_card(f,raw); d=C['d']; h=C['h']; A=C['A']; held=C['held']; SETS=C['SETS']
        G=scored(A,held); crit,opt,pos=tagsof(raw)
        cid=f[:-len('.yaml')]; order=REG[slug]['cards']; latest=order[-1]==f
        # The newest card's page is the tool's own address; an earlier card's is a page of its own under it, named by its version.
        page=f'{SITEURL}{slug}/' if latest else f'{SITEURL}{slug}/{C["ver"]}/'
        assert re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*',C['ver']), f+': the version must be usable as a folder name for its page'
        res=result(G,A,held,h.get('Held back'))
        ans=[]
        for i,_a,qt in QS:
            v=A[i][1]; x=d['answers'][i]; cost,cw,op=answer_cost(i,A,SETS); st=answer_state(i,A,SETS,held)
            ans.append({'id':i,'area':QAREA[i],'question':qt,'verdict':VWORD.get(v,v),'state':st,
                        'cost':cost,'counted_with':cw,'open':op,'cost_note':cost_note(i,A,SETS),'rule_note':rule_note(i,C['rows'][i],st),
                        'text':x['text'],'text_plain':plain(x['text']),
                        # A held-back answer's evidence is published with the details (rule 9), as its line on the card says.
                        'evidence':'Published with the details.' if st=='held' else x['evidence'],
                        'limits':[n+1 for n in LIMS.get(f,{}).get(i,[])],'under_review':CORR.get(f,{}).get(i,[]),
                        'comment':correction_link(C['name']+' '+C['ver'],i,C['rows'][i]),
                        **({'second_check':x['second_check']} if 'second_check' in x else {})})
        # The key answer the claims back (SAYSQ) counts them, so a reader can go through them one by one.
        nclaims=sum(len(b['rows']) for x in d['sections'] if x['title']=='What it says vs what it does' for b in x['blocks'] if 'Verdict' in b.get('table',[]))
        key=[{'id':k,'question':q,'short':s,'from':src,'state':key_state(C['key'][k]),'text':C['key'][k][2],'text_plain':plain(C['key'][k][2]),
              **({'claims':nclaims} if SAYSQ in src and nclaims else {})} for k,q,s,src in KEYS]
        # Concern tags go costliest first (ties keep the tag table's order); one at the severe cost or more is a Major, like its answer's mark.
        cost=lambda q:qcost(q,raw['answers'][q]['verdict']) or maxcost(q)  # noqa: B023 (used at once, for this card)
        crit=sorted(crit,key=lambda t:-cost(t[1]))
        tags=([{'label':l,'kind':'concern','question':q,'major':cost(q)>=GT['severe']} for l,q in crit]+[{'label':l,'kind':'off_by_default','question':q} for l,q in opt]
              +[{'label':l,'kind':'positive','question':q} for l,q in pos])
        # The tool's page on each of its games' mods sites, where one is tied to it.
        reg=REG[slug]
        mods=[{'site':ms,'post':reg[k]['post'],'url':MM[k]['tools'].get(slug,{}).get('link')} for k,ms in SITES.values() if k in reg and reg[k]['post']]
        badges={(suf or '-flat').lstrip('-'):f'{SITEURL}badge/{slug}/{C["ver"]}{suf}.svg' for suf,_x,_y in BADGES}
        # The card as one image (site/preview.py, the page's link preview), pinned to this release beside its badges.
        image=f'{SITEURL}badge/{slug}/{C["ver"]}-card.png'
        vt={r[2].strip('`'):r[3] for r in files_table(f,raw)}
        files=[{'name':x['name'],'sha256':x['sha256'],'note':x.get('note',''),'inside':x.get('inside'),'virustotal':vt[x['sha256']]} for x in raw['files']]
        hist=[{'date':x['date'],'date_iso':iso(x['date']),'change':x['change']} for x in raw.get('history',[])]
        card={**base,'ai_note':note,'card':cid,'tool':slug,'name':C['name'],'version':C['ver'],'latest':latest,'games':games(h),'category':h['Category'],
              'summary':plain(h['In one line']),'author':REG[slug]['author'],'analysed':h['Analysed on'],'analysed_iso':iso(h['Analysed on']),'method':h['Method'],
              'page':page,'yaml':f'{SITEURL}cards/{f}','badges':badges,'card_image':image,'result':res,'tags':tags,'files':files,
              'key_answers':key,'answers':ans,'sections':sections_out(d['sections']),'history':hist,'corrections':raw.get('corrections',[]),
              'facts':facts(h,slug),'header':[{'label':k,'text':h[k]} for k in HEADER if k in h and k not in TOP],'files_note':raw.get('files_note',''),
              'areas':[{'id':AREA_ID[ar],'name':ar,'summary':d['areas'][ar]} for ar in AREAN],
              'changes_since':changes_since(f,raw,A),'by_maintainer':bool(raw.get('by_maintainer')),'author_prompt':author_prompt(f,C['name'],C['ver'])}
        check(card,'card')
        json.dump(card,open(out+f'cards/{cid}.json','w'),indent=1,ensure_ascii=False)
        rel={'version':C['ver'],'card':cid,'analysed':h['Analysed on'],'analysed_iso':iso(h['Analysed on']),'kind':res['kind'],'score':res['score'],
             'page':page,'json':f'{SITEURL}api/v1/cards/{cid}.json','card_image':image}
        # card_image: the tool's newest card as one image, at an address that never changes, for a page that shows the tool, not
        # one release (docs/FEED.md, "Showing a card").
        t=tools.setdefault(slug,{'id':slug,'name':C['name'],'author':reg['author'],'games':games(h),'github':reg['github'],'homepage':reg['homepage'],
                                 'mods_sites':mods,'card_image':f'{SITEURL}badge/{slug}/card.png','releases':[None]*len(order)})
        # Newest release first, in the registry's order (rule 2: every card stays).
        t['releases'][len(order)-1-order.index(f)]=rel
        # How many answers are still open, by why, and how many comments are under review: the counts the tools list shows beside the tags.
        counts={k:sum(1 for x in ans if x['state']==k) for k in ('nc','na','held')}|{'under_review':sum(1 for c in raw.get('corrections',[]) if c['status']=='open' and c.get('kind')!='context')}
        if latest: t.update({'games':games(h),'category':h['Category'],'summary':plain(h['In one line']),'page':page,'latest':{**rel,'result':res,'tags':tags,'badges':badges,'counts':counts}})
        if reg['github']: add(found['github'],reg['github'].lower(),slug)
        for k,_ in SITES.values():
            if k in reg and reg[k]['post']: add(found['mods_post'],f'{k}:{reg[k]["post"]}',slug)
        for x in files: add(found['sha256'],x['sha256'],{'tool':slug,'card':cid,'version':C['ver'],'latest':latest,'file':x['name'],'inside':x['inside'],'note':x['note']})
    # Releases the weekly inventory has seen that are newer than the tool's newest card and have none yet, as published
    # (cards.pending_versions, as the "Not analysed yet" badges): the newest card image says so.
    rel_seen=json.load(open(ROOT+'registry/releases.json'))['tools']
    for slug,t in tools.items():
        src=rel_seen.get(slug,{}); pub={x.get('version') for x in src.values() if isinstance(x,dict)}
        t['not_analysed']=[v for v in pending_versions({r['version'] for r in t['releases']},max(r['analysed_iso'] for r in t['releases']),src) if v in pub]
    index={**base,'site':SITEURL,'ai_note':note,
           'areas':[{'id':AREA_ID[ar],'name':ar,'scored':ar in CONCERN} for ar in AREAN],
           'states':[{'id':k,'label':l,'meaning':m,'icon':i} for k,(l,_c,i,m) in STATES.items()],
           'money':[{'label':l,'means':x['means'],'grey':l in MLEFT} for l,x in MLAB.items()],
           'categories':[c for c in CATS if any(t['category']==c for t in tools.values())],
           'says_question':SAYSQ,'legend':legend(),'correction_kinds':CKINDS,'links':{'comment':CORRFORM,'recheck':REQFORM,'repo':REPO},
           'tags':[{'label':x['tag'],'question':x['from'],'answer':x['answer'],'kind':x['kind'].lower(),'icon':x.get('icon')} for x in SC['tags'] if x['kind']!='None'],
           'tools':sorted(tools.values(),key=lambda t:t['name'].lower())}
    check(index,'index')
    json.dump(index,open(out+'index.json','w'),indent=1,ensure_ascii=False)
    m={**base,**found}; check(m,'match')
    json.dump(m,open(out+'match.json','w'),indent=1,ensure_ascii=False)
    os.makedirs(out+'schema',exist_ok=True); json.dump(SCHEMA,open(out+'schema/feed.schema.json','w'),indent=1)
    return index

def sections_out(secs):
    # The report sections as the card has them, plus the state each "Says vs does" verdict is drawn as on the site (page.SAYS),
    # so a reader of the feed never has to map the words itself.
    out=[]
    for sec in secs:
        bl=[]
        for b in sec['blocks']:
            if 'Verdict' in b.get('table',[]):
                b={**b,'rows':[{**r,'verdict_state':SAYS[says_word(r['Verdict'])][0]} for r in b['rows']]}
            # An area's tables fold under a name that says what they list ("Connections found").
            elif 'table' in b and tuple(b['table']) in FOLDNAME: b={**b,'name':FOLDNAME[tuple(b['table'])]}
            bl.append(b)
        out.append({**sec,'blocks':bl})
    return out

def doc(md,path):
    # One of the repository's Markdown files for the feed: relative links pinned to the build's commit, the generated-table markers gone.
    d=os.path.dirname(path)
    def link(m):
        u=m.group(2)
        if u.startswith(('https://','#')): return m.group(0)
        f,_,a=u.partition('#'); full=os.path.normpath(os.path.join(d,f))
        return f'{m.group(1)}({REPO}blob/{COMMIT}/{full}{"#"+a if a else ""})'
    return re.sub(r'(\[[^\]]+\])\(([^)\s]+)\)',link,re.sub(r'<!--.*?-->\n?','',md,flags=re.S))

def sections(md):
    # A Markdown file as [{title, text}] by its "## " headings; the text before the first one is "".
    parts=re.split(r'^## (.+)$',re.sub(r'^# .*\n','',md),flags=re.M)
    out=[{'title':'','text':parts[0].strip()}] if parts[0].strip() else []
    return out+[{'title':parts[i].strip(),'text':parts[i+1].strip()} for i in range(1,len(parts),2)]

def closed_cap():
    # The highest score a closed-source tool can reach (the tools list says it): every area 100 but Transparency, which loses
    # T1's cost (T3, T4, T6 and T7 are counted with it or covered by it), weighted as the score is.
    t=100-maxcost('T1'); avg=(100*(len(CONCERN)-1)+t)/len(CONCERN); lw=GSC['lowest_weight']
    return sround((1-lw)*avg+lw*t)

def write_site(SITE,skill,agents_line):
    # The site's own text and rules, so a design can draw How it works and For authors from data, like the tools.
    when=subprocess.run(['git','-C',ROOT,'log','-1','--format=%cI'],capture_output=True,text=True).stdout.strip() or '1970-01-01T00:00:00+00:00'
    base={'feed_version':FEED_VERSION,'built_at':when,'commit':COMMIT,'rubric':RUBRICV,'licence':LICENCE}
    prm=open(ROOT+'prompts/analyse-tool.md').read()
    assert '\n## The prompt\n' in prm, 'prompts/analyse-tool.md: no "## The prompt" section'
    # The drop-in check, CLAUDE.md and the For authors page say "steps 1 to 5" (analyse and run, no card) and "skip step 6"
    # (VirusTotal): renumbering the prompt must update them too.
    assert re.search(r'^5\. Run it',prm,re.M) and re.search(r'^6\. Look up the hashes on VirusTotal',prm,re.M), 'prompts/analyse-tool.md: step 5 must be running the tool and step 6 the VirusTotal lookup, as SKILL.md, CLAUDE.md and the For authors page say; update them if the steps move'
    data={**base,'site':SITEURL,'repo':REPO,
          'heading':CONTENT['heading'],'heading_accent':CONTENT['heading_accent'],'lede':CONTENT['lede'],'ai_note':CONTENT['ai_note'],'ai_short':CONTENT['ai_short'],'maintainer_notice':CONTENT['maintainer_notice'],'under_review':CONTENT['under_review'],'tags_legend':CONTENT['tags'],
          'how_a_card_is_made':CONTENT['how_a_card_is_made'],'closed_cap':closed_cap(),
          'template':sections(doc(MDTXT['template.md'],'rules/template.md')),
          'scores':sections(doc(MDTXT['scores.md'],'rules/scores.md')),
          'prompt':{'intro':sections(doc(prm.split('\n## The prompt\n',1)[0],'prompts/analyse-tool.md')),'text':doc('## The prompt\n'+prm.split('\n## The prompt\n',1)[1],'prompts/analyse-tool.md')},
          'questions':[{'id':i,'area':QAREA[i],'question':qt,'good_when':goodwhen(i),'marks':QCELL[i],'max_cost':maxcost(i) if i in GCOST else 0} for i,_a,qt in QS],
          'key_questions':[{'id':k,'question':q,'short':s,'from':src} for k,q,s,src in KEYS],
          'authors_check':{'path':'.claude/skills/mxb-facts-check/SKILL.md','download':SITEURL+'authors/mxb-facts-check/SKILL.md','text':skill,'agents_line':agents_line},
          'links':{'request':REQFORM,'question':REPO+'issues/new?template=question.yml','comment':REPO+'issues/new?template=correction.yml','source':REPO[:-1],'conflict':REPO[:-1]+'#conflict-of-interest','maintainer':'https://github.com/thomas4f','support':'https://ko-fi.com/thomas4f'}}
    check(data,'site')
    json.dump(data,open(SITE+'api/v1/site.json','w'),indent=1,ensure_ascii=False)
